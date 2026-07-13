import telebot
from telebot import types
import threading
from flask import Flask
import os

# --- 1. RENDER 24/7 KEEP-ALIVE SERVER ---
app = Flask('')

@app.route('/')
def home():
    return "Themed Mail Bot is running 24/7!"

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- 2. BOT CONFIGURATION ---
API_TOKEN = '8688748786:AAGK1QI_5vFdiDmR8V-uPRKmCZeTvQ5wwjU'  # 👈 यहाँ अपना Bot Token डालें
ADMIN_ID = 6535711381              # 👈 यहाँ अपनी असली Telegram ID डालें

bot = telebot.TeleBot(API_TOKEN)

# In-memory database
user_data = {}

active_tasks = {
    "mail_1": {
        "title": "Gmail Creation Assignment",
        "reward": 10,
        "link": "https://accounts.google.com/signup",
        "instructions": "Create a fresh Gmail account. Take a clear screenshot of the final dashboard showing the new email ID."
    }
}

MIN_WITHDRAWAL = 30  
admin_creating_task = {}

# --- THEMED BOTTOM KEYBOARD ---
def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    markup.row(types.KeyboardButton('🧑‍💻 Account'), types.KeyboardButton('✉️ Tasks'))
    markup.row(types.KeyboardButton('💸 Withdraw'))
    return markup

@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.chat.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    
    if user_id not in user_data:
        user_data[user_id] = {
            "balance": 0, 
            "active_task_id": None, 
            "username": f"@{username}" if username else None,
            "first_name": first_name
        }
    else:
        user_data[user_id]["username"] = f"@{username}" if username else None
        user_data[user_id]["first_name"] = first_name
    
    welcome_text = "Welcome to Shorya Mail Task Bot! Select an option below to begin."
    if user_id == ADMIN_ID:
        welcome_text += (
            "\n\n🛠 **Admin Controls Active:**\n"
            "• `/ROBINmailTaskadd` - नया टास्क ऐड करें 🌟\n"
            "• `/setbalance @username [amount]` - यूजरनेम से पैसे ऐड करें\n"
            "• `/setbalance [userid] [amount]` - यूजर आईडी से पैसे ऐड करें"
        )
        
    bot.send_message(user_id, welcome_text, reply_markup=get_main_keyboard())

# --- ADMIN COMMAND: SET BALANCE VIA USERNAME OR USERID ---
@bot.message_handler(commands=['setbalance'])
def set_user_balance(message):
    if message.chat.id != ADMIN_ID:
        return
    try:
        parts = message.text.split()
        target_input = parts[1]  
        amount = int(parts[2])
        
        target_uid = None
        
        if target_input.startswith('@'):
            for uid, data in user_data.items():
                if data.get("username") and data["username"].lower() == target_input.lower():
                    target_uid = uid
                    break
            if not target_uid:
                bot.send_message(ADMIN_ID, f"❌ User with username {target_input} not found in bot database yet. (He must type /start first)")
                return
        else:
            target_uid = int(target_input)
            
        if target_uid not in user_data:
            user_data[target_uid] = {"balance": 0, "active_task_id": None, "username": None, "first_name": "Worker"}
            
        user_data[target_uid]["balance"] = amount
        bot.send_message(ADMIN_ID, f"✅ Successfully updated balance of {target_input} to **₹{amount}**.")
        bot.send_message(target_uid, f"💰 Admin updated your wallet balance! New balance: **₹{amount}**.")
    except Exception:
        bot.send_message(ADMIN_ID, "❌ Format: `/setbalance @username 50` OR `/setbalance 123456789 50`")

# --- CUSTOM ADMIN COMMAND: ADD LIVE EMAIL TASKS ---
@bot.message_handler(commands=['ROBINmailTaskadd'])
def add_mail_task_start(message):
    if message.chat.id != ADMIN_ID:
        return
    msg = bot.send_message(ADMIN_ID, "📝 Enter task title (e.g., Yahoo Mail Creation):")
    bot.register_next_step_handler(msg, process_title)

def process_title(message):
    new_id = f"mail_{len(active_tasks) + 1}"
    admin_creating_task[ADMIN_ID] = {"id": new_id, "title": message.text}
    msg = bot.send_message(ADMIN_ID, "💰 Enter Reward Amount in ₹:")
    bot.register_next_step_handler(msg, process_reward)

