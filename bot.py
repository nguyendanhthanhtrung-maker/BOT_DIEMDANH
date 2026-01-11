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

def check_time():
    tz = pytz.timezone('Asia/Ho_Chi_Minh')
    now = datetime.now(tz)
    # Hoạt động từ 6h sáng đến trước 12h trưa
    return 6 <= now.hour < 12

@bot.message_handler(func=lambda message: message.from_user.id == MY_ID)
def handle_commands(message):
    text = message.text
    tz = pytz.timezone('Asia/Ho_Chi_Minh')
    today = datetime.now(tz).strftime("%d/%m/%Y")
    
    # --- LỆNH START (HƯỚNG DẪN) ---
    if text == '/start':
        help_text = (
            "👋 Chào chủ nhân! Đây là danh sách lệnh của bạn:\n\n"
            "📅 **Lệnh hằng ngày (6h - 12h):**\n"
            "/cong : Điểm danh cộng 30,000đ\n"
            "/tru : Khấu trừ 10,000đ\n"
            "*(Lưu ý: Chỉ được chọn 1 trong 2 lệnh trên mỗi ngày)*\n\n"
            "💰 **Quản lý ví:**\n"
            "/sodu : Xem số dư hiện tại\n"
            "/rut [số tiền] : Rút tiền tùy ý (Ví dụ: /rut 50000)"
        )
        bot.reply_to(message, help_text, parse_mode="Markdown")
        return

    # Kiểm tra giờ hoạt động cho các lệnh tính toán
    if not check_time():
        bot.reply_to(message, "🚫 Hiện tại ngoài giờ hoạt động (06:00 - 12:00).")
        return

    # Đọc dữ liệu từ Sheets
    current_balance = int(sheet.acell('B1').value or 0)
    last_date = sheet.acell('B2').value

    # --- LỆNH CỘNG 30K ---
    if text == '/cong':
        if last_date == today:
            bot.reply_to(message, "⚠️ Hôm nay bạn đã dùng quyền cộng/trừ rồi!")
            return
        new_val = current_balance + 30000
        sheet.update('B1', [[new_val]])
        sheet.update('B2', [[today]])
        bot.reply_to(message, f"✅ Đã cộng 30,000đ.\n💰 Ví: {new_val:,} VNĐ")

    # --- LỆNH TRỪ 10K ---
    elif text == '/tru':
        if last_date == today:
            bot.reply_to(message, "⚠️ Hôm nay bạn đã dùng quyền cộng/trừ rồi!")
            return
        new_val = current_balance - 10000
        sheet.update('B1', [[new_val]])
        sheet.update('B2', [[today]])
        bot.reply_to(message, f"❌ Đã trừ 10,000đ.\n💰 Ví: {new_val:,} VNĐ")

    # --- LỆNH RÚT TIỀN TÙY CHỈNH ---
    elif text.startswith('/rut'):
        try:
            val_rut = int(text.split()[1])
            if val_rut > current_balance:
                bot.reply_to(message, f"❌ Không đủ tiền! (Hiện có {current_balance:,}đ)")
                return
            new_val = current_balance - val_rut
            sheet.update('B1', [[new_val]])
            bot.reply_to(message, f"💸 Đã rút {val_rut:,}đ.\n💰 Còn lại: {new_val:,} VNĐ")
        except (IndexError, ValueError):
            bot.reply_to(message, "⚠️ Cách dùng: `/rut 50000`", parse_mode="Markdown")

    # --- XEM SỐ DƯ ---
    elif text == '/sodu':
        bot.reply_to(message, f"💰 Số dư hiện tại: {current_balance:,} VNĐ")

if __name__ == "__main__":
    bot.infinity_polling()
