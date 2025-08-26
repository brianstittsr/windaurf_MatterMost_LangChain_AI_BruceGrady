# LangChain Automation Platform

A comprehensive AI automation platform integrated with Mattermost, providing visual workflow building capabilities similar to N8N but powered by LangChain and OpenAI.

## Overview

The LangChain Automation Platform allows you to create sophisticated AI-powered workflows directly within your Mattermost environment. Build automations using a visual drag-and-drop interface, leverage AI agents for intelligent processing, and integrate with external services seamlessly.

## Architecture

### Core Components

1. **Workflow Builder** - Visual interface for creating workflows
2. **Execution Engine** - LangChain-powered workflow execution
3. **AI Agents** - Specialized AI agents for different tasks
4. **Integration Layer** - Connects with Mattermost and external services
5. **Template Library** - Pre-built workflow templates

### Services

- **Main Application** (`langchain-automation/app.py`) - Flask + SocketIO server
- **Visual Builder** (`templates/workflow_builder.html`) - Web-based workflow designer
- **Database** - SQLite for workflow storage and execution logs
- **Integration** (`integration.py`) - Connects with OpenAI bot service

## Getting Started

### 1. Access the Platform

After deployment, access the automation platform at:
- **Local**: `http://localhost:5001`
- **Railway**: `https://your-langchain-automation.up.railway.app`

### 2. Create Your First Workflow

1. **Open the Workflow Builder**
   - Navigate to the automation platform URL
   - Click "New Workflow" in the sidebar

2. **Design Your Workflow**
   - Drag nodes from the palette to the canvas
   - Connect nodes by dragging from output to input
   - Double-click nodes to configure them

3. **Configure Nodes**
   - **Triggers**: Define when workflows start
   - **AI Agents**: Add intelligent processing
   - **Actions**: Perform external operations
   - **Conditions**: Add logic and branching
   - **Outputs**: Send results to Mattermost or webhooks

4. **Save and Activate**
   - Save your workflow
   - Set status to "Active" to enable execution

### 3. Bot Commands

Use these commands in Mattermost to manage workflows:

```
workflow list                    # List all workflows
workflow create "Name" "Desc"    # Create new workflow
workflow run "Workflow Name"     # Execute workflow
workflow status [execution_id]  # Check execution status
workflow help                   # Show help
```

## Node Types

### Triggers
- **Webhook Trigger** - HTTP endpoints for external systems
- **Schedule Trigger** - Time-based execution (cron)
- **Mattermost Trigger** - Channel messages and events

### AI Agents
- **Chat Agent** - General purpose conversational AI
- **Data Analyst** - Analyze and extract insights from data
- **Content Writer** - Generate and edit content

### Actions
- **HTTP Request** - Call external APIs
- **Send Email** - Email notifications
- **Database Query** - Database operations

### Logic
- **Condition** - Conditional branching
- **Transform Data** - Data manipulation and formatting

### Output
- **Mattermost Message** - Send messages to channels
- **Webhook Output** - Send data to external systems

## Pre-built Templates

### Content Processing
- **Content Summarizer** - Automatically summarize long content
- **Sentiment Analyzer** - Analyze message sentiment with alerts
- **Content Moderator** - Automated content moderation

### Customer Support
- **Automated Responder** - AI-powered customer support
- **Support Ticket Classifier** - Intelligent ticket routing

### Development
- **Code Reviewer** - Automated code review and feedback
- **Meeting Scheduler** - Intelligent meeting coordination

### Analytics
- **Data Processor** - Process and analyze incoming data

## Configuration Examples

### AI Agent Configuration
```json
{
  "prompt": "You are a helpful assistant. Process this input: {input}",
  "model": "gpt-4",
  "temperature": 0.7,
  "max_tokens": 1000
}
```

### HTTP Action Configuration
```json
{
  "url": "https://api.example.com/data",
  "method": "POST",
  "headers": {
    "Authorization": "Bearer YOUR_TOKEN",
    "Content-Type": "application/json"
  }
}
```

### Mattermost Output Configuration
```json
{
  "channel_id": "channel_id_here",
  "message_template": "🤖 **Result**: {data}\n\nProcessed at: {timestamp}"
}
```

## Advanced Features

### Real-time Updates
- WebSocket connections for live workflow monitoring
- Real-time execution logs and status updates
- Live collaboration on workflow design

