"""
Job relevance filtering functions
"""
from config import RELEVANT_KEYWORDS, IRRELEVANT_KEYWORDS, SKILLS_DATABASE

def is_job_relevant(role_title, job_description, category):
    """Check if job is relevant to the target category"""
    # Combine title and description for analysis
    text_to_analyze = f"{role_title} {job_description}".lower()
    
    # Check for irrelevant keywords first
    for irrelevant in IRRELEVANT_KEYWORDS:
        if irrelevant.lower() in text_to_analyze:
            print(f"    ❌ Rejected: Contains irrelevant keyword '{irrelevant}'")
            return False
    
    # Check for relevant keywords
    relevant_count = 0
    found_keywords = []
    
    for keyword in RELEVANT_KEYWORDS.get(category, []):
        if keyword.lower() in text_to_analyze:
            relevant_count += 1
            found_keywords.append(keyword)
    
    # Require at least 1 relevant keyword match
    if relevant_count >= 1:
        print(f"    ✅ Accepted: Found keywords {found_keywords[:3]}")
        return True
    else:
        print(f"    ❌ Rejected: No relevant keywords found for {category}")
        return False

def extract_skills_from_description(description_text, category='data_science'):
    """Extract relevant skills from job description"""
    description_lower = description_text.lower()
    found_skills = set()
    
    # Check skills from database for the specific category
    skills_list = SKILLS_DATABASE.get(category, [])
    
    for skill in skills_list:
        if skill.lower() in description_lower:
            found_skills.add(skill)
    
    return list(found_skills)