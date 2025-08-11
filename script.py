import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = "8232855202:AAEQdZio8b6vBukBZIhjqTZp69JeJ8LbMqk"
DRIVER_PATH = r"C:\edgedriver_win64\msedgedriver.exe"
PROXY_FILE = r"C:\Users\ekko2\OneDrive\Tài liệu\proxies.txt"

def get_random_proxy():
    with open(PROXY_FILE, "r", encoding="utf-8") as f:
        proxies = [p.strip() for p in f.readlines() if p.strip()]
    return random.choice(proxies)

def scrape_data(keyword):
    try:
        proxy = get_random_proxy()
        print(f"🔄 Đang sử dụng proxy: {proxy}")

        options = Options()
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-infobars")
        options.add_argument("--remote-allow-origins=*")
        service = Service(DRIVER_PATH)
        driver = webdriver.Edge(service=service, options=options)

        driver.get("https://muasamcong.mpi.gov.vn/web/guest/contractor-selection?render=index")
        print("🌐 Trang đã load thành công!")

        # Chờ ô input xuất hiện
        search_box = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='Nhập từ khoá']"))
        )
        search_box.clear()
        search_box.send_keys(keyword)

        # Click nút tìm kiếm
        search_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.button__search"))
        )
        search_button.click()

        # Chờ kết quả hiển thị
        items = WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".content__body__left__item__infor"))
        )

        results = []
        for item in items:
            try:
                title = item.find_element(By.CSS_SELECTOR, "h5.content__body__left__item__infor__contract__name").text.strip()
                investor = item.find_element(By.XPATH, ".//h6[span and contains(text(),'Chủ đầu tư')]/span").text.strip()
                location_text = item.find_element(By.XPATH, ".//h6[span and contains(text(),'Địa điểm')]/span").text.strip()
                date_posted = item.find_element(By.XPATH, ".//h6[span and contains(text(),'Ngày đăng tải thông báo')]/span").text.strip()

                results.append({
                    "title": title,
                    "investor": investor,
                    "location": location_text,
                    "date": date_posted
                })
            except Exception as e:
                print(f"Lỗi khi đọc item: {e}")
                continue

        driver.quit()
        return results

    except Exception as e:
        print(f"❌ Lỗi scrape: {e}")
        return []


# ================== TELEGRAM BOT ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Nhập từ khoá để tìm kiếm gói thầu:")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyword = update.message.text.strip()
    await update.message.reply_text(f"Đang tìm kiếm: {keyword}...")

    data = scrape_data(keyword)

    if data:
        for item in data:
            await update.message.reply_text(
                f"📌 {item['title']}\n"
                f"🏢 {item['investor']}\n"
                f"📍 {item['location']}\n"
                f"🗓 {item['date']}"
            )
    else:
        await update.message.reply_text("❌ Không tìm thấy gói thầu nào phù hợp.")


if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("✅ Bot đang chạy...")
    app.run_polling()
