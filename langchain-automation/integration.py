#!/usr/bin/env python3
"""
Integration module for connecting LangChain Automation with existing OpenAI bot
"""

import os
import json
import asyncio
import logging
import aiohttp
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class OpenAIBotIntegration:
    """Integration with the existing OpenAI bot service"""
    
    def __init__(self, openai_bot_url: str = None):
        self.openai_bot_url = openai_bot_url or os.getenv('OPENAI_BOT_URL', 'http://openai-bot:5000')
        self.session = None
    
    async def init_session(self):
        """Initialize aiohttp session"""
        if not self.session:
            self.session = aiohttp.ClientSession()
    
    async def close_session(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
    
    async def trigger_bot_response(self, channel_id: str, message: str, workflow_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Trigger the OpenAI bot to respond with workflow context"""
        await self.init_session()
        
        payload = {
            'channel_id': channel_id,
            'text': message,
            'workflow_context': workflow_context or {},
            'source': 'langchain_automation'
        }
        
        try:
            async with self.session.post(f"{self.openai_bot_url}/webhook", json=payload) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Failed to trigger bot response: {response.status}")
                    return {'error': f'Bot response failed: {response.status}'}
        except Exception as e:
            logger.error(f"Error triggering bot response: {e}")
            return {'error': str(e)}
    
    async def get_bot_status(self) -> Dict[str, Any]:
        """Get the status of the OpenAI bot"""
        await self.init_session()
        
        try:
            async with self.session.get(f"{self.openai_bot_url}/health") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {'status': 'unavailable', 'error': f'HTTP {response.status}'}
        except Exception as e:
            logger.error(f"Error getting bot status: {e}")
            return {'status': 'error', 'error': str(e)}

class WorkflowBotCommands:
    """Bot commands for workflow management"""
    
    def __init__(self, workflow_executor, db_manager):
        self.workflow_executor = workflow_executor
        self.db = db_manager
        self.openai_integration = OpenAIBotIntegration()
    
    async def handle_workflow_command(self, command: str, args: list, channel_id: str, user_id: str) -> str:
        """Handle workflow-related bot commands"""
        
        if command == 'list':
            return await self._list_workflows(channel_id)
        elif command == 'create':
            return await self._create_workflow_interactive(args, channel_id, user_id)
        elif command == 'run':
            return await self._run_workflow(args, channel_id)
        elif command == 'status':
            return await self._workflow_status(args)
        elif command == 'help':
            return self._workflow_help()
        else:
            return f"Unknown workflow command: {command}. Use `workflow help` for available commands."
    
    async def _list_workflows(self, channel_id: str) -> str:
        """List available workflows"""
        try:
            workflows = self.db.list_workflows()
            if not workflows:
                return "📋 No workflows found. Use `workflow create` to create your first workflow!"
            
            response = "📋 **Available Workflows:**\n\n"
            for workflow in workflows[:10]:  # Limit to 10 workflows
                status_emoji = {
                    'active': '✅',
                    'draft': '📝',
                    'paused': '⏸️',
                    'error': '❌'
                }.get(workflow.status.value, '❓')
                
                response += f"{status_emoji} **{workflow.name}**\n"
                response += f"   └─ {workflow.description or 'No description'}\n"
                response += f"   └─ {len(workflow.nodes)} nodes, Status: {workflow.status.value}\n\n"
            
            if len(workflows) > 10:
                response += f"... and {len(workflows) - 10} more workflows.\n"
            
            response += "\nUse `workflow run <name>` to execute a workflow."
            return response
            
        except Exception as e:
            logger.error(f"Error listing workflows: {e}")
            return f"❌ Error listing workflows: {str(e)}"
    
    async def _create_workflow_interactive(self, args: list, channel_id: str, user_id: str) -> str:
        """Create a workflow interactively"""
        if not args:
            return """🛠️ **Create New Workflow**

Use: `workflow create <name> [description]`

Example: `workflow create "Daily Summary" "Summarize daily activities"`

Or visit the Automation Platform web interface to use the visual workflow builder!"""
        
        workflow_name = args[0]
        description = ' '.join(args[1:]) if len(args) > 1 else ''
        
        try:
            # Create basic workflow
            workflow_id = str(uuid.uuid4())
            workflow = Workflow(
                id=workflow_id,
                name=workflow_name,
                description=description,
                nodes=[],
                status=WorkflowStatus.DRAFT,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                created_by=user_id,
                team_id='default'
            )
            
            self.db.save_workflow(workflow)
            
            return f"""✅ **Workflow Created Successfully!**

**Name:** {workflow_name}
**Description:** {description or 'No description'}
**ID:** {workflow_id}

🎨 **Next Steps:**
1. Visit the Automation Platform to add nodes visually
2. Or use `workflow template` to start from a template
3. Use `workflow run {workflow_name}` to test when ready

The workflow is currently in **draft** status."""
            
        except Exception as e:
            logger.error(f"Error creating workflow: {e}")
            return f"❌ Error creating workflow: {str(e)}"
    
    async def _run_workflow(self, args: list, channel_id: str) -> str:
        """Run a workflow by name"""
        if not args:
            return "❌ Please specify a workflow name: `workflow run <name>`"
        
        workflow_name = ' '.join(args)
        
        try:
            # Find workflow by name
            workflows = self.db.list_workflows()
            workflow = next((w for w in workflows if w.name.lower() == workflow_name.lower()), None)
            
            if not workflow:
                return f"❌ Workflow '{workflow_name}' not found. Use `workflow list` to see available workflows."
            
            if workflow.status != WorkflowStatus.ACTIVE:
                return f"⚠️ Workflow '{workflow_name}' is not active (status: {workflow.status.value}). Please activate it first."
            
            # Execute workflow
            trigger_data = {
                'source': 'mattermost_command',
                'channel_id': channel_id,
                'triggered_at': datetime.utcnow().isoformat(),
                'message': f'Manual execution via bot command'
            }
            
            execution_id = await self.workflow_executor.execute_workflow(
                workflow, trigger_data, channel_id
            )
            
            return f"""🚀 **Workflow Execution Started**

**Workflow:** {workflow.name}
**Execution ID:** {execution_id}
**Status:** Running

You'll receive updates as the workflow progresses. Use `workflow status {execution_id}` to check progress."""
            
        except Exception as e:
            logger.error(f"Error running workflow: {e}")
            return f"❌ Error running workflow: {str(e)}"
    
    async def _workflow_status(self, args: list) -> str:
        """Get workflow execution status"""
        if not args:
            # Show general status
            active_executions = len(self.workflow_executor.active_executions)
            return f"📊 **Workflow System Status**\n\nActive executions: {active_executions}\nSystem: Healthy ✅"
        
        execution_id = args[0]
        
        if execution_id in self.workflow_executor.active_executions:
            execution = self.workflow_executor.active_executions[execution_id]
            status = execution['status']
            started_at = execution['started_at'].strftime('%Y-%m-%d %H:%M:%S')
            
            status_emoji = {
                'running': '🔄',
                'completed': '✅',
                'error': '❌',
                'paused': '⏸️'
            }.get(status, '❓')
            
            response = f"""📊 **Execution Status**

**ID:** {execution_id}
**Status:** {status_emoji} {status.title()}
**Started:** {started_at}
**Workflow:** {execution.get('workflow_id', 'Unknown')}"""
            
            if status == 'completed' and 'completed_at' in execution:
                completed_at = execution['completed_at'].strftime('%Y-%m-%d %H:%M:%S')
                duration = execution['completed_at'] - execution['started_at']
                response += f"\n**Completed:** {completed_at}\n**Duration:** {duration}"
            
            if status == 'error' and 'error' in execution:
                response += f"\n**Error:** {execution['error']}"
            
            return response
        else:
            return f"❌ Execution ID '{execution_id}' not found or completed."
    
    def _workflow_help(self) -> str:
        """Show workflow help"""
        return """🤖 **Workflow Automation Commands**

**Basic Commands:**
• `workflow list` - List all workflows
• `workflow create <name> [description]` - Create new workflow
• `workflow run <name>` - Execute a workflow
• `workflow status [execution_id]` - Check status

**Templates:**
• `workflow template list` - Show available templates
• `workflow template create <template_name>` - Create from template

**Examples:**
• `workflow create "Daily Standup" "Automated daily standup summary"`
• `workflow run "Content Moderator"`
• `workflow status abc123`

🎨 **Visual Builder:** Visit the Automation Platform web interface for drag-and-drop workflow creation!

💡 **Pro Tip:** Workflows can be triggered by webhooks, schedules, or Mattermost events automatically."""

# Integration with the main OpenAI bot
async def enhance_openai_bot_with_workflows(bot_message: str, context: Dict[str, Any]) -> str:
    """Enhance OpenAI bot responses with workflow capabilities"""
    
    # Check if the message is workflow-related
    workflow_keywords = ['workflow', 'automation', 'automate', 'schedule', 'trigger']
    
    if any(keyword in bot_message.lower() for keyword in workflow_keywords):
        # Add workflow suggestions to the response
        workflow_suggestion = """

🤖 **Automation Suggestion:** You can automate this task using our LangChain Automation Platform! 

Use `workflow help` to get started, or visit the visual workflow builder to create custom automations."""
        
        return bot_message + workflow_suggestion
    
    return bot_message

# Workflow triggers for Mattermost events
class MattermostWorkflowTriggers:
    """Handle Mattermost events that can trigger workflows"""
    
    def __init__(self, workflow_executor, db_manager):
        self.workflow_executor = workflow_executor
        self.db = db_manager
    
    async def handle_message_event(self, message_data: Dict[str, Any]):
        """Handle new message events"""
        message_text = message_data.get('text', '').lower()
        channel_id = message_data.get('channel_id')
        user_id = message_data.get('user_id')
        
        # Find workflows triggered by this message
        workflows = self.db.list_workflows()
        
        for workflow in workflows:
            if workflow.status != WorkflowStatus.ACTIVE:
                continue
            
            # Check if workflow has Mattermost trigger
            trigger_nodes = [node for node in workflow.nodes if node.type.value == 'trigger' and node.config.get('subtype') == 'mattermost']
            
            for trigger_node in trigger_nodes:
                trigger_config = trigger_node.config
                
                # Check channel filter
                if trigger_config.get('channels') and channel_id not in trigger_config['channels']:
                    continue
                
                # Check keyword filter
                keywords = trigger_config.get('keywords', [])
                if keywords and not any(keyword.lower() in message_text for keyword in keywords):
                    continue
                
                # Trigger workflow
                trigger_data = {
                    'source': 'mattermost_message',
                    'message': message_data.get('text', ''),
                    'channel_id': channel_id,
                    'user_id': user_id,
                    'timestamp': message_data.get('create_at', datetime.utcnow().isoformat())
                }
                
                try:
                    await self.workflow_executor.execute_workflow(workflow, trigger_data, channel_id)
                    logger.info(f"Triggered workflow {workflow.name} from message in channel {channel_id}")
                except Exception as e:
                    logger.error(f"Failed to trigger workflow {workflow.name}: {e}")
    
    async def handle_reaction_event(self, reaction_data: Dict[str, Any]):
        """Handle reaction events"""
        # Implementation for reaction-based triggers
        pass
    
    async def handle_channel_event(self, channel_data: Dict[str, Any]):
        """Handle channel events (join, leave, etc.)"""
        # Implementation for channel-based triggers
        pass
