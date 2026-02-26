import requests
import hashlib
import json
import os
from datetime import date, timedelta
from datetime import datetime
from requests.adapters import HTTPAdapter

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

BASE_URL = "https://sh2-kuvandyk-r56.gosweb.gosuslugi.ru/netcat_files/24/3008/Raspisanie_na_{}.jpg"
HASH_FILE = "last_hashes.json"

HEADERS = {"User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36"}

session = requests.Session()
session.mount("https://", HTTPAdapter(max_retries=3))

def log(msg):
    ts = datetime.now().strftime('%H:%M:%S')
    print(f"[{ts}] {msg}")

def load_hashes():
    if os.path.exists(HASH_FILE):
        with open(HASH_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_hashes(hashes):
    with open(HASH_FILE, "w", encoding="utf-8") as f:
        json.dump(hashes, f, ensure_ascii=False)

last_hashes = load_hashes()

log("🚀 GitHub Actions запустился")
log("Проверяем ТОЛЬКО завтра")

try:
    tomorrow = date.today() + timedelta(days=1)
    date_str = tomorrow.strftime("%d.%m")
    url = BASE_URL.format(date_str)
    
    log(f"Проверяю завтра: {date_str} → {url}")
    
    r = session.get(url, headers=HEADERS, timeout=20)
    log(f"   Статус: {r.status_code} | Размер: {len(r.content)/1024:.1f} КБ" if r.status_code == 200 else f"   Статус: {r.status_code} (ещё не выложили)")
    
    if r.status_code == 200:
        content = r.content
        current_hash = hashlib.md5(content).hexdigest()
        
        if date_str not in last_hashes or last_hashes[date_str] != current_hash:
            log("   🆕 Новая версия! Отправляю в канал...")
            caption = f"🗓 Расписание на {date_str}"
            
            api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
            files = {'photo': ('raspisanie.jpg', content, 'image/jpeg')}
            
            resp = session.post(api_url, data={'chat_id': CHAT_ID, 'caption': caption}, files=files, timeout=25)
            
            if resp.status_code == 200:
                last_hashes[date_str] = current_hash
                save_hashes(last_hashes)
                log(f"   ✅ УСПЕШНО ОТПРАВЛЕНО на {date_str}!")
            else:
                log(f"   ❌ Ошибка отправки: {resp.status_code}")
        else:
            log("   ✅ Уже отправляли эту версию (пропускаем)")
    else:
        log("   Расписание на завтра ещё не появилось")
        
except Exception as e:
    log(f"Ошибка: {e}")

log("Проверка завершена. Следующий запуск через ~5 минут")