def process_reward(message):
    try:
        reward = int(message.text)
    except ValueError:
        bot.send_message(ADMIN_ID, "❌ Cancelled. Numbers only.")
        return
    admin_creating_task[ADMIN_ID]["reward"] = reward
    msg = bot.send_message(ADMIN_ID, "🔗 Paste registration link:")
    bot.register_next_step_handler(msg, process_link)

def process_link(message):
    admin_creating_task[ADMIN_ID]["link"] = message.text
    msg = bot.send_message(ADMIN_ID, "📋 Paste task instructions:")
    bot.register_next_step_handler(msg, process_finish)

def process_finish(message):
    instructions = message.text
    t_info = admin_creating_task[ADMIN_ID]
    active_tasks[t_info["id"]] = {
        "title": t_info['title'],
        "reward": t_info['reward'],
        "link": t_info['link'],
        "instructions": instructions
    }
    bot.send_message(ADMIN_ID, f"✅ Task Added Live! ID: `{t_info['id']}`")
    del admin_creating_task[ADMIN_ID]

# --- USER REPLY MENU CONTROLLERS ---
@bot.message_handler(func=lambda message: True)
def menu_controller(message):
    user_id = message.chat.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    
    if user_id not in user_data:
        user_data[user_id] = {"balance": 0, "active_task_id": None, "username": f"@{username}" if username else None, "first_name": first_name}

    if message.text == '🧑‍💻 Account':
        bal = user_data[user_id]["balance"]
        account_msg = (
            "👑 **ACCOUNT INFO** ✅\n\n"
            "🆔 **UID :** `{}`\n\n"
            "💰 **BALANCE : {} ₹** ✅"
        ).format(user_id, bal)
        bot.send_message(user_id, account_msg, parse_mode="Markdown")

    elif message.text == '✉️ Tasks':
        if not active_tasks:
            bot.send_message(user_id, "❌ **NO TASKS AVAILABLE** ❌", parse_mode="Markdown")
            return
        
        inline_markup = types.InlineKeyboardMarkup()
        for t_id, t_info in active_tasks.items():
            btn = types.InlineKeyboardButton(f"✉️ {t_info['title']} (₹{t_info['reward']})", callback_data=f"job_{t_id}")
            inline_markup.add(btn)
        bot.send_message(user_id, "📋 **Available Email Jobs:**", reply_markup=inline_markup, parse_mode="Markdown")

    elif message.text == '💸 Withdraw':
        bal = user_data[user_id]["balance"]
        if bal < MIN_WITHDRAWAL:
            bot.send_message(user_id, f"❌ **MINIMUM WITHDRAWAL IS {MIN_WITHDRAWAL}** ❌", parse_mode="Markdown")
        else:
            msg = bot.send_message(user_id, f"✅ You have ₹{bal}. Enter your UPI ID for payout:")
            bot.register_next_step_handler(msg, process_payout_request)

# --- CALLBACK ROUTER SYSTEM ---
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    user_id = call.message.chat.id
    data_parts = call.data.split("_")
    action = data_parts[0]

    if action == "job":
        task_id = data_parts[1]
        if task_id not in active_tasks:
            bot.answer_callback_query(call.id, "❌ Task Expired.")
            return
            
        user_data[user_id]["active_task_id"] = task_id
        t_info = active_tasks[task_id]
        
        job_card = (
            f"✉️ **JOB FILE: {t_info['title']}**\n\n"
            f"🔗 **Link:** {t_info['link']}\n\n"
            f"📋 **Instructions:**\n{t_info['instructions']}\n\n"
            "⚠️ Completion proof के लिए स्क्रीनशॉट सीधे यहाँ सेंड करें।"
        )
        bot.edit_message_text(job_card, chat_id=user_id, message_id=call.message.message_id, parse_mode="Markdown", disable_web_page_preview=True)

    elif action == "verifymail":
        target = int(data_parts[1])
        payout = int(data_parts[2])
        if target in user_data:
            user_data[target]["balance"] += payout
        bot.edit_message_caption(f"✅ **Approved!** ₹{payout} added to User ID: `{target}` balance.", chat_id=ADMIN_ID, message_id=call.message.message_id)
        bot.send_message(target, f"🎉 **Task Approved!** ₹{payout} has been credited to your balance.")

    elif action == "rejectmail":
        target = int(data_parts[1])
        bot.edit_message_caption("❌ **Proof Rejected.**", chat_id=ADMIN_ID, message_id=call.message.message_id)
        bot.send_message(target, "❌ Your screenshot proof was rejected by the admin.")

    elif action == "payok":
        target = int(data_parts[1])
        amt = int(data_parts[2])
        if target in user_data and user_data[target]["balance"] >= amt:
            user_data[target]["balance"] -= amt
        bot.edit_message_text(f"✅ **Succeeded!** Deducted ₹{amt} from user wallet.", chat_id=ADMIN_ID, message_id=call.message.message_id)
        bot.send_message(target, f"🎉 Your withdrawal request for **₹{amt}** was approved and sent via UPI!")

    elif action == "payfail":
        target = int(data_parts[1])
        bot.edit_message_text("❌ **Withdrawal Request Cancelled/Rejected.**", chat_id=ADMIN_ID, message_id=call.message.message_id)
        bot.send_message(target, "❌ Your withdrawal request was rejected by the admin.")

