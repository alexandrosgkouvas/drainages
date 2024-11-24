from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd

# 1. Initialize WebDriver with options
options = webdriver.ChromeOptions()
options.add_argument("--disable-gpu")
options.add_argument("--disable-software-rasterizer")
# Uncomment the next line to run in headless mode
# options.add_argument("--headless")

driver = webdriver.Chrome(options=options)

# 2. Open the main page
main_url = "https://drainageshow.com/exhibiting/exhibitors/"  # Replace with the actual URL
driver.get(main_url)

# Wait for the page to load fully
WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, 'h5')))  # Wait for <h5> tags

# 3. Scroll down the page to load content
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

# 4. Wait for and extract href links using the new XPath for the first set
h5_links = WebDriverWait(driver, 20).until(
    EC.presence_of_all_elements_located((By.XPATH, "//*[@id='stacks_in_384']/div/div/div[2]/h5/a"))
)

# Check how many links were found
print(f"Total links found in <h5> with XPath '//*[@id='stacks_in_384']/div/div/div[2]/h5/a': {len(h5_links)}")

hrefs = [link.get_attribute("href") for link in h5_links if link.get_attribute("href")]
print(f"Links collected: {hrefs}")

# 5. Visit each link from <h5> and collect additional links using the second XPath
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

# 6. Visit each link from the collected buttons and scrape contact information
contact_info = []
for href in collected_hrefs:
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

        contact_info.append({"URL": href, "Email": email, "Phone": phone})
    except Exception as e:
        print(f"Error visiting {href}: {e}")

print("Contact information collected:")
print(contact_info)

# 7. Save results to an Excel file
df = pd.DataFrame(contact_info)
df.to_excel("contacts.xlsx", index=False)
print("Data saved to 'contacts.xlsx'.")

# Close the browser
driver.quit()
