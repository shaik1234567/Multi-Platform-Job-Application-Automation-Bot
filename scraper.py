"""
Web scraping functions for extracting internship cards and details
"""
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import time

def get_internship_cards(driver, wait):
    """Get all internship cards from the current page"""
    try:
        print("🔍 Looking for internship cards...")
        time.sleep(3)
        
        # Try specific internship card selectors first
        specific_selectors = [
            "div.individual_internship",
            ".internship-card",
            "[data-internship-id]",
            "div.container-fluid.individual_internship"
        ]
        
        cards = []
        for selector in specific_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"✅ Found {len(elements)} cards using selector: {selector}")
                    cards = elements
                    break
            except Exception:
                continue
        
        # If no specific selectors work, try XPath
        if not cards:
            print("🔍 Trying XPath search...")
            xpath_selectors = [
                "//div[contains(@class, 'individual_internship')]",
                "//div[contains(@class, 'internship') and not(contains(@class, 'nav'))]"
            ]
            
            for xpath in xpath_selectors:
                try:
                    elements = driver.find_elements(By.XPATH, xpath)
                    if elements:
                        print(f"✅ Found {len(elements)} cards using XPath")
                        cards = elements
                        break
                except Exception:
                    continue
        
        return cards
        
    except Exception as e:
        print(f"Error getting internship cards: {e}")
        return []

def get_job_description(driver, wait):
    """Scrape job description from internship detail page"""
    try:
        # Common selectors for job description on Internshala
        desc_selectors = [
            ".internship_other_details_container",
            ".detailed_info_container",
            ".internship_details",
            "[data-detail-type='internship_summary']",
            ".detail_view"
        ]
        
        description = ""
        for selector in desc_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    description += element.text + " "
                if description.strip():
                    break
            except:
                continue
        
        return description.strip()
    except Exception as e:
        print(f"Error extracting job description: {e}")
        return ""

def save_debug_page(driver, filename):
    """Save page source for debugging"""
    try:
        from config import DEBUG_DIR
        filepath = f"{DEBUG_DIR}/{filename}"
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print(f"Debug page saved: {filepath}")
    except Exception as e:
        print(f"Error saving debug page: {e}")