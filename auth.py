# ==================== auth.py ====================
"""
Authentication and login functions
"""
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    ElementClickInterceptedException, StaleElementReferenceException
)
import time
from config import EMAIL, PASSWORD

def field_fill(wait, locator, text):
    """Fill a form field with text"""
    el = wait.until(EC.visibility_of_element_located(locator))
    el.clear()
    el.send_keys(text)
    return el

def button_is_enabled(el):
    """Check if button is enabled"""
    return not (el.get_attribute("disabled") or 
                (el.get_attribute("aria-disabled") or "").lower() == "true")

def click_login_safely(driver, wait):
    """Safely click login button with retries"""
    # Try multiple button selectors
    btn_selectors = [
        (By.XPATH, "//button[contains(text(), 'Login')]"),
        (By.XPATH, "//button[@type='submit']"),
        (By.XPATH, "//input[@type='submit']"),
        (By.CSS_SELECTOR, "button[type='submit']"),
        (By.XPATH, "//form//button"),
        (By.ID, "login_submit")
    ]
    
    btn = None
    btn_locator = None
    
    for locator in btn_selectors:
        try:
            btn = wait.until(EC.visibility_of_element_located(locator))
            btn_locator = locator
            break
        except:
            continue
    
    if not btn:
        try:
            form = driver.find_element(By.XPATH, "//form[.//input[@type='password']]")
            driver.execute_script("arguments[0].submit();", form)
            return True
        except Exception:
            return False

    # Wait for button to be enabled
    t0 = time.time()
    while not button_is_enabled(btn) and time.time() - t0 < 8:
        time.sleep(0.15)
    
    # Try clicking
    try:
        btn.click()
        return True
    except:
        try:
            driver.execute_script("arguments[0].click();", btn)
            return True
        except:
            return False

def login_to_internshala(driver, wait):
    """Complete login process"""
    print("Starting login process...")
    driver.get("https://internshala.com/login/user")
    
    email_locator = (By.XPATH, "//form//label[contains(., 'Email')]/following::input[1]")
    pwd_locator = (By.XPATH, "//form//input[@type='password']")
    
    field_fill(wait, email_locator, EMAIL)
    pwd_el = field_fill(wait, pwd_locator, PASSWORD)
    time.sleep(0.4)
    
    clicked = click_login_safely(driver, wait)
    time.sleep(1.0)
    
    error_nodes = driver.find_elements(
        By.XPATH, 
        "//*[contains(translate(., 'CAPTCHA', 'captcha'),'captcha')][not(self::script)]"
    )
    still_on_login = "login" in driver.current_url.lower()
    
    if (not clicked or error_nodes) and still_on_login:
        time.sleep(1.5)
        clicked = click_login_safely(driver, wait)
        if not clicked:
            try:
                pwd_el.submit()
            except Exception:
                pass
    
    wait.until(EC.url_contains("/student"))
    print("Logged in successfully!")
    return True