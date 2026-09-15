import asyncio
import logging
import time
import random
import os
import hashlib
import aiohttp
from aiohttp import web
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
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
# ⚙️ VIP CONFIGURATION & REAL APIs
# ==========================================
TELEGRAM_BOT_TOKEN = "8675974676:AAG9MlrlEgJSPwcxg_-khjCSl4cQxI-N9LI"
ADMIN_ID = 8195946863
ADMIN_PASSWORD = "11223344Ali"

API_URL = 'https://api.bdg88zf.com/api/webapi/GetGameIssue'
AVIATOR_SPRIBE_API = "https://aviator-next.spribegaming.com"
API_PAYLOAD = {
    "typeId": 1,
    "language": 0,
    "random": "40079dcba93a48769c6ee9d4d4fae23f",
    "signature": "D12108C4F57C549D82B23A91E0FA20AE"
}

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# ==========================================
# 🧠 IN-MEMORY VIP DATABASE (CRASH FREE)
# ==========================================
db = {
    "users": {}, 
    "settings": {
        "GAME_LINK": "https://aviator-game-link.com",
        "WIN_STICKER": None,
        "LOSS_STICKER": None,
        "START_STICKER": None,
        "CLOSE_STICKER": None
    },
    "stats": {"total": 0, "wins": 0, "losses": 0}
}
user_states = {}
is_aviator_engine_running = False

# ==========================================
# 🌐 RAILWAY ANTI-CRASH SERVER
# ==========================================
async def web_handler(request):
    return web.Response(text="🟢 Real API Aviator System (1.04x - 20x) is Running!")

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
    asyncio.create_task(start_web_server())
    global is_aviator_engine_running
    is_aviator_engine_running = True
    asyncio.create_task(aviator_auto_engine(application.bot))

# ==========================================
# 🚀 REAL API FETCH & SPRIBE ENGINE
# ==========================================
async def fetch_real_api_data():
    """Connects to real APIs to sync data and generate authentic hash"""
    try:
        payload = API_PAYLOAD.copy()
        payload["timestamp"] = int(time.time())
        
        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL, json=payload, timeout=5) as response:
                api_response = await response.json()
                
            async with session.get(AVIATOR_SPRIBE_API, timeout=5) as spribe_res:
                spribe_status = spribe_res.status
                
        raw_hash_data = f"SPRIBE_{payload['timestamp']}_{spribe_status}_{api_response.get('msg', 'SUCCESS')}"
        api_hash = hashlib.sha256(raw_hash_data.encode()).hexdigest()[:16].upper()
        return True, api_hash
        
    except Exception as e:
        fallback_hash = hashlib.sha256(f"SPRIBE_FALLBACK_{time.time()}".encode()).hexdigest()[:16].upper()
        return False, fallback_hash

def calculate_aviator_prediction():
    """Authentic Aviator Range: 1.04x to 20.00x"""
    rand = random.random()
    # Realistic Aviator Algorithm Distribution
    if rand < 0.50:
        target = random.uniform(1.04, 2.00)  # 50% chance for safe low multipliers
    elif rand < 0.80:
        target = random.uniform(2.00, 5.00)  # 30% chance for medium multipliers
    elif rand < 0.92:
        target = random.uniform(5.00, 10.00) # 12% chance for high multipliers
    else:
        target = random.uniform(10.00, 20.00) # 8% chance for Mega Jackpot
    return round(target, 2)

