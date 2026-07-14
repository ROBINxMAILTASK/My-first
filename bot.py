import telebot
from telebot import types
import threading
from flask import Flask
import os

# --- 1. RENDER 24/7 KEEP-ALIVE SERVER ---
app = Flask('')

@app.route('/')
def home():
    return "TASK WORK Bot Engine is Live!"

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- 2. BOT BASE CONFIGURATION ---
API_TOKEN = '8688748786:AAGK1QI_5vFdiDmR8V-uPRKmCZeTvQ5wwjU'  # 👈 Replace with your Telegram Bot Token
ADMIN_ID = 6535711381              # 👈 Replace with your Telegram Account Admin ID

bot = telebot.TeleBot(API_TOKEN)

# --- 3. CONFIGURATIONS & REWARDS ---
REQUIRED_CHANNELS = ["@ROBINGMAILWORK"]
MIN_WITHDRAWAL = 20

SINGLE_TASK_REWARD = 10.0
BULK_TASK_REWARD = 15.0

# ⚙️ GMAIL TASK SWITCH (True = Open, False = Force "No Task Available")
GMAIL_TASKS_ACTIVE = False  # 👈 Change this to True when you want to start giving tasks!

# 📋 DYNAMIC GMAIL WORK POOL (1-by-1 Distribution Queue)
GMAIL_TASK_POOL = [
    {
        "id": "task_001",
        "email": "fabricoespeche135@gmail.com",
        "pass": "ROBINXMAIL#112233",
        "assigned_to": None,
        "completed": False
    },
    {
        "id": "task_002",
        "email": "anotherworker99@gmail.com",
        "pass": "ROBINXMAIL#556677",
        "assigned_to": None,
        "completed": False
    }
]

SPECIFIC_TASK_TITLE = "Gmail Creation Assignment"
SPECIFIC_TASK_LINK = "https://accounts.google.com/signup"
SPECIFIC_TASK_INSTRUCTIONS = (
    "Create a fresh Gmail account using the exact structural details shown above. "
    "Once done, take a clear screenshot of your finalized Google account dashboard "
    "showing the created email ID and submit it directly here."
)

# --- 4. PERSISTENT IN-MEMORY STORAGE ---
user_db = {}

# --- 5. INTERFACE GENERATORS ---
def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    markup.row(types.KeyboardButton('📥 Get Review Task'), types.KeyboardButton('📥 Get Gmail Task'))
    markup.row(types.KeyboardButton('💳 Wallet'), types.KeyboardButton('👥 Invite & Earn'))
    markup.row(types.KeyboardButton('💸 Withdraw'), types.KeyboardButton('ℹ️ Help & Tutorial'))
    markup.row(types.KeyboardButton('🏆 Leaderboard'))
    return markup

# --- UTILITY: MEMBER FORCE JOIN ---
def is_user_subscribed(user_id):
    if user_id == ADMIN_ID:
        return True
    for channel in REQUIRED_CHANNELS:
        clean_channel = channel.strip()
        if not clean_channel or "t.me" in clean_channel or clean_channel.startswith("http"):
            continue
        try:
            member = bot.get_chat_member(clean_channel, user_id)
            if member.status in ['left', 'kicked']:
                return False
        except Exception:
            continue
    return True

def send_force_join_menu(chat_id):
    markup = types.InlineKeyboardMarkup()
    for channel in REQUIRED_CHANNELS:
        clean_ch = channel.strip()
        if "t.me" in clean_ch or clean_ch.startswith("http"):
            url = clean_ch
        else:
            url = f"https://t.me/{clean_ch.replace('@', '')}"
        markup.add(types.InlineKeyboardButton(f"Join {clean_ch} 📢", url=url))
    markup.add(types.InlineKeyboardButton("✅ I have joined", callback_data="verify_channel_joins"))
    bot.send_message(chat_id, "🚨 Join our Telegram Channels first to use this bot!", reply_markup=markup)