# --- HANDLES ATTACHED SCREENSHOT PROOF ---
@bot.message_handler(content_types=['photo'])
def audit_incoming_proof(message):
    user_id = message.chat.id
    if user_id not in user_data or not user_data[user_id]["active_task_id"]:
        bot.send_message(user_id, "❌ Click '✉️ Tasks' and select a job before sending proof.")
        return

    task_id = user_data[user_id]["active_task_id"]
    t_info = active_tasks[task_id]
    reward_amt = t_info["reward"]
    
    username = f"@{message.from_user.username}" if message.from_user.username else "No Username"
    first_name = message.from_user.first_name
    
    user_data[user_id]["active_task_id"] = None  
    bot.reply_to(message, "⏳ **Proof received!** Sent to Admin validation queue.")

    photo_token = message.photo[-1].file_id
    admin_markup = types.InlineKeyboardMarkup()
    admin_markup.add(types.InlineKeyboardButton("✅ Approve & Pay", callback_data=f"verifymail_{user_id}_{reward_amt}"),
                     types.InlineKeyboardButton("❌ Reject Work", callback_data=f"rejectmail_{user_id}_{reward_amt}"))

    admin_view_card = (
        "🧐 **NEW SCREENSHOT PROOF SUBMITTED**\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 **Name:** {first_name}\n"
        f"🌐 **Username:** {username}\n"
        f"🆔 **User ID:** `{user_id}`\n"
        f"🔗 **Profile Link:** [Click Here to Chat](tg://user?id={user_id})\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"🏷 **Task:** {t_info['title']}\n"
        f"💰 **Reward Amount:** ₹{reward_amt}\n\n"
        "👇 Approve करने के लिए नीचे बटन दबाएं, पेमेंट अपने आप ऐड हो जायेगा।"
    )
    bot.send_photo(ADMIN_ID, photo_token, caption=admin_view_card, parse_mode="Markdown", reply_markup=admin_markup)

# --- PROCESS UPI WITHDRAWAL EXTRADITION ---
def process_payout_request(message):
    user_id = message.chat.id
    upi_string = message.text
    wallet_bal = user_data[user_id]["balance"]
    username = user_data[user_id].get("username", "No Username")
    
    if "@" not in upi_string:
        bot.send_message(user_id, "❌ Canceled. Invalid UPI ID.")
        return

    bot.send_message(user_id, "⏳ Payout sheet sent to admin approval. Please wait.")

    admin_payout_panel = types.InlineKeyboardMarkup()
    admin_payout_panel.add(types.InlineKeyboardButton("✅ Confirm Sent", callback_data=f"payok_{user_id}_{wallet_bal}"),
                           types.InlineKeyboardButton("❌ Reject/Cancel", callback_data=f"payfail_{user_id}_{wallet_bal}"))

    alert_string = (
        "🚨 **WITHDRAWAL REQUISITION** 🚨\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 **Username:** {username}\n"
        f"🆔 **User UID:** `{user_id}`\n"
        f"💳 **Amount:** ₹{wallet_bal}\n"
        f"📌 **UPI ID:** `{upi_string}`"
    )
    bot.send_message(ADMIN_ID, alert_string, parse_mode="Markdown", reply_markup=admin_payout_panel)

