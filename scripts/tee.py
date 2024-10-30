import sys
import time
import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver import ChromeOptions, Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
import random
import os
from dotenv import load_dotenv
import json

# load_dotenv()

TWITTER_ACCOUNT=os.getenv("TWITTER_ACCOUNT")
if not TWITTER_ACCOUNT:
    raise ValueError("TWITTER_ACCOUNT not found in .env file")


BASE_URL = "http://127.0.0.1:3000"
REGISTER_OR_LOGIN_ENDPOINT = f"{BASE_URL}/login"
CALLBACK_ENDPOINT = f"{BASE_URL}/callback"


PASSWORD = os.getenv("TWITTER_PASSWORD")
if not PASSWORD:
    raise ValueError("TWITTER_PASSWORD not found in .env file")
X_EMAIL = os.getenv("X_EMAIL")
if not X_EMAIL:
    raise ValueError("X_EMAIL not found in .env file")

options = ChromeOptions()
options.add_argument("--start-maximized")
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--no-sandbox')
driver = uc.Chrome(headless=True, use_subprocess=False, browser_executable_path='/usr/bin/chromium', options=options)

url = "https://twitter.com/i/flow/login"
driver.get(url)

username = WebDriverWait(driver, 20).until(
    EC.visibility_of_element_located(
        (By.CSS_SELECTOR, 'input[autocomplete="username"]')
    )
)
username.send_keys(TWITTER_ACCOUNT)
username.send_keys(Keys.ENTER)
print('sent twitter account', file=sys.stderr)
time.sleep(1)

input_field = WebDriverWait(driver, 10).until(
    EC.any_of(
        EC.visibility_of_element_located((
            (By.CSS_SELECTOR, 'input[name="password"]')
        )),
        EC.visibility_of_element_located((
            (By.CSS_SELECTOR, 'input[autocomplete="on"]')
        )),
    )
)

if input_field.get_attribute('autocomplete') == 'on':
    # Handle email field
    print("Found email field", sys.stderr)
    input_field.send_keys(X_EMAIL)
    input_field.send_keys(Keys.ENTER)
    time.sleep(1)

    input_field = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located(
            (By.CSS_SELECTOR, 'input[autocomplete="current-password"]')
        )
    )
    
print('password', file=sys.stderr)
input_field.send_keys(PASSWORD)
input_field.send_keys(Keys.ENTER)

time.sleep(5)
ct0 = driver.get_cookie("ct0")["value"]
auth_token = driver.get_cookie("auth_token")["value"]
with open('cookies.env','w') as f:
    obj = dict(ct0=ct0, auth_token=auth_token)
    j = json.dumps(obj).replace('"','\\"').replace(' ','')
    f.write(f"X_AUTH_TOKENS={j}\n")

print('going to callback', file=sys.stderr)
driver.get(REGISTER_OR_LOGIN_ENDPOINT)

try:
    allow_button = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located(
            (By.CSS_SELECTOR, 'input[id="allow"]')
        )
    )
    allow_button.click()
except Exception as e:
    print(e)