def initialize_user(user_id, username=None, first_name="Worker", referrer_id=None):
    if user_id not in user_db:
        user_db[user_id] = {
            "balance": 0.0,
            "pending": 0.0,
            "gmail_count": 0,
            "referrals": 0,
            "active_task": None,        
            "waiting_approval": False,  
            "referrer_id": referrer_id,
            "username": f"@{username}" if username else "No Username",
            "first_name": first_name if first_name else "Worker"
        }
    else:
        if username:
            user_db[user_id]["username"] = f"@{username}"
        if first_name:
            user_db[user_id]["first_name"] = first_name

# --- 6. CORE BOT EVENT CONTROLLERS ---
@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.chat.id
    parts = message.text.split()
    
    referrer_id = None
    if len(parts) > 1 and parts[1].isdigit():
        potential_referrer = int(parts[1])
        if potential_referrer != user_id:
            referrer_id = potential_referrer

    initialize_user(user_id, message.from_user.username, message.from_user.first_name, referrer_id)
    
    if not is_user_subscribed(user_id):
        send_force_join_menu(user_id)
        return
        
    bot.send_message(user_id, "✅ Thanks for joining! Now you can use this bot.", reply_markup=get_main_keyboard())

@bot.message_handler(func=lambda m: True)
def process_menu_inputs(message):
    user_id = message.chat.id
    initialize_user(user_id, message.from_user.username, message.from_user.first_name)

    if not is_user_subscribed(user_id):
        send_force_join_menu(user_id)
        return

    text = message.text

    if text == '📥 Get Review Task':
        bot.send_message(user_id, "📥 **Google Maps Review Work**\n\nℹ️ For now there is no review task available. When the admin adds work we will notify you.", parse_mode="Markdown")

    elif text == '📥 Get Gmail Task':
        if user_db[user_id]["waiting_approval"]:
            bot.send_message(user_id, "⏳ **Verification Pending!**\nYou have already submitted proof for a task. Please wait until the Admin approves your work before requesting a new Gmail setup.")
            return

        if user_db[user_id]["active_task"]:
            bot.send_message(user_id, "⚠️ **Active Task Running!**\nYou already have a pending assignment details card. Please submit the screenshot proof for your current task first.")
            return

        markup = types.InlineKeyboardMarkup()
        markup.row(types.InlineKeyboardButton("Single Gmail Task", callback_data="task_select_single"))
        markup.row(types.InlineKeyboardButton("Bulk Gmail Task", callback_data="task_select_bulk"))
        
        task_menu = (
            "**The Current Available Tasks**\n\n"
            f"💰 Single Gmail Task: ₹{SINGLE_TASK_REWARD}\n"
            f"💰 Bulk Gmail Task: ₹{BULK_TASK_REWARD} per task"
        )
        bot.send_message(user_id, task_menu, parse_mode="Markdown", reply_markup=markup)

    elif text == '💳 Wallet':
        data = user_db[user_id]
        wallet_text = (
            f"Your wallet balance is: ₹{data['balance']}\n"
            "Complete more tasks to earn!"
        )
        bot.send_message(user_id, wallet_text)

    elif text == '👥 Invite & Earn':
        bot_info = bot.get_me()
        invite_link = f"https://t.me/{bot_info.username}?start={user_id}"
        refs = user_db[user_id]["referrals"]
        
        invite_card = (
            f"Share this link with your friends to earn ₹1 per referral!\n\n"
            f"Your Invite Link:\n{invite_link}\n\n"
            f"Total Referrals: {refs}\n\n"
            f"(Note: You will receive the ₹1 bonus after the invited user successfully completes their first task.)"
        )
        bot.send_message(user_id, invite_card, disable_web_page_preview=True)

    elif text == '💸 Withdraw':
        data = user_db[user_id]
        withdraw_text = (
            f"Available Balance: ₹{data['balance']}\n"
            f"(Total: ₹{data['balance']}, Pending: ₹{data['pending']})\n\n"
            f"How much would you like to withdraw? (Minimum ₹{MIN_WITHDRAWAL})"
        )
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add(types.KeyboardButton('❌ Cancel'))
        msg = bot.send_message(user_id, withdraw_text, reply_markup=markup)
        bot.register_next_step_handler(msg, process_withdrawal_amount)

    elif text == 'ℹ️ Help & Tutorial':
        help_text = (
            "ℹ️ **Help & Video Tutorial Center**\n\n"
            "Need guidance on handling standard workloads?\n"
            "Contact Support Line: @ROBINGMAILWORK for targeted manual instructions."
        )
        bot.send_message(user_id, help_text, parse_mode="Markdown")

    elif text == '🏆 Leaderboard':
        leaderboard_msg = (
            "🏆 **LEADERBOARD STATUS**\n\n"
            "👥 **Top Review Workers:**\n"
            "1. 👹DEEP 我👹 - 22 Reviews\n"
            "2. GODX - 10 Reviews\n"
            "3. Rushil - 10 Reviews\n"
            "4. ~ - 6 Reviews\n"
            "5. SANKAR - 6 Reviews\n"
            "6. Suhani - 6 Reviews\n"
            "7. Mahesh kumar - 5 Reviews\n"
            "8. Gaurav - 4 Reviews\n"
            "9. Ws fil crater - 4 Reviews\n"
            "10. SYEDSELLER ᵀᴹ - 4 Reviews\n\n"
            "📧 **Top Gmail Workers:**\n"
        )
        
        sorted_gmail = sorted(user_db.items(), key=lambda item: item[1]['gmail_count'], reverse=True)
        
        sample_gmailers = [
            ("AKASH RAWAT", 11), ("THE KIDD ‼️", 7), ("~", 6), 
            ("Satura Gojo", 6), ("N E X U S", 5), ("Rahul", 4), 
            ("YASH", 4), ("Yajur", 4), ("Krishna 🤝", 3), ("DOGGI", 3)
        ]
        
        idx = 1
        for uid, udata in sorted_gmail[:5]:
            if udata['gmail_count'] > 0:
                name = udata['first_name']
                leaderboard_msg += f"{idx}. 🧑‍💻 {name} - {udata['gmail_count']} Gmails\n"
                idx += 1
                
        for sname, scount in sample_gmailers:
            if idx <= 10:
                leaderboard_msg += f"{idx}. 🧑‍💻 {sname} - {scount} Gmails\n"
                idx += 1
                
        user_stats = user_db[user_id]
        leaderboard_msg += (
            f"\n📊 **Your Stats:**\n"
            f"Reviews: 0\n"
            f"Gmails: {user_stats['gmail_count']}"
        )
        bot.send_message(user_id, leaderboard_msg)

