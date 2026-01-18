# Telegram Rental Filter 🏠

A web application for filtering rental property listings from Telegram channels with price and location search capabilities.

## Features

- 📥 Automatic message fetching from **multiple Telegram channels** simultaneously (last 30 days)
- 💰 Price filtering (minimum and maximum)
- 📍 Location search (city, district, area)
- 🚫 Area exclusion (blacklist unwanted locations)
- 🔄 Multiple sorting options (date, price)
- 📸 Photo gallery with lazy loading and navigation
- 🖼️ Full-screen photo viewer with gallery navigation
- 🎨 Modern web interface
- 📊 Statistics dashboard
- ⚡ Data caching for fast access
- 🌐 Dynamic multi-channel management
- 📺 Channel source display for each listing
- 🌍 **Multi-language support** (Ukrainian 🇺🇦 / Vietnamese 🇻🇳)
- 🔐 **Web-based QR authentication** - no terminal needed!

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

### Start the web server

First, start the application:

```bash
python main.py
```

or using uvicorn:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Open your browser and go to: http://localhost:8000

### First Time: Telegram Authentication

If you haven't authenticated yet, you'll need to log in with Telegram:

**Option 1: Web-based QR Login (Recommended)** 🌐

1. Navigate to http://localhost:8000/register in your browser
2. A QR code will appear automatically
3. Open Telegram on your phone
4. Go to **Settings** → **Devices** → **Link Desktop Device**
5. Scan the QR code from the browser
6. ✅ You'll be redirected to the main page automatically!

**Option 2: Terminal QR Login** 💻

```bash
python qr_login.py
```

A QR code will appear in the terminal - scan it the same way as above.

💡 **QR login is more secure** - no SMS codes needed!

## Usage

### Web Interface

1. **Choose Language** 🌍 - select Ukrainian 🇺🇦 or Vietnamese 🇻🇳 from the top-right selector (preference is saved)
2. **Set Telegram Channels** - enter channel names (e.g., `@arenda_kvartir`) and click ➕ to add
3. **Refresh Messages** ⟳ - fetch latest messages from **all specified channels simultaneously**
4. **Set Filters**:
   - Minimum price (VND/USD)
   - Maximum price (VND/USD)
   - Location whitelist (e.g., "Da Nang", "District 1", "An Thuong")
   - Exclude areas blacklist (e.g., "Son Tra, Lien Chieu")
5. **Apply Filters** 🔍 - show only matching listings
6. **Sort** 📊 - by date or price (ascending/descending)
7. **Reset** ↺ - clear all filters
8. **View Photos** 📸 - click any photo to open full-screen gallery with navigation (← →)

💡 **Multiple channels can be managed dynamically** in the web interface - no need to edit `.env` file!
📺 **Each listing shows its source channel** so you know where it came from.
🌍 **All UI elements are translated** - switch languages anytime with one click!

### API Endpoints

The application provides a REST API:

**Main Pages:**
- `GET /` - Main page (web interface)
- `GET /register` - QR authentication page

**Authentication:**
- `GET /api/qr-login` - Generate QR code for authentication
- `GET /api/qr-login-status` - Check QR authentication status

**Channels & Messages:**
- `GET /api/channel-info?channel=@name` - Get channel information
- `GET /api/current-channels` - Get currently configured channels
- `POST /api/fetch-messages` - Fetch messages from multiple channels (JSON body: `{"channels": ["@ch1", "@ch2"], "days": 30}`)
- `GET /api/messages?min_price=X&max_price=Y&location=Z` - Get filtered messages
- `GET /api/photo/{photo_id}?channel=@name` - Download photo (lazy loading)
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
├── main.py                 # FastAPI web server with QR auth endpoints
├── telegram_client.py      # Telegram API client
├── message_parser.py       # Parser for extracting price and location
├── qr_login.py            # Terminal QR code authentication
├── requirements.txt        # Python dependencies
├── .env                    # Configuration (create manually)
├── .env.example           # Example configuration
├── .gitignore             # Ignored files
├── README.md              # Documentation
└── static/                # Web interface
    ├── index.html         # Main page (Ukrainian/Vietnamese)
    ├── register.html      # QR authentication page
    ├── styles.css         # Styles
    ├── script.js          # Main JavaScript code
    ├── translations.js    # i18n translations (UA/VI)
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

## Internationalization (i18n)

The application supports multiple languages with easy switching:

### Supported Languages

- 🇺🇦 **Ukrainian (Українська)** - Default language
- 🇻🇳 **Vietnamese (Tiếng Việt)** - Full translation

### How It Works

- **Client-side translations** using `translations.js`
- **localStorage persistence** - language choice is saved in browser
- **Dynamic switching** - change language without page reload
- **Complete coverage** - all UI elements, notifications, and messages are translated
- **Data-driven** - uses `data-i18n` attributes for automatic translation

### Adding New Languages

To add a new language (e.g., English):

1. Open `static/translations.js`
2. Add a new language object:
```javascript
en: {
    'app.title': '🏠 Rental Listings Filter',
    'app.subtitle': 'Search housing from Telegram channels',
    // ... add all translation keys
}
```
3. Add option to language selector in `static/index.html`:
```html
<option value="en">🇬🇧 English</option>
```
4. Translations will apply automatically!

## Troubleshooting

### Authentication Error

**Web-based QR login** (recommended):
- Navigate to `/register` page in browser
- QR code should appear automatically
- If you see "already authorized", you're good to go!
- Check browser console (F12) for errors

**Terminal QR login**:
- Check that API_ID and API_HASH are correct
- Verify phone number is in international format (+7...)
- Check internet connection
- Make sure you scan the QR code within the time limit

**Session issues**:
- Delete `session_name.session` file and re-authenticate
- Make sure only one QR login is running at a time

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

### Lazy Loading & Photo Gallery

- Photos are downloaded **on-demand** when visible (Intersection Observer API)
- First load: ~5 seconds (metadata only)
- Photos load progressively as you scroll
- Cached photos load instantly
- **Full-screen photo viewer** with keyboard navigation (← → arrows, ESC to close)
- Multiple photos per listing are displayed as a gallery
- Click on photo sides (left/right 30%) for quick navigation

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
- [x] ~~Multi-language interface~~ ✅ **Implemented** (Ukrainian/Vietnamese)
- [x] ~~Web-based QR authentication~~ ✅ **Implemented**
- [x] ~~Photo gallery with navigation~~ ✅ **Implemented**
- [ ] Price history tracking
- [ ] Favorite listings
- [ ] Email alerts
- [ ] More language options (English, Russian, Thai, etc.)

---

## Recent Updates

### Version 2.0 (Latest)

✨ **Major Features Added:**

- 🌍 **Multi-language support** - Ukrainian and Vietnamese with easy language switching
- 🔐 **Web-based QR authentication** - no need for terminal, authenticate directly in browser
- 🖼️ **Enhanced photo gallery** - full-screen viewer with keyboard navigation
- 📺 **Multi-channel support** - fetch from multiple Telegram channels simultaneously
- ⚡ **Performance improvements** - lazy loading, caching, and optimized rendering

**Breaking Changes:**
- Default language changed from Russian to Ukrainian
- QR login now available via web interface at `/register`

### Version 1.0

- Initial release with basic filtering capabilities
- Terminal-based QR authentication
- Single channel support
