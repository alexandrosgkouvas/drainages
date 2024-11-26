import time
import re
import requests
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Function to check URL quality
def is_url_good(url):
    try:
        response = requests.get(url, timeout=10)  # Use GET to fetch actual content
        status_code = response.status_code

        # Check for HTTP errors
        if status_code >= 400:
            return False, f"HTTP {status_code}"

        # Check for content type (expecting HTML pages)
        content_type = response.headers.get("Content-Type", "")
        if "text/html" not in content_type:
            return False, "Non-HTML content"

        # Check for unsafe patterns in URL
        unsafe_patterns = ["malware", "phishing", "ads", "tracking"]
        if any(pattern in url.lower() for pattern in unsafe_patterns):
            return False, "Unsafe pattern"

        # Redirects to suspicious domains
        if response.url != url:  # Final URL after redirects
            final_domain = re.findall(r"https?://([^/]+)", response.url)[0]
            original_domain = re.findall(r"https?://([^/]+)", url)[0]
            if final_domain != original_domain:
                return False, f"Redirect to {final_domain}"

        # If all checks pass
        return True, None
    except requests.exceptions.RequestException as e:
        return False, str(e)

# Initialize WebDriver with options
options = webdriver.ChromeOptions()
options.add_argument("--disable-gpu")
options.add_argument("--disable-software-rasterizer")
driver = webdriver.Chrome(options=options)

# 1. Open the main page
main_url = "https://drainageshow.com/exhibiting/exhibitors/"  
driver.get(main_url)

# Wait for the page to load fully
WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, 'h5')))  # Wait for <h5> tags

# 2. Scroll down the page to load content
scroll_pause_time = 3  # Time to wait after each scroll (increased)
scroll_height = driver.execute_script("return document.body.scrollHeight")

while True:
    # Scroll down to the bottom of the page
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(scroll_pause_time)  # Wait for the page to load more content
    new_scroll_height = driver.execute_script("return document.body.scrollHeight")
    
    # Break the loop if we have reached the bottom of the page
    if new_scroll_height == scroll_height:
        break
    scroll_height = new_scroll_height

print("Scrolling complete. Collecting links...")

# 3. Wait for and extract href links using the new XPath for the first set
h5_links = WebDriverWait(driver, 20).until(
    EC.presence_of_all_elements_located((By.XPATH, "//*[@id='stacks_in_384']/div/div/div[2]/h5/a"))
)

hrefs = [link.get_attribute("href") for link in h5_links if link.get_attribute("href")]
print(f"Links collected: {hrefs}")

# 4. Visit each link from <h5> and collect additional links using the second XPath
collected_hrefs = []
for href in hrefs:
    try:
        driver.get(href)
        
        # Wait for buttons to be present on the page using the new XPath
        WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.XPATH, "//*[@id='stacks_in_1']/div[6]/div/div/div/div/div/div[1]/a"))
        )

        # Extract href links inside the new elements
        button_links = driver.find_elements(By.XPATH, "//*[@id='stacks_in_1']/div[6]/div/div/div/div/div/div[1]/a")
        page_hrefs = [link.get_attribute("href") for link in button_links if link.get_attribute("href")]
        collected_hrefs.extend(page_hrefs)
        
        print(f"Links from {href}: {page_hrefs}")
        
    except Exception as e:
        print(f"Error visiting {href}: {e}")

print(f"Total links collected from new XPath: {len(collected_hrefs)}")

# 5. Collect contact information and check link quality
contact_info = []
for href in collected_hrefs:
    is_good, issue = is_url_good(href)  # Check if the link is good or bad
    if is_good:
        quality = "Good"
    else:
        quality = "Bad"
    
    try:
        driver.get(href)
        
        # Wait for the page to load fully
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
        
        # Look for email links (mailto:)
        try:
            email = driver.find_element(By.XPATH, "//a[contains(@href, 'mailto:')]").get_attribute("href")
        except:
            email = None

        # Look for phone links (tel:)
        try:
            phone = driver.find_element(By.XPATH, "//a[contains(@href, 'tel:')]").get_attribute("href")
        except:
            phone = None

        # Append the contact info along with URL and its quality
        contact_info.append({
            "URL": href,
            "Email": email,
            "Phone": phone,
            "Quality": quality
        })
    except Exception as e:
        print(f"Error visiting {href}: {e}")

print("Contact information collected:")

# 6. Save results to a single Excel sheet
df = pd.DataFrame(contact_info)
df.to_excel("contactsquality.xlsx", index=False)

print("Data saved to 'contacts.xlsx'.")

# Close the browser
driver.quit()
