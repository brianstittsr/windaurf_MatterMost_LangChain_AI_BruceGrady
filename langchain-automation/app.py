#!/usr/bin/env python3
"""
LangChain Automation Platform for Mattermost
A workflow automation system using LangChain for AI-powered automations
"""

import os
import json
import uuid
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum

from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_socketio import SocketIO, emit, join_room, leave_room
import aiohttp
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.agents import initialize_agent, AgentType, Tool
from langchain.memory import ConversationBufferMemory
from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain.tools import BaseTool
from langchain.callbacks.base import BaseCallbackHandler
from langchain.chains import LLMChain, SequentialChain
from langchain.prompts import PromptTemplate, ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser, OutputFixingParser
from pydantic import BaseModel, Field
import requests
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'langchain-automation-secret')
socketio = SocketIO(app, cors_allowed_origins="*")

# Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
MATTERMOST_URL = os.getenv('MATTERMOST_URL', 'http://mattermost:8000')
MATTERMOST_TOKEN = os.getenv('MATTERMOST_TOKEN')
DATABASE_PATH = os.getenv('DATABASE_PATH', 'workflows.db')

# Initialize LangChain components
llm = ChatOpenAI(
    openai_api_key=OPENAI_API_KEY,
    model_name=os.getenv('OPENAI_MODEL', 'gpt-4'),
    temperature=float(os.getenv('TEMPERATURE', '0.7'))
)

