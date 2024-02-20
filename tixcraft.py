from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from datetime import datetime, timedelta
import requests
from PIL import Image
import pytesseract
import time
import re
import io
import os
from dotenv import load_dotenv

# 從 .env 文件中加載環境變數
load_dotenv()

# 讀取環境變數
tesseract_path = os.getenv("TESSERACT_PATH")
chrome_driver_path = os.getenv("CHROME_DRIVER_PATH")

# 指定 Tesseract 執行文件的路徑
pytesseract.pytesseract.tesseract_cmd = tesseract_path # 將路徑替換為你的實際路徑

url = 'https://tixcraft.com/' # 拓元
s = Service(chrome_driver_path)

options = webdriver.ChromeOptions()
options.add_experimental_option("detach", True) # 不自動關閉視窗

driver = webdriver.Chrome(service=s, options=options)
driver.get(url)

# 等待使用者登入成功，這裡以出現 "登入成功" 文字為條件
try:
    print("請先登入")
    login_start = time.strftime("%H:%M")
    print("登入中" + login_start)
    element = WebDriverWait(driver, 300).until(
        EC.presence_of_element_located((By.XPATH, "//span[contains(text(), '會員帳戶') or contains(text(), 'My Account')]"))
    )
    login_end = time.strftime("%H:%M")
    print("登入成功" + login_end)

    # 登入成功後，將瀏覽器重新導向到其他頁面
    driver.get("https://tixcraft.com/activity/detail/24_knowknow")  # 搶票頁面
except TimeoutException:
    print("等待超時或未找到登入成功的元素，請檢查是否成功登入。")

# 通用函數，用於執行搶票
def perform_ticket_booking_procedure(date, num):
    # 找到立即購票按鈕並點擊
    buy_ticket_button = driver.find_element(By.XPATH, "//div[text()='立即購票']")

    # 使用 JavaScript 點擊按鈕
    driver.execute_script("arguments[0].click();", buy_ticket_button)

    # 等待下拉選單元素出現
    dropdown = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "dateSearchGameList"))
    )

    # 選擇日期
    dropdown = Select(dropdown)
    for option in dropdown.options:
        if date in option.get_attribute("value"):
            option.click()
            break

    # 等待立即訂購按鈕可見
    button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '立即訂購')]"))
    )
    button.click()

    print("請選擇自行位子區域")

    # 找到所有 ID 包含 TicketForm_ticketPrice 的下拉選單元素
    # 使用 WebDriverWait 等待元素出現，最多等待 1 分鐘
    dropdown_elements = WebDriverWait(driver, 60).until(
        EC.presence_of_all_elements_located((By.XPATH, "//select[contains(@id, 'TicketForm_ticketPrice')]"))
    )

    # 遍歷找到的下拉選單元素
    for dropdown_element in dropdown_elements:
        # 使用 Select 類來處理下拉選單
        dropdown_ticket = Select(dropdown_element)
        # 選擇值為 "2" 的選項
        dropdown_ticket.select_by_value(num)

    # 等待驗證碼圖片可見
    div_element = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, "div.verify-img"))
    )

    # 等待驗證碼圖片可見
    captcha_image = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.ID, "TicketForm_verifyCode-image"))
    )

    # 下載驗證碼圖片
    captcha_image_src = captcha_image.get_attribute("src")
    response = requests.get(captcha_image_src)
    captcha_image_bytes = response.content

    # 將圖片讀取成 Image 物件
    captcha_image = Image.open(io.BytesIO(captcha_image_bytes))

    # 使用 Tesseract-OCR 辨識圖片中的文字
    captcha_text = pytesseract.image_to_string(captcha_image)

    # 將辨識出的文字填入驗證碼欄位
    verify_code_input = driver.find_element(By.ID, "TicketForm_verifyCode")
    verify_code_input.clear()  # 清除原有內容
    verify_code_input.send_keys(captcha_text)
    
    # 等待一些時間，最多1秒，看看警告框是否出現
    try:
        alert = WebDriverWait(driver, 1).until(EC.alert_is_present())

        # 如果警告框出現，就處理它
        alert = driver.switch_to.alert
        alert.accept()
    except:
        # 如果警告框沒有出現，程式會繼續執行下一個步驟
        pass

    try:
        # 點擊同意會員服務條款的複選框
        agree_checkbox = driver.find_element(By.ID, "TicketForm_agree")
        agree_checkbox.click()
    except ElementClickInterceptedException:
        # 如果點擊被阻擋，則滾動頁面以確保元素可見
        action = ActionChains(driver)
        action.move_to_element(agree_checkbox).perform()
        agree_checkbox.click()

    print("請在20秒內檢察驗證碼是否錯誤")
    time.sleep(20)

    # 點擊確認按鈕
    # confirm_button = driver.find_element(By.XPATH, "//button[contains(@class, 'btn-primary') and contains(@class, 'btn-green')]")
    # confirm_button.click()

choice = input("請輸入模式(1.測試 2.搶票): ")

while True:
    date = input("請輸入日期(格式-YYYY/MM/DD): ")
    if re.match(r"\d{4}/\d{2}/\d{2}", date):
        # 符合格式要求，退出迴圈
        break
    else:
        print("日期格式不正確，請重新輸入。")
    
while True:
    num = input("請輸入張數: ")
    # 檢查用戶輸入的值是否為空
    if num.strip() == "":
        print("張數不能為空，請重新輸入。")
    # 檢查用戶輸入的值是否為有效的數字
    elif not num.isdigit():
        print("張數必須為數字，請重新輸入。")
    else:
        break

if choice == "1":
    print("進入測試模式")
    perform_ticket_booking_procedure(date, num)

elif choice == "2":
    print("進入搶票模式")
    target_time_str = input("請輸入搶票時間(24小時制)(例-15:30): ")
    target_time = datetime.strptime(target_time_str, "%H:%M").time()

    while True:
        current_time = datetime.now().time()  # 取得當前時間
        # 比較當前時間和目標時間
        if current_time >= target_time:
            print("到達指定搶票時間，開始搶票流程")
            driver.refresh()  # 在目標時間重新整理網頁
            perform_ticket_booking_procedure(date, num)
            break
        else:
            print("等待搶票時間...")
            time.sleep(1)  # 每秒檢查一次時間

else:
    print("輸入選項不正確，請重新輸入。")