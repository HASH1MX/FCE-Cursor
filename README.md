# Facebook Email Scraper

This Python application searches Facebook for businesses without websites and extracts their email addresses.

## Features

- Reads business names from a text file
- Automatically logs into Facebook
- Searches for businesses on Facebook
- Checks if the business has a website
- Extracts email addresses for businesses without websites
- Saves results to a CSV file
- Provides a user-friendly GUI interface

## Requirements

- Python 3.6+
- Chrome browser installed

## Installation

1. Clone or download this repository
2. Install the required dependencies:

```
pip install -r requirements.txt
```

## Usage

### Command Line Version

1. Create a text file named `business_list.txt` with one business name per line
2. Run the script:

```
python facebook_email_scraper.py
```

3. Enter your Facebook login credentials when prompted
4. The script will process each business and save results to `business_emails.csv`

### GUI Version

1. Run the GUI application:

```
python facebook_scraper_gui.py
```

2. Enter business names in the text area (one per line) or load from a file using the "Load Names from File" button
3. Click "Start Scraping" to begin the extraction process
4. Monitor progress with the progress bar and status updates
5. When complete, view results in the table and save them to a CSV file using the "Save Results" button

## Important Notes

- Facebook may detect and block automated access. Use with caution and add reasonable delays.
- You may need to manually handle CAPTCHA challenges if they appear.
- This tool is for educational purposes only. Be sure to comply with Facebook's Terms of Service.
- The script has built-in delays to avoid being blocked by Facebook.

## Customization

You can modify the script to:
- Change the output file name
- Adjust delays between requests
- Run in headless mode (uncomment the headless option in the code)
- Add proxy support to avoid IP blocking 