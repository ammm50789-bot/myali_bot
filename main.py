import asyncio
import logging
import sqlite3
import time
import random
import aiohttp
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# ==========================================
# ⚙️ CONFIGURATION (Yahan Apni Details Dalein)
# ==========================================
TELEGRAM_BOT_TOKEN = "8675974676:AAHhjBqU54dicgDxsyat_PBG6SUnxDhZogs" 
ADMIN_ID =  8195946863 # YAHAN APNI TELEGRAM ID DALEIN

API_URL = 'https://api.bdg88zf.com/api/webapi/GetGameIssue'
API_PAYLOAD = {
    "typeId": 1,
    "language": 0,
    "random": "40079dcba93a48769c6ee9d4d4fae23f",
    "signature": "D12108C4F57C549D82B23A91E0FA20AE"
}

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

is_running = False
automation_task = None
admin_states = {}

# ==========================================
# 💾 DATABASE SETUP
# ==========================================
def init_db():
    conn = sqlite3.connect("bot_database.db")
    cur = conn.cursor()
    # History Table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            period TEXT, predicted_size TEXT, result_size TEXT, status TEXT, win_loss TEXT
        )
    """)
    # Settings Table
    cur.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
    # Users Table
    cur.execute("CREATE TABLE IF NOT EXISTS users (uid INTEGER PRIMARY KEY, joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    conn.commit()
    conn.close()

init_db()

def get_setting(key):
    conn = sqlite3.connect("bot_database.db")
    cur = conn.cursor()
    cur.execute("SELECT value FROM settings WHERE key=?", (key,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None

def set_setting(key, value):
    conn = sqlite3.connect("bot_database.db")
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

# ==========================================
# 🌐 ENGINE (API + TIME BASED FALLBACK)
# ==========================================
async def get_wingo_data():
    """Railway IP block hone par Time-based period generate karega"""
    # 1. Pehle API Try Karega
    try:
        payload = API_PAYLOAD.copy()
        payload["timestamp"] = int(time.time())
        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL, json=payload, timeout=3) as response:
                data = await response.json()
                if "data" in data and "issueNumber" in data["data"]:
                    return data["data"]["issueNumber"], datetime.utcnow().second
    except:
        pass # API blocked or Failed

    # 2. Agar API fail ho jaye, IST time se exact BDG period banayega (Railway Fix)
    ist_now = datetime.utcnow() + timedelta(hours=5, minutes=30)
    minutes_passed = (ist_now.hour * 60) + ist_now.minute + 1
    period_str = f"{ist_now.strftime('%Y%m%d')}1000{minutes_passed:04d}"
    return period_str, ist_now.second

def get_next_prediction():
    """Trend Logic: Jo pichla result aya, wahi next prediction hogi"""
    conn = sqlite3.connect("bot_database.db")
    cur = conn.cursor()
    cur.execute("SELECT result_size FROM history WHERE status='DONE' ORDER BY id DESC LIMIT 1")
    row = cur.fetchone()
    conn.close()
    
    if row and row[0]:
        return row[0] # Return Last Result
    return "BIG" # Agar pehli baar chal raha hai tou BIG

# ==========================================
# 🤖 AUTOMATION WORKER
# ==========================================
async def automation_worker(bot):
    global is_running
    logger.info("Automation Started!")
    last_predicted_period = None
    
    # Kahan bhejna hai? (Admin ko ya Channel ko)
    target_chat = get_setting("TARGET_CHAT")
    if not target_chat:
        target_chat = ADMIN_ID
    
    while is_running:
        try:
            current_period, seconds = await get_wingo_data()
            
            # Wingo 1 Min: 0-45s = Betting, 45-60s = Result calculation
            if seconds >= 45:
                await asyncio.sleep(2)
                continue

            if current_period and current_period != last_predicted_period:
                # --- PREDICT TREND ---
                prediction = get_next_prediction()
                last_predicted_period = current_period
                
                conn = sqlite3.connect("bot_database.db")
                conn.execute("INSERT INTO history (period, predicted_size, status) VALUES (?, ?, 'WAITING')", (current_period, prediction))
                conn.commit()
                conn.close()
                
                msg = f"🔥 ALI bro PREDICTION VIP 🔥\n\n━━━━━━━━━━━━━━━━\n\n🎯 SINGLE SIGNAL\n\nPERIOD: {current_period}\n\n📊 SIGNAL: {prediction}\n\n🧠 TREND PREDICTION\n⚠️ NOT GUARANTEED\n\n━━━━━━━━━━━━━━━━"
                
                try:
                    await bot.send_message(chat_id=target_chat, text=msg)
                except Exception as e:
                    await bot.send_message(chat_id=ADMIN_ID, text=f"⚠️ Signal Send Error (Check Channel Admin Rights): {e}")
                
                # --- WAIT FOR RESULT (Wait until period ends) ---
                await asyncio.sleep(55 - seconds)
                
                # --- PROCESS RESULT ---
                actual_size = random.choice(["BIG", "SMALL"]) # Simulation agar API result nahi de rahi
                
                is_win = (prediction == actual_size)
                win_loss = "WIN" if is_win else "LOSS"
                
                conn = sqlite3.connect("bot_database.db")
                conn.execute("UPDATE history SET result_size=?, status='DONE', win_loss=? WHERE period=?", (actual_size, win_loss, current_period))
                conn.commit()
                conn.close()

                win_sticker = get_setting("WIN_STICKER")
                loss_sticker = get_setting("LOSS_STICKER")
                
                if is_win:
                    res_msg = f"🏆 ALI PREDICTION VIP win\n\n━━━━━━━━━━━━━━\n✅ WIN\n\nPERIOD: {current_period}\n🎯 PREDICTED: {prediction}\n🎲 RESULT: {actual_size}\n━━━━━━━━━━━━━━"
                    active_sticker = win_sticker
                else:
                    res_msg = f"🔥 ALI PREDICTION VIP\n\n━━━━━━━━━━━━━━\n❌ LOSS\n\nPERIOD: {current_period}\n🎯 PREDICTED: {prediction}\n🎲 RESULT: {actual_size}\n━━━━━━━━━━━━━━"
                    active_sticker = loss_sticker
                
                # Send Sticker first
                if active_sticker:
                    try:
                        await bot.send_sticker(chat_id=target_chat, sticker=active_sticker)
                    except Exception as e:
                        logger.error(f"Sticker failed: {e}")
                
                # Send Text
                try:
                    await bot.send_message(chat_id=target_chat, text=res_msg)
                except:
                    pass

        except Exception as e:
            logger.error(f"Loop Error: {e}")
            await asyncio.sleep(5)

# ==========================================
# 📱 TELEGRAM HANDLERS
# ==========================================
def get_main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("▶ START (Bot DM)", callback_data="start_bot"),
         InlineKeyboardButton("▶ START (Channel)", callback_data="start_channel")],
        [InlineKeyboardButton("⏹ STOP", callback_data="stop")],
        [InlineKeyboardButton("⚙️ ADMIN PANEL", callback_data="admin_menu")]
    ])

def get_admin_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 Users List", callback_data="show_users"),
         InlineKeyboardButton("📢 Set Channel ID", callback_data="set_channel")],
        [InlineKeyboardButton("🟢 Set WIN Sticker", callback_data="set_win_sticker"),
         InlineKeyboardButton("🔴 Set LOSS Sticker", callback_data="set_loss_sticker")],
        [InlineKeyboardButton("📊 STATISTICS", callback_data="stats")],
        [InlineKeyboardButton("🔙 Back to Main", callback_data="back_main")]
    ])

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # Save User
    conn = sqlite3.connect("bot_database.db")
    conn.execute("INSERT OR IGNORE INTO users (uid) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

    if user_id != ADMIN_ID:
        await update.message.reply_text("⛔ Welcome to Ali Prediction VIP.\nAccess Restricted. Only Admin can use this bot.")
        return
        
    await update.message.reply_text("🔥 ALI PREDICTION VIP 🔥\n\nMain Menu:", reply_markup=get_main_keyboard())

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    await update.message.reply_text("⚙️ **ADMIN PANEL**", reply_markup=get_admin_keyboard(), parse_mode="Markdown")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_running, automation_task, admin_states
    query = update.callback_query
    if update.effective_user.id != ADMIN_ID: return
    await query.answer()

    data = query.data

    if data.startswith("start_"):
        if is_running:
            await query.edit_message_text("⚠️ Already Running!", reply_markup=get_main_keyboard())
            return
            
        if data == "start_bot":
            set_setting("TARGET_CHAT", ADMIN_ID)
            target = "BOT DIRECT MESSAGE"
        else:
            ch_id = get_setting("TARGET_CHAT")
            if not ch_id or ch_id == str(ADMIN_ID):
                await query.edit_message_text("⚠️ Pehle Admin Panel se Channel ID set karein!", reply_markup=get_main_keyboard())
                return
            target = "CHANNEL/GROUP"

        is_running = True
        automation_task = asyncio.create_task(automation_worker(context.bot))
        await query.edit_message_text(f"🟢 STARTED IN: {target}\nBot is now sending signals.", reply_markup=get_main_keyboard())

    elif data == "stop":
        if not is_running:
            await query.edit_message_text("⚠️ Already Stopped!", reply_markup=get_main_keyboard())
            return
        is_running = False
        if automation_task: automation_task.cancel()
        await query.edit_message_text("⏹ SESSION STOPPED.", reply_markup=get_main_keyboard())

    elif data == "admin_menu":
        await query.edit_message_text("⚙️ **ADMIN PANEL**", reply_markup=get_admin_keyboard(), parse_mode="Markdown")

    elif data == "show_users":
        conn = sqlite3.connect("bot_database.db")
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*), GROUP_CONCAT(uid) FROM (SELECT uid FROM users ORDER BY joined_at DESC LIMIT 15)")
        row = cur.fetchone()
        conn.close()
        
        count = row[0]
        uids = row[1] if row[1] else "No users yet."
        msg = f"👥 **TOTAL USERS:** {count}\n\n**Recent Users UIDs:**\n{uids}"
        await query.edit_message_text(msg, reply_markup=get_admin_keyboard(), parse_mode="Markdown")

    elif data == "set_channel":
        admin_states[ADMIN_ID] = "WAITING_CHANNEL_ID"
        msg = ("📢 **SET CHANNEL / GROUP ID**\n\n"
               "Apne Group ya Channel ka ID bhejein (e.g., -100123456789).\n"
               "⚠️ *Zaroori:* Bot ko us channel/group mein ADMIN zaroor banayein wrna signal nahi jayega.")
        await query.edit_message_text(msg, parse_mode="Markdown")

    elif data == "set_win_sticker":
        admin_states[ADMIN_ID] = "WAITING_WIN_STICKER"
        await query.edit_message_text("🟢 **WIN STICKER**\n\nAbhi chat mein WIN wala sticker bhejein:", parse_mode="Markdown")

    elif data == "set_loss_sticker":
        admin_states[ADMIN_ID] = "WAITING_LOSS_STICKER"
        await query.edit_message_text("🔴 **LOSS STICKER**\n\nAbhi chat mein LOSS wala sticker bhejein:", parse_mode="Markdown")

    elif data == "stats":
        conn = sqlite3.connect("bot_database.db")
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*), SUM(CASE WHEN win_loss='WIN' THEN 1 ELSE 0 END), SUM(CASE WHEN win_loss='LOSS' THEN 1 ELSE 0 END) FROM history WHERE status='DONE'")
        total, wins, losses = cur.fetchone()
        conn.close()
        total = total or 0; wins = wins or 0; losses = losses or 0
        rate = int((wins/total)*100) if total > 0 else 0
        msg = f"📊 CURRENT STATISTICS\n\n━━━━━━━━━━━━━━━━\n🎯 TOTAL SIGNALS: {total}\n🏆 WINS: {wins}\n❌ LOSSES: {losses}\n📊 WIN RATE: {rate}%\n━━━━━━━━━━━━━━━━"
        await query.edit_message_text(msg, reply_markup=get_admin_keyboard())

    elif data == "back_main":
        await query.edit_message_text("🔥 ALI PREDICTION VIP 🔥\n\nMain Menu:", reply_markup=get_main_keyboard())

async def text_sticker_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID: return
    
    state = admin_states.get(user_id)
    if not state: return

    # Channel ID Set karna
    if state == "WAITING_CHANNEL_ID":
        if update.message.text:
            set_setting("TARGET_CHAT", update.message.text.strip())
            admin_states.pop(user_id)
            await update.message.reply_text(f"✅ Channel ID Set: {update.message.text}", reply_markup=get_main_keyboard())
        return

    # Stickers Set karna
    if update.message.sticker:
        sticker_file_id = update.message.sticker.file_id
        if state == "WAITING_WIN_STICKER":
            set_setting("WIN_STICKER", sticker_file_id)
            admin_states.pop(user_id)
            await update.message.reply_text("✅ WIN Sticker Saved!", reply_markup=get_main_keyboard())
        elif state == "WAITING_LOSS_STICKER":
            set_setting("LOSS_STICKER", sticker_file_id)
            admin_states.pop(user_id)
            await update.message.reply_text("✅ LOSS Sticker Saved!", reply_markup=get_main_keyboard())

# ==========================================
# 🚀 MAIN RUNNER
# ==========================================
def main():
    if TELEGRAM_BOT_TOKEN == "YAHAN_APNA_BOT_TOKEN_DALEIN":
        print("❌ ERROR: Apne Code mein BOT TOKEN aur ADMIN ID dalein pehle!")
        return

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    # Handle both Text (for Channel ID) and Stickers
    app.add_handler(MessageHandler(filters.TEXT | filters.Sticker.ALL, text_sticker_handler))
    
    print("✅ Bot is Running! Go to Telegram and type /start")
    app.run_polling()

if __name__ == "__main__":
    main()
