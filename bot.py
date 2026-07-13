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
API_TOKEN = '8688748786:AAGK1QI_5vFdiDmR8V-uPRKmCZeTvQ5wwjU'  # 👈 यहाँ अपना असली Bot Token डालें
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
    
    print("Clean Bot is running successfully...")
    bot.infinity_polling()