### Context-Aware AI
- AI agents can access conversation history
- Workflows maintain context across executions
- Integration with existing OpenAI bot for enhanced responses

### Error Handling
- Automatic retry mechanisms
- Error notifications to Mattermost
- Detailed execution logs for debugging

### Security
- Environment variable management
- Secure API key storage
- User permissions and access control

## Integration with OpenAI Bot

The automation platform seamlessly integrates with your existing OpenAI bot:

### Enhanced Bot Responses
- Bot can suggest relevant workflows
- Workflow results enhance bot context
- Unified AI experience across platforms

### Workflow Commands
- Execute workflows via bot commands
- Get workflow status through chat
- Create workflows conversationally

### Shared Context
- Workflows can trigger bot responses
- Bot conversations can trigger workflows
- Unified conversation history

## API Reference

### Workflow Management
```http
GET /api/workflows              # List workflows
POST /api/workflows             # Create workflow
GET /api/workflows/{id}         # Get workflow
PUT /api/workflows/{id}         # Update workflow
POST /api/workflows/{id}/execute # Execute workflow
```

### Webhook Triggers
```http
POST /webhook/trigger/{workflow_id}  # Trigger workflow via webhook
```

### Health Check
```http
GET /health                     # System health status
```

## Environment Variables

```bash
# Required
OPENAI_API_KEY=sk-your-openai-api-key
MATTERMOST_TOKEN=your-bot-token
MATTERMOST_URL=http://mattermost:8000

# Optional
OPENAI_MODEL=gpt-4
TEMPERATURE=0.7
SECRET_KEY=your-secret-key
DATABASE_PATH=/app/data/workflows.db
DEBUG=false
```

## Deployment

### Local Development
```bash
cd langchain-automation
pip install -r requirements.txt
python app.py
```

### Docker Compose
```bash
docker-compose up -d
```

### Railway
The platform deploys automatically with the main Mattermost service on Railway.

## Monitoring and Debugging

### Execution Logs
- Real-time logs in the web interface
- Detailed error messages and stack traces
- Performance metrics and timing

### Health Monitoring
- Service health checks
- Database connectivity status
- Integration status with other services

### Debugging Tools
- Step-by-step execution tracing
- Variable inspection at each node
- Workflow validation and testing

## Best Practices

### Workflow Design
1. **Start Simple** - Begin with basic workflows and add complexity gradually
2. **Use Templates** - Leverage pre-built templates as starting points
3. **Test Thoroughly** - Use the test feature before activating workflows
4. **Handle Errors** - Add error handling and fallback paths

### Performance
1. **Optimize Prompts** - Use clear, specific prompts for AI agents
2. **Limit Scope** - Keep workflows focused on specific tasks
3. **Monitor Usage** - Track OpenAI API usage and costs
4. **Cache Results** - Store frequently used data to reduce API calls

### Security
1. **Secure Credentials** - Use environment variables for sensitive data
2. **Validate Inputs** - Always validate external data inputs
3. **Limit Permissions** - Grant minimal necessary permissions
4. **Monitor Activity** - Review workflow execution logs regularly

## Troubleshooting

### Common Issues

**Workflow Not Triggering**
- Check trigger configuration
- Verify webhook URLs are accessible
- Ensure Mattermost integration is properly configured

**AI Agent Errors**
- Verify OpenAI API key is valid
- Check prompt formatting and variables
- Monitor API rate limits and quotas

**Integration Issues**
- Confirm Mattermost token permissions
- Check network connectivity between services
- Verify environment variables are set correctly

### Support Resources
- Check execution logs for detailed error messages
- Use the health check endpoint to verify system status
- Review the integration documentation for setup issues

## Future Enhancements

### Planned Features
- **Plugin System** - Custom node types and integrations
- **Advanced Scheduling** - More sophisticated trigger options
- **Team Collaboration** - Multi-user workflow editing
- **Version Control** - Workflow versioning and rollback
- **Marketplace** - Community-shared workflow templates

### Integration Roadmap
- **External Services** - Slack, Discord, Microsoft Teams
- **Cloud Platforms** - AWS, GCP, Azure integrations
- **Databases** - MongoDB, Redis, Elasticsearch
- **Monitoring** - Prometheus, Grafana dashboards
