import os
import asyncio
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime
import json
import io
import base64

from telegram_client import TelegramChannelClient
from message_parser import MessageParser

# Will be initialized after lifespan definition

# Initialize clients
telegram_client = TelegramChannelClient()
message_parser = MessageParser()

# Cache for messages
messages_cache: List[Dict[str, Any]] = []
cache_timestamp: Optional[datetime] = None
CACHE_DURATION_MINUTES = 30

class FilterRequest(BaseModel):
    min_price: Optional[int] = None
    max_price: Optional[int] = None
    location: Optional[str] = None
    days: Optional[int] = 30

class MessageResponse(BaseModel):
    # FAIL FAST: Required fields MUST exist
    id: int
    date: str
    text: str
    views: int
    link: str

    # Optional fields (can be missing)
    price: Optional[int] = None
    location: List[str] = []
    photo_ids: List[int] = []
    raw_text: Optional[str] = None
    channel: Optional[str] = None  # Source channel

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown"""
    # Startup
    await telegram_client.connect()
    print("✅ Telegram client connected successfully")

    yield

    # Shutdown
    await telegram_client.disconnect()
    print("👋 Telegram client disconnected")

# Update app initialization to use lifespan
app = FastAPI(title="Telegram Rental Filter", lifespan=lifespan)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def check_ip_allowed(request: Request) -> bool:
    """Check if client IP is allowed to access registration page"""
    allowed_ip = os.getenv('ALLOWED_IP', '127.0.0.1')
    client_ip = request.client.host

    # Support multiple IPs separated by comma
    allowed_ips = [ip.strip() for ip in allowed_ip.split(',')]

    return client_ip in allowed_ips

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main HTML page

    FAIL FAST: If index.html missing - crash
    """
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Registration page with QR code login - IP restricted"""
    if not check_ip_allowed(request):
        raise HTTPException(
            status_code=403,
            detail=f"Access denied. Your IP {request.client.host} is not allowed to access this page."
        )

    with open("static/register.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/api/channel-info")
async def get_channel_info(channel: Optional[str] = Query(None)):
    """Get information about the configured channel
    
    FAIL FAST: Let errors propagate to FastAPI error handler
    """
    if channel:
        telegram_client.channel_name = channel
    
    return await telegram_client.get_channel_info()

@app.get("/api/current-channel")
async def get_current_channel():
    """Get the currently configured channel name"""
    return {
        "channel": telegram_client.channel_name or os.getenv('TELEGRAM_CHANNEL', ''),
        "source": "runtime" if telegram_client.channel_name != os.getenv('TELEGRAM_CHANNEL') else "env"
    }

@app.get("/api/current-channels")
async def get_current_channels():
    """Get the currently configured channels"""
    # Support both single channel from env and multiple channels
    env_channels = os.getenv('TELEGRAM_CHANNEL', '')
    channels = [env_channels] if env_channels else []
    return {
        "channels": channels,
        "source": "env"
    }

async def _fetch_from_single_channel(channel: str, days: int, session_string: str) -> List[Dict[str, Any]]:
    """Fetch messages from a single channel using independent client with StringSession"""
    try:
        # Create independent client with StringSession (no SQLite conflicts!)
        from telethon import TelegramClient
        from telethon.sessions import StringSession

        api_id = int(os.getenv('TELEGRAM_API_ID'))
        api_hash = os.getenv('TELEGRAM_API_HASH')

        # Create client with string session - fully independent!
        client = TelegramClient(StringSession(session_string), api_id, api_hash)
        await client.connect()

        if not await client.is_user_authorized():
            print(f"❌ Not authorized for channel {channel}")
            await client.disconnect()
            return []

        print(f"🔄 Fetching from {channel}...")

        # Calculate date limit
        from datetime import timedelta
        date_limit = datetime.now() - timedelta(days=days)

        messages = []

        # Get channel entity
        channel_entity = await client.get_entity(channel)

        # Fetch messages
        from typing import Set
        processed_groups: Set[int] = set()
        all_messages = []

        async for message in client.iter_messages(channel_entity, limit=None):
            if message.date.replace(tzinfo=None) < date_limit:
                break
            all_messages.append(message)

        print(f"📊 Processing {len(all_messages)} messages from {channel}...")

        # Process messages
        for message in all_messages:
            if message.grouped_id and message.grouped_id in processed_groups:
                continue

            if not message.text:
                continue

            msg_data = {
                'id': message.id,
                'date': message.date.isoformat(),
                'text': message.text,
                'views': message.views or 0,
                'link': f"https://t.me/{channel.replace('@', '')}/{message.id}",
                'photo_ids': [],
                'channel': channel
            }

            # Handle grouped media
            if message.grouped_id:
                group_messages = [m for m in all_messages if m.grouped_id == message.grouped_id]
                processed_groups.add(message.grouped_id)

                for grouped_msg in group_messages:
                    from telethon.tl.types import MessageMediaPhoto
                    if grouped_msg.media and isinstance(grouped_msg.media, MessageMediaPhoto):
                        msg_data['photo_ids'].append(grouped_msg.id)

            # Handle single photo
            elif message.media:
                from telethon.tl.types import MessageMediaPhoto
                if isinstance(message.media, MessageMediaPhoto):
                    msg_data['photo_ids'].append(message.id)

            # Parse message
            parsed_data = message_parser.parse_message(msg_data['text'], existing_data=msg_data)
            msg_data.update(parsed_data)

            messages.append(msg_data)

        # Disconnect this independent client
        await client.disconnect()
        print(f"✅ Fetched {len(messages)} messages from {channel}")

        return messages

    except ValueError as e:
        print(f"❌ Error fetching from {channel}: {e}")
        return []
    except Exception as e:
        print(f"❌ Unexpected error fetching from {channel}: {e}")
        import traceback
        traceback.print_exc()
        return []

async def _fetch_and_cache_messages(days: int = 30, channels: Optional[List[str]] = None):
    """Internal helper function to fetch and cache messages from multiple channels in parallel

    FAIL FAST: Let errors propagate
    """
    global messages_cache, cache_timestamp

    # If no channels provided, try to use env variable
    if not channels:
        env_channel = os.getenv('TELEGRAM_CHANNEL', '')
        if env_channel:
            channels = [env_channel]

    # FAIL FAST: At least one channel must be set
    if not channels or len(channels) == 0:
        raise HTTPException(
            status_code=400,
            detail="No Telegram channels configured. Please provide 'channels' parameter."
        )

    # Clear old photos cache before fetching new messages
    import shutil
    photos_dir = os.path.join(os.path.dirname(__file__), 'static', 'photos')
    if os.path.exists(photos_dir):
        try:
            # Count files before deletion
            file_count = len([f for f in os.listdir(photos_dir) if os.path.isfile(os.path.join(photos_dir, f))])
            if file_count > 0:
                print(f"🗑️ Clearing {file_count} old photos from cache...")
                shutil.rmtree(photos_dir)
                os.makedirs(photos_dir, exist_ok=True)
                print("✅ Photo cache cleared")
        except Exception as e:
            print(f"⚠️ Could not clear photo cache: {e}")

    # Get session string for creating parallel clients
    session_string = telegram_client.get_session_string()
    if not session_string:
        raise HTTPException(
            status_code=401,
            detail="Not authorized. Please login via /register page first."
        )

    print(f"🚀 Starting PARALLEL fetch from {len(channels)} channels...")

    # Fetch from all channels in PARALLEL using asyncio.gather!
    # Each channel gets its own independent client with StringSession
    tasks = [_fetch_from_single_channel(channel, days, session_string) for channel in channels]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Combine all messages
    all_parsed_messages = []
    successful_channels = 0

    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"❌ Exception in channel {channels[i]}: {result}")
            continue

        if isinstance(result, list):
            all_parsed_messages.extend(result)
            if len(result) > 0:
                successful_channels += 1

    # Update cache
    messages_cache = all_parsed_messages
    cache_timestamp = datetime.now()

    print(f"✅ Total: {len(all_parsed_messages)} messages from {successful_channels}/{len(channels)} channels")

    return {
        "status": "success",
        "total_messages": len(all_parsed_messages),
        "channels_requested": len(channels),
        "channels_successful": successful_channels,
        "cache_updated": cache_timestamp.isoformat()
    }

class FetchMessagesRequest(BaseModel):
    channels: List[str]
    days: int = 30

@app.post("/api/fetch-messages")
async def fetch_messages(request: FetchMessagesRequest):
    """Fetch messages from multiple Telegram channels

    FAIL FAST: Let errors propagate
    """
    if request.days < 1 or request.days > 90:
        raise HTTPException(status_code=400, detail="Days must be between 1 and 90")

    return await _fetch_and_cache_messages(days=request.days, channels=request.channels)

@app.get("/api/photo/{message_id}")
async def download_photo(message_id: int, channel: str = Query(..., description="Channel name (e.g. @channel_name)")):
    """Download a specific photo by message ID (lazy loading)

    Args:
        message_id: The ID of the message containing the photo
        channel: The name of the channel where the photo is located

    FAIL FAST: If photo doesn't exist - let telegram_client raise exception
    """
    photo_url = await telegram_client.download_photo(message_id, channel)
    return {"photo_url": photo_url}

@app.get("/api/messages", response_model=List[MessageResponse])
async def get_messages(
    min_price: Optional[int] = Query(None, ge=0),
    max_price: Optional[int] = Query(None, ge=0),
    location: Optional[str] = Query(None),
    exclude_areas: Optional[str] = Query(None),
    sort_by: Optional[str] = Query("date_desc", pattern="^(date_desc|date_asc|price_desc|price_asc)$"),
    refresh: bool = Query(False)
):
    """Get filtered messages

    Returns empty list if no channels configured or no messages cached
    """
    global messages_cache, cache_timestamp

    # If no messages cached, return empty list (not an error)
    if not messages_cache:
        return []

    # Check if we need to refresh cache
    if refresh and cache_timestamp and \
       (datetime.now() - cache_timestamp).total_seconds() > CACHE_DURATION_MINUTES * 60:
        # Try to refresh, but don't fail if no channels configured
        try:
            await _fetch_and_cache_messages(days=30)
        except HTTPException:
            pass  # Ignore if no channels configured
    
    # Filter messages
    filtered_messages = message_parser.filter_messages(
        messages_cache,
        min_price=min_price,
        max_price=max_price,
        location_filter=location,
        exclude_areas=exclude_areas
    )
    
    # Sort messages - FAIL FAST: date and price MUST exist
    if sort_by == "date_desc":
        filtered_messages.sort(key=lambda x: x['date'], reverse=True)
    elif sort_by == "date_asc":
        filtered_messages.sort(key=lambda x: x['date'])
    elif sort_by == "price_desc":
        filtered_messages.sort(key=lambda x: x.get('price') or 0, reverse=True)
    elif sort_by == "price_asc":
        filtered_messages.sort(key=lambda x: x.get('price') or float('inf'))
    
    return filtered_messages

@app.get("/api/stats")
async def get_stats():
    """Get statistics about cached messages"""
    if not messages_cache:
        return {
            "total_messages": 0,
            "messages_with_price": 0,
            "messages_with_location": 0,
            "cache_age_minutes": None
        }

    messages_with_price = sum(1 for msg in messages_cache if msg.get('price'))
    messages_with_location = sum(1 for msg in messages_cache if msg.get('location'))

    cache_age = None
    if cache_timestamp:
        cache_age = (datetime.now() - cache_timestamp).total_seconds() / 60

    return {
        "total_messages": len(messages_cache),
        "messages_with_price": messages_with_price,
        "messages_with_location": messages_with_location,
        "cache_age_minutes": cache_age,
        "cache_updated": cache_timestamp.isoformat() if cache_timestamp else None
    }

@app.get("/api/auth-status")
async def get_auth_status(request: Request):
    """Check if main telegram client is authorized - IP restricted for debugging"""
    if not check_ip_allowed(request):
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        is_authorized = await telegram_client.client.is_user_authorized()

        if is_authorized:
            me = await telegram_client.client.get_me()
            return {
                "authorized": True,
                "user": {
                    "first_name": me.first_name,
                    "username": me.username,
                    "phone": me.phone
                }
            }
        else:
            return {
                "authorized": False,
                "message": "Not authorized. Please login via /register"
            }
    except Exception as e:
        return {
            "authorized": False,
            "error": str(e)
        }

@app.get("/api/qr-login")
async def get_qr_login(request: Request):
    """Generate QR code for Telegram login - IP restricted"""
    if not check_ip_allowed(request):
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        from telethon import TelegramClient
        import qrcode

        api_id = int(os.getenv('TELEGRAM_API_ID'))
        api_hash = os.getenv('TELEGRAM_API_HASH')

        # Check if main client is connected, reconnect if needed
        if not telegram_client.client or not telegram_client.client.is_connected():
            await telegram_client.connect()

        # Use existing telegram_client to check authorization
        if await telegram_client.client.is_user_authorized():
            me = await telegram_client.client.get_me()
            return {
                "status": "already_authorized",
                "user": {
                    "first_name": me.first_name,
                    "username": me.username
                }
            }

        # Create temporary client for QR login with different session name
        qr_client = TelegramClient('qr_temp_session', api_id, api_hash)
        await qr_client.connect()

        # Generate QR code
        qr_login = await qr_client.qr_login()

        # Generate QR code as base64 image
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(qr_login.url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # Convert to base64
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()

        # Store qr_login object for checking status
        app.state.qr_login = qr_login
        app.state.qr_client = qr_client
        app.state.qr_authorized = False  # Flag to track authorization

        # Create background task to wait for QR scan (only once!)
        async def wait_for_qr():
            try:
                await qr_login.wait()  # This will block until QR is scanned
                app.state.qr_authorized = True
                print("✅ QR code scanned - user authorized!")
            except Exception as e:
                print(f"❌ QR wait error: {e}")

        # Start background task
        asyncio.create_task(wait_for_qr())

        return {
            "status": "qr_ready",
            "qr_code": f"data:image/png;base64,{img_str}",
            "url": qr_login.url
        }

    except Exception as e:
        print(f"Error generating QR code: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/qr-login-status")
async def check_qr_login_status(request: Request):
    """Check if QR code was scanned and user is authorized - IP restricted"""
    if not check_ip_allowed(request):
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        if not hasattr(app.state, 'qr_login') or not hasattr(app.state, 'qr_client'):
            return {"status": "no_qr_generated"}

        qr_login = app.state.qr_login
        qr_client = app.state.qr_client

        # Check the flag set by background task
        if not hasattr(app.state, 'qr_authorized') or not app.state.qr_authorized:
            return {"status": "waiting"}

        # Double check authorization
        is_auth = await qr_client.is_user_authorized()

        if is_auth:
            print("✅ QR code scanned successfully")
            me = await qr_client.get_me()

            user_info = {
                "first_name": me.first_name,
                "username": me.username
            }

            # Disconnect QR client first
            await qr_client.disconnect()
            await asyncio.sleep(1)

            # Copy session to main session file
            import shutil
            try:
                if os.path.exists('qr_temp_session.session'):
                    # Disconnect main client to release lock
                    await telegram_client.client.disconnect()
                    await asyncio.sleep(0.5)

                    # Copy and cleanup
                    shutil.copy2('qr_temp_session.session', 'session_name.session')
                    os.remove('qr_temp_session.session')
                    if os.path.exists('qr_temp_session.session-journal'):
                        os.remove('qr_temp_session.session-journal')

                    # Reconnect to reload session from disk
                    is_authorized = await telegram_client.reconnect()

                    if is_authorized:
                        print("✅ Authorization successful - main client reconnected")
                    else:
                        print("⚠️ Authorization failed - please try again")
                else:
                    print("❌ Session file not found")

            except Exception as copy_error:
                print(f"❌ Error during authorization: {copy_error}")
                import traceback
                traceback.print_exc()

            # Clean up state
            delattr(app.state, 'qr_login')
            delattr(app.state, 'qr_client')

            return {
                "status": "authorized",
                "user": user_info
            }

        return {"status": "waiting"}

    except Exception as e:
        print(f"❌ QR login error: {e}")
        return {"status": "error", "message": str(e)}

# Mount static files (if the directory exists)
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except RuntimeError:
    pass

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    uvicorn.run(app, host=host, port=port)
