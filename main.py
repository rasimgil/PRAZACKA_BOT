import os
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Replace with your token or load it from environment variables
TOKEN = os.environ.get("TELEGRAM_TOKEN", "8899729045:AAHvyRWIGM-oezyWGgXVWOWbf95pFCotYLU")

async def get_available_slots(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = "https://jdemenato.cz/reservation/prazacka/reservationcalendaroverview"
    
    try:
        # Fetch the HTML page
        response = requests.get(url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find free time slots based on your HTML structure
        free_slots = []
        rows = soup.find_all('tr')
        
        for row in rows:
            # Look for elements matching free slots or login requirements
            free_cell = row.find('td', class_='timetableFree')
            time_header = row.find('th', class_='timeLeft')
            
            if free_cell and time_header:
                free_slots.append(time_header.get_text(strip=True))

        if free_slots:
            message = "⚽ **Available Pitch Slots Today:**\n" + "\n".join([f"• {slot}" for slot in set(free_slots)])
        else:
            message = "No free slots found or the page structure changed."
            
    except Exception as e:
        message = f"Error fetching slots: {str(e)}"

    await update.message.reply_text(message, parse_mode="Markdown")

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    
    # Command: /slots
    app.add_handler(CommandHandler("slots", get_available_slots))
    
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()