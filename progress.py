# ==================== progress.py ====================
"""
Progress tracking and logging functions
"""
import json
import csv
import os
from datetime import datetime
from config import PROGRESS_FILE, CSV_FILE, RESUME_LOG_FILE

def load_progress():
    """Load application progress from file"""
    try:
        if os.path.exists(PROGRESS_FILE):
            with open(PROGRESS_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading progress: {e}")
    
    return {
        'applied_urls': [],
        'current_category': 'data_science',
        'category_positions': {
            'data_science': 0,
            'data_analyst': 0,
            'machine_learning': 0
        }
    }

def save_progress(progress_data):
    """Save application progress to file"""
    try:
        with open(PROGRESS_FILE, 'w') as f:
            json.dump(progress_data, f, indent=2)
    except Exception as e:
        print(f"Error saving progress: {e}")

def save_to_csv(data, filename):
    """Save application data to CSV"""
    header = ["timestamp", "company", "role", "category", "stipend", "stipend_text", 
              "skills_matched", "resume_used", "application_status"]
    
    with open(filename, "a", newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=header)
        if f.tell() == 0:
            writer.writeheader()
        for row in data:
            writer.writerow(row)

def log_resume_usage(internship, skills_added, resume_path):
    """Log which resume was used for which application"""
    try:
        log_data = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'company': internship['company'],
            'role': internship['role'],
            'category': internship['category'],
            'skills_found': ', '.join(skills_added) if skills_added else 'None',
            'resume_file': os.path.basename(resume_path)
        }
        
        header = ['timestamp', 'company', 'role', 'category', 'skills_found', 'resume_file']
        
        with open(RESUME_LOG_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=header)
            if f.tell() == 0:
                writer.writeheader()
            writer.writerow(log_data)
            
    except Exception as e:
        print(f"Error logging resume usage: {e}")