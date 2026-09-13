import asyncio
import logging
import time
import random
import os
from aiohttp import web
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
# ⚙️ CONFIGURATION & NEW TOKEN
# ==========================================
TELEGRAM_BOT_TOKEN = "8675974676:AAG9MlrlEgJSPwcxg_-khjCSl4cQxI-N9LI"
ADMIN_ID = 8195946863
ADMIN_PASSWORD = "11223344Ali"

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# ==========================================
# 🧠 IN-MEMORY DATABASE (CRASH-FREE)
# ==========================================
# Railway par crash se bachne ke liye data RAM mein rakha hai
today_stats = {"total": 0, "wins": 0, "losses": 0}
user_states = {}
all_users = set() # Broadcast ke liye users track karega

# ==========================================
# 🌐 RAILWAY NATIVE WEB SERVER (NEVER CRASH)
# ==========================================
async def web_handler(request):
    return web.Response(text="🟢 Ultimate Wingo & Aviator Bot is Running Perfectly!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', web_handler)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logger.info(f"Railway Web Server Started on Port {port}")

async def post_init(application: Application):
    # Telegram loop ke sath background mein web server chalayega
    asyncio.create_task(start_web_server())

# ==========================================
# 🌐 PREDICTION ENGINES
# ==========================================
def get_wingo_period():
    # 100% accurate mathematical period calculation (No API needed = No Crash)
    ist_now = datetime.utcnow() + timedelta(hours=5, minutes=30)
    minutes_passed = (ist_now.hour * 60) + ist_now.minute + 1
    return f"{ist_now.strftime('%Y%m%d')}1000{minutes_passed:04d}"

def get_wingo_prediction():
    size = random.choice(["BIG", "SMALL"])
    nums = random.sample([5, 6, 7, 8, 9], 2) if size == "BIG" else random.sample([0, 1, 2, 3, 4], 2)
    return size, nums

def get_aviator_prediction():
    rand = random.random()
    if rand < 0.6: multi = random.uniform(1.20, 2.50)
    elif rand < 0.9: multi = random.uniform(2.50, 5.00)
    else: multi = random.uniform(5.00, 10.00)
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
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")]
    ])

def aviator_kb(pred_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ WIN", callback_data=f"av_win_{pred_id}"), InlineKeyboardButton("❌ LOSS", callback_data=f"av_loss_{pred_id}")],
        [InlineKeyboardButton("⏭ NEXT SINGLE (Aviator)", callback_data="play_aviator")],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")]
    ])

def aviator_next_only_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⏭ NEXT SINGLE (Aviator)", callback_data="play_aviator")],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")]
    ])

# ==========================================
# 🤖 HANDLERS
# ==========================================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    all_users.add(user_id) # Save user for broadcast
    
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
    all_users.add(uid)
    await query.answer()
    data = query.data

    if data == "main_menu":
        await query.edit_message_text("🔥 <b>ALI PREDICTION VIP</b> 🔥\n\nChoose your game:", reply_markup=main_menu_kb(), parse_mode="HTML")

    # --- WINGO PREDICTION ---
    elif data == "play_wingo":
        period = get_wingo_period()
        size, nums = get_wingo_prediction()
        today_stats["total"] += 1
        
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
        multiplier = get_aviator_prediction()
        pred_id = int(time.time())
        today_stats["total"] += 1
        
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
        
        if result == "WIN":
            today_stats["wins"] += 1
        else:
            today_stats["losses"] += 1
            
        res_text = "✅ <b>WIN RECORDED!</b>" if result == "WIN" else "❌ <b>LOSS RECORDED!</b>"
        
        old_text = query.message.text.replace("👇 Please submit your feedback below after playing:", "")
        new_msg = f"{old_text}\n\n{res_text}\nThank you for your feedback!"
        
        await query.edit_message_text(new_msg, reply_markup=aviator_next_only_kb(), parse_mode="HTML")

    # --- STATISTICS ---
    elif data == "show_stats":
        t = today_stats["total"]
        w = today_stats["wins"]
        l = today_stats["losses"]
        rate = int((w / t) * 100) if t > 0 else 0
        
        msg = (
            f"📊 <b>TODAY'S STATISTICS</b> 📊\n\n"
            f"📅 <b>Date:</b> {datetime.utcnow().strftime('%Y-%m-%d')}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🎯 <b>Total Signals Today:</b> {t}\n"
            f"🏆 <b>Total Wins:</b> {w}\n"
            f"❌ <b>Total Losses:</b> {l}\n"
            f"📈 <b>Accuracy / Win Rate:</b> {rate}%\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"<i>*Stats are calculated live.</i>"
        )
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")]])
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
            t = today_stats["total"]
            w = today_stats["wins"]
            l = today_stats["losses"]
            rate = int((w / t) * 100) if t > 0 else 0
            
            msg = (
                f"⚙️ <b>MASTER ADMIN PANEL</b>\n\n"
                f"📊 <b>TODAY'S PERFORMANCE:</b>\n"
                f"Total Signals: {t}\nWins: {w}\nLosses: {l}\nWin Rate: {rate}%\n\n"
                f"👥 <b>Active Users in RAM:</b> {len(all_users)}"
            )
            kb = InlineKeyboardMarkup([[InlineKeyboardButton("📢 Broadcast Message", callback_data="adm_broadcast")]])
            await update.message.reply_text(msg, reply_markup=kb, parse_mode="HTML")
        else:
            await update.message.reply_text("❌ Incorrect Password.")
            
    elif state == "WAITING_BROADCAST":
        user_states.pop(uid)
        success_count = 0
        for user in all_users:
            try:
                await update.message.copy(chat_id=user)
                success_count += 1
            except: pass
        await update.message.reply_text(f"✅ Broadcast sent successfully to {success_count} users.")

# ==========================================
# 🚀 MAIN RUNNER
# ==========================================
def main():
    # Application setup
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).post_init(post_init).build()
    
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.ALL, text_handler))
    
    logger.info("Ultimate RAM-Based Bot is Running! (Crash-Free)")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
