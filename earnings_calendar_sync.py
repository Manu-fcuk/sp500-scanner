import yfinance as yf
import datetime
import os.path
import pytz

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# --- Configuration ---

# List of tickers you want to track
TICKERS = ["GOOG", "MSFT", "AAPL", "AMZN", "NVDA", "TSLA"] # Add/remove tickers as needed

# Timezone for earnings events (e.g., 'America/New_York', 'Europe/London', 'Asia/Tokyo')
# This should ideally match the timezone in which earnings calls are announced.
# Many US earnings are announced after market close (EST/EDT).
EVENT_TIMEZONE = 'America/New_York' 

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar.events']

# The ID of the calendar to add events to.
# 'primary' refers to your default Google Calendar.
# You can also create a new calendar in Google Calendar (e.g., "Stock Earnings")
# and use its ID here. To find a calendar ID:
# Go to Google Calendar settings, find the calendar, and the ID is usually under "Integrate calendar."
CALENDAR_ID = 'primary' 

# --- Google Calendar API Authentication ---

def authenticate_google_calendar():
    """Shows user how to authenticate with Google Calendar API."""
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('calendar', 'v3', credentials=creds)

# --- Main Script ---

def sync_earnings_to_calendar():
    service = authenticate_google_calendar()
    
    print("Fetching earnings dates and syncing to Google Calendar...")

    for ticker in TICKERS:
        try:
            stock = yf.Ticker(ticker)
            earnings_history = stock.earnings_dates

            # Get only future earnings dates
            future_earnings = earnings_history[earnings_history.index > datetime.datetime.now(pytz.utc)]
            
            if future_earnings.empty:
                print(f"No future earnings dates found for {ticker} or data not available.")
                continue

            # Limit to a reasonable number, e.g., next 4 quarters
            future_earnings = future_earnings.head(4) 
            
            for index, row in future_earnings.iterrows():
                # yfinance returns datetime objects, ensure it's timezone-aware for comparison
                earnings_date_utc = index 

                # Convert to local timezone for event creation, assuming market close/after hours
                # A simple way to set a specific time for the event is to assume it's after market close.
                # Adjust time if earnings are typically before market open for specific companies.
                local_tz = pytz.timezone(EVENT_TIMEZONE)
                event_datetime_local = earnings_date_utc.astimezone(local_tz).replace(
                    hour=16, minute=15, second=0, microsecond=0
                ) # Assuming ~15 min after market close for placeholder

                event_summary = f"{ticker} Earnings (Est.)"
                event_description = f"Estimated earnings announcement for {ticker}. Check company investor relations for exact time and webcast details."

                # Check if event already exists to avoid duplicates
                events_result = service.events().list(
                    calendarId=CALENDAR_ID,
                    timeMin=event_datetime_local.isoformat(),
                    timeMax=(event_datetime_local + datetime.timedelta(hours=1)).isoformat(), # Check within a 1-hour window
                    q=event_summary, # Search for existing events with this summary
                    singleEvents=True,
                    orderBy='startTime'
                ).execute()
                existing_events = events_result.get('items', [])

                if not existing_events:
                    event = {
                        'summary': event_summary,
                        'description': event_description,
                        'start': {
                            'dateTime': event_datetime_local.isoformat(),
                            'timeZone': EVENT_TIMEZONE,
                        },
                        'end': {
                            'dateTime': (event_datetime_local + datetime.timedelta(hours=1)).isoformat(), # 1-hour event
                            'timeZone': EVENT_TIMEZONE,
                        },
                        'reminders': {
                            'useDefault': False,
                            'overrides': [
                                {'method': 'email', 'minutes': 24 * 60}, # 1 day before
                                {'method': 'popup', 'minutes': 60},      # 1 hour before
                            ],
                        },
                    }

                    event = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
                    print(f"  Event created for {ticker}: {event_summary} on {event_datetime_local.strftime('%Y-%m-%d %H:%M')}")
                else:
                    print(f"  Event already exists for {ticker}: {event_summary} on {event_datetime_local.strftime('%Y-%m-%d %H:%M')}")

        except Exception as e:
            print(f"Error processing {ticker}: {e}")

    print("\nEarnings calendar sync complete!")

if __name__ == '__main__':
    sync_earnings_to_calendar()