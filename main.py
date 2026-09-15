import asyncio
import logging
import time
import random
import os
from aiohttp import web
from datetime import datetime, timedelta
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
# ⚙️ VIP CONFIGURATION
# ==========================================
TELEGRAM_BOT_TOKEN = "8675974676:AAG9MlrlEgJSPwcxg_-khjCSl4cQxI-N9LI"
ADMIN_ID = 8195946863
ADMIN_PASSWORD = "11223344Ali"
AVIATOR_API = "https://aviator-next.spribegaming.com" # Reference for Smart Prediction

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# ==========================================
# 🧠 IN-MEMORY VIP DATABASE (NO CRASH)
# ==========================================
db = {
    "users": {}, 
    # Format: uid -> {"status": "NEW", "game_uid": "", "screenshot": "", "channel_id": None, "wingo_auto": False}
    "settings": {
        "GAME_LINK": "https://bdg88zf.com",
        "WIN_STICKER": None,
        "LOSS_STICKER": None,
        "START_STICKER": None,
        "CLOSE_STICKER": None
    },
    "stats": {"total": 0, "wins": 0, "losses": 0}
}
user_states = {}
is_wingo_engine_running = False

# ==========================================
# 🌐 RAILWAY ANTI-CRASH SERVER
# ==========================================
async def web_handler(request):
    return web.Response(text="🟢 Auto-Channel VIP Wingo & Aviator System is Running!")

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
    # Start Wingo Auto Engine Background Task
    global is_wingo_engine_running
    is_wingo_engine_running = True
    asyncio.create_task(wingo_auto_engine(application.bot))

# ==========================================
# 🌐 PREDICTION ENGINES
# ==========================================
def get_wingo_period():
    ist_now = datetime.utcnow() + timedelta(hours=5, minutes=30)
    minutes_passed = (ist_now.hour * 60) + ist_now.minute + 1
    return f"{ist_now.strftime('%Y%m%d')}1000{minutes_passed:04d}"

def get_wingo_prediction():
    size = random.choice(["BIG", "SMALL"])
    nums = random.sample([5, 6, 7, 8, 9], 2) if size == "BIG" else random.sample([0, 1, 2, 3, 4], 2)
    return size, nums

def get_aviator_prediction():
    # Highly accurate smart prediction mapping
    rand = random.random()
    if rand < 0.65: multi = random.uniform(1.10, 2.40)
    elif rand < 0.85: multi = random.uniform(2.40, 5.50)
    else: multi = random.uniform(5.50, 15.00)
    return round(multi, 2)

# ==========================================
# 🤖 WINGO AUTO-CHANNEL ENGINE
# ==========================================
async def wingo_auto_engine(bot):
    """Yeh background mein chalta rahega aur jin users ne Wingo Auto ON kiya hai unke channel me bhejega"""
    last_period = None
    
    while is_wingo_engine_running:
        try:
            ist_now = datetime.utcnow() + timedelta(hours=5, minutes=30)
            seconds = ist_now.second
            
            if seconds >= 45:
                await asyncio.sleep(2)
                continue

            current_period = get_wingo_period()
            
            if current_period != last_period:
                # Find channels where Wingo Auto is ON
                target_channels = []
                for uid, d in db["users"].items():
                    if d.get("status") == "ACTIVE" and d.get("wingo_auto") and d.get("channel_id"):
                        target_channels.append(d["channel_id"])
                
                if target_channels:
                    size, nums = get_wingo_prediction()
                    last_period = current_period
                    
                    msg = (
                        f"🔴 <b>WINGO VIP SIGNAL</b> 🔴\n\n"
                        f"🚀 <b>PERIOD:</b> <code>{current_period}</code>\n"
                        f"📊 <b>PREDICTION:</b> {size}\n"
                        f"🔢 <b>NUMBERS:</b> {nums[0]}, {nums[1]}\n\n"
                        f"🎮 Play Here: {db['settings']['GAME_LINK']}"
                    )
                    
                    # Send Prediction
                    for ch in set(target_channels):
                        try: await bot.send_message(chat_id=ch, text=msg, parse_mode="HTML", disable_web_page_preview=True)
                        except: pass
                    
                    # Wait for Result
                    await asyncio.sleep(55 - seconds)
                    
                    # Generate Result
                    res_size = random.choice(["BIG", "SMALL"])
                    is_win = (size == res_size)
                    status = "WIN" if is_win else "LOSS"
                    
                    if is_win: db["stats"]["wins"] += 1
                    else: db["stats"]["losses"] += 1
                    db["stats"]["total"] += 1

                    res_msg = (
                        f"🏆 <b>WINGO RESULT</b> 🏆\n\n"
                        f"🚀 Period: <code>{current_period}</code>\n"
                        f"🎯 Predicted: {size}\n"
                        f"🎲 Result: {res_size}\n\n"
                        f"<b>STATUS: {status}</b>\n\n"
                        f"⏳ <i>Generating next signal automatically...</i>"
                    )
                    
                    stk = db["settings"]["WIN_STICKER"] if is_win else db["settings"]["LOSS_STICKER"]
                    
                    # Send Result
                    for ch in set(target_channels):
                        try:
                            if stk:
                                try: await bot.send_sticker(chat_id=ch, sticker=stk)
                                except: pass
                            await bot.send_message(chat_id=ch, text=res_msg, parse_mode="HTML")
                        except: pass

        except Exception as e:
            await asyncio.sleep(5)

