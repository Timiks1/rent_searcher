# Telegram Rental Filter 🏠

A web application for filtering rental property listings from Telegram channels with price and location search capabilities.

## Features

- 📥 Automatic message fetching from **multiple Telegram channels** simultaneously (last 30 days)
- 💰 Price filtering (minimum and maximum)
- 📍 Location search (city, district, area)
- 🚫 Area exclusion (blacklist unwanted locations)
- 🔄 Multiple sorting options (date, price)
- 📸 Photo gallery with lazy loading
- 🎨 Modern web interface
- 📊 Statistics dashboard
- ⚡ Data caching for fast access
- 🌐 Dynamic multi-channel management
- 📺 Channel source display for each listing

## Requirements

- Python 3.8+
- Telegram account
- Telegram API credentials (get them at https://my.telegram.org)

## Installation

### 1. Clone the project or download files

```bash
cd "telegram rent"
```

### 2. Create virtual environment (recommended)

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure settings

Create `.env` file based on `.env.example`:

```bash
cp .env.example .env
```

Open `.env` and fill in the following parameters:

```env
# Get API ID and Hash at https://my.telegram.org
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash

# Your phone number in international format
TELEGRAM_PHONE=+79991234567

# Channel name (with @ or ID)
TELEGRAM_CHANNEL=@channel_username

# Server settings (defaults are fine)
HOST=0.0.0.0
PORT=8000
```

#### How to get API credentials:

1. Go to https://my.telegram.org
2. Log in with your phone number
3. Navigate to "API development tools"
4. Create a new application
5. Copy `api_id` and `api_hash`

## Running

### First Run (Telegram Authentication)

On first run, you need to authenticate with Telegram **using QR code**:

```bash
python qr_login.py
```

**A QR code will appear in the terminal:**

1. Open Telegram on your phone
2. Go to **Settings** → **Devices** → **Link Desktop Device**
3. Scan the QR code from terminal
4. ✅ Done! A session file `session_name.session` will be created

💡 **QR login is more secure** - no need to enter SMS codes!

### Start the web server

```bash
python main.py
```

or using uvicorn:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Open your browser and go to: http://localhost:8000

## Usage

### Web Interface

1. **Set Telegram Channels** - enter multiple channel names (one per line, e.g., `@arenda_kvartir`) and click 💾
2. **Refresh Messages** - fetch latest messages from **all specified channels simultaneously**
3. **Set Filters**:
   - Minimum price (VND/USD)
   - Maximum price (VND/USD)
   - Location (e.g., "Da Nang", "District 1", "An Thuong")
   - Exclude areas (e.g., "Son Tra, Lien Chieu")
4. **Apply Filters** - show only matching listings
5. **Sort** - by date or price (ascending/descending)
6. **Reset** - clear all filters

💡 **Multiple channels can be managed dynamically** in the web interface - no need to edit `.env` file!
📺 **Each listing shows its source channel** so you know where it came from.

### API Endpoints

The application provides a REST API:

- `GET /` - Main page (web interface)
- `GET /api/channel-info?channel=@name` - Get channel information
- `GET /api/current-channels` - Get currently configured channels
- `POST /api/fetch-messages` - Fetch messages from multiple channels (JSON body: `{"channels": ["@ch1", "@ch2"], "days": 30}`)
- `GET /api/messages?min_price=X&max_price=Y&location=Z` - Get filtered messages
- `GET /api/photo/{message_id}` - Download photo (lazy loading)
- `GET /api/stats` - Statistics for loaded messages

#### Request Examples:

```bash
# Get all messages
curl http://localhost:8000/api/messages

# Filter by price
curl "http://localhost:8000/api/messages?min_price=10000000&max_price=20000000"

# Filter by location
curl "http://localhost:8000/api/messages?location=Da+Nang"

# Exclude areas
curl "http://localhost:8000/api/messages?exclude_areas=Son+Tra,Lien+Chieu"

# Combined filter with sorting
curl "http://localhost:8000/api/messages?min_price=10000000&max_price=15000000&location=My+An&sort_by=price_asc"

# Refresh messages from multiple Telegram channels
curl -X POST "http://localhost:8000/api/fetch-messages" \
  -H "Content-Type: application/json" \
  -d '{"channels": ["@DaNangApartmentRent", "@VietnamRentals"], "days": 30}'
```

## Project Structure

```
telegram rent/
├── main.py                 # FastAPI web server
├── telegram_client.py      # Telegram API client
├── message_parser.py       # Parser for extracting price and location
├── qr_login.py            # QR code authentication
├── requirements.txt        # Python dependencies
├── .env                    # Configuration (create manually)
├── .env.example           # Example configuration
├── .gitignore             # Ignored files
├── README.md              # Documentation
└── static/                # Web interface
    ├── index.html         # HTML page
    ├── styles.css         # Styles
    ├── script.js          # JavaScript code
    └── photos/            # Downloaded photos cache
```

## Parser Configuration

The parser automatically recognizes:

### Prices:

- **VND (Vietnamese Dong)**: "15 triệu", "12tr VND", "20 million dong", "15 млн ₫"
- **USD**: "$500", "500 usd", "500 dollars"
- **General patterns**: "price: 15000000", "Price: 500"

### Locations:

- **Cities**: Hanoi, Ho Chi Minh (Saigon), Da Nang, Nha Trang, Hoi An, Vung Tau, Phu Quoc
- **Districts**: "District 1", "Quận 3", "район 7", "Son Tra"
- **Areas**: "My An", "An Thuong", "Thanh Khe"
- **Streets**: "đường Lê Lợi", "Tran Phu street"
- **Keywords**: beach, city center, downtown, trung tâm

To add new patterns, edit the `message_parser.py` file.

## Troubleshooting

### Authentication Error

If you get an error when running `qr_login.py`:

- Check that API_ID and API_HASH are correct
- Verify phone number is in international format (+7...)
- Check internet connection
- Make sure you scan the QR code within the time limit

### Messages Not Loading

- Ensure the channel is public or you are a member
- Check that channel name is correct (should start with @)
- Try using channel ID instead of username
- Verify you have an active session (`session_name.session` exists)

### Server Won't Start

- Check that port 8000 is not occupied by another application
- Try changing the port in `.env` file
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check terminal logs for specific error messages

### Photos Not Loading

- Photos are loaded lazily when you scroll
- Check browser console (F12) for errors
- Verify `/static/photos/` directory exists and is writable
- Check network tab in browser DevTools

## Security

⚠️ **Important:**

- Do not publish the `.env` file with your API credentials
- The `session_name.session` file contains authorization tokens - keep it secure
- Use `.gitignore` to avoid committing sensitive data
- QR login is more secure than SMS code login

## Performance

### Lazy Loading

- Photos are downloaded **on-demand** when visible
- First load: ~5 seconds (metadata only)
- Photos load progressively as you scroll
- Cached photos load instantly

### Fail Fast Philosophy

The application follows **fail-fast** principles:

- Missing required environment variables → immediate crash
- Invalid data → explicit error (no silent fallbacks)
- API errors → clear error messages
- Easier debugging and faster bug detection

## License

MIT License - free to use for your projects.

## Support

If you have questions or found a bug:

1. Check the Troubleshooting section
2. Ensure you're using the latest dependencies
3. Check console logs
4. Verify `.env` configuration

## Possible Improvements

- [ ] Add database for persistent storage
- [ ] Implement notifications for new listings
- [ ] Add more filters (rooms, square footage)
- [ ] Export results to CSV/Excel
- [ ] Telegram bot for management
- [ ] Multi-language interface
- [ ] Price history tracking
- [ ] Favorite listings
- [ ] Email alerts
