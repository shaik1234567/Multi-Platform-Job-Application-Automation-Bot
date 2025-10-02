# ==================== parser.py ====================
"""
Parse internship data from web elements
"""
from selenium.webdriver.common.by import By
import re
from utils import sanitize_filename, parse_stipend
from filters import is_job_relevant

def parse_internship(card, category):
    """Parse internship data from a card element"""
    try:
        # Extract company name
        company = None
        company_selectors = [
            ".company_name", 
            ".company-name", 
            "[class*='company']", 
            ".employer_name",
            ".organization_name"
        ]
        
        for selector in company_selectors:
            try:
                element = card.find_element(By.CSS_SELECTOR, selector)
                company_text = element.text.strip()
                company_text = re.sub(r'\s*actively\s+hiring\s*', '', company_text, flags=re.IGNORECASE)
                if company_text and len(company_text) > 1:
                    company = company_text
                    break
            except:
                continue
        
        # Extract role/job title
        role = None
        role_selectors = [
            ".profile_name", 
            ".profile-name", 
            "[class*='profile']", 
            ".job-title", 
            ".role-name",
            ".position_name",
            ".internship_profile"
        ]
        
        for selector in role_selectors:
            try:
                element = card.find_element(By.CSS_SELECTOR, selector)
                role_text = element.text.strip()
                if role_text and len(role_text) > 2:
                    role = role_text
                    break
            except:
                continue
        
        if not role:
            try:
                link_element = card.find_element(By.CSS_SELECTOR, "a[href*='internship']")
                link_text = link_element.text.strip()
                if link_text and len(link_text) > 2:
                    role = link_text
            except:
                pass
        
        # Extract stipend
        stipend_text = "Not specified"
        stipend_selectors = [
            ".stipend_container", 
            ".stipend", 
            "[class*='stipend']", 
            "[class*='salary']"
        ]
        
        for selector in stipend_selectors:
            try:
                element = card.find_element(By.CSS_SELECTOR, selector)
                stipend_text = element.text.strip()
                if stipend_text:
                    break
            except:
                continue
        
        stipend_value = parse_stipend(stipend_text)
        
        # Extract detail link
        detail_link = None
        link_selectors = [
            "a.view_detail_button", 
            "a[href*='internship/detail']",
            "a[href*='internship']"
        ]
        
        for selector in link_selectors:
            try:
                element = card.find_element(By.CSS_SELECTOR, selector)
                link = element.get_attribute('href')
                if link and 'internship' in link and 'detail' in link:
                    detail_link = link
                    break
            except:
                continue
        
        if not company or not role or not detail_link:
            return None
        
        if not is_job_relevant(role, "", category):
            return None
        
        return {
            'company': sanitize_filename(company), 
            'role': sanitize_filename(role),
            'stipend': stipend_value, 
            'stipend_text': stipend_text,
            'url': detail_link,
            'category': category
        }
        
    except Exception as e:
        return None