# --- DUAL EXECUTION ENGINE SYSTEM ---
if __name__ == "__main__":
    web_engine = threading.Thread(target=run_web_server)
    web_engine.daemon = True
    web_engine.start()
    
    print("Themed Bot with Username & Custom Command is listening...")
    bot.infinity_polling()    try:
        reward = int(message.text)
    except ValueError:
        bot.send_message(ADMIN_ID, "❌ Invalid number. Task setup canceled. Try /addtask again.")
        return
        
    admin_creating_task[ADMIN_ID]["reward"] = reward
    msg = bot.send_message(ADMIN_ID, "🔗 Step 3: Paste the **Link** for this task (e.g., Google Map URL or website link):")
    bot.register_next_step_handler(msg, process_admin_task_link)

def process_admin_task_link(message):
    link = message.text
    admin_creating_task[ADMIN_ID]["link"] = link
    msg = bot.send_message(ADMIN_ID, "📝 Step 4: Write specific **Instructions** for your workers:")
    bot.register_next_step_handler(msg, process_admin_task_finish)

def process_admin_task_finish(message):
    instructions = message.text
    task_info = admin_creating_task[ADMIN_ID]
    
    # Save to dynamic dictionary database
    active_tasks[task_info["id"]] = {
        "title": task_info["title"],
        "reward": task_info["reward"],
        "link": task_info["link"],
        "instructions": instructions
    }
    
    bot.send_message(ADMIN_ID, f"✅ **Task successfully added live!**\n\n📌 **ID:** {task_info['id']}\n📋 **Title:** {task_info['title']}\n💰 **Reward:** ₹{task_info['reward']}")
    del admin_creating_task[ADMIN_ID]

# --- HANDLE TEXT BUTTONS ---
@bot.message_handler(func=lambda message: True)
def handle_menu(message):
    user_id = message.chat.id
    if user_id not in user_data:
        user_data[user_id] = {"balance": 0, "active_task_id": None}

    if message.text == '📋 View Tasks':
        if not active_tasks:
            bot.send_message(user_id, "😔 No active tasks available right now. Check back later!")
            return
            
        # Dynamically build inline keyboard buttons based on active_tasks list
        inline_markup = types.InlineKeyboardMarkup()
        for t_id, t_info in active_tasks.items():
            btn = types.InlineKeyboardButton(f"{t_info['title']} (₹{t_info['reward']})", callback_data=f"select_{t_id}")
            inline_markup.add(btn)
        
        bot.send_message(user_id, "📌 **Select an available task to perform:**", parse_mode="Markdown", reply_markup=inline_markup)

    elif message.text == '💰 Check Balance':
        bal = user_data[user_id]["balance"]
        bot.send_message(user_id, f"💳 Your Current Balance: **₹{bal}**", parse_mode="Markdown")

    elif message.text == '💸 Withdraw Money':
        bal = user_data[user_id]["balance"]
        if bal < MIN_WITHDRAWAL:
            bot.send_message(user_id, f"❌ Minimum withdrawal is ₹{MIN_WITHDRAWAL}. You need ₹{MIN_WITHDRAWAL - bal} more.")
        else:
            msg = bot.send_message(user_id, f"✅ You have ₹{bal}. Please type your UPI ID to request payout:")
            bot.register_next_step_handler(msg, process_withdrawal_request)

# --- HANDLE INLINE SELECTIONS & ADMIN ACTIONS ---
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    user_id = call.message.chat.id
    data_parts = call.data.split("_")
    action = data_parts[0]

    # --- User Selects Dynamic Task ---
    if action == "select":
        task_id = data_parts[1]
        
        if task_id not in active_tasks:
            bot.answer_callback_query(call.id, "❌ This task is no longer available.")
            return
            
        user_data[user_id]["active_task_id"] = task_id
        task_info = active_tasks[task_id]
        
        instructions = (
            f"📝 **Task Activated: {task_info['title']}**\n\n"
            f"🔗 **Task Link:** {task_info['link']}\n\n"
            f"**Instructions:**\n{task_info['instructions']}\n\n"
            f"⚠️ After finishing, take a screenshot and **send the photo directly here** as proof."
        )
        bot.edit_message_text(instructions, chat_id=user_id, message_id=call.message.message_id, parse_mode="Markdown", disable_web_page_preview=True)

    # --- Admin Work Approval Panel ---
    elif action == "taskapp":
        target_user = int(data_parts[1])
        reward = int(data_parts[2])
        if target_user in user_data:
            user_data[target_user]["balance"] += reward
        bot.edit_message_caption(f"✅ **Proof Approved!** Added ₹{reward} to User `{target_user}`.", chat_id=ADMIN_ID, message_id=call.message.message_id)
        bot.send_message(target_user, f"🎉 **Task Approved!** ₹{reward} has been added to your balance.")

    elif action == "taskrej":
        target_user = int(data_parts[1])
        bot.edit_message_caption(f"❌ **Proof Rejected!** Denied user `{target_user}`.", chat_id=ADMIN_ID, message_id=call.message.message_id)
        bot.send_message(target_user, "❌ Your proof screenshot was rejected by the admin. Please redo the job accurately.")

    # --- Admin Withdrawal Panel ---
    elif action == "wdapp":
        target_user = int(data_parts[1])
        amount = int(data_parts[2])
        if target_user in user_data and user_data[target_user]["balance"] >= amount:
            user_data[target_user]["balance"] -= amount
        bot.edit_message_text(f"✅ **Withdrawal Settled!** Paid ₹{amount} to User `{target_user}`.", chat_id=ADMIN_ID, message_id=call.message.message_id)
        bot.send_message(target_user, f"🎉 **Withdrawal Approved!** ₹{amount} has been successfully sent.")

    elif action == "wdrej":
        target_user = int(data_parts[1])
        bot.edit_message_text(f"❌ **Withdrawal Rejected** for User `{target_user}`.", chat_id=ADMIN_ID, message_id=call.message.message_id)
        bot.send_message(target_user, "❌ Your withdrawal request was rejected by the admin.")

