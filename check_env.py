import os
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / '.env')

print("🔍 Проверка переменных окружения Telegram:")
print("=" * 50)

token = os.getenv('TELEGRAM_BOT_TOKEN')
username = os.getenv('TELEGRAM_BOT_USERNAME')
webhook = os.getenv('TELEGRAM_WEBHOOK_URL')

if token:
    print(f"✅ TELEGRAM_BOT_TOKEN: установлен ({len(token)} символов)")
    print(f"   Первые 20 символов: {token[:20]}...")
else:
    print("❌ TELEGRAM_BOT_TOKEN: НЕ УСТАНОВЛЕН!")

if username:
    print(f"✅ TELEGRAM_BOT_USERNAME: @{username}")
else:
    print("❌ TELEGRAM_BOT_USERNAME: НЕ УСТАНОВЛЕН!")

if webhook:
    print(f"✅ TELEGRAM_WEBHOOK_URL: {webhook}")
else:
    print("ℹ️ TELEGRAM_WEBHOOK_URL: не установлен (нормально для разработки)")

print("\n" + "=" * 50)

# Проверка что бот доступен
if token:
    import requests
    try:
        response = requests.get(f'https://api.telegram.org/bot{token}/getMe', timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                bot_info = data['result']
                print(f"🤖 Бот доступен!")
                print(f"   Имя: {bot_info['first_name']}")
                print(f"   Username: @{bot_info.get('username', 'N/A')}")
                print(f"   ID: {bot_info['id']}")
            else:
                print(f"⚠️ Ошибка API Telegram: {data.get('description')}")
        else:
            print(f"⚠️ HTTP ошибка: {response.status_code}")
    except Exception as e:
        print(f"⚠️ Не удалось подключиться к Telegram API: {e}")

print("✅ Проверка завершена")