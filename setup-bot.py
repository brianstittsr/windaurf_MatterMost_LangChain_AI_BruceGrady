#!/usr/bin/env python3
"""
Mattermost Bot Setup Script
Automates the setup of the OpenAI bot in Mattermost
"""

import os
import sys
import json
import requests
from urllib.parse import urljoin

def setup_mattermost_bot():
    """Setup the OpenAI bot in Mattermost"""
    
    # Configuration
    mattermost_url = os.getenv('MATTERMOST_URL', 'http://localhost:8000')
    admin_email = input("Enter admin email: ")
    admin_password = input("Enter admin password: ")
    bot_webhook_url = os.getenv('BOT_WEBHOOK_URL', 'http://localhost:5000/webhook')
    
    session = requests.Session()
    
    try:
        # Login as admin
        print("Logging in as admin...")
        login_data = {
            'login_id': admin_email,
            'password': admin_password
        }
        
        response = session.post(
            urljoin(mattermost_url, '/api/v4/users/login'),
            json=login_data
        )
        
        if response.status_code != 200:
            print(f"Login failed: {response.text}")
            return False
        
        print("✓ Admin login successful")
        
        # Create bot user
        print("Creating bot user...")
        bot_data = {
            'email': 'aibot@example.com',
            'username': 'aibot',
            'first_name': 'AI',
            'last_name': 'Bot',
            'password': 'BotPassword123!',
            'locale': 'en',
            'props': {}
        }
        
        response = session.post(
            urljoin(mattermost_url, '/api/v4/users'),
            json=bot_data
        )
        
        if response.status_code == 201:
            bot_user = response.json()
            bot_id = bot_user['id']
            print(f"✓ Bot user created with ID: {bot_id}")
        elif response.status_code == 400 and 'already exists' in response.text:
            # Bot already exists, get its ID
            response = session.get(
                urljoin(mattermost_url, '/api/v4/users/username/aibot')
            )
            if response.status_code == 200:
                bot_user = response.json()
                bot_id = bot_user['id']
                print(f"✓ Bot user already exists with ID: {bot_id}")
            else:
                print(f"Failed to get existing bot user: {response.text}")
                return False
        else:
            print(f"Failed to create bot user: {response.text}")
            return False
        
        # Create bot token
        print("Creating bot access token...")
        token_data = {
            'description': 'OpenAI Bot Token'
        }
        
        response = session.post(
            urljoin(mattermost_url, f'/api/v4/users/{bot_id}/tokens'),
            json=token_data
        )
        
        if response.status_code == 201:
            token_info = response.json()
            bot_token = token_info['token']
            print(f"✓ Bot token created: {bot_token[:10]}...")
        else:
            print(f"Failed to create bot token: {response.text}")
            return False
        
        # Get team ID (assuming first team)
        print("Getting team information...")
        response = session.get(urljoin(mattermost_url, '/api/v4/teams'))
        
        if response.status_code == 200:
            teams = response.json()
            if teams:
                team_id = teams[0]['id']
                team_name = teams[0]['name']
                print(f"✓ Using team: {team_name} ({team_id})")
            else:
                print("No teams found")
                return False
        else:
            print(f"Failed to get teams: {response.text}")
            return False
        
        # Add bot to team
        print("Adding bot to team...")
        response = session.post(
            urljoin(mattermost_url, f'/api/v4/teams/{team_id}/members'),
            json={'team_id': team_id, 'user_id': bot_id}
        )
        
        if response.status_code in [201, 400]:  # 400 if already member
            print("✓ Bot added to team")
        else:
            print(f"Failed to add bot to team: {response.text}")
        
        # Create outgoing webhook
        print("Creating outgoing webhook...")
        webhook_data = {
            'team_id': team_id,
            'channel_id': '',  # All channels
            'trigger_words': ['@aibot', 'ai:'],
            'callback_urls': [bot_webhook_url],
            'display_name': 'OpenAI Bot Webhook',
            'description': 'Webhook for OpenAI bot integration',
            'content_type': 'application/json'
        }
        
        response = session.post(
            urljoin(mattermost_url, '/api/v4/hooks/outgoing'),
            json=webhook_data
        )
        
        if response.status_code == 201:
            webhook = response.json()
            print(f"✓ Outgoing webhook created: {webhook['id']}")
        else:
            print(f"Failed to create outgoing webhook: {response.text}")
        
        # Create slash command
        print("Creating slash command...")
        command_data = {
            'team_id': team_id,
            'trigger': 'ai',
            'method': 'POST',
            'url': bot_webhook_url.replace('/webhook', '/slash-command'),
            'display_name': 'AI Assistant',
            'description': 'Ask the AI assistant a question',
            'auto_complete': True,
            'auto_complete_desc': 'Ask AI: /ai <your question>',
            'auto_complete_hint': '<your question or prompt>'
        }
        
        response = session.post(
            urljoin(mattermost_url, '/api/v4/commands'),
            json=command_data
        )
        
        if response.status_code == 201:
            command = response.json()
            print(f"✓ Slash command created: /{command['trigger']}")
        else:
            print(f"Failed to create slash command: {response.text}")
        
        # Print configuration summary
        print("\n" + "="*50)
        print("SETUP COMPLETE!")
        print("="*50)
        print(f"Bot Token: {bot_token}")
        print(f"Bot User ID: {bot_id}")
        print(f"Team ID: {team_id}")
        print("\nAdd this to your .env file:")
        print(f"MATTERMOST_TOKEN={bot_token}")
        print("\nUsage:")
        print("- Mention @aibot in any channel")
        print("- Use 'ai: <question>' to ask questions")
        print("- Use '/ai <question>' slash command")
        
        return True
        
    except Exception as e:
        print(f"Setup failed: {e}")
        return False

if __name__ == '__main__':
    if setup_mattermost_bot():
        print("\n✓ Bot setup completed successfully!")
    else:
        print("\n✗ Bot setup failed!")
        sys.exit(1)
