import time
import csv
import re
import os
import traceback
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

class FacebookEmailScraper:
    def __init__(self, business_list_file, output_file="results.csv"):
        print("Initializing Facebook Email Scraper...")
        self.business_list_file = business_list_file
        self.output_file = output_file
        self.setup_driver()
        self.results = []
        
    def setup_driver(self):
        """Setup Chrome WebDriver with appropriate options"""
        print("Setting up Chrome WebDriver...")
        chrome_options = Options()
        # Uncomment the line below to run in headless mode (no browser UI)
        # chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        
        try:
            # Use this alternative setup method for Chrome
            print("Trying alternative WebDriver setup...")
            self.driver = webdriver.Chrome(options=chrome_options)
            print("WebDriver initialized successfully")
            self.wait = WebDriverWait(self.driver, 10)
        except Exception as e:
            print(f"Error setting up WebDriver: {str(e)}")
            traceback.print_exc()
            raise
    
    def handle_cookies_dialog(self):
        """Handle cookie consent dialog if it appears"""
        try:
            print("Checking for cookie consent dialog...")
            
            # Look for specific "Allow all cookies" button (as shown in the screenshot)
            allow_cookies_buttons = self.driver.find_elements(By.XPATH, 
                "//button[contains(text(), 'Allow all cookies')]")
            
            if allow_cookies_buttons:
                print("Found 'Allow all cookies' button, clicking with JavaScript...")
                try:
                    self.driver.execute_script("arguments[0].click();", allow_cookies_buttons[0])
                    time.sleep(2)
                    return True
                except Exception as e:
                    print(f"JavaScript click failed: {str(e)}")
            
            # Try more generic cookie consent buttons
            cookie_buttons = self.driver.find_elements(By.XPATH, 
                "//button[contains(text(), 'Allow') or contains(text(), 'Accept') or contains(text(), 'Okay')]")
            
            if cookie_buttons:
                print("Found cookie consent button, clicking with JavaScript...")
                try:
                    self.driver.execute_script("arguments[0].click();", cookie_buttons[0])
                    time.sleep(2)
                    return True
                except Exception as e:
                    print(f"JavaScript click failed: {str(e)}")
            
            # Try by class name or data attributes for cookie consent dialog buttons
            cookie_buttons_by_class = self.driver.find_elements(By.CSS_SELECTOR, 
                "[data-testid='cookie-policy-manage-dialog-accept-button'], [aria-label='Allow all cookies']")
            
            if cookie_buttons_by_class:
                print("Found cookie button by class/attribute, clicking with JavaScript...")
                try:
                    self.driver.execute_script("arguments[0].click();", cookie_buttons_by_class[0])
                    time.sleep(2)
                    return True
                except Exception as e:
                    print(f"JavaScript click failed: {str(e)}")
            
            # Try clicking buttons with certain text content
            try:
                print("Trying to find cookie dialog buttons with JavaScript...")
                self.driver.execute_script("""
                    var buttons = document.querySelectorAll('button');
                    for (var i = 0; i < buttons.length; i++) {
                        if (buttons[i].textContent.includes('Allow all cookies') || 
                            buttons[i].textContent.includes('Accept all') ||
                            buttons[i].textContent.includes('Accept cookies')) {
                            buttons[i].click();
                            return true;
                        }
                    }
                    return false;
                """)
                time.sleep(2)
            except Exception as e:
                print(f"JavaScript button search failed: {str(e)}")
                
            print("No cookie consent dialog found or couldn't interact with it")
            return False
                
        except Exception as e:
            print(f"Error handling cookies: {str(e)}")
            traceback.print_exc()
        
        return False
    
    def load_business_names(self):
        """Load business names from text file"""
        try:
            print(f"Loading business names from {self.business_list_file}...")
            with open(self.business_list_file, 'r') as file:
                businesses = [line.strip() for line in file.readlines() if line.strip()]
                print(f"Successfully loaded {len(businesses)} business names")
                return businesses
        except Exception as e:
            print(f"Error loading business names: {str(e)}")
            traceback.print_exc()
            return []
    
    def search_business(self, business_name):
        """Search for a business on Facebook without login"""
        try:
            print(f"Searching for business: {business_name}")
            # Direct URL format that might work without login
            # First try direct business name URL format
            business_url = f"https://www.facebook.com/{business_name.lower().replace(' ', '')}"
            print(f"Trying direct URL: {business_url}")
            self.driver.get(business_url)
            time.sleep(3)
            
            # Handle cookie dialog immediately after page load
            self.handle_cookies_dialog()
            
            # Check if we got redirected to login page
            if "login" in self.driver.current_url or "checkpoint" in self.driver.current_url:
                print("Redirected to login page. Trying another approach...")
                
                # Try public search URL
                search_url = f"https://www.facebook.com/public/{business_name.replace(' ', '-')}"
                print(f"Trying public search URL: {search_url}")
                self.driver.get(search_url)
                time.sleep(3)
                
                # Handle cookie dialog again after new page load
                self.handle_cookies_dialog()
                
                # Try to find and click on a business result
                business_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/pages/') or contains(@href, '/business/')]")
                
                if not business_links:
                    print(f"No results found for {business_name}")
                    return False
                
                print(f"Found {len(business_links)} potential business links")
                business_links[0].click()
                time.sleep(3)
                
                # Handle cookie dialog after clicking
                self.handle_cookies_dialog()
            
            # Check if we're on a content page or login wall
            if "login" in self.driver.current_url:
                print(f"Facebook requires login to view {business_name}. Skipping.")
                return False
                
            print(f"Successfully accessed page for {business_name}")
            return True
            
        except Exception as e:
            print(f"Error searching for {business_name}: {str(e)}")
            traceback.print_exc()
            return False
    
    def check_website_exists(self):
        """Check if the business has a website link on their Facebook page"""
        try:
            print("Checking if business has a website...")
            # Check for website links directly on the page
            website_elements = self.driver.find_elements(
                By.XPATH, 
                "//a[contains(@href, 'http') and not(contains(@href, 'facebook.com'))]"
            )
            
            print(f"Found {len(website_elements)} potential website links")
            
            for element in website_elements:
                href = element.get_attribute('href')
                if href and ('facebook.com' not in href and 'fb.com' not in href):
                    print(f"Website found: {href}")
                    return True
            
            # Try to find About section if it's accessible without login
            about_links = self.driver.find_elements(By.XPATH, "//a[contains(text(), 'About') or contains(@href, '/about')]")
            
            if about_links:
                print("Found About section, attempting to click...")
                try:
                    # Try normal click first
                    about_links[0].click()
                except Exception as e:
                    print(f"Normal click failed: {str(e)}")
                    try:
                        # Try using JavaScript to click the element
                        print("Trying JavaScript click...")
                        self.driver.execute_script("arguments[0].click();", about_links[0])
                    except Exception as js_e:
                        print(f"JavaScript click also failed: {str(js_e)}")
                        # Try direct navigation to about page
                        current_url = self.driver.current_url
                        if not current_url.endswith('/'):
                            current_url += '/'
                        about_url = current_url + 'about'
                        print(f"Trying direct navigation to: {about_url}")
                        self.driver.get(about_url)
                
                time.sleep(2)
                
                # Check again for website links
                website_elements = self.driver.find_elements(
                    By.XPATH, 
                    "//a[contains(@href, 'http') and not(contains(@href, 'facebook.com'))]"
                )
                
                print(f"Found {len(website_elements)} potential website links in About section")
                
                for element in website_elements:
                    href = element.get_attribute('href')
                    if href and ('facebook.com' not in href and 'fb.com' not in href):
                        print(f"Website found in About section: {href}")
                        return True
            
            print("No website found for this business")
            return False
            
        except Exception as e:
            print(f"Error checking website: {str(e)}")
            traceback.print_exc()
            return True  # Assume website exists in case of error to avoid false positives
    
    def clean_email(self, raw_email):
        """Clean up extracted email address"""
        # Extract just the email part using regex
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        match = re.search(email_pattern, raw_email)
        if match:
            return match.group(0)
        return raw_email
        
    def extract_email(self):
        """Extract email address from the Facebook page"""
        try:
            print("Attempting to extract email address...")
            # Get page source and parse with BeautifulSoup
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Look for email patterns in the page content
            email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            text_content = soup.get_text()
            emails = re.findall(email_pattern, text_content)
            
            print(f"Found {len(emails)} email addresses in page content")
            
            # Filter out common Facebook emails
            filtered_emails = [email for email in emails if 'facebook' not in email.lower()]
            
            print(f"After filtering: {len(filtered_emails)} potential business emails")
            
            if filtered_emails:
                cleaned_email = self.clean_email(filtered_emails[0])
                print(f"Email found: {cleaned_email}")
                return cleaned_email  # Return the first email found
            
            # Try to find and click Contact Info if available without login
            contact_links = self.driver.find_elements(
                By.XPATH, 
                "//a[contains(text(), 'Contact') or contains(@href, '/contact')]"
            )
            
            if contact_links:
                print("Found Contact section, clicking...")
                try:
                    # Try normal click first
                    contact_links[0].click()
                except Exception as e:
                    print(f"Normal click failed: {str(e)}")
                    try:
                        # Try using JavaScript to click the element
                        print("Trying JavaScript click...")
                        self.driver.execute_script("arguments[0].click();", contact_links[0])
                    except Exception as js_e:
                        print(f"JavaScript click also failed: {str(js_e)}")
                
                time.sleep(2)
                page_source = self.driver.page_source
                soup = BeautifulSoup(page_source, 'html.parser')
                text_content = soup.get_text()
                emails = re.findall(email_pattern, text_content)
                filtered_emails = [email for email in emails if 'facebook' not in email.lower()]
                
                print(f"Found {len(filtered_emails)} emails in Contact section")
                
                if filtered_emails:
                    cleaned_email = self.clean_email(filtered_emails[0])
                    print(f"Email found in Contact section: {cleaned_email}")
                    return cleaned_email
            
            print("No valid email address found")
            return None
            
        except Exception as e:
            print(f"Error extracting email: {str(e)}")
            traceback.print_exc()
            return None
    
    def save_results(self):
        """Save results to CSV file"""
        try:
            print(f"Saving {len(self.results)} results to {self.output_file}...")
            with open(self.output_file, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(['Business Name', 'Email'])
                writer.writerows(self.results)
            
            print(f"Results saved to {self.output_file}")
            return True
        except Exception as e:
            print(f"Error saving results: {str(e)}")
            traceback.print_exc()
            return False
    
    def run(self):
        """Run the scraper for all businesses without login"""
        print("Starting scraper in no-login mode (note: results may be limited)")
        
        businesses = self.load_business_names()
        if not businesses:
            print("No businesses found to process. Exiting.")
            return
            
        print(f"Loaded {len(businesses)} businesses to process")
        
        for business_name in businesses:
            print(f"\n{'='*50}")
            print(f"Processing: {business_name}")
            print(f"{'='*50}")
            
            if self.search_business(business_name):
                has_website = self.check_website_exists()
                
                if not has_website:
                    print(f"{business_name} has no website. Checking for email...")
                    email = self.extract_email()
                    
                    if email:
                        print(f"Email found: {email}")
                        self.results.append([business_name, email])
                    else:
                        print(f"No email found for {business_name}")
                        self.results.append([business_name, "No email found"])
                else:
                    print(f"{business_name} has a website. Skipping.")
            else:
                print(f"Could not access {business_name} without login. Skipping.")
                self.results.append([business_name, "Not accessible without login"])
            
            # Add delay between requests to avoid being blocked
            delay = 3
            print(f"Waiting {delay} seconds before next business...")
            time.sleep(delay)
        
        self.save_results()
        self.driver.quit()


if __name__ == "__main__":
    try:
        print("Facebook Email Scraper starting...")
        business_file = "test_businesses.txt"  # Using the test file with specific businesses
        output_file = "business_emails.csv"  # Output file for results
        
        scraper = FacebookEmailScraper(business_file, output_file)
        scraper.run()
        print("Facebook Email Scraper completed successfully")
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        traceback.print_exc() 