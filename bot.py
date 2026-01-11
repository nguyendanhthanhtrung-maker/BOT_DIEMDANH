import telebot
import os
import gspread
import json
from datetime import datetime
import pytz
from oauth2client.service_account import ServiceAccountCredentials

# --- CẤU HÌNH ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
MY_ID = 7346983056 
G_JSON = os.getenv('G_SHEETS_JSON')

# Kết nối Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(G_JSON)
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open("BotData").sheet1

bot = telebot.TeleBot(TOKEN)

# Hàm kiểm tra khung giờ 6h - 12h
def is_within_time_limit():
    tz = pytz.timezone('Asia/Ho_Chi_Minh')
    now = datetime.now(tz)
    return 6 <= now.hour < 12

@bot.message_handler(func=lambda message: message.from_user.id == MY_ID)
def handle_commands(message):
    text = message.text
    tz = pytz.timezone('Asia/Ho_Chi_Minh')
    today = datetime.now(tz).strftime("%d/%m/%Y")
    
    # Đọc dữ liệu từ Sheets
    current_balance = int(sheet.acell('B1').value or 0)
    last_date = sheet.acell('B2').value

    # --- LỆNH START (KHÔNG GIỚI HẠN GIỜ) ---
    if text == '/start':
        help_text = (
            "👋 Chào chủ nhân! Danh sách lệnh của bạn:\n\n"
            "⚠️ **Chỉ dùng được từ 06:00 - 12:00:**\n"
            "/cong : Cộng 30,000đ điểm danh\n"
            "/tru : Khấu trừ 10,000đ\n"
            "*(Giới hạn 1 lần/ngày cho cả 2 lệnh này)*\n\n"
            "🔓 **Dùng được bất cứ lúc nào:**\n"
            "/sodu : Xem số dư hiện tại\n"
            "/rut [số tiền] : Rút tiền tùy ý"
        )
        bot.reply_to(message, help_text, parse_mode="Markdown")
        return

    # --- XEM SỐ DƯ (KHÔNG GIỚI HẠN GIỜ) ---
    elif text == '/sodu':
        bot.reply_to(message, f"💰 Số dư hiện tại: {current_balance:,} VNĐ")
        return

    # --- RÚT TIỀN (KHÔNG GIỚI HẠN GIỜ) ---
    elif text.startswith('/rut'):
        try:
            val_rut = int(text.split()[1])
            if val_rut > current_balance:
                bot.reply_to(message, f"❌ Không đủ tiền! (Bạn có {current_balance:,}đ)")
                return
            new_val = current_balance - val_rut
            sheet.update('B1', [[new_val]])
            bot.reply_to(message, f"💸 Đã rút {val_rut:,}đ.\n💰 Còn lại: {new_val:,} VNĐ")
        except (IndexError, ValueError):
            bot.reply_to(message, "⚠️ Cách dùng: `/rut 50000`", parse_mode="Markdown")
        return

    # --- LỆNH CỘNG/TRỪ (GIỚI HẠN GIỜ 6H-12H VÀ 1 LẦN/NGÀY) ---
    if text == '/cong' or text == '/tru':
        # 1. Kiểm tra giờ
        if not is_within_time_limit():
            bot.reply_to(message, "🚫 Lệnh /cong và /tru chỉ hoạt động từ 06:00 đến 12:00.")
            return
        
        # 2. Kiểm tra ngày
        if last_date == today:
            bot.reply_to(message, "⚠️ Hôm nay bạn đã dùng quyền cộng/trừ rồi!")
            return

        if text == '/cong':
            new_val = current_balance + 30000
            msg = f"✅ Đã cộng 30,000đ.\n💰 Ví: {new_val:,} VNĐ"
        else:
            new_val = current_balance - 10000
            msg = f"❌ Đã trừ 10,000đ.\n💰 Ví: {new_val:,} VNĐ"
        
        sheet.update('B1', [[new_val]])
        sheet.update('B2', [[today]])
        bot.reply_to(message, msg)

if __name__ == "__main__":
    bot.infinity_polling()
