import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import time

# Email credentials from environment variables (GitHub Secrets)
SENDER_EMAIL = os.environ.get()
APP_PASSWORD = os.environ.get()
RECEIVER_EMAIL = os.environ.get()

# Configuration
TARGET_PRICE = 31
PRODUCT_URL = "https://www.zara.com/ng/en/cut-out-lace-dress-p01067002.html?v1=495703199"

# Chrome options for GitHub Actions (headless mode)
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run in background (required for GitHub Actions)
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920,1080")

# Initialize driver with webdriver-manager (auto-downloads ChromeDriver)
driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=chrome_options
)

try:
    print("🔍 Checking Zara dress price...")
    driver.get(PRODUCT_URL)
    
    # Wait for page to load
    time.sleep(5)
    
    # Get price
    price_of_dress = driver.find_element(
        By.XPATH, 
        value='//*[@id="main"]/div/div/div/div/div[1]/div[2]/div/div[1]/div[2]/div/span/span/span/div/span'
    )
    
    price = price_of_dress.text.split()[0]
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
