# ==================== utils.py ====================
"""
Utility functions for the automation
"""
import time
import re

def sanitize_filename(filename):
    """Remove invalid characters for Windows filenames"""
    filename = filename.replace('\n', ' ').replace('\r', ' ')
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename.strip()[:100]

def parse_stipend(stipend_text):
    """Enhanced stipend parsing to handle various formats"""
    stipend_text = stipend_text.lower().strip()
    
    if 'unpaid' in stipend_text:
        return 0
    
    if any(word in stipend_text for word in ['negotiable', 'performance', 'discussed']):
        return 5000
    
    numbers = re.findall(r'\d+', stipend_text.replace(',', ''))
    if numbers:
        return int(numbers[0])
    
    return 0

def wait_with_message(seconds, message="Waiting"):
    """Wait with progress message"""
    minutes = seconds // 60
    if minutes > 0:
        print(f"{message} {minutes} minutes...")
    time.sleep(seconds)

