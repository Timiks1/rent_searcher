import os
import asyncio
from datetime import datetime, timedelta
from telethon import TelegramClient
from telethon.tl.types import Channel, MessageMediaPhoto, MessageMediaDocument
from typing import List, Dict, Any, Set
from dotenv import load_dotenv
import hashlib

load_dotenv()

# Create photos directory if it doesn't exist
PHOTOS_DIR = os.path.join(os.path.dirname(__file__), 'static', 'photos')
os.makedirs(PHOTOS_DIR, exist_ok=True)

class TelegramChannelClient:
    def __init__(self):
        # FAIL FAST: If env vars missing - crash immediately
        api_id = os.getenv('TELEGRAM_API_ID')
        api_hash = os.getenv('TELEGRAM_API_HASH')
        phone = os.getenv('TELEGRAM_PHONE')
        
        assert api_id, "TELEGRAM_API_ID is required in .env"
        assert api_hash, "TELEGRAM_API_HASH is required in .env"
        assert phone, "TELEGRAM_PHONE is required in .env"
        
        self.api_id = int(api_id)
        self.api_hash = api_hash
        self.phone = phone
        self.channel_name = os.getenv('TELEGRAM_CHANNEL')
        self.client = None
        
    async def connect(self):
        """Connect to Telegram"""
        self.client = TelegramClient('session_name', self.api_id, self.api_hash)
        await self.client.start(phone=self.phone)
        print("Connected to Telegram")
        
    async def download_photo(self, message_id: int) -> str:
        """Download a specific photo by message ID (on-demand)
        
        FAIL FAST: If photo doesn't exist or download fails - raise exception
        """
        # Connect if not connected
        if not self.client or not self.client.is_connected():
            await self.connect()
        
        # Get channel
        assert self.channel_name, "Channel name must be set"
        channel = await self.client.get_entity(self.channel_name)
        
        # Generate unique filename
        photo_hash = hashlib.md5(f"{message_id}_{self.channel_name}".encode()).hexdigest()
        photo_filename = f"{photo_hash}.jpg"
        photo_path = os.path.join(PHOTOS_DIR, photo_filename)
        
        # Return if already cached
        if os.path.exists(photo_path):
            return f"/static/photos/{photo_filename}"
        
        # Fetch the specific message
        message = await self.client.get_messages(channel, ids=message_id)
        
        # FAIL FAST: Photo MUST exist
        assert message, f"Message {message_id} not found"
        assert message.media, f"Message {message_id} has no media"
        assert isinstance(message.media, MessageMediaPhoto), f"Message {message_id} media is not a photo"
        
        await self.client.download_media(message.media, photo_path)
        print(f"  📥 Downloaded photo for message {message_id}")
        return f"/static/photos/{photo_filename}"
    
    async def disconnect(self):
        """Disconnect from Telegram"""
        if self.client:
            await self.client.disconnect()
            
    async def fetch_messages(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        Fetch messages from the channel for the last N days
        
        Args:
            days: Number of days to look back
            
        Returns:
            List of message dictionaries
        """
        if not self.client:
            await self.connect()
            
        # Calculate the date limit (messages older than this will be skipped)
        date_limit = datetime.now() - timedelta(days=days)
        
        messages = []
        
        try:
            # FAIL FAST: Channel name must be set
            if not self.channel_name:
                raise ValueError("Channel name is not set. Please configure TELEGRAM_CHANNEL in .env file.")
            
            # Get the channel entity
            channel = await self.client.get_entity(self.channel_name)
            
            print(f"Fetching messages from {self.channel_name} (last {days} days)...")
            
            # Track grouped messages to handle albums
            processed_groups: Set[int] = set()
            
            # First pass: collect all messages
            all_messages = []
            async for message in self.client.iter_messages(channel, limit=None):
                # Check if message is too old
                if message.date.replace(tzinfo=None) < date_limit:
                    break
                all_messages.append(message)
            
            print(f"Processing {len(all_messages)} messages (metadata only, photos on-demand)...")
            
            # Second pass: process messages metadata (NO photo downloads yet!)
            for message in all_messages:
                # Skip if already processed as part of a group
                if message.grouped_id and message.grouped_id in processed_groups:
                    continue
                    
                # FAIL FAST: Only process messages with text
                if not message.text:
                    continue
                    
                msg_data = {
                    'id': message.id,
                    'date': message.date.isoformat(),
                    'text': message.text,
                    'views': message.views or 0,  # FAIL FAST: views should exist, if None use 0
                    'link': f"https://t.me/{self.channel_name.replace('@', '')}/{message.id}",
                    'photo_ids': []
                }
                
                # Handle grouped media (albums with video + photos)
                if message.grouped_id:
                    group_messages = [m for m in all_messages if m.grouped_id == message.grouped_id]
                    processed_groups.add(message.grouped_id)
                    
                    for grouped_msg in group_messages:
                        if grouped_msg.media and isinstance(grouped_msg.media, MessageMediaPhoto):
                            msg_data['photo_ids'].append(grouped_msg.id)
                
                # Handle single photo (not grouped)
                elif message.media and isinstance(message.media, MessageMediaPhoto):
                    msg_data['photo_ids'].append(message.id)
                
                messages.append(msg_data)
                    
            print(f"Fetched {len(messages)} messages (from {days} days)")
            if messages:
                latest = datetime.fromisoformat(messages[0]['date']).strftime('%Y-%m-%d %H:%M')
                oldest = datetime.fromisoformat(messages[-1]['date']).strftime('%Y-%m-%d %H:%M')
                print(f"  Latest: {latest}")
                print(f"  Oldest: {oldest}")
            return messages
            
        except ValueError as e:
            # Re-raise ValueError as-is (these are our validation errors)
            raise
        except Exception as e:
            error_msg = str(e)
            if "UsernameInvalidError" in error_msg or "Nobody is using this username" in error_msg:
                raise ValueError(
                    f"Invalid channel name: '{self.channel_name}'. "
                    f"Please check that the channel exists and the name is correct. "
                    f"Channel names should be like '@channelname' or a numeric channel ID."
                ) from e
            print(f"Error fetching messages: {e}")
            raise
            
    async def get_channel_info(self) -> Dict[str, Any]:
        """Get information about the channel
        
        FAIL FAST: If channel doesn't exist or API fails - raise exception
        """
        if not self.client:
            await self.connect()
        
        assert self.channel_name, "Channel name must be set"
        channel = await self.client.get_entity(self.channel_name)
        
        # FAIL FAST: Channel fields MUST exist
        return {
            'title': channel.title,
            'username': channel.username,
            'participants_count': channel.participants_count,
            'description': channel.about
        }


# Example usage
async def main():
    client = TelegramChannelClient()
    try:
        await client.connect()
        info = await client.get_channel_info()
        print(f"Channel info: {info}")
        
        messages = await client.fetch_messages(days=30)
        print(f"Total messages: {len(messages)}")
        
        # Print first 5 messages
        for msg in messages[:5]:
            print(f"\n{msg['date']}: {msg['text'][:100]}...")
            
    finally:
        await client.disconnect()


if __name__ == '__main__':
    asyncio.run(main())
