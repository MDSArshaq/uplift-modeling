---
description: How to deploy the Streamlit app to Streamlit Community Cloud
---

# Deploy to Streamlit Community Cloud

## Prerequisites
- GitHub repo with the project code pushed
- [Streamlit Community Cloud account](https://share.streamlit.io) (free, sign in with GitHub)

## Step 1: Create GitHub Repo
1. Go to https://github.com/new
2. Name: `uplift-modeling` (or your preferred name)
3. Visibility: Public
4. Leave all other defaults (no README, no .gitignore, no license — we already have these)
5. Click "Create repository"

## Step 2: Push Code to GitHub
```bash
cd "d:\Resume Project - Uplift Modeling"
git init
git add .
git commit -m "Initial commit: Uplift Modeling - The Persuadable Hunter"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/uplift-modeling.git
git push -u origin main
```

## Step 3: Deploy on Streamlit Cloud
1. Go to https://share.streamlit.io
2. Sign in with your GitHub account
3. Click "New app"
4. Select your repo: `YOUR_USERNAME/uplift-modeling`
5. Branch: `main`
6. Main file path: `streamlit_app/app.py`
7. Click "Deploy"

## Step 4: Update README
After deployment, update the live app URL in README.md:
```
[Try the Interactive App](https://YOUR_APP_URL.streamlit.app)
```

## Notes
- Streamlit Cloud automatically installs from `streamlit_app/requirements.txt`
- The data file is committed to the repo, so no external data setup needed
- App will auto-redeploy on every push to main
