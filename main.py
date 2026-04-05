import os
import discord
from discord.ext import commands
import requests
import html
import re
from flask import Flask
from threading import Thread

# ===== НАСТРОЙКИ =====
USER_TOKEN = os.environ["DISCORD_TOKEN"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = "948828396"

MY_NAMES = ["Smurfik_Kryzov", "Scydo", "scydoz", "905581302571470848"]

client = commands.Bot(command_prefix="!", self_bot=True)

# ===== TELEGRAM =====
def send_telegram(text, url=None):
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    if url:
        payload["reply_markup"] = {
            "inline_keyboard": [[{"text": "Открыть", "url": url}]]
        }
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json=payload,
            timeout=10,
        )
    except Exception as e:
        print("TG ERROR:", e)

# ===== ЛОГИКА =====
def contains_me(text):
    return any(n.lower() in text.lower() for n in MY_NAMES)

def is_invite(text):
    return "приглашены следующие кандидаты" in text.lower()

def is_appointed(text):
    return "назначен" in text.lower() and "лидер" in text.lower()

def normalize_faction(name):
    n = name.lower()
    if "federal investigation bureau" in n or "fib" in n:
        return "FIB"
    if "los santos police department" in n or "lspd" in n:
        return "LSPD"
    if "los santos sheriff department" in n or "sheriff" in n:
        return "LSSD"
    if "national guard" in n:
        return "NG"
    if "emergency medical service" in n:
        return "EMS"
    if "government" in n:
        return "GOV"
    return name.strip()

def parse_faction(text):
    clean = re.sub(r":[^:\s]+:", "", text)
    match = re.search(r"пост лидера(.*?)назначен", clean, re.IGNORECASE)
    if match:
        faction = match.group(1).strip()
        faction = faction.replace("—", "").replace("-", "")
        return normalize_faction(faction)
    match = re.search(r"лидера(.*?)назначен", clean, re.IGNORECASE)
    if match:
        return normalize_faction(match.group(1).strip())
    return "Неизвестная фракция"

# ===== EVENTS =====
@client.event
async def on_ready():
    print("✅ Бот запущен и работает!")

@client.event
async def on_message(message):
    if message.author.id == client.user.id:
        return
    text = message.content
    if not contains_me(text):
        return
    faction = parse_faction(text)

    if is_invite(text):
        send_telegram(
            f"<b>ПРИГЛАШЕНИЕ</b>\n\nТы приглашен на лидерку <b>{html.escape(faction)}</b>",
            message.jump_url,
        )
        return
    if is_appointed(text):
        send_telegram(
            f"<b>НАЗНАЧЕНИЕ</b>\n\nТы назначен на пост лидера <b>{html.escape(faction)}</b>",
            message.jump_url,
        )
        return

    safe = html.escape(text[:400])
    send_telegram(
        f"<b>УПОМИНАНИЕ</b>\n\n<code>{safe}</code>",
        message.jump_url,
    )

# ===== FLASK WEB SERVER ДЛЯ RENDER =====
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is alive"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)

Thread(target=run_web, daemon=True).start()

client.run(USER_TOKEN)
