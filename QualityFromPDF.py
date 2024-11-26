import re
import requests
import pandas as pd
from PyPDF2 import PdfReader  
reader = PdfReader("EPS_2024_EXHIBITOR_LIST.pdf")
if reader.is_encrypted:
    print("The PDF is encrypted.")
else:
    print("The PDF is not encrypted.")

# Function to check URL quality
def is_url_good(url):
    try:
        response = requests.get(url, timeout=10)
        status_code = response.status_code

        # Check for HTTP errors
        if status_code >= 400:
            return False, f"HTTP {status_code}"

        # Check for content type
        content_type = response.headers.get("Content-Type", "")
        if "text/html" not in content_type:
            return False, "Non-HTML content"

        # Unsafe patterns
        unsafe_patterns = ["malware", "phishing", "ads", "tracking"]
        if any(pattern in url.lower() for pattern in unsafe_patterns):
            return False, "Unsafe pattern"

        # Redirects to suspicious domains
        if response.url != url:
            final_domain = re.findall(r"https?://([^/]+)", response.url)[0]
            original_domain = re.findall(r"https?://([^/]+)", url)[0]
            if final_domain != original_domain:
                return False, f"Redirect to {final_domain}"

        return True, None
    except requests.exceptions.RequestException as e:
        return False, str(e)


# Function to extract URLs from a PDF
def extract_urls_from_pdf(pdf_path):
    urls = []
    try:
        reader = PdfReader(pdf_path)
        for page in reader.pages:
            text = page.extract_text()
            if text:
                # Use regex to find all URLs in the text
                page_urls = re.findall(r"https?://[^\s]+", text)
                urls.extend(page_urls)
    except Exception as e:
        print(f"Error reading PDF: {e}")
    return urls


# Main workflow
def validate_urls_in_pdf(pdf_path, output_file):
    # Extract URLs
    urls = extract_urls_from_pdf(pdf_path)
    if not urls:
        print("No URLs found in the PDF.")
        return

    print(f"Found {len(urls)} URLs. Checking quality...")

    # Check URL quality
    results = []
    for url in urls:
        is_good, issue = is_url_good(url)
        results.append({
            "URL": url,
            "Quality": "Good" if is_good else "Bad",
            "Issue": issue
        })

    # Save results to Excel
    df = pd.DataFrame(results)
    df.to_excel(output_file, index=False)
    print(f"Results saved to '{output_file}'.")


# Specify the input PDF and output Excel file
pdf_path = "EPS_2024_EXHIBITOR_LIST.pdf"  
output_file = "pdf_url_quality.xlsx"

validate_urls_in_pdf(pdf_path, output_file)