# --- 7. WORKFLOW INTERACTION HANDLING ---
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    user_id = call.message.chat.id
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass

    if call.data == "verify_channel_joins":
        if is_user_subscribed(user_id):
            try:
                bot.delete_message(user_id, call.message.message_id)
            except Exception:
                pass
            bot.send_message(user_id, "✅ Thanks for joining! Now you can use this bot.", reply_markup=get_main_keyboard())
        else:
            bot.send_message(user_id, "❌ You haven't joined the required channel yet! Please join and click verification again.")

    elif call.data in ["task_select_single", "task_select_bulk"]:
        # 🚨 CHECK 1: If master switch is turned off, show "No Task Available" right away
        if not GMAIL_TASKS_ACTIVE:
            no_task_text = (
                "📥 **Gmail Work Assignment**\n\n"
                "ℹ️ For now There is no Task Available.\n"
                "📢 When the admin adds we will notify.\n\n"
                "• Stay Tuned"
            )
            bot.send_message(user_id, no_task_text, parse_mode="Markdown")
            return

        # Find the next available account from pool
        assigned_task = None
        for task in GMAIL_TASK_POOL:
            if not task["completed"] and task["assigned_to"] is None:
                assigned_task = task
                break

        # 🚨 CHECK 2: If pool is empty out of accounts, show the same alert
        if not assigned_task:
            no_task_text = (
                "📥 **Gmail Work Assignment**\n\n"
                "ℹ️ For now There is no Task Available.\n"
                "📢 When the admin adds we will notify.\n\n"
                "• Stay Tuned"
            )
            bot.send_message(user_id, no_task_text, parse_mode="Markdown")
            return

        assigned_task["assigned_to"] = user_id
        task_type = "Single" if "single" in call.data else "Bulk"
        reward = SINGLE_TASK_REWARD if task_type == "Single" else BULK_TASK_REWARD
        
        user_db[user_id]["active_task"] = {
            "task_id": assigned_task["id"],
            "type": task_type,
            "reward": reward,
            "email": assigned_task["email"],
            "pass": assigned_task["pass"]
        }
        
        job_card = (
            f"✉️ **JOB FILE: {SPECIFIC_TASK_TITLE} ({task_type})**\n\n"
            f"💰 **Reward:** ₹{reward}\n"
            f"🔗 **Link:** {SPECIFIC_TASK_LINK}\n\n"
            f"ℹ️ **Target Creation Setup:**\n"
            f"Details - {assigned_task['email']}\n"
            f"Pass- {assigned_task['pass']}\n\n"
            f"📋 **Instructions:**\n{SPECIFIC_TASK_INSTRUCTIONS}\n\n"
            "⚠️ Send your screenshot completion proof directly to this chat window now."
        )
        bot.send_message(user_id, job_card, parse_mode="Markdown", disable_web_page_preview=True)

    elif call.data.startswith("approve_"):
        _, target_id, payout_str, pool_task_id = call.data.split("_")
        target_id = int(target_id)
        payout = float(payout_str)
        
        if target_id in user_db:
            user_db[target_id]["balance"] += payout
            if user_db[target_id]["pending"] >= payout:
                user_db[target_id]["pending"] -= payout
            user_db[target_id]["gmail_count"] += 1
            user_db[target_id]["waiting_approval"] = False 
            
            for t in GMAIL_TASK_POOL:
                if t["id"] == pool_task_id:
                    t["completed"] = True
                    break
            
            ref_id = user_db[target_id]["referrer_id"]
            if ref_id and ref_id in user_db and user_db[target_id]["gmail_count"] == 1:
                user_db[ref_id]["balance"] += 1.0
                user_db[ref_id]["referrals"] += 1
                try:
                    bot.send_message(ref_id, f"🎉 You received ₹1 referral reward because a user you invited completed their first task!")
                except Exception:
                    pass

            bot.edit_message_caption(f"✅ **Approved!** ₹{payout} added to User Wallet ID: `{target_id}`", chat_id=ADMIN_ID, message_id=call.message.message_id)
            try:
                bot.send_message(target_id, f"🎉 **Task Approved!** ₹{payout} has been credited to your balance.\n\n📥 You can now click **'📥 Get Gmail Task'** to claim your next assignment!")
            except Exception:
                pass

    elif call.data.startswith("reject_"):
        _, target_id, pool_task_id = call.data.split("_")
        target_id = int(target_id)
        
        if target_id in user_db:
            user_db[target_id]["waiting_approval"] = False 
            
            for t in GMAIL_TASK_POOL:
                if t["id"] == pool_task_id:
                    t["assigned_to"] = None
                    break
                    
            bot.edit_message_caption("❌ **Proof Rejected.**", chat_id=ADMIN_ID, message_id=call.message.message_id)
            try:
                bot.send_message(target_id, "❌ Your screenshot proof was rejected by the admin. The task has been put back into the pool.")
            except Exception:
                pass