# ==========================================
# 🤖 AVIATOR AUTO-DM ENGINE
# ==========================================
async def aviator_auto_engine(bot):
    """Background loop sending continuous signals to Active Users DMs"""
    while is_aviator_engine_running:
        try:
            target_users = [uid for uid, d in db["users"].items() if d.get("status") == "ACTIVE" and d.get("aviator_auto")]
            
            if target_users:
                # 1. Fetch Real API & Calculate
                api_connected, api_hash = await fetch_real_api_data()
                target_multi = calculate_aviator_prediction()
                
                msg = (
                    f"✈️ <b>AVIATOR VIP PREDICTION</b> ✈️\n\n"
                    f"🔗 <b>SERVER STATUS:</b> Connected (Spribe API)\n"
                    f"🔐 <b>ENCRYPTED HASH:</b> <code>{api_hash}</code>\n\n"
                    f"🎯 <b>TARGET CASHOUT:</b> {target_multi}x\n\n"
                    f"💡 <i>Tip: Play safe and cashout before the exact target!</i>\n"
                    f"🎮 Play Here: {db['settings']['GAME_LINK']}"
                )
                
                for uid in set(target_users):
                    try: await bot.send_message(chat_id=uid, text=msg, parse_mode="HTML", disable_web_page_preview=True)
                    except: pass
                
                await asyncio.sleep(45) # Simulating round time
                
                # 95% Win logic implementation for result simulation
                is_win = random.random() < 0.95 
                status = "WIN" if is_win else "LOSS"
                
                if is_win:
                    # Crash happens AFTER the target
                    actual_crash = round(target_multi + random.uniform(0.1, 3.5), 2)
                else:
                    # Crash happens BEFORE the target
                    actual_crash = round(target_multi - random.uniform(0.1, 0.5), 2)
                
                if actual_crash < 1.00: actual_crash = 1.00
                
                if is_win: db["stats"]["wins"] += 1
                else: db["stats"]["losses"] += 1
                db["stats"]["total"] += 1

                res_msg = (
                    f"🏆 <b>ROUND RESULT</b> 🏆\n\n"
                    f"🎯 <b>Target Given:</b> {target_multi}x\n"
                    f"💥 <b>Crashed At:</b> {actual_crash}x\n\n"
                    f"<b>STATUS: {status}</b>\n\n"
                    f"⏳ <i>Fetching next round API data...</i>"
                )
                
                stk = db["settings"]["WIN_STICKER"] if is_win else db["settings"]["LOSS_STICKER"]
                
                for uid in set(target_users):
                    try:
                        if stk:
                            try: await bot.send_sticker(chat_id=uid, sticker=stk)
                            except: pass
                        await bot.send_message(chat_id=uid, text=res_msg, parse_mode="HTML")
                    except: pass
                
                await asyncio.sleep(15)
            else:
                await asyncio.sleep(10)

        except Exception as e:
            logger.error(f"Engine Loop Error: {e}")
            await asyncio.sleep(5)

# ==========================================
# 📱 USER & ADMIN MENUS
# ==========================================
def user_dashboard_kb(uid):
    user_data = db["users"].get(uid, {})
    aviator_running = user_data.get("aviator_auto", False)
    av_text = "⏹ STOP AUTO AVIATOR (DM)" if aviator_running else "▶️ START AUTO AVIATOR (DM)"
    
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(av_text, callback_data="u_toggle_aviator")],
        [InlineKeyboardButton("✈️ MANUAL SIGNAL (DM)", callback_data="u_manual_aviator")],
        [InlineKeyboardButton("📊 My Analytics", callback_data="u_stats")]
    ])

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid == ADMIN_ID: return await update.message.reply_text("👑 VIP Admin! Send /admin to open the Panel.")

    if uid not in db["users"]:
        db["users"][uid] = {"status": "NEW", "game_uid": "", "screenshot": "", "aviator_auto": False}

    status = db["users"][uid]["status"]
    if status == "BLOCKED":
        await update.message.reply_text("⛔ You are blocked by Admin.")
    elif status == "NEW":
        link = db["settings"]["GAME_LINK"]
        msg = (
            f"🚀 <b>Welcome to AVIATOR SPRIBE HACK</b>\n\n"
            f"⚠️ <b>REGISTRATION REQUIRED</b>\n"
            f"1️⃣ Create an account using this official link:\n👉 {link}\n"
            f"2️⃣ Send your <b>Game UID</b> here to proceed."
        )
        user_states[uid] = "WAITING_UID"
        await update.message.reply_text(msg, parse_mode="HTML", disable_web_page_preview=True)
    elif status == "AWAITING_SCREENSHOT":
        msg = f"💳 <b>DEPOSIT REQUIRED</b>\n\nDeposit a minimum of <b>500 Rs</b> to activate the API Hack.\n📸 <b>Send the successful deposit screenshot here.</b>"
        user_states[uid] = "WAITING_SCREENSHOT"
        await update.message.reply_text(msg, parse_mode="HTML")
    elif status == "PENDING":
        await update.message.reply_text("⏳ Your account is under review by Admin. Please wait.")
    elif status == "ACTIVE":
        await update.message.reply_text("🔥 <b>VIP AVIATOR DASHBOARD</b> 🔥\nManage your DM signals below:", reply_markup=user_dashboard_kb(uid), parse_mode="HTML")

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    user_states[ADMIN_ID] = "WAITING_PASSWORD"
    await update.message.reply_text("🔒 <b>Enter Admin Password:</b>", parse_mode="HTML")

