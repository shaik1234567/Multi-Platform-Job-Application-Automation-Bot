# ==================== web_driver.py ====================
"""
WebDriver setup and basic browser functions
"""
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

def create_driver():
    """Create and configure Chrome WebDriver"""
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("detach", True)
    
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), 
        options=options
    )
    driver.set_page_load_timeout(60)
    return driver

def create_wait(driver, timeout=25):
    """Create WebDriverWait instance"""
    return WebDriverWait(driver, timeout)
