import re
import requests
import pandas as pd
from PyPDF2 import PdfReader


# Function to extract text from PDF
def extract_text_from_pdf(pdf_path):
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return None


# Function to extract links from text
def extract_links_from_text(text):
    return re.findall(r"https?://[^\s]+|www\.[^\s]+", text)


# Function to clean extracted URLs
def clean_urls(urls):
    return [url.strip().strip("'\"") for url in urls]


# Function to ensure URLs have a scheme
def ensure_scheme(url):
    if not url.startswith(("http://", "https://")):
        return "http://" + url  # Default to HTTP
    return url


# Function to check URL quality
def is_url_good(url):
    try:
        response = requests.get(url, timeout=10)
        status_code = response.status_code

        if status_code >= 400:
            return False, f"HTTP {status_code}"

        content_type = response.headers.get("Content-Type", "")
        if "text/html" not in content_type:
            return False, "Non-HTML content"

        return True, None
    except requests.exceptions.RequestException as e:
        return False, str(e)


# Main workflow to process URLs and save results to Excel
def process_urls_to_excel(pdf_path, output_file):
    # Extract text from PDF
    extracted_text = extract_text_from_pdf(pdf_path)
    if not extracted_text:
        print("No text extracted from the PDF.")
        return

    # Extract URLs
    raw_links = extract_links_from_text(extracted_text)
    if not raw_links:
        print("No links found in the text.")
        return

    print(f"Found {len(raw_links)} raw links: {raw_links}")

    # Clean URLs
    cleaned_links = clean_urls(raw_links)
    print(f"Cleaned URLs: {cleaned_links}")

    # Add scheme to URLs if missing
    final_links = [ensure_scheme(url) for url in cleaned_links]
    print(f"Final URLs with schemes: {final_links}")

    # Validate URLs and store results
    results = []
    for url in final_links:
        is_good, issue = is_url_good(url)
        results.append({
            "URL": url,
            "Quality": "Good" if is_good else "Bad",
            "Issue": issue
        })

    # Save results to an Excel file
    df = pd.DataFrame(results)
    df.to_excel(output_file, index=False)
    print(f"Results saved to '{output_file}'.")


# Run the process
pdf_path = "EPS_2024_EXHIBITOR_LIST.pdf"
output_file = "validated_urls.xlsx"
process_urls_to_excel(pdf_path, output_file)
