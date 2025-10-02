"""
Main execution file for Internshala automation
"""
import time
from datetime import datetime

# Import all modules
from config import ROLE_CATEGORIES, MIN_STIPEND, BATCH_SIZE, CATEGORY_DELAY, APPLICATION_DELAY
from web_driver import create_driver, create_wait
from auth import login_to_internshala
from scraper import get_internship_cards, save_debug_page
from parser import parse_internship
from application import apply_to_internship
from progress import load_progress, save_progress, save_to_csv
from utils import wait_with_message

def collect_all_internships(driver, wait, progress_data):
    """Collect all relevant internships from all categories"""
    all_internships = {
        'data_science': [],
        'data_analyst': [],
        'machine_learning': []
    }
    
    processed_urls = set(progress_data.get('applied_urls', []))
    
    for category, url in ROLE_CATEGORIES.items():
        print(f"\n{'='*60}")
        print(f"🔍 Collecting {category.replace('_', ' ').title()} internships...")
        print(f"{'='*60}")
        
        driver.get(url)
        time.sleep(5)
        
        # Get all internship cards
        cards = get_internship_cards(driver, wait)
        print(f"Found {len(cards)} potential cards")
        
        if not cards:
            print(f"⚠️ No cards found, saving debug page...")
            save_debug_page(driver, f"debug_{category}.html")
            continue
        
        # Parse each card
        valid_count = 0
        for i, card in enumerate(cards):
            try:
                print(f"  Card {i+1}/{len(cards)}", end=" - ")
                internship = parse_internship(card, category)
                
                if internship:
                    # Skip if already applied
                    if internship['url'] in processed_urls:
                        print(f"Already applied")
                        continue
                    
                    # Check stipend requirement
                    if internship['stipend'] >= MIN_STIPEND:
                        all_internships[category].append(internship)
                        valid_count += 1
                        print(f"✅ {internship['company']} - {internship['role']} (₹{internship['stipend']})")
                    else:
                        print(f"Low stipend (₹{internship['stipend']})")
                else:
                    print(f"Skipped")
                
                time.sleep(0.5)
                
            except Exception as e:
                print(f"Error: {e}")
        
        print(f"✅ Found {valid_count} valid {category} internships")
    
    return all_internships

def display_summary_and_confirm(all_internships):
    """Display internship summary and ask for confirmation"""
    print("\n" + "="*60)
    print("📋 INTERNSHIP SUMMARY")
    print("="*60)
    
    total_count = 0
    for category, internships in all_internships.items():
        if internships:
            category_name = category.replace('_', ' ').title()
            print(f"\n{category_name} ({len(internships)} positions):")
            
            for i, internship in enumerate(internships[:10], 1):
                stipend_display = f"₹{internship['stipend']}" if internship['stipend'] > 0 else internship['stipend_text']
                print(f"  {i}. {internship['company']} - {internship['role']} ({stipend_display})")
            
            if len(internships) > 10:
                print(f"    ... and {len(internships) - 10} more")
            
            total_count += len(internships)
    
    print(f"\n📊 Total Internships: {total_count}")
    print("="*60)
    
    if total_count == 0:
        print("No relevant internships found matching your criteria.")
        return False
    
    user_input = input("\n🚀 Proceed with round-robin applications? (y/n): ").strip().lower()
    return user_input == 'y'

def process_round_robin(driver, wait, all_internships, progress_data):
    """Process applications in round-robin fashion"""
    positions = progress_data.get('category_positions', {
        'data_science': 0,
        'data_analyst': 0,
        'machine_learning': 0
    })
    
    total_attempted = 0
    total_successful = 0
    
    print("\n" + "="*60)
    print("🚀 STARTING ROUND-ROBIN APPLICATION PROCESS")
    print("="*60)
    
    # Continue until all categories exhausted
    while any(positions[cat] < len(all_internships[cat]) for cat in positions.keys()):
        
        for category in ['data_science', 'data_analyst', 'machine_learning']:
            current_pos = positions[category]
            available = all_internships[category]
            
            # Skip if category exhausted
            if current_pos >= len(available):
                continue
            
            batch_end = min(current_pos + BATCH_SIZE, len(available))
            batch_size = batch_end - current_pos
            
            print(f"\n{'='*60}")
            print(f"🎯 {category.replace('_', ' ').title().upper()} - Round {current_pos//BATCH_SIZE + 1}")
            print(f"Processing {batch_size} applications ({current_pos+1} to {batch_end} of {len(available)})")
            print(f"{'='*60}")
            
            # Process batch
            for i in range(current_pos, batch_end):
                internship = available[i]
                print(f"\n[{i+1}/{len(available)}] Applying to: {internship['company']} - {internship['role']}")
                
                success, skills = apply_to_internship(driver, wait, internship)
                
                # Update progress
                progress_data['applied_urls'].append(internship['url'])
                
                # Log application
                log_entry = {
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'company': internship['company'],
                    'role': internship['role'],
                    'category': category,
                    'stipend': internship['stipend'],
                    'stipend_text': internship['stipend_text'],
                    'skills_matched': ', '.join(skills) if skills else 'None',
                    'resume_used': f"resume_{category.split('_')[0]}.pdf",
                    'application_status': 'Applied' if success else 'Failed'
                }
                
                save_to_csv([log_entry], "applied_internships_detailed.csv")
                
                if success:
                    total_successful += 1
                
                total_attempted += 1
                time.sleep(APPLICATION_DELAY)
            
            # Update position
            positions[category] = batch_end
            progress_data['category_positions'] = positions
            save_progress(progress_data)
            
            # Delay before next category
            remaining = [cat for cat in ['data_science', 'data_analyst', 'machine_learning'] 
                        if positions[cat] < len(all_internships[cat])]
            
            if len(remaining) > 1 and category != remaining[-1]:
                wait_with_message(CATEGORY_DELAY, "⏳ Switching to next category in")
    
    return total_attempted, total_successful

def main():
    """Main execution function"""
    print("="*60)
    print("INTERNSHALA AUTO-APPLY BOT")
    print("="*60)
    
    driver = create_driver()
    wait = create_wait(driver)
    
    try:
        # Login
        print("\nStep 1: Login")
        login_to_internshala(driver, wait)
        
        # Load progress
        print("\nStep 2: Loading progress")
        progress_data = load_progress()
        print(f"Loaded progress: {len(progress_data.get('applied_urls', []))} applications completed")
        
        # Collect all internships
        print("\nStep 3: Collecting internships")
        all_internships = collect_all_internships(driver, wait, progress_data)
   
        
        # Display summary and get confirmation
        if not display_summary_and_confirm(all_internships):
            print("\n❌ Application process cancelled by user")
            return
        
        # Process round-robin applications
        attempted, successful = process_round_robin(driver, wait, all_internships, progress_data)
        
        # Final summary
        print("\n" + "="*60)
        print("📊 FINAL SUMMARY")
        print("="*60)
        print(f"Total applications attempted: {attempted}")
        print(f"Successful applications: {successful}")
        print(f"Success rate: {(successful/attempted*100):.1f}%" if attempted > 0 else "N/A")
        print(f"📁 Logs saved in: applied_internships_detailed.csv")
        print("="*60)
        
    except Exception as e:
        print(f"\nError occurred at: {e}")
        import traceback
        traceback.print_exc()
        save_debug_page(driver, "error_page.html")
    
    finally:
        print("\n✅ Process completed. Browser will remain open.")

if __name__ == "__main__":
    main()