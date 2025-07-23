import os
import requests
import json
import csv

# --- User Input and Configuration ---

# This is the ajs_user_id of the agent creating the ticket on behalf of the requester
user_submitter_id = "<USER_SUBMITTER_ID>"
zenDeskCookie = "<ZD_COOKIE_TOKEN>"
xcsrfValue = "<XCSRF_TOKEN>"
zendesk_domain = "liferay-support.zendesk.com" # Your Zendesk domain

# --- Product Configuration ---
# This dictionary maps a product tag to the required custom fields.
# You may need to add more products or adjust the fields based on your Zendesk setup.
# Find the Custom Field IDs in your Zendesk Admin Center (Objects and rules -> Tickets -> Fields)
PRODUCT_CUSTOM_FIELDS = {
    "prd_lxc_sm": [
        {"id": 360006076471, "value": "prd_lxc_sm"},
        {"id": 360021499771, "value": "lxc_sm_services"}
    ],
    "prd_liferay_dxp_7_4": [
        # DXP 7.1 likely does not have the "lxc_sm_services" field.
        # This only sets the main product field.
        {"id": 360006076471, "value": "prd_liferay_dxp_7_4"}
    ],
    "prd_liferay_dxp_7_3": [
        # DXP 7.1 likely does not have the "lxc_sm_services" field.
        # This only sets the main product field.
        {"id": 360006076471, "value": "prd_liferay_dxp_7_3"}
    ],
    "prd_liferay_dxp_7_2": [
        # DXP 7.1 likely does not have the "lxc_sm_services" field.
        # This only sets the main product field.
        {"id": 360006076471, "value": "prd_liferay_dxp_7_2"}
    ],
    "prd_liferay_dxp_7_1": [
        # DXP 7.1 likely does not have the "lxc_sm_services" field.
        # This only sets the main product field.
        {"id": 360006076471, "value": "prd_liferay_dxp_7_1"}
    ]
    # Add other products here, for example:
    # "prd_liferay_dxp_7_3": [
    #     {"id": 360006076471, "value": "prd_liferay_dxp_7_3"}
    # ]
}

# The product you intend to create tickets for. This must be a key in the dictionary above.
lrProduct = "prd_liferay_dxp_7_1"

# --- API Functions ---

def getURL(cookie, url):
    headers = {'Cookie': f'{cookie}'}
    print(f"GET Request to: {url}")
    response = requests.get(url, headers=headers)
    return response

def postURL(cookie, xcsrf, url, data):
    headers = {
        'Cookie': f'{cookie}',
        'X-Csrf-Token': f'{xcsrf}',
        'Content-Type': 'application/json'
    }
    print(f"POST Request to: {url}")
    response = requests.post(url, headers=headers, json=data)
    return response

def fetch_user_id_from_org(cookie, url_prefix, organization_id):
    """
    Finds the first valid end-user in an organization to act as the requester.
    """
    url = f"{url_prefix}/api/v2/organizations/{organization_id}/users.json"
    response = getURL(cookie, url)

    if response.status_code == 200:
        data = response.json()
        for user in data.get('users', []):
            email = user.get('email', '')
            role = user.get('role')
            # Skip internal users, broken accounts, and agents
            # Use .lower() to catch all variations like "noreply", "NoReply", "NO-REPLY", etc.
            if "noreply" not in email.lower() and "no-reply" not in email.lower() and "liferay.com" not in email and "broken" not in email and role == 'end-user':
                print(f"Found valid requester: {user['id']} ({email})")
                return user['id']
        print(f"Warning: No valid 'end-user' found for organization {organization_id}")
        return None
    else:
        print(f"Error fetching users for org {organization_id}: {response.status_code} - {response.text}")
        return None

def create_ticket(cookie, xcsrf, url_prefix, subject, comment, requester_id, organization_id, product_tag):
    """
    Creates a new Zendesk ticket with dynamically assigned custom fields.
    """
    if product_tag not in PRODUCT_CUSTOM_FIELDS:
        print(f"Error: Product '{product_tag}' is not configured in PRODUCT_CUSTOM_FIELDS. Cannot create ticket.")
        return

    # Build the ticket data payload
    data = {
        "ticket": {
            "brand_id": 360000598252,
            "status": "new",
            "submitter_id": user_submitter_id, # The agent creating the ticket
            "requester_id": requester_id,     # The customer who the ticket is for
            "organization_id": organization_id,
            "subject": subject,
            "comment": {
                "html_body": comment,
                "public": False # Set to True to make the first comment visible to the customer
            },
            "ticket_form_id": 360000077272,
            # Dynamically set custom fields based on the product
            "custom_fields": PRODUCT_CUSTOM_FIELDS[product_tag]
        }
    }

    url = f"{url_prefix}/api/v2/tickets.json"
    response = postURL(cookie, xcsrf, url, data)

    print(f"Response Status Code: {response.status_code}")
    
    # CRITICAL: Print the error message from Zendesk if it fails
    if response.status_code != 201:
        print("--- ERROR CREATING TICKET ---")
        print(response.text)
        print("-----------------------------")
    else:
        ticket_data = response.json()
        ticket_id = ticket_data['ticket']['id']
        print(f"Successfully created ticket: https://{zendesk_domain}/agent/tickets/{ticket_id}")

def process_csv_file(file_path, cookie, xcsrf, url_prefix):
    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as csv_file:
            csv_reader = csv.reader(csv_file)
            header = next(csv_reader, None) # Skip header

            for i, row in enumerate(csv_reader):
                print(f"\n--- Processing Row {i+1} ---")
                account_code = row[0]
                organization_id = int(row[1])
                subject = row[2]
                description = row[3]

                # Find a valid requester ID from the organization
                requester_id = fetch_user_id_from_org(cookie, url_prefix, organization_id)
                
                if requester_id is None:
                    print(f"Error: Could not find a valid requester for Org ID {organization_id}. Skipping ticket creation.")
                    continue

                print(f'Creating Ticket for Org: {organization_id}, Requester: {requester_id}, Product: {lrProduct}')
                create_ticket(cookie, xcsrf, url_prefix, subject, description, requester_id, organization_id, lrProduct)

    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# --- Main Execution ---
if __name__ == "__main__":
    if '<' in user_submitter_id or '<' in zenDeskCookie or '<' in xcsrfValue:
        print("Please replace placeholder values for user_submitter_id, zenDeskCookie, and xcsrfValue.")
    else:
        csv_file_path = 'csv_create_tickets.csv'
        url_prefix = f"https://{zendesk_domain}"
        
        process_csv_file(csv_file_path, zenDeskCookie, xcsrfValue, url_prefix)
