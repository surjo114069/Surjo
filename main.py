import os
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from pymongo import MongoClient

# ================== CONFIG ==================
BOT_TOKEN = os.getenv(":AAHVgEFLa8Ni86B6aJPztiG3UoLSONzzlZk")
MONGO_URI = os.getenv(":R0mkj4IRfFuO34yO@ac-tragtmd-shard-00-00.bvojpfb.mongodb.net:27017,ac-tragtmd-shard-00-01.bvojpfb.mongodb.net:27017,ac-tragtmd-shard-00-02.bvojpfb.mongodb.net:27017/?ssl=true&replicaSet=atlas-xhpy7x-shard-0&authSource=admin&appName=Cluster0")
# ============================================

client = MongoClient(MONGO_URI)
db = client["savings_bot"]
collection = db["users"]

def get_user_data(user_id):
    user = collection.find_one({"_id": str(user_id)})
    if not user:
        user = {
            "_id": str(user_id),
            "target_amount": 0,
            "remaining_amount": 0,
            "target_days": 0,
            "remaining_days": 0,
            "saved_amount": 0
        }
        collection.insert_one(user)
    return user

def update_user_data(user_id, data):
    collection.update_one({"_id": str(user_id)}, {"$set": data}, upsert=True)

# ================== /start ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user_data(user_id)

    amount = user["target_amount"] if user["target_amount"] > 0 else ""
    days = user["target_days"] if user["target_days"] > 0 else ""

    menu = f"""==============================
|        It's Your Biggest Dream        |
==============================
|     Set Amount / Target Your Days     |
==============================
          ( Set Target Like This )

Enter Your Amount = {amount}
Enter Your Target Days = {days}

------------------------------
Saved Amount     : {user['saved_amount']}
Remaining Amount : {user['remaining_amount']}
Days Left        : {user['remaining_days']}
------------------------------

Commands:
/start
/status
/Save 500
/Minus 300
/Reset 50
/Reset 100
/Reset 200
/Reset amount
/Reset Days
/Reset All"""

    await update.message.reply_text(menu)

# ================== /status ==================
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user_data(update.effective_user.id)
    msg = f"""📊 Current Status
==============================
Target Amount    : {user['target_amount']}
Remaining Amount : {user['remaining_amount']}
Saved Amount     : {user['saved_amount']}
Target Days      : {user['target_days']}
Days Left        : {user['remaining_days']}
=============================="""
    await update.message.reply_text(msg)

