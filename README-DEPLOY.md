
# Deploy on Streamlit Cloud (free)

1) Create a new GitHub repo and upload this folder (all files).
2) Go to https://share.streamlit.io → "New app" → select your repo, branch, and **app.py** as the entry file.
3) (First run) The app will auto-download the spaCy model if missing; build may take 2–3 minutes.
4) Done. Share your Streamlit app URL.

Notes:
- If `newspaper3k` causes install issues, comment it out of `requirements.txt` and redeploy (the app falls back to Readability).
- You can change RSS sources inside the app sidebar or edit `src/config.py` and redeploy.
