from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException, NoSuchElementException
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
email = os.getenv("EMAIL")
password = os.getenv("PASSWORD")

# 指定 Tesseract 執行文件的路徑
pytesseract.pytesseract.tesseract_cmd = tesseract_path # 將路徑替換為你的實際路徑

url = 'https://kktix.com/?locale=zh-TW' # KKTIX
s = Service(chrome_driver_path)

options = webdriver.ChromeOptions()
options.add_experimental_option("detach", True) # 不自動關閉視窗

driver = webdriver.Chrome(service=s, options=options)
driver.get(url)

# 等待使用者登入成功，這裡以出現 "登入成功" 文字為條件
try:
    # 找到登入連結元素並點選
    login_link = WebDriverWait(driver, 300).until(
        EC.presence_of_element_located((By.XPATH, "//a[contains(text(), 'Sign In') or contains(text(), '登入')]"))
    )
    login_link.click()

    # 找到帳號輸入框元素並輸入帳號
    username_input = driver.find_element(By.ID, "user_login")
    username_input.clear()  # 清空輸入框
    username_input.send_keys(email)  # 更改為你的帳號

    # 找到密碼輸入框元素並輸入密碼
    password_input = driver.find_element(By.ID, "user_password")
    password_input.clear()  # 清空輸入框
    password_input.send_keys(password)  # 更改為你的密碼

    # 找到登入按鈕並點擊
    login_button = driver.find_element(By.NAME, "commit")
    login_button.click()

    # 登入成功後，將瀏覽器重新導向到其他頁面
    driver.get("https://goldendeerjr.kktix.cc/events/keswlkfo1?locale=zh-TW")  # 搶票頁面
except TimeoutException:
    print("等待超時或未找到登入成功的元素，請檢查是否成功登入。")

#通用函數，用於執行搶票
def perform_ticket_booking_procedure():
    # 點選下一步連結
    next_button = driver.find_element(By.XPATH, '//a[@class="btn-point" and (text()="下一步" or text()="Next Step")]')
    driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
    next_button.click()

    print("請自行選擇票種後按下一步")

    # 我已經閱讀並同意 服務條款 與 隱私權政策
    checkbox = driver.find_element(By.ID, 'person_agree_terms')
    if not checkbox.is_selected():
        checkbox.click()
    
    # 等待系統選位通知出現，並設置 5 分鐘的等待時間
    try:
        modal_title = WebDriverWait(driver, 300).until(
            EC.visibility_of_element_located((By.XPATH, '//h4[@id="seatModalLabel" and contains(text(), "系統選位通知")]'))
        )
        print("系統選位通知出現了")
        # 在這裡執行你的下一步操作
    except TimeoutException:
        print("等待系統選位通知出現超時")
        # 如果超時，你可以根據情況執行其他處理邏輯

    try:
        button = driver.find_element(By.XPATH, '//button[@class="btn btn-primary pull-right ng-binding" and contains(text(), "知道了")]')
        button.click()
    except NoSuchElementException:
        print("未找到知道了按鈕，無座位")

    print("確認無誤後點擊確認座位->完成選位->確認表單資訊->繳費")

choice = input("請輸入模式(1.測試 2.搶票): ")

if choice == "1":
    print("進入測試模式")
    perform_ticket_booking_procedure()

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
            perform_ticket_booking_procedure()
            break
        else:
            print("等待搶票時間...")
            time.sleep(1)  # 每秒檢查一次時間

else:
    print("輸入選項不正確，請重新輸入。")