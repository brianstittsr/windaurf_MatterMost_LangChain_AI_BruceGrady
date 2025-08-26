# Mattermost on Railway

A complete Mattermost deployment configuration for Railway platform.

## Quick Deploy to Railway

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/mattermost)

## Features

- **Mattermost Team Edition** - Full-featured team collaboration platform
- **OpenAI Integration** - AI-powered chat assistant with GPT-4 support
- **LangChain Automation Platform** - Visual workflow builder similar to N8N
- **PostgreSQL Database** - Reliable data storage
- **Docker-based** - Consistent deployment across environments
- **Railway Optimized** - Configured specifically for Railway platform
- **Environment Variables** - Easy configuration management
- **Multiple Interaction Methods** - Webhooks, slash commands, and mentions
- **Pre-built Templates** - Ready-to-use automation workflows

## Prerequisites

- Railway account
- Basic understanding of environment variables

## Deployment Steps

### 1. Deploy to Railway

1. Click the "Deploy on Railway" button above, or:
2. Fork this repository
3. Connect your Railway account to GitHub
4. Create a new Railway project from this repository

### 2. Add PostgreSQL Database

1. In your Railway project dashboard, click "Add Service"
2. Select "Database" → "PostgreSQL"
3. Railway will automatically create the database and provide connection details

### 3. Configure Environment Variables

Railway will automatically set most variables, but you should configure:

```bash
# Required - Set your domain
SITE_URL=https://your-app-name.up.railway.app
MM_SERVICESETTINGS_SITEURL=https://your-app-name.up.railway.app

# Required - OpenAI Integration
OPENAI_API_KEY=sk-your-openai-api-key-here
MATTERMOST_TOKEN=your-bot-token-here

# Optional - Customize your instance
MM_TEAMSETTINGS_SITENAME="Your Team Chat"
MM_TEAMSETTINGS_MAXUSERSPERTEAM=50
BOT_USERNAME=aibot
OPENAI_MODEL=gpt-4
```

### 4. Database Connection

Railway automatically provides `DATABASE_URL`. The application will use this for PostgreSQL connection.

If you need to manually configure:
```bash
MM_SQLSETTINGS_DATASOURCE=postgresql://username:password@host:port/database?sslmode=require
```

## Local Development

### Using Docker Compose

1. Copy environment file:
```bash
cp .env.example .env
```

2. Edit `.env` with your configuration

3. Start services:
```bash
docker-compose up -d
```

4. Access Mattermost at `http://localhost:8000`

### Using Docker

1. Build the image:
```bash
docker build -t mattermost-railway .
```

2. Run with PostgreSQL:
```bash
docker run -d \
  -p 8000:8000 \
  -e MM_SQLSETTINGS_DATASOURCE="your_postgres_connection_string" \
  -e MM_SERVICESETTINGS_SITEURL="http://localhost:8000" \
  mattermost-railway
```

## Configuration

### Key Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MM_SERVICESETTINGS_SITEURL` | Your Mattermost URL | Required |
| `MM_SQLSETTINGS_DATASOURCE` | PostgreSQL connection string | Auto-configured on Railway |
| `MM_TEAMSETTINGS_SITENAME` | Site display name | "Mattermost" |
| `MM_TEAMSETTINGS_MAXUSERSPERTEAM` | Max users per team | 50 |
| `MM_PASSWORDSETTINGS_MINIMUMLENGTH` | Minimum password length | 8 |

### Custom Configuration

For advanced configuration, modify `config/config.json` or use environment variables following the [Mattermost documentation](https://docs.mattermost.com/administration/config-settings.html).

## First Time Setup

### Mattermost Setup
1. Navigate to your deployed Mattermost URL
2. Create the first admin account
3. Set up your team and invite users

### OpenAI Bot Setup
4. Get your OpenAI API key from [OpenAI Platform](https://platform.openai.com/api-keys)
5. Run the bot setup script:
   ```bash
   python setup-bot.py
   ```
6. Add the generated `MATTERMOST_TOKEN` to your environment variables
7. Restart the OpenAI bot service

### Using the AI Bot

The AI bot responds to several interaction methods:

**Mentions:**
```
@aibot What's the weather like today?
@aibot Help me write a Python function
```

**Prefix Commands:**
```
ai: Explain quantum computing
ai: Write a haiku about programming
```

**Slash Commands:**
```
/ai What are the best practices for Docker?
/ai Summarize this conversation
```

The bot provides context-aware responses and can maintain conversation threads.

## File Storage

By default, files are stored locally. For production, consider:

- **Railway Volumes** - For persistent local storage
- **AWS S3** - For scalable cloud storage
- **Other cloud providers** - Configure via environment variables

### S3 Configuration Example

```bash
MM_FILESETTINGS_DRIVERNAME=amazons3
MM_FILESETTINGS_AMAZONS3ACCESSKEYID=your_access_key
MM_FILESETTINGS_AMAZONS3SECRETACCESSKEY=your_secret_key
MM_FILESETTINGS_AMAZONS3BUCKET=your_bucket_name
MM_FILESETTINGS_AMAZONS3REGION=us-east-1
```

## Email Configuration

For production use, configure SMTP:

```bash
MM_EMAILSETTINGS_SENDEMAILNOTIFICATIONS=true
MM_EMAILSETTINGS_SMTPSERVER=smtp.gmail.com
MM_EMAILSETTINGS_SMTPPORT=587
MM_EMAILSETTINGS_SMTPUSERNAME=your_email@gmail.com
MM_EMAILSETTINGS_SMTPPASSWORD=your_app_password
MM_EMAILSETTINGS_CONNECTIONSECURITY=STARTTLS
```

## Security Considerations

- Use strong passwords for admin accounts
- Enable two-factor authentication
- Configure proper CORS settings
- Use HTTPS in production (Railway provides this automatically)
- Regularly update Mattermost version

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Verify `DATABASE_URL` is set correctly
   - Check PostgreSQL service is running

2. **Site URL Mismatch**
   - Ensure `MM_SERVICESETTINGS_SITEURL` matches your Railway domain
   - Check for trailing slashes

3. **File Upload Issues**
   - Verify file size limits in configuration
   - Check storage permissions

### Logs

View application logs in Railway dashboard or using:
```bash
docker-compose logs mattermost
```

## Scaling

Railway automatically handles:
- Load balancing
- SSL certificates
- Domain management
- Health checks

For high-traffic deployments, consider:
- Database connection pooling
- External file storage (S3)
- Redis for session storage
- CDN for static assets

## Support

- [Mattermost Documentation](https://docs.mattermost.com/)
- [Railway Documentation](https://docs.railway.app/)
- [GitHub Issues](https://github.com/your-username/mattermost-railway/issues)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Mattermost is licensed under the [Mattermost Source Available License](https://github.com/mattermost/mattermost-server/blob/master/LICENSE.txt).
