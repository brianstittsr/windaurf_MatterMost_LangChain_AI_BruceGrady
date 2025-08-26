#!/usr/bin/env python3
"""
Workflow Templates for LangChain Automation Platform
Pre-built workflow templates for common automation scenarios
"""

import json
from datetime import datetime
from typing import Dict, List, Any

class WorkflowTemplates:
    """Collection of pre-built workflow templates"""
    
    @staticmethod
    def get_all_templates() -> List[Dict[str, Any]]:
        """Get all available workflow templates"""
        return [
            WorkflowTemplates.content_summarizer(),
            WorkflowTemplates.sentiment_analyzer(),
            WorkflowTemplates.automated_responder(),
            WorkflowTemplates.data_processor(),
            WorkflowTemplates.meeting_scheduler(),
            WorkflowTemplates.code_reviewer(),
            WorkflowTemplates.customer_support(),
            WorkflowTemplates.content_moderator()
        ]
    
    @staticmethod
    def content_summarizer() -> Dict[str, Any]:
        """Template for summarizing long content"""
        return {
            "name": "Content Summarizer",
            "description": "Automatically summarize long messages or documents",
            "category": "Content Processing",
            "nodes": [
                {
                    "id": "trigger_1",
                    "type": "trigger",
                    "name": "Webhook Trigger",
                    "position": {"x": 0, "y": 0},
                    "config": {
                        "subtype": "webhook",
                        "url": "/webhook/content-summarizer",
                        "method": "POST"
                    },
                    "connections": ["ai_1"]
                },
                {
                    "id": "ai_1",
                    "type": "ai_agent",
                    "name": "Summarizer Agent",
                    "position": {"x": 200, "y": 0},
                    "config": {
                        "subtype": "chat",
                        "prompt": """You are a professional content summarizer. 
                        
Please summarize the following content in a clear, concise manner:
- Keep the summary to 2-3 key points
- Maintain the original tone and intent
- Highlight any action items or important dates

Content to summarize: {input}""",
                        "model": "gpt-4"
                    },
                    "connections": ["output_1"]
                },
                {
                    "id": "output_1",
                    "type": "output",
                    "name": "Send Summary",
                    "position": {"x": 400, "y": 0},
                    "config": {
                        "subtype": "mattermost",
                        "channel_id": "",
                        "message_template": "📝 **Content Summary**\n\n{data}"
                    },
                    "connections": []
                }
            ]
        }
    
    @staticmethod
    def sentiment_analyzer() -> Dict[str, Any]:
        """Template for analyzing sentiment of messages"""
        return {
            "name": "Sentiment Analyzer",
            "description": "Analyze sentiment of messages and trigger alerts for negative sentiment",
            "category": "Analytics",
            "nodes": [
                {
                    "id": "trigger_1",
                    "type": "trigger",
                    "name": "Message Trigger",
                    "position": {"x": 0, "y": 0},
                    "config": {
                        "subtype": "mattermost",
                        "channels": ["support", "feedback"],
                        "keywords": []
                    },
                    "connections": ["ai_1"]
                },
                {
                    "id": "ai_1",
                    "type": "ai_agent",
                    "name": "Sentiment Analyzer",
                    "position": {"x": 200, "y": 0},
                    "config": {
                        "subtype": "analyst",
                        "prompt": """Analyze the sentiment of this message and provide:
1. Overall sentiment (positive, negative, neutral)
2. Confidence score (0-100)
3. Key emotional indicators
4. Suggested response tone

Message: {input}

Return your analysis in JSON format:
{
  "sentiment": "positive|negative|neutral",
  "confidence": 85,
  "emotions": ["frustrated", "urgent"],
  "suggested_tone": "empathetic and solution-focused"
}""",
                        "model": "gpt-4"
                    },
                    "connections": ["condition_1"]
                },
                {
                    "id": "condition_1",
                    "type": "condition",
                    "name": "Check Negative Sentiment",
                    "position": {"x": 400, "y": 0},
                    "config": {
                        "condition": "json.loads(data['ai_result'])['sentiment'] == 'negative' and json.loads(data['ai_result'])['confidence'] > 70"
                    },
                    "connections": ["output_1"]
                },
                {
                    "id": "output_1",
                    "type": "output",
                    "name": "Alert Team",
                    "position": {"x": 600, "y": 0},
                    "config": {
                        "subtype": "mattermost",
                        "channel_id": "alerts",
                        "message_template": "🚨 **Negative Sentiment Detected**\n\nMessage: {data[original_data][message]}\nAnalysis: {data[ai_result]}"
                    },
                    "connections": []
                }
            ]
        }
    
    @staticmethod
    def automated_responder() -> Dict[str, Any]:
        """Template for automated responses to common questions"""
        return {
            "name": "Automated Responder",
            "description": "Automatically respond to common questions with AI-generated answers",
            "category": "Customer Support",
            "nodes": [
                {
                    "id": "trigger_1",
                    "type": "trigger",
                    "name": "Question Trigger",
                    "position": {"x": 0, "y": 0},
                    "config": {
                        "subtype": "mattermost",
                        "channels": ["support", "general"],
                        "keywords": ["help", "how to", "question", "?"]
                    },
                    "connections": ["ai_1"]
                },
                {
                    "id": "ai_1",
                    "type": "ai_agent",
                    "name": "Support Agent",
                    "position": {"x": 200, "y": 0},
                    "config": {
                        "subtype": "chat",
                        "prompt": """You are a helpful customer support agent. 

Based on this question, provide a helpful, accurate response:
- Be friendly and professional
- If you're not sure, suggest they contact human support
- Include relevant links or resources when possible
- Keep responses concise but complete

Question: {input}""",
                        "model": "gpt-4"
                    },
                    "connections": ["condition_1"]
                },
                {
                    "id": "condition_1",
                    "type": "condition",
                    "name": "Confidence Check",
                    "position": {"x": 400, "y": 0},
                    "config": {
                        "condition": "len(data['ai_result']) > 50 and 'not sure' not in data['ai_result'].lower()"
                    },
                    "connections": ["output_1"]
                },
                {
                    "id": "output_1",
                    "type": "output",
                    "name": "Send Response",
                    "position": {"x": 600, "y": 0},
                    "config": {
                        "subtype": "mattermost",
                        "channel_id": "",
                        "message_template": "🤖 **Automated Response**\n\n{data[ai_result]}\n\n*If this doesn't help, please tag @support for human assistance.*"
                    },
                    "connections": []
                }
            ]
        }
    
    @staticmethod
    def data_processor() -> Dict[str, Any]:
        """Template for processing and analyzing data"""
        return {
            "name": "Data Processor",
            "description": "Process incoming data, analyze patterns, and generate reports",
            "category": "Data Analytics",
            "nodes": [
                {
                    "id": "trigger_1",
                    "type": "trigger",
                    "name": "Data Webhook",
                    "position": {"x": 0, "y": 0},
                    "config": {
                        "subtype": "webhook",
                        "url": "/webhook/data-processor",
                        "method": "POST"
                    },
                    "connections": ["transform_1"]
                },
                {
                    "id": "transform_1",
                    "type": "transform",
                    "name": "Clean Data",
                    "position": {"x": 200, "y": 0},
                    "config": {
                        "script": """
# Clean and validate data
cleaned_data = {}
for key, value in data.items():
    if value is not None and value != '':
        cleaned_data[key] = value

# Add metadata
cleaned_data['processed_at'] = datetime.now().isoformat()
cleaned_data['record_count'] = len([k for k in cleaned_data.keys() if not k.startswith('_')])

return cleaned_data
""",
                        "language": "python"
                    },
                    "connections": ["ai_1"]
                },
                {
                    "id": "ai_1",
                    "type": "ai_agent",
                    "name": "Data Analyst",
                    "position": {"x": 400, "y": 0},
                    "config": {
                        "subtype": "analyst",
                        "prompt": """Analyze this data and provide insights:

1. Key patterns or trends
2. Anomalies or outliers
3. Actionable recommendations
4. Data quality assessment

Data to analyze: {input}

Provide your analysis in a structured format with clear sections.""",
                        "model": "gpt-4"
                    },
                    "connections": ["output_1"]
                },
                {
                    "id": "output_1",
                    "type": "output",
                    "name": "Send Report",
                    "position": {"x": 600, "y": 0},
                    "config": {
                        "subtype": "mattermost",
                        "channel_id": "analytics",
                        "message_template": "📊 **Data Analysis Report**\n\n{data[ai_result]}\n\n*Raw data processed: {data[original_data][record_count]} records*"
                    },
                    "connections": []
                }
            ]
        }
    
    @staticmethod
    def meeting_scheduler() -> Dict[str, Any]:
        """Template for intelligent meeting scheduling"""
        return {
            "name": "Meeting Scheduler",
            "description": "Automatically schedule meetings based on natural language requests",
            "category": "Productivity",
            "nodes": [
                {
                    "id": "trigger_1",
                    "type": "trigger",
                    "name": "Schedule Request",
                    "position": {"x": 0, "y": 0},
                    "config": {
                        "subtype": "mattermost",
                        "channels": ["general", "team"],
                        "keywords": ["schedule", "meeting", "call", "sync"]
                    },
                    "connections": ["ai_1"]
                },
                {
                    "id": "ai_1",
                    "type": "ai_agent",
                    "name": "Schedule Parser",
                    "position": {"x": 200, "y": 0},
                    "config": {
                        "subtype": "chat",
                        "prompt": """Extract meeting details from this request:

Request: {input}

Extract and return in JSON format:
{
  "title": "meeting title",
  "participants": ["person1", "person2"],
  "duration": "30 minutes",
  "preferred_times": ["tomorrow 2pm", "friday morning"],
  "agenda": "brief agenda if mentioned",
  "urgency": "high|medium|low"
}

If information is missing, indicate with null values.""",
                        "model": "gpt-4"
                    },
                    "connections": ["action_1"]
                },
                {
                    "id": "action_1",
                    "type": "action",
                    "name": "Check Calendar",
                    "position": {"x": 400, "y": 0},
                    "config": {
                        "subtype": "http",
                        "url": "https://api.calendar.com/check-availability",
                        "method": "POST",
                        "headers": {"Authorization": "Bearer YOUR_TOKEN"}
                    },
                    "connections": ["output_1"]
                },
                {
                    "id": "output_1",
                    "type": "output",
                    "name": "Propose Times",
                    "position": {"x": 600, "y": 0},
                    "config": {
                        "subtype": "mattermost",
                        "channel_id": "",
                        "message_template": "📅 **Meeting Scheduling**\n\nI've found these available times:\n{data[http_result]}\n\nReact with ✅ to confirm or 📝 to suggest alternatives."
                    },
                    "connections": []
                }
            ]
        }
    
    @staticmethod
    def code_reviewer() -> Dict[str, Any]:
        """Template for automated code review"""
        return {
            "name": "Code Reviewer",
            "description": "Automatically review code changes and provide feedback",
            "category": "Development",
            "nodes": [
                {
                    "id": "trigger_1",
                    "type": "trigger",
                    "name": "Code Webhook",
                    "position": {"x": 0, "y": 0},
                    "config": {
                        "subtype": "webhook",
                        "url": "/webhook/code-review",
                        "method": "POST"
                    },
                    "connections": ["ai_1"]
                },
                {
                    "id": "ai_1",
                    "type": "ai_agent",
                    "name": "Code Reviewer",
                    "position": {"x": 200, "y": 0},
                    "config": {
                        "subtype": "chat",
                        "prompt": """Review this code change and provide feedback:

Code: {input}

Please analyze:
1. Code quality and best practices
2. Potential bugs or issues
3. Performance considerations
4. Security concerns
5. Suggestions for improvement

Provide constructive feedback in a friendly, helpful tone.""",
                        "model": "gpt-4"
                    },
                    "connections": ["condition_1"]
                },
                {
                    "id": "condition_1",
                    "type": "condition",
                    "name": "Check for Issues",
                    "position": {"x": 400, "y": 0},
                    "config": {
                        "condition": "'issue' in data['ai_result'].lower() or 'bug' in data['ai_result'].lower() or 'problem' in data['ai_result'].lower()"
                    },
                    "connections": ["output_1", "output_2"]
                },
                {
                    "id": "output_1",
                    "type": "output",
                    "name": "Alert Developer",
                    "position": {"x": 600, "y": -50},
                    "config": {
                        "subtype": "mattermost",
                        "channel_id": "dev-alerts",
                        "message_template": "⚠️ **Code Review Alert**\n\nPotential issues found:\n{data[ai_result]}"
                    },
                    "connections": []
                },
                {
                    "id": "output_2",
                    "type": "output",
                    "name": "Post Review",
                    "position": {"x": 600, "y": 50},
                    "config": {
                        "subtype": "mattermost",
                        "channel_id": "code-reviews",
                        "message_template": "👨‍💻 **Code Review Complete**\n\n{data[ai_result]}"
                    },
                    "connections": []
                }
            ]
        }
    
    @staticmethod
    def customer_support() -> Dict[str, Any]:
        """Template for customer support automation"""
        return {
            "name": "Customer Support",
            "description": "Intelligent customer support with escalation handling",
            "category": "Customer Support",
            "nodes": [
                {
                    "id": "trigger_1",
                    "type": "trigger",
                    "name": "Support Request",
                    "position": {"x": 0, "y": 0},
                    "config": {
                        "subtype": "mattermost",
                        "channels": ["support"],
                        "keywords": ["help", "issue", "problem", "bug"]
                    },
                    "connections": ["ai_1"]
                },
                {
                    "id": "ai_1",
                    "type": "ai_agent",
                    "name": "Support Classifier",
                    "position": {"x": 200, "y": 0},
                    "config": {
                        "subtype": "chat",
                        "prompt": """Classify this support request:

Request: {input}

Classify as:
1. Category: technical|billing|general|urgent
2. Priority: high|medium|low
3. Can be automated: yes|no
4. Suggested response or escalation

Return in JSON format:
{
  "category": "technical",
  "priority": "medium",
  "automated": "yes",
  "response": "suggested response or escalation reason"
}""",
                        "model": "gpt-4"
                    },
                    "connections": ["condition_1"]
                },
                {
                    "id": "condition_1",
                    "type": "condition",
                    "name": "Can Automate?",
                    "position": {"x": 400, "y": 0},
                    "config": {
                        "condition": "json.loads(data['ai_result'])['automated'] == 'yes'"
                    },
                    "connections": ["output_1", "output_2"]
                },
                {
                    "id": "output_1",
                    "type": "output",
                    "name": "Auto Response",
                    "position": {"x": 600, "y": -50},
                    "config": {
                        "subtype": "mattermost",
                        "channel_id": "",
                        "message_template": "🎧 **Support Response**\n\n{data[ai_result][response]}\n\n*Ticket ID: AUTO-{execution_id}*"
                    },
                    "connections": []
                },
                {
                    "id": "output_2",
                    "type": "output",
                    "name": "Escalate to Human",
                    "position": {"x": 600, "y": 50},
                    "config": {
                        "subtype": "mattermost",
                        "channel_id": "support-team",
                        "message_template": "🚨 **Support Escalation**\n\nCategory: {data[ai_result][category]}\nPriority: {data[ai_result][priority]}\n\nRequest: {data[original_data][message]}\n\nReason: {data[ai_result][response]}"
                    },
                    "connections": []
                }
            ]
        }
    
    @staticmethod
    def content_moderator() -> Dict[str, Any]:
        """Template for content moderation"""
        return {
            "name": "Content Moderator",
            "description": "Automatically moderate content for inappropriate material",
            "category": "Moderation",
            "nodes": [
                {
                    "id": "trigger_1",
                    "type": "trigger",
                    "name": "New Message",
                    "position": {"x": 0, "y": 0},
                    "config": {
                        "subtype": "mattermost",
                        "channels": ["general", "random"],
                        "keywords": []
                    },
                    "connections": ["ai_1"]
                },
                {
                    "id": "ai_1",
                    "type": "ai_agent",
                    "name": "Content Moderator",
                    "position": {"x": 200, "y": 0},
                    "config": {
                        "subtype": "chat",
                        "prompt": """Analyze this message for inappropriate content:

Message: {input}

Check for:
1. Offensive language
2. Harassment or bullying
3. Spam or promotional content
4. Inappropriate images/links
5. Policy violations

Return assessment in JSON:
{
  "appropriate": true|false,
  "confidence": 85,
  "violations": ["spam", "offensive"],
  "action": "none|warn|remove|escalate",
  "reason": "explanation"
}""",
                        "model": "gpt-4"
                    },
                    "connections": ["condition_1"]
                },
                {
                    "id": "condition_1",
                    "type": "condition",
                    "name": "Content Appropriate?",
                    "position": {"x": 400, "y": 0},
                    "config": {
                        "condition": "not json.loads(data['ai_result'])['appropriate'] and json.loads(data['ai_result'])['confidence'] > 80"
                    },
                    "connections": ["action_1"]
                },
                {
                    "id": "action_1",
                    "type": "action",
                    "name": "Remove Message",
                    "position": {"x": 600, "y": 0},
                    "config": {
                        "subtype": "http",
                        "url": f"{os.getenv('MATTERMOST_URL', 'http://mattermost:8000')}/api/v4/posts/{{message_id}}",
                        "method": "DELETE",
                        "headers": {"Authorization": f"Bearer {os.getenv('MATTERMOST_TOKEN')}"}
                    },
                    "connections": ["output_1"]
                },
                {
                    "id": "output_1",
                    "type": "output",
                    "name": "Notify Moderators",
                    "position": {"x": 800, "y": 0},
                    "config": {
                        "subtype": "mattermost",
                        "channel_id": "moderation-log",
                        "message_template": "🛡️ **Content Moderated**\n\nAction: {data[ai_result][action]}\nReason: {data[ai_result][reason]}\nViolations: {data[ai_result][violations]}\n\nOriginal message removed."
                    },
                    "connections": []
                }
            ]
        }

def create_workflow_from_template(template_data: Dict[str, Any], workflow_name: str = None) -> Dict[str, Any]:
    """Create a workflow from a template"""
    import uuid
    
    workflow = {
        "id": str(uuid.uuid4()),
        "name": workflow_name or template_data["name"],
        "description": template_data["description"],
        "nodes": [],
        "status": "draft",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "created_by": "template",
        "team_id": "default",
        "trigger_config": {}
    }
    
    # Convert template nodes to workflow nodes
    for node_template in template_data["nodes"]:
        node = {
            "id": node_template["id"],
            "type": node_template["type"],
            "name": node_template["name"],
            "config": node_template["config"],
            "position": node_template["position"],
            "connections": node_template.get("connections", [])
        }
        workflow["nodes"].append(node)
    
    return workflow
