import telebot
import os
import gspread
import json
import sys
from datetime import datetime
import pytz
from oauth2client.service_account import ServiceAccountCredentials

# --- CẤU HÌNH ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
MY_ID = 7346983056  # ID Telegram của bạn
G_JSON = os.getenv('G_SHEETS_JSON')

# Kết nối Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(G_JSON)
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open("BotData").sheet1

bot = telebot.TeleBot(TOKEN)

def check_and_update(amount, action_name):
    tz = pytz.timezone('Asia/Ho_Chi_Minh')
    now = datetime.now(tz)
    
    # Rào chắn giờ hoạt động: Đúng 6h sáng đến trước 12h trưa
    if not (6 <= now.hour < 12):
        return "🚫 Bot chỉ hoạt động từ 06:00 đến 12:00 hằng ngày."

    today = now.strftime("%d/%m/%Y")
    current_balance = int(sheet.acell('B1').value or 0)
    last_date = sheet.acell('B2').value
    
    if last_date == today:
        return f"⚠️ Hôm nay bạn đã điểm danh rồi!"
    
    new_balance = current_balance + amount
    sheet.update('B1', [[new_balance]])
    sheet.update('B2', [[today]])
    return f"✅ Đã {action_name}.\n💰 Số dư mới: {new_balance:,} VNĐ"

@bot.message_handler(func=lambda message: message.from_user.id == MY_ID)
def handle_commands(message):
    if message.text == '/cong':
        bot.reply_to(message, check_and_update(30000, "cộng 30k"))
    elif message.text == '/tru':
        bot.reply_to(message, check_and_update(-10000, "trừ 10k"))
    elif message.text == '/sodu':
        val = int(sheet.acell('B1').value or 0)
        bot.reply_to(message, f"💰 Số dư hiện tại: {val:,} VNĐ")

if __name__ == "__main__":
    print("Bot đang chờ lệnh trong khung giờ 6h-12h...")
    bot.infinity_polling()
