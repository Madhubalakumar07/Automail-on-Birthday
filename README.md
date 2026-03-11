# 🎂 AutoMail — Birthday Reminder (Streamlit)

Automatically scan a CSV of friends and send birthday emails — with a clean Streamlit UI.

## 🚀 Quick Start

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open http://localhost:8501 in your browser.

## 📁 Project Structure

```
automail/
├── app.py           # Streamlit UI
├── core.py          # Email & CSV logic
├── friends.csv      # Sample friends list
└── requirements.txt
```

## 📋 CSV Format

```csv
name,email,birthday,nickname
Alice Johnson,alice@gmail.com,1990-03-11,Ali
Bob Smith,bob@gmail.com,1985-07-22,Bobby
```

| Column     | Required | Format       |
|------------|----------|--------------|
| name       | ✅        | Text         |
| email      | ✅        | Email        |
| birthday   | ✅        | YYYY-MM-DD   |
| nickname   | ❌        | Text         |

## 📧 Gmail Setup

1. Enable **2-Step Verification** on your Google Account
2. Go to **Security → App Passwords**
3. Generate an App Password for "Mail"
4. Use that as the password in the sidebar — NOT your real password

## 🖥️ UI Features

- **Load Friends tab** — Upload CSV or use the sample file
- **Send Birthdays tab** — Pick any date, preview emails, send with one click
- **All Friends tab** — Browse all friends, see days until each birthday, search
- **Activity Log tab** — Full log of all actions taken
- **Dry Run toggle** — Test everything safely before going live
