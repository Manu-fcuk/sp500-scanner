# How to Deploy Your Stock Dashboard to Streamlit Community Cloud

Since I cannot directly deploy applications to your personal accounts, here is a step-by-step guide to deploy your app for free using Streamlit Community Cloud.

## Prerequisites
1.  **GitHub Account**: You need a GitHub account.
2.  **Streamlit Account**: Sign up at [share.streamlit.io](https://share.streamlit.io/) using your GitHub account.

## Step 1: Push Your Code to GitHub
You need to upload your code to a GitHub repository.

1.  Create a new repository on GitHub (e.g., `stock-dashboard`).
2.  Upload the following files to the repository:
    -   `stock_dashboard.py`
    -   `requirements.txt` (I have created this for you)

## Step 2: Deploy on Streamlit Community Cloud
1.  Go to [share.streamlit.io](https://share.streamlit.io/).
2.  Click **"New app"**.
3.  Select your GitHub repository (`stock-dashboard`).
4.  Select the branch (usually `main` or `master`).
5.  In "Main file path", enter `stock_dashboard.py`.
6.  Click **"Deploy!"**.

## Step 3: Access Your App
Streamlit will install the dependencies from `requirements.txt` and launch your app. Once finished, you will get a URL (e.g., `https://stock-dashboard.streamlit.app`) that you can share with anyone!

## Troubleshooting
-   **"Module not found"**: Ensure `requirements.txt` is in the root of your repository and contains all libraries used (`streamlit`, `yfinance`, `pandas`, `numpy`, `plotly`, `textblob`).
-   **TextBlob Error**: If you see an error related to `TextBlob` corpora, you might need to add a command to download them, but for basic sentiment analysis, the default installation usually works.
