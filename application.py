"""
Application submission functions
"""
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import time
import os
from config import RESUME_PATHS
from scraper import get_job_description
from filters import extract_skills_from_description, is_job_relevant
from progress import log_resume_usage

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
        # Wait for form to load
        time.sleep(2)
        
        # Common question field selectors for Internshala
        # TODO: Need to update these with actual Internshala selectors
        question_patterns = [
            ("why", "why_join"),
            ("about", "about_yourself"),
            ("suitable", "suitable_for_role"),
            ("cover", "cover_letter"),
            ("letter", "cover_letter")
        ]
        
        filled_count = 0
        for keyword, answer_key in question_patterns:
            try:
                # Look for text areas with specific patterns
                fields = driver.find_elements(
                    By.XPATH, 
                    f"//textarea[contains(@placeholder, '{keyword}') or contains(@name, '{keyword}') or contains(@id, '{keyword}')] | //input[contains(@placeholder, '{keyword}') or contains(@name, '{keyword}')]"
                )
                
                for field in fields:
                    if field.is_displayed() and field.is_enabled():
                        field.clear()
                        field.send_keys(answers.get(answer_key, ""))
                        filled_count += 1
                        time.sleep(1)
                        break
            except Exception:
                continue
        
        return filled_count > 0
    except Exception as e:
        print(f"    Error filling form: {e}")
        return False

def apply_to_internship(driver, wait, internship):
    """Apply to a single internship"""
    print(f"  Navigating to: {internship['company']} - {internship['role']}")
    driver.get(internship['url'])
    time.sleep(3)
    
    applied = False
    job_skills = []
    
    try:
        # Get job description for detailed relevance check
        job_description = get_job_description(driver, wait)
        if job_description:
            # Final relevance check with full description
            if not is_job_relevant(internship['role'], job_description, internship['category']):
                print(f"    ❌ Failed detailed relevance check")
                return False, []
            
            # Extract skills
            job_skills = extract_skills_from_description(job_description, internship['category'])
            if job_skills:
                print(f"    📋 Skills found: {', '.join(job_skills[:5])}")
        
        # Select appropriate resume based on category
        resume_path = RESUME_PATHS.get(internship['category'], RESUME_PATHS['data_science'])
        
        if not os.path.exists(resume_path):
            print(f"    ❌ Resume not found: {resume_path}")
            return False, []
        
        # Click Apply button
        apply_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Apply now')]"))
        )
        apply_btn.click()
        time.sleep(3)
        
        # Upload resume
        try:
            upload_input = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
            )
            upload_input.send_keys(resume_path)
            print(f"    📎 Resume uploaded: {os.path.basename(resume_path)}")
            time.sleep(2)
        except Exception as e:
            print(f"    ⚠️ Resume upload issue: {e}")
        
        # Generate and fill application answers
        answers = generate_application_answers(internship['company'], internship['role'], job_skills)
        if fill_application_form(driver, wait, answers):
            print(f"    ✏️ Filled application form")
        else:
            print(f"    ⚠️ Could not fill all form fields")
        
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
                print(f"    ✅ Application submitted!")
                break
            except Exception:
                continue
        
        # Log resume usage
        if applied:
            log_resume_usage(internship, job_skills, resume_path)
        
    except Exception as e:
        print(f"    ❌ Application failed: {e}")
    
    return applied, job_skills