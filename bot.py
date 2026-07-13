import telebot
from telebot import types

# 1. Configuration
API_TOKEN = '8688748786:AAGK1QI_5vFdiDmR8V-uPRKmCZeTvQ5wwjU'
ADMIN_ID = 6535711381  # 👈 REPLACE THIS WITH YOUR ACTUAL TELEGRAM ID NUMBERS

bot = telebot.TeleBot(API_TOKEN)

# In-memory database
user_data = {}

# Active tasks database created by the Admin
# Format: {"task_id_1": {"title": "Name", "reward": 5, "link": "url", "instructions": "text"}}
active_tasks = {
    "task_1": {
        "title": "⭐ Google Maps Review",
        "reward": 5,
        "link": "https://maps.google.com",
        "instructions": "Give a 5-star review and write a positive comment."
    },
    "task_2": {
        "title": "✉️ Create Gmail Account",
        "reward": 10,
        "link": "https://accounts.google.com",
        "instructions": "Create a new fresh Gmail account and send the screenshot of the inbox profile."
    }
}

MIN_WITHDRAWAL = 15

# Global temp variable for admin task creation step-by-step
admin_creating_task = {}

# --- WELCOME COMMAND ---
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.chat.id
    if user_id not in user_data:
        user_data[user_id] = {"balance": 0, "active_task_id": None}
    
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton('📋 View Tasks')
    btn2 = types.KeyboardButton('💰 Check Balance')
    btn3 = types.KeyboardButton('💸 Withdraw Money')
    markup.add(btn1, btn2, btn3)
    
    welcome_text = "👋 Welcome! Choose an option from the menu to start earning."
    # If the admin starts the bot, remind them of their special control command
    if user_id == ADMIN_ID:
        welcome_text += "\n\n🛠 **Admin Note:** Use /addtask to add a new task for your workers."
        
    bot.send_message(user_id, welcome_text, reply_markup=markup)

# --- ADMIN PANEL: ADD NEW TASK COMMAND ---
@bot.message_handler(commands=['addtask'])
def add_task_start(message):
    if message.chat.id != ADMIN_ID:
        bot.reply_to(message, "❌ You are not authorized to use this command.")
        return
    
    msg = bot.send_message(ADMIN_ID, "📝 Step 1: Enter the **Title / Type** of the task (e.g., 'Review Hotel ABC' or 'Create Outlook Mail'):")
    bot.register_next_step_handler(msg, process_admin_task_title)

def process_admin_task_title(message):
    title = message.text
    new_task_id = f"task_{len(active_tasks) + 1}"
    admin_creating_task[ADMIN_ID] = {"id": new_task_id, "title": title}
    
    msg = bot.send_message(ADMIN_ID, f"💰 Step 2: Enter the **Reward Amount** in ₹ for completing this task (numbers only):")
    bot.register_next_step_handler(msg, process_admin_task_reward)

def process_admin_task_reward(message):
    try:
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
