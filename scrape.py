
import time
import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from google.oauth2 import service_account
from googleapiclient.discovery import build

import openai

'''********************************************************************
                            GLOBAL
********************************************************************'''

# Load the .env file
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


# Replace with the ID of your Google Sheets document
SHEET_ID = '1JgWcqd-ftVZencplEOxkmahyOgKvlsiaa_rVKR6DmJE'

# Replace with the name of your service account key file
KEY_FILE_LOCATION = 'service_account_lino.json'

# Create credentials object from the service account key file
CREDENTIALS = service_account.Credentials.from_service_account_file(
                        KEY_FILE_LOCATION, scopes=['https://www.googleapis.com/auth/drive'])

# Create Drive API client
SHEETS_SERVICE = build('sheets', 'v4', credentials=CREDENTIALS)



# Set the time to run the script (6:20 am)
hour = 5
minute = 0

'''********************************************************************
                           MAIN METHODS
********************************************************************'''

def get_info_from_google_sheet():

    # Define the range of cells you want to retrieve data from (e.g. A:B)
    range_name = 'Sheet1!A:B'

    # Call the Sheets API to retrieve the data
    result = SHEETS_SERVICE.spreadsheets().values().get(
                    spreadsheetId=SHEET_ID, range=range_name).execute()

    # Print the data to the console
    values = result.get('values', [])
    if not values:
        print('No data found.')
        return []
    
    return values 

def scrape_data_from_yahoo(url = 'https://finance.yahoo.com/quote/TSLA/'):
    try:
          

            # Make a request to the website
            r = requests.get(url)

            # Create a BeautifulSoup object
            soup = BeautifulSoup(r.content, 'html.parser')

            text = soup.get_text()

            return text
    except Exception:
         return None
    
def gpt_assessment(text):
    response = openai.ChatCompletion.create(
                model='gpt-4',#"gpt-3.5-turbo",
                messages=[
                        {"role": "system", "content": "You are a helpful stock and cryto currency assistant. Respond with only Buy, Sell, or Hold based on the provided input. Then in the next line a short description of why you have decided that."},
                        {"role": "user", "content": f"Given the following text, recommend whether to buy, hold, or sell a stock: '{text}'.\n\nRecommendation:"}
                    ]
                )

    assessment = response['choices'][0]['message']['content']
    break_down = assessment.split('\n')
    decision, rational  = break_down[0], ' '.join(break_down[1:])
    return decision, rational

def update_google_sheet(name, decision, rational, row = 1):

    # Define the range of cells you want to update (e.g. A2:B2)
    range_name = f'Sheet2!A{row}:C{row}'

    # Define the new values you want to update the row with
    new_values = [name, decision, rational]

    # Define the value input option as RAW to accept input as string values
    value_input_option = 'RAW'

    # Create a value range object to hold the new values
    value_range_body = {
        'values': [new_values]
    }

    # Call the Sheets API to update the row with the new values
    result = SHEETS_SERVICE.spreadsheets().values().update(
            spreadsheetId=SHEET_ID, range=range_name,
            valueInputOption=value_input_option, body=value_range_body).execute()

    # Print the result to the console
    print('{0} cells updated.'.format(result.get('updatedCells')))



def main_job():
    values = get_info_from_google_sheet()
    for i, row in enumerate(values, start=1):
            name, link = row[0], row[1]
            print(f'Looking for {name}')
            text = scrape_data_from_yahoo(link)
            if text:
                decision, rational = gpt_assessment(text)
                update_google_sheet(name, decision, rational, row = i)
    
    
    # Get the current time as a struct_time object
    current_time = time.localtime()
    
    # Format the current time as a string
    time_string = time.strftime('%Y-%m-%d %H:%M:%S', current_time)
    
    #Include of message of last time this was runned
    update_google_sheet("LastRun", "", time_string, row = i+1)
                
                
def run_schedule():        
    while True:
        # Get the current time
        now = time.localtime()
    
        # Check if it's time to run the script
        if now.tm_hour >= hour and now.tm_hour < hour + 2:
         
            main_job()
            # Wait until the next day
            print('Sleeping 2 hour')
            time.sleep(2 * 60 * 60)

        print('Sleeping 1 hour')
        time.sleep(1 * 60 * 60)

            
            

if __name__=="__main__":
   run_schedule()
