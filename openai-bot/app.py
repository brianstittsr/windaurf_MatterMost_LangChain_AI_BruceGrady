#!/usr/bin/env python3
"""
OpenAI Mattermost Bot
A service that integrates OpenAI with Mattermost for AI-powered conversations.
"""

import os
import json
import logging
import asyncio
from typing import Dict, Any, Optional
from flask import Flask, request, jsonify
from openai import AsyncOpenAI
import aiohttp
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
MATTERMOST_URL = os.getenv('MATTERMOST_URL', 'http://mattermost:8000')
MATTERMOST_TOKEN = os.getenv('MATTERMOST_TOKEN')
BOT_USERNAME = os.getenv('BOT_USERNAME', 'aibot')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4')
MAX_TOKENS = int(os.getenv('MAX_TOKENS', '1000'))
TEMPERATURE = float(os.getenv('TEMPERATURE', '0.7'))

# Initialize OpenAI client
if not OPENAI_API_KEY:
    logger.error("OPENAI_API_KEY environment variable is required")
    exit(1)

openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

class MattermostBot:
    def __init__(self):
        self.session = None
        
    async def init_session(self):
        """Initialize aiohttp session"""
        if not self.session:
            self.session = aiohttp.ClientSession()
    
    async def close_session(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
    
    async def send_message(self, channel_id: str, message: str, thread_id: Optional[str] = None):
        """Send a message to Mattermost channel"""
        await self.init_session()
        
        url = f"{MATTERMOST_URL}/api/v4/posts"
        headers = {
            'Authorization': f'Bearer {MATTERMOST_TOKEN}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'channel_id': channel_id,
            'message': message
        }
        
        if thread_id:
            payload['root_id'] = thread_id
        
        try:
            async with self.session.post(url, headers=headers, json=payload) as response:
                if response.status == 201:
                    logger.info(f"Message sent successfully to channel {channel_id}")
                    return await response.json()
                else:
                    logger.error(f"Failed to send message: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return None
    
    async def get_channel_history(self, channel_id: str, limit: int = 10):
        """Get recent messages from a channel for context"""
        await self.init_session()
        
        url = f"{MATTERMOST_URL}/api/v4/channels/{channel_id}/posts"
        headers = {
            'Authorization': f'Bearer {MATTERMOST_TOKEN}',
        }
        
        params = {'per_page': limit}
        
        try:
            async with self.session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Failed to get channel history: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error getting channel history: {e}")
            return None

bot = MattermostBot()

async def generate_ai_response(prompt: str, context: Optional[str] = None) -> str:
    """Generate AI response using OpenAI"""
    try:
        messages = [
            {
                "role": "system",
                "content": "You are a helpful AI assistant integrated with Mattermost. Be concise, helpful, and professional. If you're responding in a team chat, keep responses focused and relevant to the conversation."
            }
        ]
        
        if context:
            messages.append({
                "role": "system",
                "content": f"Recent conversation context: {context}"
            })
        
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        response = await openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE
        )
        
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        logger.error(f"Error generating AI response: {e}")
        return f"Sorry, I encountered an error: {str(e)}"

def extract_context_from_history(history_data: Dict[str, Any]) -> str:
    """Extract relevant context from channel history"""
    if not history_data or 'posts' not in history_data:
        return ""
    
    posts = history_data['posts']
    context_messages = []
    
    # Get the last few messages for context
    for post_id in list(posts.keys())[-5:]:  # Last 5 messages
        post = posts[post_id]
        message = post.get('message', '').strip()
        if message and not message.startswith('@aibot'):
            context_messages.append(message)
    
    return " | ".join(context_messages)

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming webhooks from Mattermost"""
    try:
        data = request.json
        
        # Skip if no data
        if not data:
            return jsonify({'status': 'no data'}), 200
        
        # Extract message info
        text = data.get('text', '').strip()
        channel_id = data.get('channel_id')
        user_name = data.get('user_name')
        trigger_word = data.get('trigger_word', '')
        
        # Skip if bot is talking to itself
        if user_name == BOT_USERNAME:
            return jsonify({'status': 'ignored - bot message'}), 200
        
        # Skip if no trigger word or mention
        if not (trigger_word or '@aibot' in text.lower() or text.lower().startswith('ai:')):
            return jsonify({'status': 'ignored - no trigger'}), 200
        
        # Clean the message
        clean_text = text.replace(trigger_word, '').replace('@aibot', '').replace('ai:', '').strip()
        
        if not clean_text:
            clean_text = "Hello! How can I help you?"
        
        # Process the request asynchronously
        asyncio.create_task(process_ai_request(channel_id, clean_text, data))
        
        return jsonify({'status': 'processing'}), 200
    
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({'error': str(e)}), 500

async def process_ai_request(channel_id: str, prompt: str, original_data: Dict[str, Any]):
    """Process AI request asynchronously"""
    try:
        # Get channel context
        history = await bot.get_channel_history(channel_id, limit=5)
        context = extract_context_from_history(history) if history else None
        
        # Generate AI response
        ai_response = await generate_ai_response(prompt, context)
        
        # Send response back to Mattermost
        thread_id = original_data.get('post_id')  # Reply in thread if available
        await bot.send_message(channel_id, ai_response, thread_id)
        
    except Exception as e:
        logger.error(f"Error processing AI request: {e}")
        await bot.send_message(channel_id, f"Sorry, I encountered an error: {str(e)}")

@app.route('/slash-command', methods=['POST'])
def slash_command():
    """Handle slash commands from Mattermost"""
    try:
        data = request.form.to_dict()
        
        command = data.get('command', '')
        text = data.get('text', '').strip()
        channel_id = data.get('channel_id')
        user_name = data.get('user_name')
        
        if command == '/ai':
            if not text:
                return jsonify({
                    'response_type': 'ephemeral',
                    'text': 'Usage: `/ai <your question or prompt>`'
                })
            
            # Process the request asynchronously
            asyncio.create_task(process_ai_request(channel_id, text, data))
            
            return jsonify({
                'response_type': 'in_channel',
                'text': f'🤖 Processing your request: "{text[:100]}{"..." if len(text) > 100 else ""}"'
            })
        
        return jsonify({'text': 'Unknown command'}), 400
    
    except Exception as e:
        logger.error(f"Slash command error: {e}")
        return jsonify({'text': f'Error: {str(e)}'}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'openai_configured': bool(OPENAI_API_KEY),
        'mattermost_configured': bool(MATTERMOST_TOKEN)
    })

@app.route('/interactive', methods=['POST'])
def interactive():
    """Handle interactive components (buttons, menus, etc.)"""
    try:
        data = request.json
        
        # Handle different interactive actions
        action = data.get('context', {}).get('action')
        
        if action == 'regenerate':
            # Regenerate the last response
            channel_id = data.get('channel', {}).get('id')
            original_prompt = data.get('context', {}).get('prompt', 'Please regenerate your response')
            
            asyncio.create_task(process_ai_request(channel_id, f"Please provide an alternative response to: {original_prompt}", data))
            
            return jsonify({'update': {'message': '🔄 Regenerating response...'}})
        
        return jsonify({'text': 'Action not recognized'}), 400
    
    except Exception as e:
        logger.error(f"Interactive error: {e}")
        return jsonify({'text': f'Error: {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'false').lower() == 'true'
    
    logger.info(f"Starting OpenAI Mattermost Bot on port {port}")
    logger.info(f"OpenAI Model: {OPENAI_MODEL}")
    logger.info(f"Mattermost URL: {MATTERMOST_URL}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
