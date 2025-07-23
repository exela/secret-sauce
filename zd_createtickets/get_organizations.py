import requests
import csv

# --- User Configuration ---
# Your Zendesk domain (e.g., "your-company.zendesk.com")
ZENDESK_DOMAIN = "liferay-support.zendesk.com"
# Your Zendesk authentication cookie. Keep this private.
ZD_COOKIE = "<ZD_COOKIE_TOKEN>"
# The name of the output file you want to create.
OUTPUT_CSV_FILE = 'zendesk_organizations_list.csv'

def api_get_request(cookie, url):
    """
    Performs a GET request to the Zendesk API with the necessary cookie authentication.
    Returns the response object.
    """
    headers = {'Cookie': f'{cookie}'}
    try:
        response = requests.get(url, headers=headers)
        # Raise an exception for bad status codes (4xx or 5xx)
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        print(f"API Request Failed: {e}")
        return None

def generate_organizations_csv(cookie, domain, output_file):
    """
    Fetches all organizations from Zendesk and writes them to a CSV file.
    Handles API pagination automatically.
    """
    print(f"Starting to fetch organizations from {domain}...")
    
    # The starting URL for the API endpoint. We ask for 100 results per page (the max).
    next_page_url = f"https://{domain}/api/v2/organizations.json?page[size]=100"
    
    total_orgs_processed = 0
    page_count = 1

    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as csv_file:
            csv_writer = csv.writer(csv_file)
            
            # --- Write the header row to the CSV file ---
            csv_writer.writerow(['ACCOUNT CODE', 'ACCOUNT ID', 'ACCOUNT NAME'])

            # --- Loop through all pages of results ---
            while next_page_url:
                print(f"Fetching page #{page_count}...")
                response = api_get_request(cookie, next_page_url)

                if not response:
                    print("Halting script due to API request failure.")
                    break

                data = response.json()
                organizations = data.get('organizations', [])

                if not organizations:
                    print("No organizations found on this page.")
                    break

                for org in organizations:
                    # --- Safely extract data using .get() to prevent errors ---
                    # .get('key', {}) provides a default empty dictionary if 'organization_fields' is missing
                    org_fields = org.get('organization_fields', {})
                    
                    account_code = org_fields.get('account_code', 'N/A') # Provides 'N/A' if code is missing
                    org_id = org.get('id')
                    name = org.get('name')

                    # Write the cleaned data to the CSV
                    if org_id and name:
                        csv_writer.writerow([account_code, org_id, name])
                        total_orgs_processed += 1

                # Check if there is a next page to fetch
                if data.get('meta', {}).get('has_more'):
                    next_page_url = data['links']['next']
                    page_count += 1
                else:
                    # This was the last page
                    next_page_url = None

    except IOError as e:
        print(f"Error writing to file {output_file}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    print(f"\n--- Process Complete ---")
    print(f"Successfully processed {total_orgs_processed} organizations.")
    print(f"Data has been saved to '{output_file}'")

# --- Main Execution Block ---
if __name__ == "__main__":
    if "<" in ZD_COOKIE or ">" in ZD_COOKIE:
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("!!! ERROR: Please replace the <ZD_COOKIE_TOKEN>      !!!")
        print("!!! placeholder with your actual Zendesk cookie value. !!!")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    else:
        generate_organizations_csv(ZD_COOKIE, ZENDESK_DOMAIN, OUTPUT_CSV_FILE)