# --- 8. PROOF PROCESSING LOGIC ---
@bot.message_handler(content_types=['photo'])
def audit_incoming_proof(message):
    user_id = message.chat.id
    if not is_user_subscribed(user_id):
        send_force_join_menu(user_id)
        return

    if user_id not in user_db or not user_db[user_id]["active_task"]:
        bot.send_message(user_id, "❌ Click '📥 Get Gmail Task' to view your job before sending proof.")
        return

    task_info = user_db[user_id]["active_task"]
    reward = task_info["reward"]
    task_type = task_info["type"]
    pool_task_id = task_info["task_id"]
    
    user_db[user_id]["pending"] += reward
    user_db[user_id]["waiting_approval"] = True  
    user_db[user_id]["active_task"] = None       
    
    bot.reply_to(message, "⏳ **Proof received!** Sent to Admin validation queue.", reply_markup=get_main_keyboard())

    photo_token = message.photo[-1].file_id
    admin_markup = types.InlineKeyboardMarkup()
    admin_markup.add(
        types.InlineKeyboardButton("✅ Approve & Pay", callback_data=f"approve_{user_id}_{reward}_{pool_task_id}"),
        types.InlineKeyboardButton("❌ Reject Work", callback_data=f"reject_{user_id}_{pool_task_id}")
    )

    admin_view_card = (
        "🧐 **NEW TASK PROOF SUBMITTED**\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 **Name:** {user_db[user_id]['first_name']}\n"
        f"🌐 **Username:** {user_db[user_id]['username']}\n"
        f"🆔 **User ID:** `{user_id}`\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"🏷 **Task Type:** {task_type} Gmail\n"
        f"📧 **Assigned Email:** `{task_info['email']}`\n"
        f"💰 **Reward Amount:** ₹{reward}\n"
    )
    bot.send_photo(ADMIN_ID, photo_token, caption=admin_view_card, parse_mode="Markdown", reply_markup=admin_markup)

