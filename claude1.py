from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    ElementClickInterceptedException, StaleElementReferenceException, TimeoutException, NoSuchElementException
)
from webdriver_manager.chrome import ChromeDriverManager
import time
import csv
import re
import os
from datetime import datetime
import PyPDF2
from docx import Document
from docx.shared import Inches
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from io import BytesIO

# Configuration
EMAIL = "shaikshivaji2004@gmail.com"
PASSWORD = "b@NymuFRDfY28WX"
BASE_RESUME_PATH = r"C:\Users\shaik\automation\resume.pdf"
CSV_FILE = "applied_internships_detailed.csv"
RESUME_LOG_FILE = "resume_customization_log.csv"
CUSTOMIZED_RESUME_DIR = "customized_resumes"

ROLE_LINKS = [
    "https://internshala.com/internships/keywords-data-science/",
    "https://internshala.com/internships/keywords-data-analyst/",
    "https://internshala.com/internships/keywords-machine-learning/"
]
MIN_STIPEND = 5000

# Skills database for matching
SKILLS_DATABASE = {
    'data_science': [
        'python', 'r', 'sql', 'machine learning', 'deep learning', 'statistics', 
        'pandas', 'numpy', 'scikit-learn', 'tensorflow', 'pytorch', 'keras',
        'data visualization', 'matplotlib', 'seaborn', 'plotly', 'tableau',
        'jupyter', 'git', 'docker', 'aws', 'azure', 'spark', 'hadoop'
    ],
    'data_analyst': [
        'excel', 'sql', 'python', 'r', 'tableau', 'power bi', 'statistics',
        'data visualization', 'pandas', 'numpy', 'matplotlib', 'seaborn',
        'google analytics', 'looker', 'business intelligence', 'etl', 'dashboards'
    ],
    'machine_learning': [
        'python', 'tensorflow', 'pytorch', 'scikit-learn', 'keras', 'opencv',
        'nlp', 'computer vision', 'deep learning', 'neural networks', 'algorithms',
        'feature engineering', 'model deployment', 'mlops', 'docker', 'kubernetes'
    ]
}

# Create directories
os.makedirs(CUSTOMIZED_RESUME_DIR, exist_ok=True)

def create_driver():
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("detach", True)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.set_page_load_timeout(60)
    return driver

def field_fill(wait, locator, text):
    el = wait.until(EC.visibility_of_element_located(locator))
    el.clear()
    el.send_keys(text)
    return el

def button_is_enabled(el):
    return not (el.get_attribute("disabled") or (el.get_attribute("aria-disabled") or "").lower() == "true")

def click_login_safely(driver, wait):
    btn_locator = (By.XPATH, "//form//button[contains(., 'Login') or @type='submit']")
    wait.until(EC.presence_of_element_located(btn_locator))
    btn = wait.until(EC.visibility_of_element_located(btn_locator))

    t0 = time.time()
    while not button_is_enabled(btn) and time.time() - t0 < 8:
        time.sleep(0.15)
        try:
            btn = driver.find_element(*btn_locator)
        except StaleElementReferenceException:
            btn = driver.find_element(*btn_locator)

    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
    try:
        wait.until(EC.element_to_be_clickable(btn_locator))
        btn.click()
        return True
    except (ElementClickInterceptedException, StaleElementReferenceException):
        try:
            btn = wait.until(EC.visibility_of_element_located(btn_locator))
            driver.execute_script("arguments[0].click();", btn)
            return True
        except Exception:
            try:
                form = driver.find_element(By.XPATH, "//form[.//input[@type='password']]")
                driver.execute_script("arguments[0].submit();", form)
                return True
            except Exception:
                return False

def parse_stipend(stipend_text):
    """Enhanced stipend parsing to handle various formats"""
    stipend_text = stipend_text.lower().strip()
    
    if 'unpaid' in stipend_text:
        return 0
    
    if any(word in stipend_text for word in ['negotiable', 'performance', 'discussed']):
        return MIN_STIPEND  # Consider as meeting minimum requirement
    
    # Extract numbers from stipend text
    numbers = re.findall(r'\d+', stipend_text.replace(',', ''))
    if numbers:
        # If range (e.g., 5000-8000), take the minimum
        return int(numbers[0])
    
    return 0