# ================== /Save ==================
async def save_money(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user_data(user_id)

    if not context.args:
        await update.message.reply_text("Usage: /Save 500")
        return

    try:
        amount = float(context.args[0])
        if amount <= 0:
            await update.message.reply_text("Amount must be greater than 0")
            return

        user["saved_amount"] += amount
        user["remaining_amount"] = max(0, user["remaining_amount"] - amount)

        if amount >= 500:
            user["remaining_days"] = max(0, user["remaining_days"] - 1)

        update_user_data(user_id, user)

        await update.message.reply_text(
            f"""✅ Saved {amount}

Saved Amount     : {user['saved_amount']}
Remaining Amount : {user['remaining_amount']}
Days Left        : {user['remaining_days']}"""
        )
    except:
        await update.message.reply_text("Please send a valid number\nExample: /Save 500")

# ================== /Minus ==================
async def minus_money(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user_data(user_id)

    if not context.args:
        await update.message.reply_text("Usage: /Minus 300")
        return

    try:
        amount = float(context.args[0])
        if amount <= 0:
            await update.message.reply_text("Amount must be greater than 0")
            return

        user["saved_amount"] = max(0, user["saved_amount"] - amount)
        update_user_data(user_id, user)

        await update.message.reply_text(
            f"""✅ Subtracted {amount}

Saved Amount     : {user['saved_amount']}
Remaining Amount : {user['remaining_amount']}
Days Left        : {user['remaining_days']}"""
        )
    except:
        await update.message.reply_text("Please send a valid number\nExample: /Minus 300")

# ================== /Reset 50 / 100 / 200 ==================
async def reset_quick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user_data(user_id)

    if not context.args:
        await update.message.reply_text("Usage: /Reset 50")
        return

    try:
        amount = float(context.args[0])
        if amount <= 0:
            await update.message.reply_text("Amount must be greater than 0")
            return

        user["saved_amount"] = max(0, user["saved_amount"] - amount)
        update_user_data(user_id, user)

        await update.message.reply_text(
            f"""✅ Reset {amount} from Saved

Saved Amount     : {user['saved_amount']}
Remaining Amount : {user['remaining_amount']}
Days Left        : {user['remaining_days']}"""
        )
    except:
        await update.message.reply_text("Please send a valid number\nExample: /Reset 100")

# ================== /Reset amount ==================
async def reset_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["waiting_for"] = "new_amount"
    await update.message.reply_text("Please Enter New Amount:")

# ================== /Reset Days ==================
async def reset_days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["waiting_for"] = "new_days"
    await update.message.reply_text("Please Enter New Target Days:")

# ================== /Reset All ==================
async def reset_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = {
        "target_amount": 0,
        "remaining_amount": 0,
        "target_days": 0,
        "remaining_days": 0,
        "saved_amount": 0
    }
    update_user_data(user_id, data)
    await update.message.reply_text("✅ Everything has been fully reset")

# ================== Handle text messages ==================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    user = get_user_data(user_id)

    # If waiting for new amount
    if context.user_data.get("waiting_for") == "new_amount":
        try:
            amount = float(text)
            if amount <= 0:
                await update.message.reply_text("Amount must be greater than 0")
                return

            user["target_amount"] = amount
            user["remaining_amount"] = amount
            user["saved_amount"] = 0
            update_user_data(user_id, user)
            context.user_data["waiting_for"] = None

            await update.message.reply_text(
                f"""✅ New Amount Set Successfully!

Target Amount    : {user['target_amount']}
Remaining Amount : {user['remaining_amount']}
Saved Amount     : 0"""
            )
        except:
            await update.message.reply_text("Please enter a valid number")
        return

    # If waiting for new days
    if context.user_data.get("waiting_for") == "new_days":
        try:
            days = int(text)
            if days <= 0:
                await update.message.reply_text("Days must be greater than 0")
                return

            user["target_days"] = days
            user["remaining_days"] = days
            update_user_data(user_id, user)
            context.user_data["waiting_for"] = None

            await update.message.reply_text(
                f"""✅ New Days Set Successfully!

Target Days : {user['target_days']}
Days Left   : {user['remaining_days']}"""
            )
        except:
            await update.message.reply_text("Please enter a valid number")
        return

    # Normal form filling
    amount_match = re.search(r'(?:Enter Your Amount|Amount)\s*=\s*([0-9]+(?:\.[0-9]+)?)', text, re.IGNORECASE)
    days_match = re.search(r'(?:Enter Your Target Days|Days)\s*=\s*([0-9]+)', text, re.IGNORECASE)

    if amount_match or days_match:
        if amount_match:
            amount = float(amount_match.group(1))
            user["target_amount"] = amount
            user["remaining_amount"] = amount
            user["saved_amount"] = 0

        if days_match:
            days = int(days_match.group(1))
            user["target_days"] = days
            user["remaining_days"] = days

        update_user_data(user_id, user)

        await update.message.reply_text(
            f"""✅ Targets Saved Successfully!

Target Amount    : {user['target_amount']}
Target Days      : {user['target_days']}
Remaining Amount : {user['remaining_amount']}
Days Left        : {user['remaining_days']}
Saved Amount     : {user['saved_amount']}"""
        )
    else:
        await update.message.reply_text("Please send in this format:\n\nEnter Your Amount = 300000\nEnter Your Target Days = 800")

# ================== MAIN ==================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("Save", save_money))
    app.add_handler(CommandHandler("Minus", minus_money))
    app.add_handler(CommandHandler("Reset", reset_quick))
    app.add_handler(CommandHandler("reset_amount", reset_amount))
    app.add_handler(CommandHandler("Reset_amount", reset_amount))
    app.add_handler(CommandHandler("reset_days", reset_days))
    app.add_handler(CommandHandler("Reset_Days", reset_days))
    app.add_handler(CommandHandler("Reset_All", reset_all))
    app.add_handler(CommandHandler("reset_all", reset_all))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
