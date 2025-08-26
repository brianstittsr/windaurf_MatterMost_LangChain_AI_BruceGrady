# OpenAI Integration Guide

This guide covers the complete OpenAI integration for your Mattermost deployment.

## Architecture

The OpenAI integration consists of:

- **OpenAI Bot Service** (`openai-bot/`) - Python Flask service that handles AI interactions
- **Mattermost Webhooks** - Outgoing webhooks that trigger the bot
- **Slash Commands** - Direct `/ai` commands for users
- **Bot User** - Dedicated Mattermost user for the AI assistant

## Setup Process

### 1. Get OpenAI API Key

1. Visit [OpenAI Platform](https://platform.openai.com/api-keys)
2. Create a new API key
3. Copy the key (starts with `sk-`)

### 2. Deploy Services

The project includes both Mattermost and the OpenAI bot service:

```bash
# Local development
docker-compose up -d

# Railway deployment
# Both services deploy automatically via railway.toml
```

### 3. Configure Bot in Mattermost

Run the automated setup script:

```bash
python setup-bot.py
```

This script will:
- Create the `aibot` user
- Generate a bot access token
- Set up outgoing webhooks
- Create the `/ai` slash command
- Configure permissions

### 4. Set Environment Variables

Add these to your Railway project or `.env` file:

```bash
# Required
OPENAI_API_KEY=sk-your-key-here
MATTERMOST_TOKEN=bot-token-from-setup-script

# Optional customization
BOT_USERNAME=aibot
OPENAI_MODEL=gpt-4
MAX_TOKENS=1000
TEMPERATURE=0.7
```

## Usage Examples

### Basic Interactions

**Ask questions with mentions:**
```
@aibot What is Docker and how does it work?
@aibot Help me debug this Python error: NameError
```

**Use prefix commands:**
```
ai: Explain the difference between REST and GraphQL
ai: Write a bash script to backup a database
```

**Slash commands:**
```
/ai How do I optimize PostgreSQL queries?
/ai What are the best practices for API design?
```

### Advanced Features

**Context-aware responses:**
The bot reads recent channel history to provide contextual answers.

**Thread support:**
Responses maintain conversation threads when replying to specific messages.

**Error handling:**
The bot gracefully handles API errors and provides helpful feedback.

## Customization

### Model Configuration

Adjust the AI behavior by modifying environment variables:

```bash
# Use different OpenAI models
OPENAI_MODEL=gpt-3.5-turbo  # Faster, cheaper
OPENAI_MODEL=gpt-4          # More capable
OPENAI_MODEL=gpt-4-turbo    # Latest version

# Control response length
MAX_TOKENS=500   # Shorter responses
MAX_TOKENS=2000  # Longer responses

# Adjust creativity
TEMPERATURE=0.1  # More focused
TEMPERATURE=0.9  # More creative
```

### Custom Prompts

Modify the system prompt in `openai-bot/app.py`:

```python
messages = [
    {
        "role": "system",
        "content": "You are a helpful DevOps assistant specialized in Docker, Kubernetes, and cloud deployments. Be concise and provide practical examples."
    }
]
```

### Webhook Triggers

Add custom trigger words by modifying the webhook configuration:

```python
# In setup-bot.py
webhook_data = {
    'trigger_words': ['@aibot', 'ai:', 'hey ai', 'assistant'],
    # ... other config
}
```

## Monitoring and Debugging

### Health Checks

Check bot status:
```bash
curl http://localhost:5000/health
```

### Logs

View bot logs:
```bash
# Docker Compose
docker-compose logs openai-bot

# Railway
# Check logs in Railway dashboard
```

### Common Issues

**Bot not responding:**
1. Check `MATTERMOST_TOKEN` is set correctly
2. Verify webhook URLs are accessible
3. Ensure bot user has proper permissions

**API errors:**
1. Verify `OPENAI_API_KEY` is valid
2. Check OpenAI account has sufficient credits
3. Monitor rate limits

**Connection issues:**
1. Verify `MATTERMOST_URL` is correct
2. Check network connectivity between services
3. Ensure webhooks are properly configured

## Security Considerations

### API Key Management
- Never commit API keys to version control
- Use Railway's environment variables for production
- Rotate keys regularly

### Bot Permissions
- Limit bot to specific channels if needed
- Review webhook trigger words
- Monitor bot usage and costs

### Network Security
- Use HTTPS in production
- Restrict webhook endpoints
- Implement rate limiting if needed

## Cost Management

### OpenAI Usage
- Monitor token usage in OpenAI dashboard
- Set usage limits and alerts
- Use `gpt-3.5-turbo` for cost-effective responses

### Optimization Tips
- Limit `MAX_TOKENS` to control response length
- Use context efficiently (only recent messages)
- Implement caching for common queries

## Extending the Integration

### Custom Commands

Add specialized commands by extending the bot:

```python
@app.route('/custom-command', methods=['POST'])
def custom_command():
    # Handle specialized AI tasks
    pass
```

### Integration with External APIs

Combine OpenAI with other services:

```python
async def enhanced_response(prompt):
    # Get weather data, search results, etc.
    external_data = await fetch_external_data()
    
    # Include in AI prompt
    enhanced_prompt = f"{prompt}\n\nContext: {external_data}"
    return await generate_ai_response(enhanced_prompt)
```

### Plugin Development

Create Mattermost plugins for advanced features:
- Custom UI components
- Advanced permissions
- Integration with Mattermost workflows

## Support

For issues with:
- **OpenAI API**: [OpenAI Support](https://help.openai.com/)
- **Mattermost**: [Mattermost Documentation](https://docs.mattermost.com/)
- **Railway**: [Railway Documentation](https://docs.railway.app/)
- **This Integration**: Check the GitHub repository issues
