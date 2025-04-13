from playwright.sync_api import sync_playwright
import time
import csv
import random  # To randomize the delay between requests
import html  # To handle HTML entities like &nbsp;

# Function to read physician IDs from the active list or generate sequence
def get_physician_ids(starting_id=None, check_active=False):
    if check_active:
        # If checking active IDs, read from active_ids.txt
        with open("active_ids.txt", "r") as f:
            return [line.strip() for line in f.readlines()]
    else:
        # Generate IDs starting from 1 or starting_id if provided
        if starting_id:
            start_index = int(starting_id)
            return [str(i).zfill(5) for i in range(start_index, 10000)]  # Format as 5 digits with leading zeros
        return [str(i).zfill(5) for i in range(1, 10000)]  # Default: Start from 00001 to 09999

# Initialize a list to store the results
results = []

# Files to track inactive and active IDs
inactive_ids = []
active_ids = []

# File to track the last checked ID
last_checked_id = None

# Set the starting ID (change this ID as needed to specify where to start)
starting_id = None  # Set this to the desired starting physician ID or leave as None to start from 00001
check_active = False  # Set this to True if you want to check the active physician IDs, otherwise False

# Start Playwright
with sync_playwright() as p:
    
    # Launch Chromium (headless for production or False for UI debugging)
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()

    # Go to the McLaren Physician Directory
    directory_url = "https://www.mclaren.org/main/physician-directory/"

    # Get the list of IDs based on the current mode (starting ID or checking active IDs)
    physicians = get_physician_ids(starting_id, check_active)

    for physician in physicians:
        # Skip the physician ID if it's the last checked ID
        if last_checked_id and physician < last_checked_id:
            continue

        # Construct the URL for the physician based on their 5-digit ID
        physician_url = directory_url + physician

        # Initialize the status flag for each physician
        status = "active"
        url = physician_url  # Default URL for active physicians

        # Initialize variables to avoid "undefined" errors
        name = None
        specialty_list = []
        subspecialty_list = []
        education_info = []
        locations_data = []

        # Navigate to the physician's page
        page.goto(physician_url)
        time.sleep(1)  # Wait for the page to load

        # Check if the page title contains "Error 404 - file not found" for inactive IDs
        title = page.title()
        if "Error 404 - file not found" in title:
            print(f"ERROR: {physician} - Inactive URL (404 Error)")
            status = "inactive"  # Set status to inactive
            url = ""  # Clear the URL for inactive physicians
            inactive_ids.append(physician)  # Append the inactive ID to the list
            # Immediately write to the inactive IDs file
            with open("inactive_ids.txt", "a") as f:
                f.write(f"{physician}\n")
        else:
            # If the page is active, extract the name from the title
            name = title.split('|')[0].strip()  # Get the part before "| McLaren Physician Directory"
            name = html.unescape(name)  # Convert HTML entities like &nbsp; to normal characters
            name = name.replace('\xa0', ' ')  # Replace any non-breaking spaces with regular spaces

            print(f"SUCCESS: {physician} - Name: {name}")

            # Scrape the specialties (fix for multiple specialties)
            specialties_section = page.query_selector("span.pre-header:has-text('Specialties') + ul")
            if specialties_section:
                specialties_items = specialties_section.query_selector_all("li")
                specialty_list = [item.inner_text().strip() for item in specialties_items]

            # Scrape the subspecialties
            subspecialties_section = page.query_selector("span.pre-header:has-text('Subspecialties') + ul")
            if subspecialties_section:
                subspecialty_items = subspecialties_section.query_selector_all("li")
                subspecialty_list = [item.inner_text().strip() for item in subspecialty_items]

            # Scrape the location details (handle multiple addresses)
            locations = []
            location_section = page.query_selector("#physicianLocationTab .location-details__wrapper")
            if location_section:
                # For each address block, extract the necessary details (up to 5 addresses)
                address_blocks = location_section.query_selector_all(".col-12.col-md-6")
                for block in address_blocks:
                    # Extract location name, address, phone, and fax
                    location_name = block.query_selector(".location-name").inner_text() if block.query_selector(".location-name") else "N/A"
                    address = block.inner_text().split("\n") if block else []
                    address_line = address[0] if len(address) > 0 else "N/A"
                    city_state_zip = address[1] if len(address) > 1 else "N/A"
                    phone = block.query_selector(".phone a")  # Find phone number
                    phone_number = phone.inner_text() if phone else "N/A"
                    fax = block.query_selector(".fax")  # Find fax number
                    fax_number = fax.inner_text() if fax else "N/A"
                    
                    locations.append({
                        "location_name": location_name,
                        "address_line": address_line,
                        "city_state_zip": city_state_zip,
                        "phone_number": phone_number,
                        "fax_number": fax_number
                    })

            # Scrape the education details
            education_data = {"medical_school": "N/A", "residency": "N/A", "fellowships": "N/A"}
            education_section = page.query_selector("#physicianEducationTab")
            if education_section:
                # Extract medical school, residency, and fellowships
                medical_school = education_section.query_selector("h4:has-text('Medical School') + ul li")
                residency = education_section.query_selector("h4:has-text('Residency') + ul li")
                fellowships = education_section.query_selector("h4:has-text('Fellowships') + ul li")
                
                education_data["medical_school"] = medical_school.inner_text() if medical_school else "N/A"
                education_data["residency"] = residency.inner_text() if residency else "N/A"
                education_data["fellowships"] = fellowships.inner_text() if fellowships else "N/A"

            # Save this result into the results list (convert specialties, locations, and education to strings for CSV)
            locations_data = []
            for location in locations:
                locations_data.append(
                    f"{location['location_name']}, {location['address_line']}, {location['city_state_zip']}, {location['phone_number']}, {location['fax_number']}"
                )
            
            # Save the education data as strings
            education_info = [education_data["medical_school"], education_data["residency"], education_data["fellowships"]]
            
            # Add the physician information, specialties, subspecialties, locations, and education to results
            results.append([status, url, physician, name, ", ".join(specialty_list), ", ".join(subspecialty_list)] + education_info + locations_data)

            # Track the last checked ID
            last_checked_id = physician

            # Add this ID to active_ids if it's active
            if status == "active":
                active_ids.append(physician)
                # Immediately write to the active IDs file
                with open("active_ids.txt", "a") as f:
                    f.write(f"{physician}\n")

        # Immediately save to the CSV after each physician is checked (Only active physicians)
        if status == "active":  # Only write to CSV for active physicians
            with open("physicians_active.csv", "a", newline="") as f:
                writer = csv.writer(f)
                # Write the headers only if the file is empty
                if f.tell() == 0:
                    writer.writerow(["Status", "URL", "Physician ID", "Name", "Specialties", "Subspecialties", "Medical School", "Residency", "Fellowships", "Location 1 Name", "Location 1 Address", "Location 1 City, State, Zip", "Location 1 Phone", "Location 1 Fax"])
                writer.writerow([status, url, physician, name, ", ".join(specialty_list), ", ".join(subspecialty_list)] + education_info + locations_data)

        # Immediately write the last checked ID to a file after each ID is processed (for both active and inactive)
        with open("last_checked_id.txt", "w") as f:
            f.write(str(last_checked_id))

        # Introduce a random delay between 2 to 5 seconds (to avoid overloading the server)
        delay = random.randint(2, 5)
        print(f"Pausing for {delay} seconds...\n")
        time.sleep(delay)

    print(f"Data collection completed. {len(results)} active entries saved.")
    print(f"Inactive physician IDs saved to 'inactive_ids.txt'.")
    print(f"Active physician IDs saved to 'active_ids.txt'.")
    print(f"Last checked ID saved to 'last_checked_id.txt'.")