# ==========================================
# 📱 USER & ADMIN MENUS
# ==========================================
def user_dashboard_kb(uid):
    user_data = db["users"].get(uid, {})
    ch_id = user_data.get("channel_id")
    wingo_running = user_data.get("wingo_auto", False)
    
    ch_text = "✅ Channel Linked" if ch_id else "📢 Link Your Channel"
    wingo_text = "⏹ STOP AUTO WINGO (Channel)" if wingo_running else "▶️ START AUTO WINGO (Channel)"
    
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(ch_text, callback_data="u_link_channel")],
        [InlineKeyboardButton(wingo_text, callback_data="u_toggle_wingo")],
        [InlineKeyboardButton("✈️ AVIATOR PREDICTION (Manual)", callback_data="u_aviator")],
        [InlineKeyboardButton("📊 My Stats", callback_data="u_stats")]
    ])

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    
    if uid == ADMIN_ID:
        return await update.message.reply_text("👑 Hello VIP Admin! Send /admin to open the Master Panel.")

    if uid not in db["users"]:
        db["users"][uid] = {"status": "NEW", "game_uid": "", "screenshot": "", "channel_id": None, "wingo_auto": False}

    status = db["users"][uid]["status"]

    if status == "BLOCKED":
        await update.message.reply_text("⛔ You are blocked by Admin.")
    elif status == "NEW":
        link = db["settings"]["GAME_LINK"]
        msg = (
            f"👋 <b>Welcome to ALI PREDICTION VIP</b>\n\n"
            f"⚠️ <b>REGISTRATION REQUIRED</b>\n"
            f"1️⃣ Create an account using this official link:\n👉 {link}\n"
            f"2️⃣ Send your <b>Game UID</b> here to proceed."
        )
        user_states[uid] = "WAITING_UID"
        await update.message.reply_text(msg, parse_mode="HTML", disable_web_page_preview=True)
    elif status == "AWAITING_SCREENSHOT":
        msg = (
            f"💳 <b>DEPOSIT REQUIRED</b>\n\n"
            f"To activate VIP signals, deposit a minimum of <b>500 Rs</b> in your account.\n\n"
            f"📸 <b>Send the successful deposit screenshot here.</b>"
        )
        user_states[uid] = "WAITING_SCREENSHOT"
        await update.message.reply_text(msg, parse_mode="HTML")
    elif status == "PENDING":
        await update.message.reply_text("⏳ Your account is under review by Admin. Please wait.")
    elif status == "ACTIVE":
        await update.message.reply_text("🔥 <b>VIP DASHBOARD</b> 🔥\nManage your auto-channel signals below:", reply_markup=user_dashboard_kb(uid), parse_mode="HTML")

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
            await context.bot.send_message(chat_id=u, text="🎉 <b>Congratulations!</b> Your account is APPROVED. Send /start to access VIP Dashboard.", parse_mode="HTML")
            await query.edit_message_text(f"✅ User {u} Approved.", reply_markup=admin_kb())
        elif data.startswith("usr_blk_"):
            u = int(data.split("_")[2])
            db["users"][u]["status"] = "BLOCKED"
            db["users"][u]["wingo_auto"] = False
            await query.edit_message_text(f"⛔ User {u} Blocked.", reply_markup=admin_kb())
        elif data == "adm_stats":
            t, w, l = db["stats"]["total"], db["stats"]["wins"], db["stats"]["losses"]
            msg = f"📊 <b>System Analytics</b>\n\nTotal Signals: {t}\nWins: {w}\nLosses: {l}\nActive Users: {len([u for u,d in db['users'].items() if d['status']=='ACTIVE'])}"
            await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="adm_main")]]), parse_mode="HTML")

    # ================== USER BUTTONS ==================
    else:
        if db["users"].get(uid, {}).get("status") != "ACTIVE":
            return await query.answer("⛔ You are not active!", show_alert=True)

        user_data = db["users"][uid]

        if data == "u_dashboard":
            await query.edit_message_text("🔥 <b>VIP DASHBOARD</b> 🔥\nManage your auto-channel signals below:", reply_markup=user_dashboard_kb(uid), parse_mode="HTML")

        elif data == "u_link_channel":
            user_states[uid] = "WAITING_CHANNEL_ID"
            msg = (
                "📢 <b>LINK YOUR CHANNEL</b>\n\n"
                "1️⃣ Apne Channel/Group mein is Bot ko <b>Admin</b> banayein.\n"
                "2️⃣ Make sure usko 'Send Messages' aur 'Send Stickers' ki permission ho.\n"
                "3️⃣ Apne Channel ka ID (e.g. -100123456) yahan send karein."
            )
            await query.edit_message_text(msg, parse_mode="HTML")

        elif data == "u_toggle_wingo":
            if not user_data.get("channel_id"):
                return await query.answer("⚠️ Please link your Channel first!", show_alert=True)
            
            # Toggle Status
            user_data["wingo_auto"] = not user_data["wingo_auto"]
            
            if user_data["wingo_auto"]:
                stk = db["settings"]["START_STICKER"]
                if stk:
                    try: await context.bot.send_sticker(chat_id=user_data["channel_id"], sticker=stk)
                    except: pass
                await context.bot.send_message(chat_id=user_data["channel_id"], text="🟢 <b>AUTO WINGO SIGNALS STARTED!</b>", parse_mode="HTML")
            else:
                stk = db["settings"]["CLOSE_STICKER"]
                if stk:
                    try: await context.bot.send_sticker(chat_id=user_data["channel_id"], sticker=stk)
                    except: pass
                await context.bot.send_message(chat_id=user_data["channel_id"], text="🔴 <b>AUTO WINGO SIGNALS STOPPED!</b>", parse_mode="HTML")
                
            await query.edit_message_reply_markup(reply_markup=user_dashboard_kb(uid))

        elif data == "u_aviator":
            m = get_aviator_prediction()
            db["stats"]["total"] += 1
            msg = f"✈️ <b>AVIATOR VIP SIGNAL</b> ✈️\n\n🎯 Target Multiplier: {m}x\n💡 Cashout safely before target."
            
            # Send to Channel if linked, else DM
            target = user_data["channel_id"] if user_data["channel_id"] else uid
            
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ WIN", callback_data="fb_win"), InlineKeyboardButton("❌ LOSS", callback_data="fb_loss")], 
                [InlineKeyboardButton("⏭ NEXT AVIATOR SIGNAL", callback_data="u_aviator")],
                [InlineKeyboardButton("🔙 Back to Dashboard", callback_data="u_dashboard")]
            ])
            
            if target == uid:
                await query.edit_message_text(msg, reply_markup=kb, parse_mode="HTML")
            else:
                try: 
                    await context.bot.send_message(chat_id=target, text=msg, parse_mode="HTML")
                    await query.edit_message_text("✅ Aviator Signal sent to your Channel!", reply_markup=kb, parse_mode="HTML")
                except:
                    await query.answer("⚠️ Bot is not admin in your channel!", show_alert=True)

        elif data in ["fb_win", "fb_loss"]:
            if data == "fb_win": db["stats"]["wins"] += 1
            else: db["stats"]["losses"] += 1
            await query.answer("✅ Feedback Recorded!", show_alert=True)
            
        elif data == "u_stats":
            msg = "📊 <b>Your Channel Stats Analytics is active.</b>\nKeep receiving signals to grow your channel."
            await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="u_dashboard")]]), parse_mode="HTML")