# --- 9. WITHDRAWAL PIPELINE LOGIC ---
def process_withdrawal_amount(message):
    user_id = message.chat.id
    if message.text == '❌ Cancel':
        bot.send_message(user_id, "Action cancelled.", reply_markup=get_main_keyboard())
        return

    try:
        amount = float(message.text)
        if amount < MIN_WITHDRAWAL:
            bot.send_message(user_id, f"❌ Minimum withdrawal is ₹{MIN_WITHDRAWAL}.", reply_markup=get_main_keyboard())
            return
        if amount > user_db[user_id]["balance"]:
            bot.send_message(user_id, "❌ Insufficient balance in your wallet account.", reply_markup=get_main_keyboard())
            return
            
        msg = bot.send_message(user_id, "Enter your UPI ID for payout:")
        bot.register_next_step_handler(msg, lambda m: process_withdrawal_upi(m, amount))
    except ValueError:
        bot.send_message(user_id, "❌ Invalid value input. Cancelled.", reply_markup=get_main_keyboard())

def process_withdrawal_upi(message, amount):
    user_id = message.chat.id
    upi_string = message.text
    
    if upi_string == '❌ Cancel':
        bot.send_message(user_id, "Action cancelled.", reply_markup=get_main_keyboard())
        return
        
    if "@" not in upi_string:
        bot.send_message(user_id, "❌ Invalid UPI Address layout formatting.", reply_markup=get_main_keyboard())
        return

    user_db[user_id]["balance"] -= amount
    bot.send_message(user_id, "⏳ Payout sheet sent to admin approval. Please wait.", reply_markup=get_main_keyboard())

    alert_string = (
        "🚨 **WITHDRAWAL REQUISITION** 🚨\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 **Username:** {user_db[user_id]['username']}\n"
        f"🆔 **User UID:** `{user_id}`\n"
        f"💳 **Amount:** ₹{amount}\n"
        f"📌 **UPI ID:** `{upi_string}`"
    )
    bot.send_message(ADMIN_ID, alert_string, parse_mode="Markdown")

# --- 10. SYSTEM EXECUTION ---
if __name__ == "__main__":
    web_engine = threading.Thread(target=run_web_server)
    web_engine.daemon = True
    web_engine.start()
    
    print("Task Engine Core Online...")
    bot.infinity_polling()