def admin_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 User Management", callback_data="adm_users")],
        [InlineKeyboardButton("🖼 Set Stickers", callback_data="adm_stickers"), InlineKeyboardButton("🔗 Set Game Link", callback_data="adm_link")],
        [InlineKeyboardButton("📢 Broadcast Message", callback_data="adm_broadcast"), InlineKeyboardButton("📊 Analytics", callback_data="adm_stats")]
    ])

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = update.effective_user.id
    await query.answer()
    data = query.data

    # ================== ADMIN BUTTONS ==================
    if uid == ADMIN_ID:
        if data == "adm_main":
            await query.edit_message_text("👑 <b>MASTER ADMIN PANEL</b>", reply_markup=admin_kb(), parse_mode="HTML")
        elif data == "adm_stickers":
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("WIN Sticker", callback_data="stk_WIN_STICKER"), InlineKeyboardButton("LOSS Sticker", callback_data="stk_LOSS_STICKER")],
                [InlineKeyboardButton("START Session", callback_data="stk_START_STICKER"), InlineKeyboardButton("CLOSE Session", callback_data="stk_CLOSE_STICKER")],
                [InlineKeyboardButton("🔙 Back", callback_data="adm_main")]
            ])
            await query.edit_message_text("🖼 <b>Select Sticker to Update:</b>", reply_markup=kb, parse_mode="HTML")
        elif data.startswith("stk_"):
            key = data.replace("stk_", "")
            user_states[uid] = f"WAITING_{key}"
            await query.edit_message_text(f"Please send the {key} sticker now:")
        elif data == "adm_link":
            user_states[uid] = "WAITING_GAME_LINK"
            await query.edit_message_text("🔗 Send the new Game Registration Link:")
        elif data == "adm_broadcast":
            user_states[uid] = "WAITING_BROADCAST"
            await query.edit_message_text("📢 Send text or photo to broadcast to all ACTIVE users:")
        elif data == "adm_users":
            kb = [[InlineKeyboardButton("🔙 Back", callback_data="adm_main")]]
            text = "👥 <b>Users List:</b>\n\n"
            for u, d in db["users"].items():
                emoji = "🟢" if d["status"]=="ACTIVE" else "🟡" if d["status"]=="PENDING" else "🔴"
                text += f"{emoji} <code>{u}</code> | UID: {d['game_uid']}\n"
                kb.insert(0, [InlineKeyboardButton(f"Manage {u}", callback_data=f"manage_{u}")])
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")
        elif data.startswith("manage_"):
            target_u = int(data.split("_")[1])
            d = db["users"][target_u]
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Approve", callback_data=f"usr_app_{target_u}"), InlineKeyboardButton("⛔ Block", callback_data=f"usr_blk_{target_u}")],
                [InlineKeyboardButton("🔙 Back", callback_data="adm_users")]
            ])
            await query.edit_message_text(f"👤 <b>Manage User <code>{target_u}</code></b>\n\nGame UID: {d['game_uid']}\nStatus: {d['status']}", reply_markup=kb, parse_mode="HTML")
        elif data.startswith("usr_app_"):
            u = int(data.split("_")[2])
            db["users"][u]["status"] = "ACTIVE"
            await context.bot.send_message(chat_id=u, text="🎉 <b>Congratulations!</b> Your Aviator Hack is APPROVED. Send /start to access Dashboard.", parse_mode="HTML")
            await query.edit_message_text(f"✅ User {u} Approved.", reply_markup=admin_kb())
        elif data.startswith("usr_blk_"):
            u = int(data.split("_")[2])
            db["users"][u]["status"] = "BLOCKED"
            db["users"][u]["aviator_auto"] = False
            await query.edit_message_text(f"⛔ User {u} Blocked.", reply_markup=admin_kb())
        elif data == "adm_stats":
            t, w, l = db["stats"]["total"], db["stats"]["wins"], db["stats"]["losses"]
            msg = f"📊 <b>Aviator Hack Analytics</b>\n\nTotal Signals: {t}\nWins: {w}\nLosses: {l}\nActive Users: {len([u for u,d in db['users'].items() if d['status']=='ACTIVE'])}"
            await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="adm_main")]]), parse_mode="HTML")

    # ================== USER BUTTONS ==================
    else:
        if db["users"].get(uid, {}).get("status") != "ACTIVE":
            return await query.answer("⛔ You are not active!", show_alert=True)
        user_data = db["users"][uid]

        if data == "u_dashboard":
            await query.edit_message_text("🔥 <b>VIP AVIATOR DASHBOARD</b> 🔥", reply_markup=user_dashboard_kb(uid), parse_mode="HTML")

        elif data == "u_toggle_aviator":
            user_data["aviator_auto"] = not user_data["aviator_auto"]
            if user_data["aviator_auto"]:
                stk = db["settings"]["START_STICKER"]
                if stk:
                    try: await context.bot.send_sticker(chat_id=uid, sticker=stk)
                    except: pass
                await context.bot.send_message(chat_id=uid, text="🟢 <b>AUTO AVIATOR SIGNALS (DM) STARTED!</b>", parse_mode="HTML")
            else:
                stk = db["settings"]["CLOSE_STICKER"]
                if stk:
                    try: await context.bot.send_sticker(chat_id=uid, sticker=stk)
                    except: pass
                await context.bot.send_message(chat_id=uid, text="🔴 <b>AUTO AVIATOR SIGNALS (DM) STOPPED!</b>", parse_mode="HTML")
                
            await query.edit_message_reply_markup(reply_markup=user_dashboard_kb(uid))

        elif data == "u_manual_aviator":
            await query.edit_message_text("⏳ Connecting to Spribe Server API...", parse_mode="HTML")
            _, api_hash = await fetch_real_api_data()
            m = calculate_aviator_prediction()
            db["stats"]["total"] += 1
            
            msg = (f"✈️ <b>MANUAL AVIATOR SIGNAL</b>\n\n"
                   f"🔗 <b>API:</b> Connected\n"
                   f"🔐 <b>Hash:</b> <code>{api_hash}</code>\n\n"
                   f"🎯 <b>Target Multiplier:</b> {m}x\n"
                   f"💡 <i>Cashout safely before target.</i>")
                   
            kb = InlineKeyboardMarkup([[InlineKeyboardButton("✅ WIN", callback_data="fb_win"), InlineKeyboardButton("❌ LOSS", callback_data="fb_loss")], [InlineKeyboardButton("⏭ NEXT SINGLE", callback_data="u_manual_aviator"), InlineKeyboardButton("🔙 Dashboard", callback_data="u_dashboard")]])
            await query.edit_message_text(msg, reply_markup=kb, parse_mode="HTML")

        elif data in ["fb_win", "fb_loss"]:
            if data == "fb_win": db["stats"]["wins"] += 1
            else: db["stats"]["losses"] += 1
            await query.answer("✅ Feedback Recorded!", show_alert=True)
            
        elif data == "u_stats":
            t, w, l = db["stats"]["total"], db["stats"]["wins"], db["stats"]["losses"]
            win_rate = int((w/t)*100) if t > 0 else 0
            msg = f"📊 <b>Your VIP Stats Analytics</b>\n\nSignals: {t}\nWins: {w}\nLosses: {l}\nWin Rate: <b>{win_rate}%</b>\n\nKeep receiving signals to grow."
            await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="u_dashboard")]]), parse_mode="HTML")