# --- HANDLES SCREENSHOT PROOF SUBMISSION ---
@bot.message_handler(content_types=['photo'])
def handle_screenshot_proof(message):
    user_id = message.chat.id
    
    if user_id not in user_data or not user_data[user_id]["active_task_id"]:
        bot.send_message(user_id, "❌ You don't have an active task right now.")
        return

    task_id = user_data[user_id]["active_task_id"]
    if task_id not in active_tasks:
        bot.send_message(user_id, "❌ Sorry, this task was deleted by admin.")
        user_data[user_id]["active_task_id"] = None
        return

    task_info = active_tasks[task_id]
    reward = task_info["reward"]
    
    # Reset user's active status
    user_data[user_id]["active_task_id"] = None
    
    bot.reply_to(message, "⏳ **Proof received!** Sent to Admin verification panel. Please wait.")

    photo_id = message.photo[-1].file_id
    admin_markup = types.InlineKeyboardMarkup()
    approve_btn = types.InlineKeyboardButton("✅ Approve Work", callback_data=f"taskapp_{user_id}_{reward}")
    reject_btn = types.InlineKeyboardButton("❌ Reject Work", callback_data=f"taskrej_{user_id}_{reward}")
    admin_markup.add(approve_btn, reject_btn)

    caption_text = (
        "🧐 **DYNAMIC TASK SUBMISSION** 🧐\n\n"
        f"👤 **User ID:** `{user_id}`\n"
        f"📋 **Task:** {task_info['title']}\n"
        f"💰 **Reward:** ₹{reward}\n\n"
        "Verify the visual proof below:"
    )
    bot.send_photo(ADMIN_ID, photo_id, caption=caption_text, parse_mode="Markdown", reply_markup=admin_markup)

# --- PROCESS WITHDRAWAL REQUEST ---
def process_withdrawal_request(message):
    user_id = message.chat.id
    upi_id = message.text
    bal = user_data[user_id]["balance"]
    
    if "@" not in upi_id:
        bot.send_message(user_id, "❌ Invalid UPI ID. Canceled.")
        return

    bot.send_message(user_id, "⏳ Payout request submitted to admin approval.")

    admin_markup = types.InlineKeyboardMarkup()
    approve_btn = types.InlineKeyboardButton("✅ Settle Payout", callback_data=f"wdapp_{user_id}_{bal}")
    reject_btn = types.InlineKeyboardButton("❌ Reject", callback_data=f"wdrej_{user_id}_{bal}")
    admin_markup.add(approve_btn, reject_btn)

    admin_alert = (
        "🚨 **WITHDRAWAL REQUEST** 🚨\n\n"
        f"👤 **User ID:** `{user_id}`\n"
        f"💰 **Amount:** ₹{bal}\n"
        f"💳 **UPI ID:** `{upi_id}`"
    )
    bot.send_message(ADMIN_ID, admin_alert, parse_mode="Markdown", reply_markup=admin_markup)

# --- START THE BOT ---
print("Dynamic Task Bot is running successfully...")
bot.infinity_polling()
