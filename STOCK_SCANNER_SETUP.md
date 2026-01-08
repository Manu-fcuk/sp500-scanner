# S&P 500 Golden Cross Scanner Setup Guide

This application scans all S&P 500 stocks every hour and identifies Golden Cross patterns (Daily and Hourly). The results are automatically uploaded to a new Google Sheet in your account.

## 1. Google Cloud Setup (One-time)
To allow the bot to create Google Sheets in your account:
1.  Go to the [Google Cloud Console](https://console.cloud.google.com/).
2.  Create a new project (e.g., `Stock-Scanner`).
3.  Go to **APIs & Services > Library**.
4.  Search for and **Enable** both:
    -   **Google Sheets API**
    -   **Google Drive API**
5.  Go to **APIs & Services > Credentials**.
6.  Click **Create Credentials > Service Account**.
7.  Follow the prompts to create it (no specific roles are needed for basic sheet access).
8.  Once created, click on the Service Account email.
9.  Go to the **Keys** tab, click **Add Key > Create new key**, select **JSON**, and download it.
10. **Keep this file safe!** You will need its contents for GitHub.

## 2. GitHub Configuration
1.  Create a new GitHub repository (or use an existing one).
2.  Upload the following files from your local machine:
    -   `sp500_scanner.py`
    -   `.github/workflows/hourly_scan.yml`
    -   `requirements.txt`
3.  Go to your GitHub Repository **Settings > Secrets and variables > Actions**.
4.  Add two **New repository secrets**:
    -   **`GOOGLE_CREDENTIALS`**: Open the JSON file you downloaded from Google Cloud. Copy its *entire* content and paste it here.
    -   **`USER_EMAIL`**: Enter your Google email address (e.g., `yourname@gmail.com`). This is where the bot will share the newly created sheets.

## 3. How it Works
-   **Schedule**: The scanner runs automatically every hour (at minute 0) via GitHub Actions.
-   **Analysis**:
    -   Fetches all 500 stocks from Wikipedia.
    -   Checks for a **Daily Golden Cross** (50-day SMA crossing above 200-day SMA).
    -   If a stock is Bullish (50-SMA > 200-SMA), it checks for an **Hourly Golden Cross** on the 1-hour timeframe.
-   **Output**: Every hour, you will see a new spreadsheet in your Google Drive named `S&P 500 Golden Cross Report YYYY-MM-DD HH:MM`.

## Local Testing
If you want to run it locally to test:
1.  Set the environment variable: `export GOOGLE_CREDENTIALS='{...your json content...}'`
2.  Run: `python sp500_scanner.py`
