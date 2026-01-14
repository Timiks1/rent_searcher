"""
Test script to verify parser works with different message formats
"""
from message_parser import MessageParser

parser = MessageParser()

# Test messages from different channels
test_messages = [
    # Format 1: Original with "Area:" field
    """Type: Studio
- Address: Hoàng Kế Viêm st
- Price: 12 million
- Area: Mỹ An
- Available 16th December""",
    
    # Format 2: New format with "Location:" and "Rent:"
    """Luxury 1BR Apartment for Rent – Da Nang City Center
📍 Location: Tran Phu Street, Hai Chau District – prime location by Han River, heart of Da Nang
• 🏋️ Rooftop super view
• 💼 Spacious 60m2, have Dragon bridge view
• 🛋 Fully furnished with modern, high-end interior
• 🌅 Cleaning service
• 💵 Rent: 15,000,000
📞 Zalo/WhatsApp: +84 931 82 43 06""",
    
    # Format 3: Various price formats
    """Studio apartment in Hòa Hải area
Price: 8 million VND per month""",
    
    """2BR in An Thượng beach
Rent $600/month""",
    
    """House in Khuê Mỹ district
15tr/tháng""",
]

print("=" * 80)
print("TESTING MESSAGE PARSER")
print("=" * 80)

for i, msg in enumerate(test_messages, 1):
    print(f"\n📨 TEST MESSAGE {i}:")
    print("-" * 80)
    print(msg[:200] + "..." if len(msg) > 200 else msg)
    print("-" * 80)
    
    parsed = parser.parse_message(msg)
    
    print(f"💰 Price: {parsed['price']:,}" if parsed['price'] else "💰 Price: Not found")
    if parsed['price']:
        if parsed['price'] < 10000:
            print(f"   → ${parsed['price']}")
        else:
            print(f"   → {parsed['price']:,} VND ({parsed['price']/1000000:.1f} million)")
    
    print(f"📍 Locations found: {len(parsed['location'])}")
    for loc in parsed['location']:
        print(f"   • {loc}")
    
    if not parsed['location']:
        print("   ⚠️  No locations found")
    
    print()

print("=" * 80)
print("✅ Testing complete!")
print("=" * 80)

# Test filtering with exclusions
print("\n" + "=" * 80)
print("TESTING EXCLUSION FILTER")
print("=" * 80)

messages_data = []
for msg in test_messages:
    parsed = parser.parse_message(msg)
    messages_data.append({
        'text': msg,
        'price': parsed['price'],
        'location': parsed['location']
    })

print(f"\nTotal messages: {len(messages_data)}")

# Test exclusion
exclude_test = "Hòa Hải, Khuê Mỹ"
print(f"\nExcluding areas: {exclude_test}")
filtered = parser.filter_messages(messages_data, exclude_areas=exclude_test)
print(f"After exclusion: {len(filtered)} messages")

for msg in filtered:
    price_str = f"{msg['price']:,} VND" if msg['price'] and msg['price'] >= 10000 else f"${msg['price']}"
    locations_str = ", ".join(msg['location'][:2]) if msg['location'] else "No location"
    print(f"  ✓ {price_str} - {locations_str}")

print("\n" + "=" * 80)