def extract_skills_from_description(description_text):
    """Extract relevant skills from job description"""
    description_lower = description_text.lower()
    found_skills = set()
    
    # Check all skills from database
    for category, skills in SKILLS_DATABASE.items():
        for skill in skills:
            if skill.lower() in description_lower:
                found_skills.add(skill)
    
    return list(found_skills)

def get_job_description(driver, wait):
    """Scrape job description from internship page"""
    try:
        # Common selectors for job description on Internshala
        desc_selectors = [
            ".internship_other_details_container",
            ".detailed_info_container",
            ".internship_details",
            "[data-detail-type='internship_summary']"
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

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF resume"""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return ""

def customize_resume(base_resume_text, job_skills, company_name, role_name):
    """Customize resume by enhancing skills section"""
    try:
        # Create a simple customized resume text
        lines = base_resume_text.split('\n')
        customized_lines = []
        skills_section_found = False
        
        for line in lines:
            customized_lines.append(line)
            
            # Look for skills section and add relevant skills
            if any(keyword in line.lower() for keyword in ['skills', 'technical', 'competencies']):
                skills_section_found = True
                if job_skills:
                    customized_lines.append(f"Relevant Skills for {role_name}: {', '.join(job_skills[:8])}")
        
        # If no skills section found, add one
        if not skills_section_found and job_skills:
            customized_lines.extend([
                "",
                "RELEVANT TECHNICAL SKILLS:",
                f"{', '.join(job_skills[:10])}"
            ])
        
        return '\n'.join(customized_lines)
    except Exception as e:
        print(f"Error customizing resume: {e}")
        return base_resume_text

def create_pdf_from_text(text, output_path):
    """Convert text to PDF using reportlab"""
    try:
        doc = SimpleDocTemplate(output_path, pagesize=letter, 
                              topMargin=0.5*inch, bottomMargin=0.5*inch,
                              leftMargin=0.75*inch, rightMargin=0.75*inch)
        
        styles = getSampleStyleSheet()
        story = []
        
        # Create custom styles
        title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], 
                                   fontSize=14, spaceAfter=12, textColor='black')
        normal_style = ParagraphStyle('CustomNormal', parent=styles['Normal'], 
                                    fontSize=10, spaceAfter=6)
        skill_style = ParagraphStyle('SkillStyle', parent=styles['Normal'], 
                                   fontSize=10, spaceAfter=6, leftIndent=0.25*inch,
                                   backColor='lightgrey')
        
        # Split text into lines and process
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                story.append(Spacer(1, 0.1*inch))
                continue
            
            # Check if line is a header/title (all caps or contains keywords)
            if (line.isupper() and len(line) > 3) or any(word in line.upper() for word in ['SKILLS', 'EXPERIENCE', 'EDUCATION', 'PROJECTS']):
                story.append(Paragraph(line, title_style))
            elif 'Relevant Skills for' in line:
                story.append(Paragraph(line, skill_style))
            else:
                story.append(Paragraph(line, normal_style))
        
        # Build PDF
        doc.build(story)
        return True
        
    except Exception as e:
        print(f"Error creating PDF with reportlab: {e}")
        return False

def debug_page_structure(driver):
    """Debug function to understand current page structure"""
    try:
        print("🔍 DEBUG: Analyzing page structure...")
        
        # Check if we're on the right page
        current_url = driver.current_url
        print(f"Current URL: {current_url}")
        
        # Wait for page to load properly
        time.sleep(2)
        
        # Look for specific internship content areas (avoid navigation)
        content_areas = [
            "#internship_list_container",
            ".search-results", 
            "[class*='results']",
            ".main-content",
            "#main"
        ]
        
        main_content = None
        for area in content_areas:
            try:
                main_content = driver.find_element(By.CSS_SELECTOR, area)
                if main_content:
                    print(f"✅ Found main content area: {area}")
                    break
            except:
                continue
        
        if not main_content:
            main_content = driver.find_element(By.TAG_NAME, "body")
        
        # Look for actual internship cards within main content
        potential_cards = main_content.find_elements(By.XPATH, ".//*[contains(@class, 'internship') and not(contains(@class, 'nav')) and not(contains(@class, 'menu')) and not(contains(@class, 'dropdown'))]")
        print(f"Found {len(potential_cards)} potential internship elements (excluding nav)")
        
        # Also try looking for cards with company info
        company_cards = driver.find_elements(By.XPATH, "//*[contains(@class, 'company') or contains(text(), 'Apply') or contains(@class, 'job-card')]")
        print(f"Found {len(company_cards)} elements with company/apply/job-card classes")
        
        # Sample first few elements to understand structure
        cards_to_check = potential_cards if potential_cards else company_cards[:5]
        
        if cards_to_check:
            for i, card in enumerate(cards_to_check[:3]):
                try:
                    print(f"\n--- Card {i+1} Structure ---")
                    print(f"Tag: {card.tag_name}")
                    print(f"Classes: {card.get_attribute('class')}")
                    text_preview = card.text.strip()[:150]
                    print(f"Text preview: {text_preview}...")
                    
                    # Look for apply buttons or internship links
                    apply_buttons = card.find_elements(By.XPATH, ".//button[contains(text(), 'Apply')] | .//a[contains(text(), 'Apply')] | .//a[contains(@href, 'internship')]")
                    print(f"Apply buttons/links found: {len(apply_buttons)}")
                    
                    for btn in apply_buttons[:2]:
                        if btn.tag_name.lower() == 'a':
                            href = btn.get_attribute('href')
                            print(f"  - Link: {btn.text[:30]} -> {href}")
                        else:
                            print(f"  - Button: {btn.text[:30]}")
                    
                except Exception as e:
                    print(f"Error analyzing card {i+1}: {e}")
        
        return len(cards_to_check) > 0
        
    except Exception as e:
        print(f"Debug error: {e}")
        return False

def get_internship_cards(driver, wait):
    try:
        print("🔍 Looking for internship cards...")
        
        # Wait for page content to load
        time.sleep(3)
        
        # Try specific internship card selectors first
        specific_selectors = [
            "div.individual_internship",
            ".internship-card",
            "[data-internship-id]",
            ".job-card",
            ".listing-item"
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
        
        # If no specific selectors work, try broader search
        if not cards:
            print("🔍 Trying broader search...")
            
            # Look for elements that contain both company name and apply button
            xpath_selectors = [
                "//div[contains(@class, 'internship') and not(contains(@class, 'nav')) and .//a[contains(@href, 'internship')]]",
                "//div[.//button[contains(text(), 'Apply')] or .//a[contains(text(), 'Apply')]]",
                "//article[contains(@class, 'job') or contains(@class, 'internship')]",
                "//div[contains(@class, 'card') and (.//span[contains(@class, 'company')] or .//div[contains(@class, 'company')])]"
            ]
            
            for xpath in xpath_selectors:
                try:
                    elements = driver.find_elements(By.XPATH, xpath)
                    if elements:
                        print(f"✅ Found {len(elements)} cards using XPath: {xpath}")
                        cards = elements
                        break
                except Exception:
                    continue
        
        # Final fallback - look for any container with internship-related content
        if not cards:
            print("🔍 Final fallback search...")
            try:
                # Look for containers that have both text content and links
                all_divs = driver.find_elements(By.TAG_NAME, "div")
                potential_cards = []
                
                for div in all_divs:
                    try:
                        text = div.text.strip()
                        links = div.find_elements(By.TAG_NAME, "a")
                        
                        # Check if this div looks like an internship card
                        if (len(text) > 50 and len(text) < 500 and  # Reasonable text length
                            links and  # Has links
                            any(keyword in text.lower() for keyword in ['apply', 'internship', 'company', 'stipend', 'salary']) and
                            not any(nav_word in div.get_attribute('class').lower() for nav_word in ['nav', 'menu', 'header', 'footer'])):
                            potential_cards.append(div)
                            
                        if len(potential_cards) >= 20:  # Don't get too many
                            break
                            
                    except Exception:
                        continue
                
                if potential_cards:
                    cards = potential_cards
                    print(f"✅ Found {len(cards)} potential cards using fallback method")
            
            except Exception as e:
                print(f"Fallback search failed: {e}")
        
        return cards[:20] if cards else []  # Limit to reasonable number
        
    except Exception as e:
        print(f"Error getting internship cards: {e}")
        return []
    try:
        # Multiple selectors for internship cards
        card_selectors = [
            "div.individual_internship",
            ".internship_meta",
            "[class*='internship']",
            ".job-card",
            ".listing-card",
            "[data-internship-id]"
        ]
        
        cards = []
        for selector in card_selectors:
            try:
                wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector)))
                cards = driver.find_elements(By.CSS_SELECTOR, selector)
                if cards:
                    print(f"✅ Found {len(cards)} internship cards using selector: {selector}")
                    break
            except Exception:
                continue
        
        if not cards:
            # Try alternative approach - look for any div containing internship info
            try:
                cards = driver.find_elements(By.XPATH, "//div[contains(@class, 'internship') or contains(@id, 'internship')]")
                if cards:
                    print(f"✅ Found {len(cards)} cards using XPath fallback")
            except Exception:
                pass
        
        return cards
    except Exception as e:
        print(f"Error getting internship cards: {e}")
        return []

def parse_internship(card):
    try:
        # Multiple selectors for company name
        company = None
        company_selectors = [".company_name", ".company-name", "[class*='company']", "h3", ".heading-6"]
        for selector in company_selectors:
            try:
                company = card.find_element(By.CSS_SELECTOR, selector).text.strip()
                if company:
                    break
            except:
                continue
        
        # Multiple selectors for role/profile name
        role = None
        role_selectors = [".profile_name", ".profile-name", "[class*='profile']", ".job-title", ".role-name", "h4", ".heading-4", "a[href*='internship']"]
        for selector in role_selectors:
            try:
                role = card.find_element(By.CSS_SELECTOR, selector).text.strip()
                if role and len(role) > 2:  # Ensure it's not just whitespace
                    break
            except:
                continue
        
        # Multiple selectors for stipend
        stipend_text = "Not specified"
        stipend_selectors = [".stipend_container", ".stipend", "[class*='stipend']", "[class*='salary']", ".pay"]
        for selector in stipend_selectors:
            try:
                stipend_element = card.find_element(By.CSS_SELECTOR, selector)
                stipend_text = stipend_element.text.strip()
                if stipend_text:
                    break
            except:
                continue
        
        stipend_value = parse_stipend(stipend_text)
        
        # Multiple selectors for detail link
        detail_link = None
        link_selectors = ["a.view_detail_button", "a[href*='internship']", "a[class*='detail']", "a[class*='view']"]
        for selector in link_selectors:
            try:
                detail_link = card.find_element(By.CSS_SELECTOR, selector).get_attribute('href')
                if detail_link:
                    break
            except:
                continue
        
        # If we couldn't find essential info, skip this card
        if not company or not role or not detail_link:
            print(f"⚠️ Missing essential data - Company: {company}, Role: {role}, Link: {bool(detail_link)}")
            return None
        
        return {
            'company': company, 
            'role': role,
            'stipend': stipend_value, 
            'stipend_text': stipend_text,
            'url': detail_link
        }
    except Exception as e:
        print(f"Error parsing internship: {e}")
        return None

def generate_application_answers(company_name, role_name, skills_list):
    """Generate template answers for common application questions"""
    answers = {
        'why_join': f"I am excited to join {company_name} because of your reputation for innovation in {role_name}. Your company's commitment to excellence aligns with my career goals, and I believe I can contribute meaningfully to your team's success.",
        
        'about_yourself': f"I am a passionate and dedicated professional with strong technical skills in {', '.join(skills_list[:5]) if skills_list else 'data analysis and problem-solving'}. I have hands-on experience with various projects and am eager to apply my knowledge in a real-world environment.",
        
        'suitable_for_role': f"My technical expertise in {', '.join(skills_list[:3]) if skills_list else 'relevant technologies'} makes me well-suited for this {role_name} position. I have practical experience with data analysis, problem-solving, and am committed to delivering high-quality results.",
        
        'cover_letter': f"Dear {company_name} Team,\n\nI am writing to express my interest in the {role_name} internship. With my background in {', '.join(skills_list[:4]) if skills_list else 'data analysis'}, I am excited about the opportunity to contribute to your organization while gaining valuable industry experience.\n\nThank you for considering my application.\n\nBest regards"
    }
    return answers

def fill_application_form(driver, wait, answers):
    """Fill application form with generated answers"""
    try:
        # Common question field selectors
        question_fields = [
            ("why", "why_join"),
            ("about", "about_yourself"),
            ("suitable", "suitable_for_role"),
            ("cover", "cover_letter"),
            ("letter", "cover_letter")
        ]
        
        for keyword, answer_key in question_fields:
            try:
                # Look for text areas or input fields containing the keyword
                fields = driver.find_elements(By.XPATH, f"//textarea[contains(@placeholder, '{keyword}') or contains(@name, '{keyword}')] | //input[contains(@placeholder, '{keyword}') or contains(@name, '{keyword}')]")
                
                for field in fields:
                    if field.is_displayed() and field.is_enabled():
                        field.clear()
                        field.send_keys(answers.get(answer_key, ""))
                        time.sleep(1)
                        break
            except Exception:
                continue
        
        return True
    except Exception as e:
        print(f"Error filling application form: {e}")
        return False

def apply_to_internship(driver, wait, internship, base_resume_text):
    """Enhanced application process with resume customization"""
    print(f"🔍 Getting job details for {internship['company']} - {internship['role']}")
    driver.get(internship['url'])
    time.sleep(3)
    
    applied = False
    customized_resume_path = BASE_RESUME_PATH
    job_skills = []
    answers_used = {}
    
    try:
        # Extract job description and skills
        job_description = get_job_description(driver, wait)
        if job_description:
            job_skills = extract_skills_from_description(job_description)
            print(f"📋 Found skills: {job_skills[:5]}...")
            
            if job_skills:
                # Customize resume
                customized_text = customize_resume(base_resume_text, job_skills, internship['company'], internship['role'])
                
                # Create customized resume file
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                customized_resume_path = os.path.join(CUSTOMIZED_RESUME_DIR, f"{internship['company']}_{internship['role']}_{timestamp}.pdf")
                
                if create_pdf_from_text(customized_text, customized_resume_path):
                    print(f"📄 Created customized resume: {customized_resume_path}")
                else:
                    customized_resume_path = BASE_RESUME_PATH
                    print("⚠️ Using base resume (customization failed)")
        
        # Generate application answers
        answers_used = generate_application_answers(internship['company'], internship['role'], job_skills)
        
        # Start application process
        apply_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Apply now')]")))
        apply_btn.click()
        time.sleep(3)
        
        # Upload resume
        try:
            upload_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']")))
            upload_input.send_keys(customized_resume_path)
            time.sleep(2)
            print(f"📎 Uploaded resume: {os.path.basename(customized_resume_path)}")
        except Exception as e:
            print(f"⚠️ Resume upload issue: {e}")
        
        # Fill application questions
        if fill_application_form(driver, wait, answers_used):
            print("✏️ Filled application questions")
        
        # Submit application
        submit_selectors = [
            "//button[contains(text(),'Submit application')]",
            "//button[contains(text(),'Submit')]",
            "//input[@type='submit']"
        ]
        
        for selector in submit_selectors:
            try:
                submit_btn = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                submit_btn.click()
                applied = True
                print(f"✅ Application submitted successfully!")
                break
            except Exception:
                continue
        
        # Log resume customization
        log_resume_customization(internship, job_skills, customized_resume_path, answers_used)
        
    except Exception as e:
        print(f"❌ Could not apply to {internship['company']} - {internship['role']}: {e}")
    
    return applied, job_skills, customized_resume_path, answers_used

def log_resume_customization(internship, skills_added, resume_path, answers_used):
    """Log resume customization details"""
    try:
        log_data = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'company': internship['company'],
            'role': internship['role'],
            'skills_added': ', '.join(skills_added) if skills_added else 'None',
            'resume_file': os.path.basename(resume_path),
            'answers_provided': 'Yes' if answers_used else 'No'
        }
        
        header = ['timestamp', 'company', 'role', 'skills_added', 'resume_file', 'answers_provided']
        
        with open(RESUME_LOG_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=header)
            if f.tell() == 0:
                writer.writeheader()
            writer.writerow(log_data)
            
    except Exception as e:
        print(f"Error logging resume customization: {e}")

def save_to_csv(data, filename):
    """Enhanced CSV logging with more details"""
    header = ["timestamp", "company", "role", "stipend", "stipend_text", "skills_matched", "resume_used", "application_status"]
    
    with open(filename, "a", newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=header)
        if f.tell() == 0:
            writer.writeheader()
        for row in data:
            writer.writerow(row)

def main():
    driver = create_driver()
    wait = WebDriverWait(driver, 25)
    
    try:
        # Extract base resume text for customization
        print("📖 Reading base resume...")
        base_resume_text = extract_text_from_pdf(BASE_RESUME_PATH)
        if not base_resume_text:
            print("⚠️ Could not read base resume. Using file path only.")
        
        # Login process
        print("🔐 Starting login process...")
        driver.get("https://internshala.com/login/user")
        
        email_locator = (By.XPATH, "//form//label[contains(., 'Email')]/following::input[1]")
        pwd_locator = (By.XPATH, "//form//input[@type='password']")
        
        field_fill(wait, email_locator, EMAIL)
        pwd_el = field_fill(wait, pwd_locator, PASSWORD)
        time.sleep(0.4)
        
        clicked = click_login_safely(driver, wait)
        time.sleep(1.0)
        
        # Handle potential CAPTCHA or login issues
        error_nodes = driver.find_elements(By.XPATH, "//*[contains(translate(., 'CAPTCHA', 'captcha'),'captcha')][not(self::script)]")
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
        print("✅ Logged in successfully!")
        
        # Auto-apply process
        applied_internships = []
        total_found = 0
        
        for url in ROLE_LINKS:
            print(f"\n🔍 Searching internships at: {url}")
            driver.get(url)
            time.sleep(5)  # Increased wait time
            
            # Debug page structure first
            debug_page_structure(driver)
            
            internship_cards = get_internship_cards(driver, wait)
            total_found += len(internship_cards)
            print(f"Found {len(internship_cards)} internships")
            
            if not internship_cards:
                print("❌ No internship cards found! Saving page source for debugging...")
                with open(f"debug_page_{url.split('/')[-1]}.html", "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                print(f"Page source saved as debug_page_{url.split('/')[-1]}.html")
                continue
            
            for card in internship_cards:
                internship = parse_internship(card)
                
                if internship and internship["stipend"] >= MIN_STIPEND:
                    print(f"\n🎯 Target: {internship['company']} - {internship['role']} (Stipend: {internship['stipend_text']})")
                    
                    success, skills_matched, resume_used, answers = apply_to_internship(
                        driver, wait, internship, base_resume_text
                    )
                    
                    # Log application
                    log_entry = {
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'company': internship['company'],
                        'role': internship['role'],
                        'stipend': internship['stipend'],
                        'stipend_text': internship['stipend_text'],
                        'skills_matched': ', '.join(skills_matched) if skills_matched else 'None',
                        'resume_used': os.path.basename(resume_used),
                        'application_status': 'Applied' if success else 'Failed'
                    }
                    
                    applied_internships.append(log_entry)
                    save_to_csv([log_entry], CSV_FILE)
                    
                    if success:
                        print(f"✅ Successfully applied!")
                    else:
                        print(f"❌ Application failed")
                    
                    time.sleep(3)  # Respectful delay
                    
                else:
                    if internship:
                        print(f"⏭️ Skipping {internship['company']} - {internship['role']} (Stipend: {internship.get('stipend_text', 'Unknown')})")
        
        # Final summary
        successful_applications = len([app for app in applied_internships if app['application_status'] == 'Applied'])
        print(f"\n📊 SUMMARY:")
        print(f"Total internships found: {total_found}")
        print(f"Applications attempted: {len(applied_internships)}")
        print(f"Successful applications: {successful_applications}")
        print(f"📁 Detailed logs saved in: {CSV_FILE}")
        print(f"📁 Resume logs saved in: {RESUME_LOG_FILE}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        try:
            print(f"Current URL: {driver.current_url}")
            with open("internshala_debug.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            print("Debug info saved to internshala_debug.html")
        except Exception:
            pass

if __name__ == "__main__":
    main()