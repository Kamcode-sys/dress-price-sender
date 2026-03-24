import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import time

# Email credentials
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
APP_PASSWORD = os.environ.get("APP_PASSWORD")
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL")

# Configuration
TARGET_PRICE = 26
PRODUCT_URL = "https://www.zara.com/ng/en/cut-out-lace-dress-p01067002.html?v1=495703199"

# Chrome options - make headless browser look more real
chrome_options = Options()
chrome_options.add_argument("--headless=new")  # New headless mode
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option('useAutomationExtension', False)
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=chrome_options
)

# Mask automation
driver.execute_cdp_cmd('Network.setUserAgentOverride', {
    "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36'
})
driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

float_price = None

try:
    print("🔍 Loading Zara page...")
    driver.get(PRODUCT_URL)
    
    # Wait for page to fully load
    print("⏳ Waiting for page to load...")
    time.sleep(15)  # Give it plenty of time
    
    # Take screenshot for debugging
    driver.save_screenshot("zara_page.png")
    print("📸 Screenshot saved")
    
    # Save page source for debugging
    with open("zara_page.html", "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    print("💾 Page source saved")
    
    # Try multiple CSS selectors
    css_selectors = [
        "span.money-amount__main",
        ".price-current__amount",
        "span[data-qa-qualifier='product.price']",
        "div.price span",
        "[class*='money-amount']",
        "[class*='price']"
    ]
    
    print("🔎 Searching for price element...")
    price_element = None
    
    for selector in css_selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                for elem in elements:
                    text = elem.text.strip()
                    if text and any(char.isdigit() for char in text):
                        print(f"✓ Found with {selector}: {text}")
                        price_element = elem
                        break
            if price_element:
                break
        except:
            continue
    
    if not price_element:
        # Try finding ANY element with price-like text
        all_spans = driver.find_elements(By.TAG_NAME, "span")
        print(f"📊 Found {len(all_spans)} span elements, checking for prices...")
        for span in all_spans:
            text = span.text.strip()
            # Look for EUR or numbers with decimal
            if ("EUR" in text or "€" in text) and any(char.isdigit() for char in text):
                print(f"✓ Found price-like text: {text}")
                price_element = span
                break
    
    if not price_element:
        raise Exception("Could not find price element anywhere on page")
    
    price_text = price_element.text.strip()
    print(f"📝 Raw price text: '{price_text}'")
    
    # Extract number
    # Handle formats like "29.95 EUR", "EUR 29.95", "€29.95", "29.95"
    import re
    numbers = re.findall(r'\d+\.?\d*', price_text)
    if numbers:
        float_price = float(numbers[0])
        print(f"✅ Extracted price: €{float_price}")
    else:
        raise Exception(f"Could not extract number from: {price_text}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    driver.quit()
    exit(1)

finally:
    driver.quit()

# Email alert
if float_price and float_price < TARGET_PRICE:
    try:
        msg = MIMEMultipart()
        msg["Subject"] = f"🛍️ Zara Dress Price Drop - Now €{float_price}!"
        msg["From"] = SENDER_EMAIL
        msg["To"] = RECEIVER_EMAIL
        
        body = f"""
Hi Bridget,

Great news! The Zara Cut-Out Lace Dress price has dropped!

Current Price: €{float_price}
Your Target: €{TARGET_PRICE}
You Save: €{TARGET_PRICE - float_price:.2f}

Product Link:
{PRODUCT_URL}

Happy shopping! 🛍️
        """
        
        msg.attach(MIMEText(body, "plain", "utf-8"))
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(SENDER_EMAIL, APP_PASSWORD)
            smtp.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        
        print(f"✅ Email sent! Price: €{float_price}")
        
    except Exception as e:
        print(f"❌ Email failed: {e}")
else:
    print(f"💤 No alert (€{float_price} >= €{TARGET_PRICE})")
