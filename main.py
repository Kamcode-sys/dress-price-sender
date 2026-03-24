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

# Email credentials from environment variables
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
APP_PASSWORD = os.environ.get("APP_PASSWORD")
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL")

# Configuration
TARGET_PRICE = 26
PRODUCT_URL = "https://www.zara.com/ng/en/cut-out-lace-dress-p01067002.html?v1=495703199"

# Chrome options for GitHub Actions
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36")

# Initialize driver
driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=chrome_options
)

try:
    print("🔍 Checking Zara dress price...")
    driver.get(PRODUCT_URL)
    
    # Wait longer for page to load
    time.sleep(10)
    
    # Try multiple selectors
    price_element = None
    selectors = [
        (By.CSS_SELECTOR, "span.money-amount__main"),
        (By.CSS_SELECTOR, ".price__amount"),
        (By.CSS_SELECTOR, "span[class*='price']"),
        (By.XPATH, "//span[contains(@class, 'money-amount')]"),
        (By.XPATH, "//*[@id='main']/div/div/div/div/div[1]/div[2]/div/div[1]/div[2]/div/span/span/span/div/span"),
    ]
    
    for by, selector in selectors:
        try:
            print(f"Trying selector: {selector}")
            price_element = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((by, selector))
            )
            print(f"✓ Found price with: {selector}")
            break
        except:
            continue
    
    if not price_element:
        # Save page source for debugging
        with open("zara_page.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print("❌ Could not find price element. Page source saved.")
        raise Exception("Price element not found")
    
    price_text = price_element.text
    print(f"Found price text: {price_text}")
    
    # Extract numeric value
    price = price_text.split()[0].replace("EUR", "").replace("€", "").strip()
    float_price = float(price)
    
    print(f"✓ Current price: €{float_price}")
    print(f"✓ Target price: €{TARGET_PRICE}")
    
except Exception as e:
    print(f"❌ Error fetching price: {e}")
    driver.quit()
    exit(1)

finally:
    driver.quit()

# Send email if price drops below target
if float_price < TARGET_PRICE:
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
You Save: €{TARGET_PRICE - float_price}

Grab it now before the price goes back up!

Product Link:
{PRODUCT_URL}

Happy shopping! 🛍️
        """
        
        msg.attach(MIMEText(body, "plain", "utf-8"))
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(SENDER_EMAIL, APP_PASSWORD)
            smtp.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        
        print(f"✅ Price alert sent! Dress is now €{float_price}")
        
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        exit(1)
else:
    print(f"💤 Price still above target (€{float_price} >= €{TARGET_PRICE})")
    print("No alert sent.")
