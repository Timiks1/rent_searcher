import re
from typing import Dict, List, Optional, Any

class MessageParser:
    """Parser for extracting location and price information from rental messages"""
    
    def __init__(self):
        # Common price patterns (supports different currencies)
        self.price_patterns = [
            # Specific format: "Price: 8 million" or "Price: 12 million VND"
            r'(?:rent|price|giá|цена|аренда|thuê)[:\s]+([\d,.\s]+?)\s+(?:million|triệu|млн)',
            r'(?:rent|price|giá|цена|аренда|thuê)[:\s]+([\d,.\s]+?)\s+(?:thousand|nghìn|тыс|k)',
            # Format: "Rent: 15,000,000" (number only)
            r'(?:rent|price|giá|цена|аренда|thuê)[:\s]+([\d,.\s]+?)(?:\s*vnd|\s*$|\s*\n)',
            # Vietnamese Dong (VND) with separators
            r'(\d+[\d,.\s]*)\s*(?:vnd|₫|đ|dong|донг)',
            r'(\d+[\d,.\s]*)\s*(?:tr|triệu|млн)',  # millions (triệu)
            r'(\d+[\d,.\s]*)\s*(?:k|nghìn|тыс)',   # thousands (nghìn)
            # USD (common in Vietnam)
            r'\$\s*([\d,.\s]+)',
            r'([\d,.\s]+)\s*(?:usd|долл)',
            # Standalone numbers (last resort)
            r'(?:price|цена|giá)[:\s]+([\d,.\s]+)',
            r'([\d,.\s]+)\s*(?:/month|в месяц|tháng)',
        ]
        
        # Common location keywords for Vietnam
        self.location_keywords = [
            # Major cities
            'hanoi', 'hà nội', 'ханой',
            'ho chi minh', 'hcmc', 'saigon', 'сайгон', 'хошимин',
            'da nang', 'đà nẵng', 'дананг',
            'hoi an', 'hội an', 'хойан',
            'nha trang', 'нячанг',
            'vung tau', 'vũng tàu', 'вунгтау',
            'phu quoc', 'phú quốc', 'фукуок',
            'hue', 'huế', 'хюэ',
            'halong', 'hạ long', 'халонг',
            'dalat', 'đà lạt', 'далат',
            # Districts/Areas
            'district', 'quận', 'район',
            'ward', 'phường',
            'street', 'đường', 'улица',
            'city center', 'trung tâm', 'центр',
            # Common descriptors
            'beach', 'bãi biển', 'пляж',
            'downtown', 'старый город',
        ]
        
    def parse_message(self, message_text: str, existing_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Parse a message and extract structured information
        
        Args:
            message_text: Raw message text
            existing_data: Existing message data to preserve (e.g., photos, id, date)
            
        Returns:
            Dictionary with parsed data
        """
        text_lower = message_text.lower()
        
        parsed = {
            'price': self.extract_price(text_lower),
            'location': self.extract_location(text_lower, message_text),
            'raw_text': message_text
        }
        
        # Preserve existing data if provided (like photos, id, date, etc.)
        if existing_data:
            result = existing_data.copy()
            result.update(parsed)
            return result
        
        return parsed
        
    def extract_price(self, text: str) -> Optional[int]:
        """
        Extract price from text
        
        Args:
            text: Message text (lowercase)
            
        Returns:
            Price as integer or None
        """
        for pattern in self.price_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # Clean up the price string - remove all separators
                price_str = match.group(1).replace(' ', '').replace(',', '').replace('.', '')
                
                # Skip if empty or not a number
                if not price_str or not price_str.isdigit():
                    continue
                    
                try:
                    price = int(price_str)
                    
                    # Handle multipliers
                    context = text[max(0, match.start()-5):min(len(text), match.end() + 20)].lower()
                    
                    # Millions (triệu in Vietnamese, млн in Russian)
                    if any(x in context for x in ['tr', 'triệu', 'триệу', 'млн', 'million', 'mil']):
                        price *= 1000000
                    # Thousands (nghìn in Vietnamese, тыс in Russian)
                    elif any(x in context for x in ['k', 'nghìn', 'тыс', 'тысяч', 'thousand']):
                        price *= 1000
                    
                    # Sanity check for Vietnam rental prices
                    # Typical range: 2M - 100M VND ($100-10000) or 100-10000 USD
                    if 100 <= price <= 100000000:  # Wide range to catch both VND and USD
                        return price
                        
                    # If the number is very small, might need millions multiplier
                    # e.g., "Rent: 15" likely means 15 million
                    if 5 <= price <= 100 and 'rent' in context:
                        return price * 1000000
                        
                except ValueError:
                    continue
                    
        return None
        
    def extract_location(self, text_lower: str, text_original: str) -> List[str]:
        """
        Extract location information from text, with priority for Area field
        
        Args:
            text_lower: Message text in lowercase
            text_original: Original message text with proper capitalization
            
        Returns:
            List of found locations (Area first if found)
        """
        locations = []
        
        # PRIORITY 1: Extract "Area:" or "Location:" field with district
        area_patterns = [
            r'(?:area|khu vực|район)[:\s]+([^\n\r-]+?)(?:\n|-|$)',
            r'-\s*area[:\s]+([^\n\r-]+?)(?:\n|-|$)',
            # Also extract district from Location field
            r'(?:location|địa điểm)[:\s]+([^\n\r]+?)(?:district|quận)([^\n\r,]+)',
        ]
        
        for pattern in area_patterns:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                # Handle different group patterns
                if match.lastindex and match.lastindex >= 2:
                    # Pattern with district - combine groups
                    area = (match.group(1) + ' ' + match.group(2)).strip()
                else:
                    area = match.group(1).strip()
                    
                if area and len(area) > 1:
                    # Find in original text for proper capitalization
                    start_pos = text_lower.find(area.lower())
                    if start_pos >= 0:
                        area_proper = text_original[start_pos:start_pos + len(area)].strip()
                        if area_proper and area_proper not in locations:
                            locations.insert(0, area_proper)  # Insert at beginning
        
        # Check for location keywords
        for keyword in self.location_keywords:
            if keyword in text_lower:
                # Try to extract context around the keyword
                pattern = rf'[\w\s]*{re.escape(keyword)}[\w\s]*'
                matches = re.finditer(pattern, text_lower)
                for match in matches:
                    # Get the original text with proper capitalization
                    start, end = match.span()
                    location_context = text_original[start:end].strip()
                    if location_context and location_context not in locations:
                        locations.append(location_context[:50])  # Limit length
                        
        # Also try to extract addresses (Vietnamese and international)
        address_patterns = [
            # Vietnamese patterns
            r'(?:đường|đ\.)\s+[\w\s]+(?:\d+)?',      # street
            r'(?:quận|q\.)\s+\d+',                    # district
            r'(?:phường|p\.)\s+[\w\s]+',              # ward
            r'district\s+\d+',                         # district (English)
            # General patterns
            r'[\w\s]+\s+(?:district|area|район)',
            r'(?:улица|ул\.)\s+[\w\s]+',
        ]
        
        for pattern in address_patterns:
            matches = re.finditer(pattern, text_original, re.IGNORECASE)
            for match in matches:
                location = match.group(0).strip()
                if location and location not in locations:
                    locations.append(location)
                    
        return locations[:10]  # Return max 10 locations
        
    def filter_messages(
        self,
        messages: List[Dict[str, Any]],
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        location_filter: Optional[str] = None,
        exclude_areas: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Filter messages based on criteria
        
        Args:
            messages: List of messages with parsed data
            min_price: Minimum price filter
            max_price: Maximum price filter
            location_filter: Location keyword to filter by (whitelist)
            exclude_areas: Comma-separated areas to exclude (blacklist)
            
        Returns:
            Filtered list of messages
        """
        filtered = []
        
        # Parse exclude areas
        excluded_list = []
        if exclude_areas:
            excluded_list = [area.strip().lower() for area in exclude_areas.split(',') if area.strip()]
        
        for msg in messages:
            # Parse the message if not already parsed
            if 'price' not in msg:
                parsed = self.parse_message(msg.get('text', ''), existing_data=msg)
                msg.update(parsed)
            
            # FIRST: Apply exclusion filter (most important)
            if excluded_list:
                text_lower = msg.get('text', '').lower()
                locations_lower = [loc.lower() for loc in msg.get('location', [])]
                
                # Check if any excluded area is in the message
                should_exclude = False
                for excluded in excluded_list:
                    if excluded in text_lower or any(excluded in loc for loc in locations_lower):
                        should_exclude = True
                        break
                
                if should_exclude:
                    continue  # Skip this message
                
            # Apply price filters
            if min_price is not None and (msg['price'] is None or msg['price'] < min_price):
                continue
                
            if max_price is not None and (msg['price'] is None or msg['price'] > max_price):
                continue
                
            # Apply location filter (whitelist)
            if location_filter:
                location_filter_lower = location_filter.lower()
                text_lower = msg.get('text', '').lower()
                locations_lower = [loc.lower() for loc in msg.get('location', [])]
                
                if location_filter_lower not in text_lower and \
                   not any(location_filter_lower in loc for loc in locations_lower):
                    continue
                    
            filtered.append(msg)
            
        return filtered


# Example usage
if __name__ == '__main__':
    parser = MessageParser()
    
    test_messages = [
        "Apartment for rent in District 1, Ho Chi Minh City. Price: 15 triệu VND/month",
        "Studio in Hanoi city center, $500/month, fully furnished",
        "2-bedroom near beach Da Nang, 12tr VND, swimming pool",
        "House in Nha Trang, 20 million dong per month",
    ]
    
    for msg in test_messages:
        parsed = parser.parse_message(msg)
        print(f"\nОригинал: {msg}")
        print(f"Цена: {parsed['price']}")
        print(f"Локация: {parsed['location']}")
