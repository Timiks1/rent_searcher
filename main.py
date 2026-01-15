import os
import asyncio
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime
import json

from telegram_client import TelegramChannelClient
from message_parser import MessageParser

app = FastAPI(title="Telegram Rental Filter")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

@app.on_event("startup")
async def startup_event():
    """Initialize Telegram client on startup
    
    FAIL FAST: If connection fails - crash the app
    """
    await telegram_client.connect()
    print("✅ Telegram client connected successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await telegram_client.disconnect()

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main HTML page
    
    FAIL FAST: If index.html missing - crash
    """
    with open("static/index.html", "r", encoding="utf-8") as f:
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

async def _fetch_and_cache_messages(days: int = 30, channel: Optional[str] = None):
    """Internal helper function to fetch and cache messages
    
    FAIL FAST: Let errors propagate
    """
    global messages_cache, cache_timestamp
    
    if channel:
        telegram_client.channel_name = channel
    
    # FAIL FAST: Channel name must be set
    if not telegram_client.channel_name:
        raise HTTPException(
            status_code=400,
            detail="Telegram channel not configured. Please set TELEGRAM_CHANNEL in .env file or provide 'channel' parameter."
        )
    
    # Fetch and parse messages
    try:
        messages = await telegram_client.fetch_messages(days=days)
    except ValueError as e:
        # Convert ValueError to HTTPException for better API responses
        raise HTTPException(status_code=400, detail=str(e))
    
    parsed_messages = []
    for msg in messages:
        parsed_data = message_parser.parse_message(msg['text'], existing_data=msg)
        msg.update(parsed_data)
        parsed_messages.append(msg)
    
    # Update cache
    messages_cache = parsed_messages
    cache_timestamp = datetime.now()
    
    return {
        "status": "success",
        "total_messages": len(parsed_messages),
        "cache_updated": cache_timestamp.isoformat()
    }

@app.post("/api/fetch-messages")
async def fetch_messages(
    days: int = Query(30, ge=1, le=90),
    channel: Optional[str] = Query(None)
):
    """Fetch messages from Telegram channel
    
    FAIL FAST: Let errors propagate
    """
    return await _fetch_and_cache_messages(days=days, channel=channel)

@app.get("/api/photo/{message_id}")
async def download_photo(message_id: int):
    """Download a specific photo by message ID (lazy loading)
    
    FAIL FAST: If photo doesn't exist - let telegram_client raise exception
    """
    photo_url = await telegram_client.download_photo(message_id)
    return {"photo_url": photo_url}

@app.get("/api/messages", response_model=List[MessageResponse])
async def get_messages(
    min_price: Optional[int] = Query(None, ge=0),
    max_price: Optional[int] = Query(None, ge=0),
    location: Optional[str] = Query(None),
    exclude_areas: Optional[str] = Query(None),
    sort_by: Optional[str] = Query("date_desc", regex="^(date_desc|date_asc|price_desc|price_asc)$"),
    refresh: bool = Query(False)
):
    """Get filtered messages
    
    FAIL FAST: If cache empty and fetch fails - let it crash
    """
    global messages_cache, cache_timestamp
    
    # Check if we need to refresh cache
    if refresh or not messages_cache or not cache_timestamp or \
       (datetime.now() - cache_timestamp).total_seconds() > CACHE_DURATION_MINUTES * 60:
        # FAIL FAST: If this fails, let it crash
        await _fetch_and_cache_messages(days=30)
    
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
