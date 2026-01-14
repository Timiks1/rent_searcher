"""
Авторизация через QR код (без SMS)
Просто отсканируйте QR код в мобильном Telegram
"""
import os
import asyncio
from telethon import TelegramClient
from dotenv import load_dotenv
import qrcode_terminal

load_dotenv()

api_id = int(os.getenv('TELEGRAM_API_ID'))
api_hash = os.getenv('TELEGRAM_API_HASH')

async def qr_login():
    client = TelegramClient('session_name', api_id, api_hash)
    
    await client.connect()
    
    if await client.is_user_authorized():
        print("✅ Вы уже авторизованы!")
        me = await client.get_me()
        print(f"👤 {me.first_name}")
        await client.disconnect()
        return
    
    print("=" * 60)
    print("🔐 Авторизация через QR код (БЕЗ SMS!)")
    print("=" * 60)
    print()
    print("📱 Откройте Telegram на телефоне:")
    print("   Settings → Devices → Link Desktop Device")
    print()
    print("📸 Отсканируйте QR код ниже:")
    print()
    
    # Получаем QR код для входа
    qr_login = await client.qr_login()
    
    # Показываем QR в терминале
    try:
        import qrcode_terminal
        qrcode_terminal.draw(qr_login.url)
    except ImportError:
        print("⚠️ Для отображения QR кода установите: pip install qrcode-terminal")
        print(f"\nИли откройте эту ссылку на телефоне: {qr_login.url}")
    
    print("\n⏳ Ожидание сканирования...")
    
    try:
        await qr_login.wait(timeout=300)  # Ждём 5 минут
        print("\n✅ Успешная авторизация через QR код!")
        
        me = await client.get_me()
        print(f"👤 Вы вошли как: {me.first_name}")
        
    except asyncio.TimeoutError:
        print("\n⏰ Время ожидания истекло. Попробуйте снова.")
    
    await client.disconnect()

if __name__ == '__main__':
    try:
        asyncio.run(qr_login())
    except ImportError:
        print("\n💡 Для QR авторизации нужна библиотека qrcode-terminal")
        print("Установите: pip install qrcode-terminal")
        print("\nИли используйте Pyrogram: python test_pyrogram.py")
