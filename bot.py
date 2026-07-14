import telebot
from telebot import types
import threading
from flask import Flask
import os

# --- 1. RENDER 24/7 KEEP-ALIVE SERVER ---
app = Flask('')

@app.route('/')
def home():
    return "ROBINxMAIL TASK Bot is running 24/7!"

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- 2. BOT CONFIGURATION ---
API_TOKEN = '8688748786:AAGK1QI_5vFdiDmR8V-uPRKmCZeTvQ5wwjU'  # 👈 Put your real Bot Token here
ADMIN_ID = 6535711381              # 👈 Put your real Telegram Admin ID here

bot = telebot.TeleBot(API_TOKEN)

# --- 3. HARDCODED GOAL EMAIL CONFIGURATIONS ---
SPECIFIC_TASK_TITLE = "Gmail Creation Assignment"
SPECIFIC_TASK_REWARD = 10
SPECIFIC_TASK_LINK = "https://accounts.google.com/signup"
SPECIFIC_TASK_DETAILS = (
    "Details - fabricoespeche135@gmail.com\n"
    "Pass- ROBINXMAIL#112233"
)
SPECIFIC_TASK_INSTRUCTIONS = (
    "Create a fresh Gmail account using the exact structural details shown above. "
    "Once done, take a clear screenshot of your finalized Google account dashboard "
    "showing the created email ID and submit it directly here."
)

REQUIRED_CHANNELS = ["@ROBINGMAILWORK", ""]
# In-memory database for tracking balances
user_data = {}
MIN_WITHDRAWAL = 30  

# --- THEMED BOTTOM KEYBOARD ---
def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    markup.row(types.KeyboardButton('🧑‍💻 Account'), types.KeyboardButton('✉️ Tasks'))
    markup.row(types.KeyboardButton('💸 Withdraw'))
    return markup

# --- UTILITY: CHECK MEMBERSHIP STATUS ---
def is_user_subscribed(user_id):
    """
    Checks if the user is a member of all channels in REQUIRED_CHANNELS.
    Note: The bot MUST be an Admin in your channels for this check to work properly.
    """
    if user_id == ADMIN_ID:
        return True  # Bypass subscription check for the Admin
        
    for channel in REQUIRED_CHANNELS:
        clean_channel = channel.strip()
        if not clean_channel:
            continue
        try:
            member = bot.get_chat_member(clean_channel, user_id)
            if member.status in ['left', 'kicked']:
                return False
        except Exception:
            # If bot isn't admin yet or channel is invalid, we fallback to False to be safe
            return False
    return True

# --- UTILITY: SEND FORCE JOIN INTERFACE ---
def send_force_join_menu(chat_id, text_prefix="🚨 Join our Telegram Channels first to use this bot!"):
    markup = types.InlineKeyboardMarkup()
    
    # Dynamically generate join buttons for each channel in configuration
    for channel in REQUIRED_CHANNELS:
        username_clean = channel.replace("@", "").strip()
        btn_label = f"Join {channel}"
        btn_url = f"https://t.me/{username_clean}"
        markup.add(types.InlineKeyboardButton(btn_label, url=btn_url))
        
    # Add confirmation check verification button
    markup.add(types.InlineKeyboardButton("✅ I have joined", callback_data="verify_channel_joins"))
    bot.send_message(chat_id, text_prefix, reply_markup=markup)

# --- COMMAND: START ---
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.chat.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    
    # Save user info
    if user_id not in user_data:
        user_data[user_id] = {
            "balance": 0, 
            "active_task_status": False, 
            "username": f"@{username}" if username else None,
            "first_name": first_name
        }
    else:
        user_data[user_id]["username"] = f"@{username}" if username else None
        user_data[user_id]["first_name"] = first_name

    # Check Force Join Membership
    if not is_user_subscribed(user_id):
        send_force_join_menu(user_id)
        return
    
    welcome_text = "Welcome to ROBINxMAIL TASK Bot! Select an option below to begin."
    if user_id == ADMIN_ID:
        welcome_text += (
            "\n\n🛠 **Admin Controls Active:**\n"
            "• `/setchannels @chan1 @chan2` - Set Dynamic Join Channels\n"
            "• `/setbalance @username [amount]` - Set Balance by Username\n"
            "• `/setbalance [userid] [amount]` - Set Balance by User ID"
        )
        
    bot.send_message(user_id, welcome_text, reply_markup=get_main_keyboard())

# --- ADMIN COMMAND: DYNAMICALLY UPDATE REQUIRED CHANNELS ---
@bot.message_handler(commands=['setchannels'])
def update_bot_channels(message):
    global REQUIRED_CHANNELS
    if message.chat.id != ADMIN_ID:
        return
    
    try:
        parts = message.text.split()
        if len(parts) < 2:
            raise ValueError
            
        new_channels = []
        for p in parts[1:]:
            if p.startswith("@"):
                new_channels.append(p)
            else:
                new_channels.append(f"@{p}")
                
        REQUIRED_CHANNELS = new_channels
        bot.send_message(ADMIN_ID, f"✅ **Channels updated successfully!**\nUsers must now join:\n" + "\n".join(REQUIRED_CHANNELS))
    except Exception:
        bot.send_message(ADMIN_ID, "❌ **Usage:** `/setchannels @chan1 @chan2 @chan3` (You can add as many as you want!)")

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
            user_data[target_uid] = {"balance": 0, "active_task_status": False, "username": None, "first_name": "Worker"}
            
        user_data[target_uid]["balance"] = amount
        bot.send_message(ADMIN_ID, f"✅ Successfully updated balance of {target_input} to **₹{amount}**.")
        bot.send_message(target_uid, f"💰 Admin updated your wallet balance! New balance: **₹{amount}**.")
    except Exception:
        bot.send_message(ADMIN_ID, "❌ Format: `/setbalance @username 50` OR `/setbalance 123456789 50`")