class WorkflowStatus(Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"
    COMPLETED = "completed"

class NodeType(Enum):
    TRIGGER = "trigger"
    ACTION = "action"
    CONDITION = "condition"
    AI_AGENT = "ai_agent"
    TRANSFORM = "transform"
    OUTPUT = "output"

@dataclass
class WorkflowNode:
    id: str
    type: NodeType
    name: str
    config: Dict[str, Any]
    position: Dict[str, int]
    connections: List[str] = None
    
    def __post_init__(self):
        if self.connections is None:
            self.connections = []

@dataclass
class Workflow:
    id: str
    name: str
    description: str
    nodes: List[WorkflowNode]
    status: WorkflowStatus
    created_at: datetime
    updated_at: datetime
    created_by: str
    team_id: str
    trigger_config: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.trigger_config is None:
            self.trigger_config = {}

class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Workflows table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS workflows (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                nodes TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
                created_by TEXT,
                team_id TEXT,
                trigger_config TEXT
            )
        ''')
        
        # Workflow executions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS workflow_executions (
                id TEXT PRIMARY KEY,
                workflow_id TEXT NOT NULL,
                status TEXT NOT NULL,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                input_data TEXT,
                output_data TEXT,
                error_message TEXT,
                FOREIGN KEY (workflow_id) REFERENCES workflows (id)
            )
        ''')
        
        # Workflow logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS workflow_logs (
                id TEXT PRIMARY KEY,
                execution_id TEXT NOT NULL,
                node_id TEXT,
                level TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp TIMESTAMP,
                data TEXT,
                FOREIGN KEY (execution_id) REFERENCES workflow_executions (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_workflow(self, workflow: Workflow):
        """Save workflow to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO workflows 
            (id, name, description, nodes, status, created_at, updated_at, created_by, team_id, trigger_config)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            workflow.id,
            workflow.name,
            workflow.description,
            json.dumps([asdict(node) for node in workflow.nodes]),
            workflow.status.value,
            workflow.created_at,
            workflow.updated_at,
            workflow.created_by,
            workflow.team_id,
            json.dumps(workflow.trigger_config)
        ))
        
        conn.commit()
        conn.close()
    
    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Get workflow by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM workflows WHERE id = ?', (workflow_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            nodes_data = json.loads(row[3])
            nodes = [WorkflowNode(**node_data) for node_data in nodes_data]
            
            return Workflow(
                id=row[0],
                name=row[1],
                description=row[2],
                nodes=nodes,
                status=WorkflowStatus(row[4]),
                created_at=datetime.fromisoformat(row[5]),
                updated_at=datetime.fromisoformat(row[6]),
                created_by=row[7],
                team_id=row[8],
                trigger_config=json.loads(row[9]) if row[9] else {}
            )
        return None
    
    def list_workflows(self, team_id: str = None) -> List[Workflow]:
        """List all workflows, optionally filtered by team"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if team_id:
            cursor.execute('SELECT * FROM workflows WHERE team_id = ? ORDER BY updated_at DESC', (team_id,))
        else:
            cursor.execute('SELECT * FROM workflows ORDER BY updated_at DESC')
        
        rows = cursor.fetchall()
        conn.close()
        
        workflows = []
        for row in rows:
            nodes_data = json.loads(row[3])
            nodes = [WorkflowNode(**node_data) for node_data in nodes_data]
            
            workflows.append(Workflow(
                id=row[0],
                name=row[1],
                description=row[2],
                nodes=nodes,
                status=WorkflowStatus(row[4]),
                created_at=datetime.fromisoformat(row[5]),
                updated_at=datetime.fromisoformat(row[6]),
                created_by=row[7],
                team_id=row[8],
                trigger_config=json.loads(row[9]) if row[9] else {}
            ))
        
        return workflows

# Initialize database
db = DatabaseManager(DATABASE_PATH)

class MattermostCallbackHandler(BaseCallbackHandler):
    """Custom callback handler for LangChain to send updates to Mattermost"""
    
    def __init__(self, channel_id: str, execution_id: str):
        self.channel_id = channel_id
        self.execution_id = execution_id
        self.session = None
    
    async def init_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession()
    
    async def send_message(self, message: str):
        """Send message to Mattermost channel"""
        await self.init_session()
        
        url = f"{MATTERMOST_URL}/api/v4/posts"
        headers = {
            'Authorization': f'Bearer {MATTERMOST_TOKEN}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'channel_id': self.channel_id,
            'message': f"🤖 **Workflow Update**: {message}"
        }
        
        try:
            async with self.session.post(url, headers=headers, json=payload) as response:
                if response.status != 201:
                    logger.error(f"Failed to send message: {response.status}")
        except Exception as e:
            logger.error(f"Error sending message: {e}")
    
    def on_chain_start(self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs):
        """Called when a chain starts running"""
        asyncio.create_task(self.send_message(f"Starting workflow step: {serialized.get('name', 'Unknown')}"))
    
    def on_chain_end(self, outputs: Dict[str, Any], **kwargs):
        """Called when a chain ends"""
        asyncio.create_task(self.send_message("Workflow step completed successfully"))
    
    def on_chain_error(self, error: Exception, **kwargs):
        """Called when a chain errors"""
        asyncio.create_task(self.send_message(f"Workflow step failed: {str(error)}"))

class MattermostTool(BaseTool):
    """Custom LangChain tool for Mattermost interactions"""
    
    name = "mattermost_tool"
    description = "Send messages, create posts, and interact with Mattermost"
    
    def _run(self, action: str, **kwargs) -> str:
        """Execute Mattermost action"""
        if action == "send_message":
            channel_id = kwargs.get('channel_id')
            message = kwargs.get('message')
            return self._send_message(channel_id, message)
        elif action == "get_channel_info":
            channel_id = kwargs.get('channel_id')
            return self._get_channel_info(channel_id)
        elif action == "search_messages":
            query = kwargs.get('query')
            return self._search_messages(query)
        else:
            return f"Unknown action: {action}"
    
    def _send_message(self, channel_id: str, message: str) -> str:
        """Send message to Mattermost channel"""
        url = f"{MATTERMOST_URL}/api/v4/posts"
        headers = {
            'Authorization': f'Bearer {MATTERMOST_TOKEN}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'channel_id': channel_id,
            'message': message
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 201:
                return "Message sent successfully"
            else:
                return f"Failed to send message: {response.status_code}"
        except Exception as e:
            return f"Error sending message: {str(e)}"
    
    def _get_channel_info(self, channel_id: str) -> str:
        """Get channel information"""
        url = f"{MATTERMOST_URL}/api/v4/channels/{channel_id}"
        headers = {'Authorization': f'Bearer {MATTERMOST_TOKEN}'}
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                channel_data = response.json()
                return json.dumps({
                    'name': channel_data.get('name'),
                    'display_name': channel_data.get('display_name'),
                    'type': channel_data.get('type'),
                    'member_count': channel_data.get('total_msg_count', 0)
                })
            else:
                return f"Failed to get channel info: {response.status_code}"
        except Exception as e:
            return f"Error getting channel info: {str(e)}"
    
    def _search_messages(self, query: str) -> str:
        """Search messages in Mattermost"""
        url = f"{MATTERMOST_URL}/api/v4/posts/search"
        headers = {
            'Authorization': f'Bearer {MATTERMOST_TOKEN}',
            'Content-Type': 'application/json'
        }
        
        payload = {'terms': query}
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                results = response.json()
                posts = results.get('posts', {})
                return json.dumps([
                    {
                        'message': post.get('message', '')[:200],
                        'create_at': post.get('create_at'),
                        'user_id': post.get('user_id')
                    }
                    for post in posts.values()
                ][:5])  # Return top 5 results
            else:
                return f"Failed to search messages: {response.status_code}"
        except Exception as e:
            return f"Error searching messages: {str(e)}"

class WorkflowExecutor:
    """Execute LangChain workflows"""
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=5)
        self.active_executions = {}
    
    async def execute_workflow(self, workflow: Workflow, trigger_data: Dict[str, Any], channel_id: str = None) -> str:
        """Execute a workflow with given trigger data"""
        execution_id = str(uuid.uuid4())
        
        # Create callback handler for Mattermost updates
        callback_handler = MattermostCallbackHandler(channel_id, execution_id) if channel_id else None
        
        # Store execution info
        self.active_executions[execution_id] = {
            'workflow_id': workflow.id,
            'status': 'running',
            'started_at': datetime.utcnow(),
            'channel_id': channel_id
        }
        
        try:
            # Find trigger node
            trigger_node = next((node for node in workflow.nodes if node.type == NodeType.TRIGGER), None)
            if not trigger_node:
                raise ValueError("No trigger node found in workflow")
            
            # Execute workflow nodes in sequence
            current_data = trigger_data
            execution_path = self._build_execution_path(workflow.nodes, trigger_node.id)
            
            for node_id in execution_path:
                node = next((n for n in workflow.nodes if n.id == node_id), None)
                if not node:
                    continue
                
                logger.info(f"Executing node: {node.name} ({node.type.value})")
                
                if node.type == NodeType.AI_AGENT:
                    current_data = await self._execute_ai_agent_node(node, current_data, callback_handler)
                elif node.type == NodeType.ACTION:
                    current_data = await self._execute_action_node(node, current_data)
                elif node.type == NodeType.CONDITION:
                    should_continue = await self._execute_condition_node(node, current_data)
                    if not should_continue:
                        break
                elif node.type == NodeType.TRANSFORM:
                    current_data = await self._execute_transform_node(node, current_data)
                elif node.type == NodeType.OUTPUT:
                    await self._execute_output_node(node, current_data, channel_id)
            
            # Mark execution as completed
            self.active_executions[execution_id]['status'] = 'completed'
            self.active_executions[execution_id]['completed_at'] = datetime.utcnow()
            
            return execution_id
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            self.active_executions[execution_id]['status'] = 'error'
            self.active_executions[execution_id]['error'] = str(e)
            
            if callback_handler:
                await callback_handler.send_message(f"Workflow execution failed: {str(e)}")
            
            raise e
    
    def _build_execution_path(self, nodes: List[WorkflowNode], start_node_id: str) -> List[str]:
        """Build execution path from workflow nodes"""
        path = []
        visited = set()
        
        def traverse(node_id: str):
            if node_id in visited:
                return
            
            visited.add(node_id)
            path.append(node_id)
            
            # Find node and traverse its connections
            node = next((n for n in nodes if n.id == node_id), None)
            if node:
                for connection in node.connections:
                    traverse(connection)
        
        traverse(start_node_id)
        return path
    
    async def _execute_ai_agent_node(self, node: WorkflowNode, data: Dict[str, Any], callback_handler=None) -> Dict[str, Any]:
        """Execute AI agent node using LangChain"""
        config = node.config
        prompt_template = config.get('prompt', 'Process this data: {input}')
        
        # Create tools for the agent
        tools = [MattermostTool()]
        
        # Initialize agent
        memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        agent = initialize_agent(
            tools=tools,
            llm=llm,
            agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
            memory=memory,
            callbacks=[callback_handler] if callback_handler else []
        )
        
        # Format input data
        input_text = json.dumps(data) if isinstance(data, dict) else str(data)
        
        # Execute agent
        result = await asyncio.get_event_loop().run_in_executor(
            None, 
            lambda: agent.run(prompt_template.format(input=input_text))
        )
        
        return {'ai_result': result, 'original_data': data}
    
    async def _execute_action_node(self, node: WorkflowNode, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute action node"""
        config = node.config
        action_type = config.get('action_type')
        
        if action_type == 'http_request':
            url = config.get('url')
            method = config.get('method', 'GET')
            headers = config.get('headers', {})
            
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.request(method, url, headers=headers, json=data) as response:
                        result = await response.json()
                        return {'http_result': result, 'status_code': response.status}
            except Exception as e:
                return {'error': str(e)}
        
        elif action_type == 'data_transform':
            # Simple data transformation
            transform_script = config.get('transform_script', 'return data')
            # Note: In production, use a safer evaluation method
            try:
                result = eval(transform_script, {'data': data, 'json': json})
                return result
            except Exception as e:
                return {'error': str(e)}
        
        return data
    
    async def _execute_condition_node(self, node: WorkflowNode, data: Dict[str, Any]) -> bool:
        """Execute condition node"""
        config = node.config
        condition = config.get('condition', 'True')
        
        try:
            # Simple condition evaluation
            # Note: In production, use a safer evaluation method
            result = eval(condition, {'data': data, 'json': json})
            return bool(result)
        except Exception as e:
            logger.error(f"Condition evaluation failed: {e}")
            return False
    
    async def _execute_transform_node(self, node: WorkflowNode, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute transform node using LangChain"""
        config = node.config
        transform_prompt = config.get('prompt', 'Transform this data: {input}')
        
        prompt = PromptTemplate(
            input_variables=['input'],
            template=transform_prompt
        )
        
        chain = LLMChain(llm=llm, prompt=prompt)
        
        input_text = json.dumps(data) if isinstance(data, dict) else str(data)
        result = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: chain.run(input=input_text)
        )
        
        try:
            # Try to parse as JSON
            parsed_result = json.loads(result)
            return parsed_result
        except:
            # Return as text if not valid JSON
            return {'transformed_data': result, 'original_data': data}
    
    async def _execute_output_node(self, node: WorkflowNode, data: Dict[str, Any], channel_id: str = None):
        """Execute output node"""
        config = node.config
        output_type = config.get('output_type', 'mattermost')
        
        if output_type == 'mattermost' and channel_id:
            message = config.get('message_template', 'Workflow completed: {data}')
            formatted_message = message.format(data=json.dumps(data, indent=2))
            
            # Send to Mattermost
            tool = MattermostTool()
            tool._send_message(channel_id, formatted_message)
        
        elif output_type == 'webhook':
            webhook_url = config.get('webhook_url')
            if webhook_url:
                async with aiohttp.ClientSession() as session:
                    await session.post(webhook_url, json=data)

# Initialize workflow executor
workflow_executor = WorkflowExecutor()

# Web routes
@app.route('/')
def index():
    """Main workflow builder interface"""
    return render_template('workflow_builder.html')

@app.route('/api/workflows', methods=['GET'])
def list_workflows():
    """List all workflows"""
    team_id = request.args.get('team_id')
    workflows = db.list_workflows(team_id)
    
    return jsonify([{
        'id': w.id,
        'name': w.name,
        'description': w.description,
        'status': w.status.value,
        'created_at': w.created_at.isoformat(),
        'updated_at': w.updated_at.isoformat(),
        'node_count': len(w.nodes)
    } for w in workflows])

@app.route('/api/workflows', methods=['POST'])
def create_workflow():
    """Create new workflow"""
    data = request.json
    
    workflow = Workflow(
        id=str(uuid.uuid4()),
        name=data['name'],
        description=data.get('description', ''),
        nodes=[],
        status=WorkflowStatus.DRAFT,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        created_by=data.get('created_by', 'unknown'),
        team_id=data.get('team_id', 'default')
    )
    
    db.save_workflow(workflow)
    
    return jsonify({'id': workflow.id, 'status': 'created'})

@app.route('/api/workflows/<workflow_id>', methods=['GET'])
def get_workflow(workflow_id):
    """Get workflow by ID"""
    workflow = db.get_workflow(workflow_id)
    if not workflow:
        return jsonify({'error': 'Workflow not found'}), 404
    
    return jsonify({
        'id': workflow.id,
        'name': workflow.name,
        'description': workflow.description,
        'nodes': [asdict(node) for node in workflow.nodes],
        'status': workflow.status.value,
        'created_at': workflow.created_at.isoformat(),
        'updated_at': workflow.updated_at.isoformat(),
        'created_by': workflow.created_by,
        'team_id': workflow.team_id,
        'trigger_config': workflow.trigger_config
    })

@app.route('/api/workflows/<workflow_id>', methods=['PUT'])
def update_workflow(workflow_id):
    """Update workflow"""
    workflow = db.get_workflow(workflow_id)
    if not workflow:
        return jsonify({'error': 'Workflow not found'}), 404
    
    data = request.json
    
    # Update workflow properties
    workflow.name = data.get('name', workflow.name)
    workflow.description = data.get('description', workflow.description)
    workflow.updated_at = datetime.utcnow()
    
    # Update nodes
    if 'nodes' in data:
        workflow.nodes = [WorkflowNode(**node_data) for node_data in data['nodes']]
    
    # Update status
    if 'status' in data:
        workflow.status = WorkflowStatus(data['status'])
    
    db.save_workflow(workflow)
    
    return jsonify({'status': 'updated'})

@app.route('/api/workflows/<workflow_id>/execute', methods=['POST'])
async def execute_workflow_endpoint(workflow_id):
    """Execute workflow via API"""
    workflow = db.get_workflow(workflow_id)
    if not workflow:
        return jsonify({'error': 'Workflow not found'}), 404
    
    data = request.json
    trigger_data = data.get('trigger_data', {})
    channel_id = data.get('channel_id')
    
    try:
        execution_id = await workflow_executor.execute_workflow(workflow, trigger_data, channel_id)
        return jsonify({'execution_id': execution_id, 'status': 'started'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/webhook/trigger/<workflow_id>', methods=['POST'])
async def webhook_trigger(workflow_id):
    """Webhook endpoint to trigger workflows"""
    workflow = db.get_workflow(workflow_id)
    if not workflow:
        return jsonify({'error': 'Workflow not found'}), 404
    
    trigger_data = request.json or {}
    
    try:
        execution_id = await workflow_executor.execute_workflow(workflow, trigger_data)
        return jsonify({'execution_id': execution_id, 'status': 'started'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'active_executions': len(workflow_executor.active_executions)
    })

# Socket.IO events for real-time updates
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    emit('connected', {'status': 'connected'})

@socketio.on('join_workflow')
def handle_join_workflow(data):
    """Join workflow room for real-time updates"""
    workflow_id = data['workflow_id']
    join_room(workflow_id)
    emit('joined_workflow', {'workflow_id': workflow_id})

@socketio.on('leave_workflow')
def handle_leave_workflow(data):
    """Leave workflow room"""
    workflow_id = data['workflow_id']
    leave_room(workflow_id)
    emit('left_workflow', {'workflow_id': workflow_id})

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    debug = os.getenv('DEBUG', 'false').lower() == 'true'
    
    logger.info(f"Starting LangChain Automation Platform on port {port}")
    logger.info(f"OpenAI Model: {os.getenv('OPENAI_MODEL', 'gpt-4')}")
    logger.info(f"Mattermost URL: {MATTERMOST_URL}")
    
    socketio.run(app, host='0.0.0.0', port=port, debug=debug)
