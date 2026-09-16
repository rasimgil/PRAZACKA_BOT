import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# --- 1. Tiny Web Server for Render Health Checks ---
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive!")

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHandler)
    server.serve_forever()

# --- 2. Telegram Bot Logic ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")

async def get_available_slots(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    target_day = args[0].lower() if args else "today"
    url = "https://jdemenato.cz/reservation/prazacka/reservationcalendaroverview"
    
    try:
        # Use Playwright (headless browser) to bypass Cloudflare
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Go to the site and wait for Cloudflare/content to load
            await page.goto(url, timeout=60000)
            await page.wait_for_timeout(3000) # Give 3 seconds for JS/Cloudflare to clear
            
            html_content = await page.content()
            await browser.close()
            
        soup = BeautifulSoup(html_content, 'html.parser')
        free_slots = []
        rows = soup.find_all('tr')
        
        for row in rows:
            free_cell = row.find('td', class_='timetableFree')
            time_header = row.find('th', class_='timeLeft')
            
            if free_cell and time_header:
                free_slots.append(time_header.get_text(strip=True))

        if free_slots:
            message = f"⚽ **Available Pitch Slots ({target_day.capitalize()}):**\n" + "\n".join([f"• {slot}" for slot in set(free_slots)])
        else:
            message = f"No free slots found for {target_day}."
            
    except Exception as e:
        message = f"Error fetching slots: {str(e)}"

    await update.message.reply_text(message, parse_mode="Markdown")

def main():
    if not TOKEN:
        raise ValueError("No TELEGRAM_TOKEN found in environment variables!")

    server_thread = threading.Thread(target=run_web_server, daemon=True)
    server_thread.start()

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("slots", get_available_slots))
    
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()