# --- USER REPLY MENU CONTROLLERS ---
@bot.message_handler(func=lambda message: True)
def menu_controller(message):
    user_id = message.chat.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    
    # Initialize profile
    if user_id not in user_data:
        user_data[user_id] = {"balance": 0, "active_task_status": False, "username": f"@{username}" if username else None, "first_name": first_name}

    # Intercept with Force Join check
    if not is_user_subscribed(user_id):
        send_force_join_menu(user_id)
        return

    if message.text == '🧑‍💻 Account':
        bal = user_data[user_id]["balance"]
        account_msg = (
            "👑 **ACCOUNT INFO** ✅\n\n"
            "🆔 **UID :** `{}`\n\n"
            "💰 **BALANCE : {} ₹** ✅"
        ).format(user_id, bal)
        bot.send_message(user_id, account_msg, parse_mode="Markdown")

    elif message.text == '✉️ Tasks':
        user_data[user_id]["active_task_status"] = True
        
        job_card = (
            f"✉️ **JOB FILE: {SPECIFIC_TASK_TITLE}**\n\n"
            f"💰 **Reward:** ₹{SPECIFIC_TASK_REWARD}\n"
            f"🔗 **Link:** {SPECIFIC_TASK_LINK}\n\n"
            f"ℹ️ **Target Creation Setup:**\n"
            f"`{SPECIFIC_TASK_DETAILS}`\n\n"
            f"📋 **Instructions:**\n{SPECIFIC_TASK_INSTRUCTIONS}\n\n"
            "⚠️ Send your screenshot completion proof directly to this chat window now."
        )
        bot.send_message(user_id, job_card, parse_mode="Markdown", disable_web_page_preview=True)

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

    # Handle membership verification confirmation button click
    if action == "verify_channel_joins":
        if is_user_subscribed(user_id):
            bot.delete_message(chat_id=user_id, message_id=call.message.message_id)
            bot.answer_callback_query(call.id, "🎉 Success! Bot unlocked.", show_alert=True)
            
            # Show Welcome UI
            welcome_text = "Welcome to ROBINxMAIL TASK Bot! Select an option below to begin."
            bot.send_message(user_id, welcome_text, reply_markup=get_main_keyboard())
        else:
            bot.answer_callback_query(call.id, "❌ You haven't joined all required channels yet!", show_alert=True)
        return

    if action == "verifymail":
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
    
    # Intercept proof submissions if not joined
    if not is_user_subscribed(user_id):
        send_force_join_menu(user_id)
        return

    if user_id not in user_data or not user_data[user_id]["active_task_status"]:
        bot.send_message(user_id, "❌ Click '✉️ Tasks' to view your job before sending proof.")
        return
    
    username = f"@{message.from_user.username}" if message.from_user.username else "No Username"
    first_name = message.from_user.first_name
    
    user_data[user_id]["active_task_status"] = False  
    bot.reply_to(message, "⏳ **Proof received!** Sent to Admin validation queue.")

    photo_token = message.photo[-1].file_id
    admin_markup = types.InlineKeyboardMarkup()
    admin_markup.add(types.InlineKeyboardButton("✅ Approve & Pay", callback_data=f"verifymail_{user_id}_{SPECIFIC_TASK_REWARD}"),
                     types.InlineKeyboardButton("❌ Reject Work", callback_data=f"rejectmail_{user_id}_{SPECIFIC_TASK_REWARD}"))

    admin_view_card = (
        "🧐 **NEW SCREENSHOT PROOF SUBMITTED**\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 **Name:** {first_name}\n"
        f"🌐 **Username:** {username}\n"
        f"🆔 **User ID:** `{user_id}`\n"
        f"🔗 **Profile Link:** [Click Here to Chat](tg://user?id={user_id})\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"🏷 **Task:** {SPECIFIC_TASK_TITLE}\n"
        f"💰 **Reward Amount:** ₹{SPECIFIC_TASK_REWARD}\n\n"
        "👇 Press a button below to evaluate."
    )
    bot.send_photo(ADMIN_ID, photo_token, caption=admin_view_card, parse_mode="Markdown", reply_markup=admin_markup)

# --- PROCESS UPI WITHDRAWAL EXTRADITION ---
def process_payout_request(message):
    user_id = message.chat.id
    upi_string = message.text
    wallet_bal = user_data[user_id]["balance"]
    username = user_data[user_id].get("username", "No Username")
    
    # Intercept payout processing if not joined
    if not is_user_subscribed(user_id):
        send_force_join_menu(user_id)
        return

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
    
    print("ROBINxMAIL TASK Hardcoded Core is running...")
    bot.infinity_polling()