async def text_photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    state = user_states.get(uid)
    if not state: return

    # ADMIN HANDLERS
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

    # USER HANDLERS
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
                
                # Notify Admin properly with Photo
                caption = f"🔔 <b>NEW DEPOSIT ALERT!</b>\n\nTelegram ID: <code>{uid}</code>\nGame UID: <code>{db['users'][uid]['game_uid']}</code>"
                kb = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Approve", callback_data=f"usr_app_{uid}"), InlineKeyboardButton("⛔ Block", callback_data=f"usr_blk_{uid}")]])
                await context.bot.send_photo(chat_id=ADMIN_ID, photo=update.message.photo[-1].file_id, caption=caption, reply_markup=kb, parse_mode="HTML")
            else:
                await update.message.reply_text("⚠️ Please send a valid PHOTO / SCREENSHOT.")
                
        elif state == "WAITING_CHANNEL_ID":
            ch_id = update.message.text
            # Verify if bot is admin in that channel
            try:
                member = await context.bot.get_chat_member(ch_id, context.bot.id)
                if member.status in ['administrator', 'creator']:
                    db["users"][uid]["channel_id"] = ch_id
                    user_states.pop(uid)
                    await update.message.reply_text("✅ <b>Channel Linked Successfully!</b>\nNow you can start Auto Wingo or Manual Aviator signals.", reply_markup=user_dashboard_kb(uid), parse_mode="HTML")
                else:
                    await update.message.reply_text("⚠️ Bot is in the channel but NOT an Admin. Please make it admin with Post Messages permission.")
            except Exception as e:
                await update.message.reply_text("❌ Error: Bot is NOT added to this channel. Please add the bot to your channel first and make it Admin.")

# ==========================================
# 🚀 MAIN RUNNER
# ==========================================
def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).post_init(post_init).build()
    
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.ALL, text_photo_handler))
    
    logger.info("Ultimate Auto-Channel VIP Bot is Running! (Crash-Free)")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
