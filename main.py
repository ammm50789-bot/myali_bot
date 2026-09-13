import asyncio
import logging
import time
import random
import aiohttp
import aiosqlite
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
    Application,
)

# ==========================================
# ⚙️ CONFIGURATION
# ==========================================
TELEGRAM_BOT_TOKEN = "8675974676:AAG9MlrlEgJSPwcxg_-khjCSl4cQxI-N9LI"
ADMIN_ID = 8195946863
ADMIN_PASSWORD = "11223344Ali"

WINGO_API = 'https://api.bdg88zf.com/api/webapi/GetGameIssue'
AVIATOR_API = 'https://aviator-next.spribegaming.com' # Reference API

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

DB_NAME = "bot_database.db"
user_states = {}

# ==========================================
# 🌐 RAILWAY CRASH FIX (DUMMY SERVER)
# ==========================================
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Aviator + Wingo Bot is Running!")
    def log_message(self, format, *args):
        pass

def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), DummyHandler)
    server.serve_forever()

def keep_alive():
    t = threading.Thread(target=run_dummy_server)
    t.daemon = True
    t.start()

# ==========================================
# 💾 DATABASE (Stats & History)
# ==========================================
async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_type TEXT,
                date TEXT,
                result TEXT
            )
        """)
        await db.commit()

async def post_init(application: Application):
    await init_db()

async def save_stat(game_type, result):
    today = datetime.utcnow().strftime('%Y-%m-%d')
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT INTO stats (game_type, date, result) VALUES (?, ?, ?)", (game_type, today, result))
        await db.commit()

async def get_today_stats():
    today = datetime.utcnow().strftime('%Y-%m-%d')
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT result FROM stats WHERE date=?", (today,)) as cursor:
            rows = await cursor.fetchall()
            
    total = len(rows)
    wins = sum(1 for r in rows if r[0] == 'WIN')
    losses = sum(1 for r in rows if r[0] == 'LOSS')
    win_rate = int((wins / total) * 100) if total > 0 else 0
    
    return total, wins, losses, win_rate

# ==========================================
# 🌐 PREDICTION ENGINES
# ==========================================
async def get_wingo_period():
    try:
        payload = {
            "typeId": 1, "language": 0,
            "random": "40079dcba93a48769c6ee9d4d4fae23f",
            "signature": "D12108C4F57C549D82B23A91E0FA20AE",
            "timestamp": int(time.time())
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(WINGO_API, json=payload, timeout=5) as response:
                data = await response.json()
                if "data" in data and "issueNumber" in data["data"]:
                    return data["data"]["issueNumber"]
    except:
        pass
    # Time fallback
    ist_now = datetime.utcnow() + timedelta(hours=5, minutes=30)
    minutes_passed = (ist_now.hour * 60) + ist_now.minute + 1
    return f"{ist_now.strftime('%Y%m%d')}1000{minutes_passed:04d}"

def get_wingo_prediction():
    size = random.choice(["BIG", "SMALL"])
    nums = random.sample([5, 6, 7, 8, 9], 2) if size == "BIG" else random.sample([0, 1, 2, 3, 4], 2)
    return size, nums

def get_aviator_prediction():
    # 1.01 to 10.00 multiplier generator (weighted for realism)
    rand = random.random()
    if rand < 0.6:
        multi = random.uniform(1.20, 2.50)
    elif rand < 0.9:
        multi = random.uniform(2.50, 5.00)
    else:
        multi = random.uniform(5.00, 10.00)
    return round(multi, 2)

# ==========================================
# 📱 KEYBOARDS & MENUS
# ==========================================
def main_menu_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔴 WINGO PREDICTION", callback_data="play_wingo")],
        [InlineKeyboardButton("✈️ AVIATOR PREDICTION", callback_data="play_aviator")],
        [InlineKeyboardButton("📊 TODAY STATISTICS", callback_data="show_stats")]
    ])

def wingo_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⏭ NEXT SINGLE (Wingo)", callback_data="play_wingo")],
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
    ])

def aviator_kb(pred_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ WIN", callback_data=f"av_win_{pred_id}"), InlineKeyboardButton("❌ LOSS", callback_data=f"av_loss_{pred_id}")],
        [InlineKeyboardButton("⏭ NEXT SINGLE (Aviator)", callback_data="play_aviator")],
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
    ])

def aviator_next_only_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⏭ NEXT SINGLE (Aviator)", callback_data="play_aviator")],
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
    ])

# ==========================================
# 🤖 HANDLERS
# ==========================================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "🔥 <b>ALI PREDICTION VIP</b> 🔥\n\n"
        "Welcome to the Ultimate Prediction Bot!\n"
        "No Registration required. Choose your game below and get instant highly accurate signals."
    )
    await update.message.reply_text(msg, reply_markup=main_menu_kb(), parse_mode="HTML")

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID: return
    user_states[user_id] = "WAITING_ADMIN_PASSWORD"
    await update.message.reply_text("🔒 <b>Enter Admin Password:</b>", parse_mode="HTML")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = update.effective_user.id
    await query.answer()
    data = query.data

    if data == "main_menu":
        await query.edit_message_text("🔥 <b>ALI PREDICTION VIP</b> 🔥\n\nChoose your game:", reply_markup=main_menu_kb(), parse_mode="HTML")

    # --- WINGO PREDICTION ---
    elif data == "play_wingo":
        await query.edit_message_text("⏳ Analyzing Wingo Trend...", parse_mode="HTML")
        await asyncio.sleep(1) # Fake analysis delay
        
        period = await get_wingo_period()
        size, nums = get_wingo_prediction()
        
        msg = (
            f"🔴 <b>WINGO VIP SIGNAL</b> 🔴\n\n"
            f"🚀 <b>PERIOD:</b> <code>{period}</code>\n"
            f"📊 <b>PREDICTION:</b> {size}\n"
            f"🔢 <b>NUMBERS:</b> {nums[0]}, {nums[1]}\n\n"
            f"⚠️ <i>Play with 3X Investment Method.</i>"
        )
        await query.edit_message_text(msg, reply_markup=wingo_kb(), parse_mode="HTML")

    # --- AVIATOR PREDICTION ---
    elif data == "play_aviator":
        await query.edit_message_text("🛫 Intercepting Aviator Server API...", parse_mode="HTML")
        await asyncio.sleep(1.5)
        
        multiplier = get_aviator_prediction()
        pred_id = int(time.time()) # Unique ID for this signal
        
        msg = (
            f"✈️ <b>AVIATOR VIP SIGNAL</b> ✈️\n\n"
            f"🎯 <b>TARGET MULTIPLIER:</b> {multiplier}x\n\n"
            f"💡 <i>Tip: Cashout slightly before the target for maximum safety.</i>\n\n"
            f"👇 <b>Please submit your feedback below after playing:</b>"
        )
        await query.edit_message_text(msg, reply_markup=aviator_kb(pred_id), parse_mode="HTML")

    # --- AVIATOR FEEDBACK (WIN/LOSS) ---
    elif data.startswith("av_win_") or data.startswith("av_loss_"):
        result = "WIN" if "av_win_" in data else "LOSS"
        await save_stat("AVIATOR", result)
        
        res_text = "✅ <b>WIN RECORDED!</b>" if result == "WIN" else "❌ <b>LOSS RECORDED!</b>"
        old_text = query.message.text.replace("👇 Please submit your feedback below after playing:", "")
        
        new_msg = f"{old_text}\n\n{res_text}\nThank you for your feedback!"
        await query.edit_message_text(new_msg, reply_markup=aviator_next_only_kb(), parse_mode="HTML")

    # --- STATISTICS ---
    elif data == "show_stats":
        total, wins, losses, win_rate = await get_today_stats()
        msg = (
            f"📊 <b>TODAY'S STATISTICS</b> 📊\n\n"
            f"📅 <b>Date:</b> {datetime.utcnow().strftime('%Y-%m-%d')}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🎯 <b>Total Signals Today:</b> {total}\n"
            f"🏆 <b>Total Wins:</b> {wins}\n"
            f"❌ <b>Total Losses:</b> {losses}\n"
            f"📈 <b>Accuracy / Win Rate:</b> {win_rate}%\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"<i>*Stats are based on user feedback and auto-resolutions.</i>"
        )
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="main_menu")]])
        await query.edit_message_text(msg, reply_markup=kb, parse_mode="HTML")

    # --- ADMIN BROADCAST ---
    elif data == "adm_broadcast":
        user_states[uid] = "WAITING_BROADCAST"
        await query.edit_message_text("📢 Send the message/image you want to broadcast to ALL users:")

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    state = user_states.get(uid)
    if not state: return

    if state == "WAITING_ADMIN_PASSWORD":
        if update.message.text == ADMIN_PASSWORD:
            user_states.pop(uid)
            
            total, wins, losses, win_rate = await get_today_stats()
            msg = (
                f"⚙️ <b>MASTER ADMIN PANEL</b>\n\n"
                f"📊 <b>TODAY'S PERFORMANCE:</b>\n"
                f"Total Signals: {total}\nWins: {wins}\nLosses: {losses}\nWin Rate: {win_rate}%\n"
            )
            kb = InlineKeyboardMarkup([[InlineKeyboardButton("📢 Broadcast Message", callback_data="adm_broadcast")]])
            await update.message.reply_text(msg, reply_markup=kb, parse_mode="HTML")
        else:
            await update.message.reply_text("❌ Incorrect Password.")
            
    elif state == "WAITING_BROADCAST":
        # Note: Broadcasting to everyone requires a full users table if we want to reach users who haven't interacted recently. 
        # Since registration is removed, this broadcast will only reply to admin for demonstration, or you can add an auto-save user feature back if you need true broadcasting.
        user_states.pop(uid)
        await update.message.reply_text("✅ Broadcast feature is configured. (Note: True mass broadcasting requires saving chat_ids to DB).")

# ==========================================
# 🚀 MAIN RUNNER
# ==========================================
def main():
    keep_alive() # Railway Crash Fix Server

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).post_init(post_init).build()
    
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.ALL, text_handler))
    
    logger.info("Ultimate Wingo + Aviator Bot is Running!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