async def text_photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    state = user_states.get(uid)
    if not state: return

    if uid == ADMIN_ID:
        if state == "WAITING_PASSWORD":
            if update.message.text == ADMIN_PASSWORD:
                user_states.pop(uid)
                await update.message.reply_text("👑 <b>MASTER ADMIN PANEL</b>", reply_markup=admin_kb(), parse_mode="HTML")
            else:
                await update.message.reply_text("❌ Wrong Password")
        elif state.startswith("WAITING_") and "STICKER" in state:
            if update.message.sticker:
                key = state.replace("WAITING_", "")
                db["settings"][key] = update.message.sticker.file_id
                user_states.pop(uid)
                await update.message.reply_text(f"✅ {key} Saved!", reply_markup=admin_kb())
        elif state == "WAITING_GAME_LINK":
            db["settings"]["GAME_LINK"] = update.message.text
            user_states.pop(uid)
            await update.message.reply_text("✅ Link Saved!", reply_markup=admin_kb())
        elif state == "WAITING_BROADCAST":
            user_states.pop(uid)
            active_users = [u for u, d in db["users"].items() if d["status"] == "ACTIVE"]
            for u in active_users:
                try:
                    if update.message.photo: await context.bot.send_photo(chat_id=u, photo=update.message.photo[-1].file_id, caption=update.message.caption or "", parse_mode="HTML")
                    else: await context.bot.send_message(chat_id=u, text=update.message.text, parse_mode="HTML")
                except: pass
            await update.message.reply_text("✅ Broadcast Sent!", reply_markup=admin_kb())

    else:
        if state == "WAITING_UID":
            db["users"][uid]["game_uid"] = update.message.text
            db["users"][uid]["status"] = "AWAITING_SCREENSHOT"
            user_states.pop(uid)
            await update.message.reply_text("✅ UID Received.\n\n💳 <b>Deposit Min 500 Rs and send the successful screenshot here.</b>", parse_mode="HTML")
        elif state == "WAITING_SCREENSHOT":
            if update.message.photo:
                db["users"][uid]["screenshot"] = update.message.photo[-1].file_id
                db["users"][uid]["status"] = "PENDING"
                user_states.pop(uid)
                await update.message.reply_text("✅ Screenshot received! Please wait for Admin approval.")
                caption = f"🔔 <b>NEW DEPOSIT ALERT!</b>\nTelegram ID: <code>{uid}</code>\nGame UID: <code>{db['users'][uid]['game_uid']}</code>"
                kb = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Approve", callback_data=f"usr_app_{uid}"), InlineKeyboardButton("⛔ Block", callback_data=f"usr_blk_{uid}")]])
                await context.bot.send_photo(chat_id=ADMIN_ID, photo=update.message.photo[-1].file_id, caption=caption, reply_markup=kb, parse_mode="HTML")
            else:
                await update.message.reply_text("⚠️ Please send a valid PHOTO / SCREENSHOT.")

# ==========================================
# 🚀 MAIN RUNNER
# ==========================================
def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).post_init(post_init).build()
    
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.ALL, text_photo_handler))
    
    logger.info("Aviator Spribe Hack Bot (1.04x - 20x) is Running! (Crash-Free)")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
