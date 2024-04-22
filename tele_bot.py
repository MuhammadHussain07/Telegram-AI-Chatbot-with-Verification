import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, ConversationHandler
import openai
from config import OPENAI_API_KEY, TELEGRAM_BOT_TOKEN

# Configure logging
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Set your OpenAI API key
openai.api_key = OPENAI_API_KEY

# Conversation states
VERIFY, VERIFY_RESPONSE, DEFAULT = range(3)

# Predefined questions and answers for training
training_data = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is your name?"},
    {"role": "assistant", "content": "I'm an AI created by OpenAI."},
    {"role": "user", "content": "What is your DOB?"},
    {"role": "assistant", "content": "I was created by OpenAI, so I don't have a date of birth."},
    {"role": "user", "content": "How many siblings do you have?"},
    {"role": "assistant", "content": "I'm an AI and don't have siblings."},
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send a message when the command /start is issued and prompt for verification."""
    await update.message.reply_text(
        "Hello! To verify you, I will ask some questions.\n"
        "If you're ready, type anything to continue or /cancel to stop."
    )
    return VERIFY

async def verify(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Ask verification questions."""
    await update.message.reply_text("Let's start the verification. Please answer the following questions:")
    await update.message.reply_text(training_data[1]["content"])  # Ask the first question
    return VERIFY_RESPONSE

async def verify_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the verification response and move to next question or end verification."""
    if 'question_index' not in context.user_data:
        context.user_data['question_index'] = 1
    
    question_index = context.user_data['question_index']
    
    # Assuming user correctly answers or skips verification questions, adjust logic as needed
    if question_index < len(training_data) - 1:
        question_index += 2  # Move to the next question
        context.user_data['question_index'] = question_index
        await update.message.reply_text(training_data[question_index]["content"])
        return VERIFY_RESPONSE
    else:
        await update.message.reply_text("Verification complete. You can now ask me anything!")
        return DEFAULT  # Transition to the default state

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle general messages from the user."""
    user_message = update.message.text
    chat_id = update.effective_chat.id

    # Combine training data with the new user message
    conversation = training_data + [{"role": "user", "content": user_message}]

    # Generate a response from OpenAI's ChatGPT
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=conversation,
    )

    # Send the generated response to the user
    await context.bot.send_message(chat_id=chat_id, text=response.choices[0].message["content"])

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the current operation."""
    await update.message.reply_text('Operation cancelled.')
    return ConversationHandler.END

def main() -> None:
    """Start the bot."""
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            VERIFY: [MessageHandler(filters.TEXT & ~filters.COMMAND, verify)],
            VERIFY_RESPONSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, verify_response)],
            DEFAULT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(conv_handler)

    # Start the Bot
    application.run_polling()

if __name__ == '__main__':
    main()
