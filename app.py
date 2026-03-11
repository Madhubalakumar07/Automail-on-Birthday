"""
AutoMail — Birthday Reminder System (Streamlit UI)
Run with: streamlit run app.py
"""

import streamlit as st
import pandas as pd
from datetime import date, datetime
import time

from core import (
    load_friends_from_csv_text,
    load_friends_from_file,
    get_todays_birthdays,
    days_until_birthday,
    send_birthday_email,
    build_email_text,
    Friend,
)

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AutoMail — Birthday Reminder",
    page_icon="🎂",
    layout="wide",
)

# ── Session state defaults ────────────────────────────────────────────────────
if "friends" not in st.session_state:
    st.session_state.friends = []
if "logs" not in st.session_state:
    st.session_state.logs = []
if "smtp_ok" not in st.session_state:
    st.session_state.smtp_ok = False


def log_entry(msg: str, level: str = "info"):
    icon = {"info": "ℹ️", "success": "✅", "error": "❌", "warn": "⚠️"}.get(level, "•")
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.logs.append(f"`{timestamp}` {icon} {msg}")


# ══════════════════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════════════════
st.title("🎂 AutoMail — Birthday Reminder")
st.caption("Upload your friends CSV, configure email settings, and send birthday wishes automatically.")
st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR — SMTP Settings
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.header("📧 Email Settings")

    smtp_host = st.text_input("SMTP Host", value="smtp.gmail.com", placeholder="smtp.gmail.com")
    smtp_port = st.number_input("SMTP Port", value=587, min_value=1, max_value=65535)
    smtp_user = st.text_input("Your Email", placeholder="you@gmail.com")
    smtp_pass = st.text_input("App Password", type="password", placeholder="xxxx xxxx xxxx xxxx")
    sender_name = st.text_input("Sender Name", value="AutoMail Birthday Bot")

    st.caption("💡 Gmail users: use an [App Password](https://myaccount.google.com/apppasswords), not your real password.")

    st.divider()

    dry_run = st.toggle("🔍 Dry Run (preview only, no emails sent)", value=True)

    st.divider()
    st.markdown("**📋 CSV Format Required:**")
    st.code("name,email,birthday,nickname\nAlice,alice@x.com,1990-03-11,Ali", language="csv")
    st.caption("`birthday` must be `YYYY-MM-DD`. `nickname` is optional.")

# ══════════════════════════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4 = st.tabs(["📁 Load Friends", "🎂 Send Birthdays", "👥 All Friends", "📜 Activity Log"])


# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 — Load Friends
# ─────────────────────────────────────────────────────────────────────────────
with tab1:
    st.subheader("Load Your Friends List")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Upload a CSV file**")
        uploaded = st.file_uploader("Choose CSV", type=["csv"], label_visibility="collapsed")
        if uploaded:
            content = uploaded.read().decode("utf-8")
            friends, errors = load_friends_from_csv_text(content)
            if errors:
                for e in errors:
                    st.warning(f"⚠️ {e}")
            if friends:
                st.session_state.friends = friends
                log_entry(f"Loaded {len(friends)} friend(s) from '{uploaded.name}'", "success")
                st.success(f"✅ Loaded **{len(friends)}** friend(s) from `{uploaded.name}`")

    with col2:
        st.markdown("**Or use the sample file**")
        if st.button("📂 Load Sample `friends.csv`", use_container_width=True):
            friends, errors = load_friends_from_file("friends.csv")
            if errors:
                for e in errors:
                    st.warning(f"⚠️ {e}")
            if friends:
                st.session_state.friends = friends
                log_entry(f"Loaded {len(friends)} friend(s) from sample CSV", "success")
                st.success(f"✅ Loaded **{len(friends)}** friend(s)")

    # Quick preview
    if st.session_state.friends:
        st.divider()
        st.markdown(f"**{len(st.session_state.friends)} friends loaded** — preview:")
        preview_data = [
            {
                "Name": f.name,
                "Email": f.email,
                "Birthday": f.birthday.strftime("%b %d, %Y"),
                "Nickname": f.nickname or "—",
            }
            for f in st.session_state.friends[:5]
        ]
        st.dataframe(pd.DataFrame(preview_data), use_container_width=True, hide_index=True)
        if len(st.session_state.friends) > 5:
            st.caption(f"...and {len(st.session_state.friends) - 5} more. See **All Friends** tab.")


# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 — Send Birthdays
# ─────────────────────────────────────────────────────────────────────────────
with tab2:
    st.subheader("Send Birthday Emails")

    if not st.session_state.friends:
        st.info("👈 Load your friends list first in the **Load Friends** tab.")
    else:
        col_left, col_right = st.columns([1, 1])

        with col_left:
            st.markdown("**Check date**")
            check_date = st.date_input(
                "Find birthdays on:",
                value=date.today(),
                label_visibility="collapsed",
            )

            birthday_friends = get_todays_birthdays(st.session_state.friends, check_date)

            if birthday_friends:
                st.success(f"🎂 **{len(birthday_friends)} birthday(s)** on {check_date.strftime('%B %d, %Y')}:")
                for f in birthday_friends:
                    st.markdown(f"- **{f.name}** ({f.email}) — turning **{f.age_on(check_date)}** 🎉")
            else:
                st.info(f"No birthdays on {check_date.strftime('%B %d, %Y')}.")

        with col_right:
            if birthday_friends:
                st.markdown("**Email preview**")
                preview_friend = birthday_friends[0]
                preview_text = build_email_text(preview_friend, sender_name or "AutoMail")
                st.text_area("Preview (first recipient)", preview_text, height=220, disabled=True)

        st.divider()

        if birthday_friends:
            if dry_run:
                st.warning("🔍 **Dry Run mode is ON** — emails will be previewed but NOT sent. Toggle it off in the sidebar to send real emails.")

            btn_label = f"🔍 Preview {len(birthday_friends)} Email(s)" if dry_run else f"🚀 Send {len(birthday_friends)} Email(s)"

            if st.button(btn_label, type="primary", use_container_width=True):
                if not dry_run and (not smtp_user or not smtp_pass):
                    st.error("❌ Please fill in your SMTP credentials in the sidebar.")
                else:
                    progress = st.progress(0, text="Starting...")
                    results_sent, results_failed = [], []

                    for i, friend in enumerate(birthday_friends):
                        progress.progress((i) / len(birthday_friends), text=f"Processing {friend.name}...")
                        time.sleep(0.3)

                        if dry_run:
                            log_entry(f"[DRY RUN] Would send to {friend.name} <{friend.email}>", "warn")
                            results_sent.append(friend.name)
                        else:
                            ok, msg = send_birthday_email(
                                friend, smtp_host, smtp_port, smtp_user, smtp_pass, sender_name
                            )
                            if ok:
                                log_entry(f"Email sent → {friend.name} <{friend.email}>", "success")
                                results_sent.append(friend.name)
                            else:
                                log_entry(f"Failed → {friend.name}: {msg}", "error")
                                results_failed.append(friend.name)

                    progress.progress(1.0, text="Done!")
                    time.sleep(0.5)
                    progress.empty()

                    col_s, col_f = st.columns(2)
                    col_s.metric("✅ Sent / Previewed", len(results_sent))
                    col_f.metric("❌ Failed", len(results_failed))

                    if results_failed:
                        st.error(f"Failed: {', '.join(results_failed)}")


# ─────────────────────────────────────────────────────────────────────────────
# TAB 3 — All Friends
# ─────────────────────────────────────────────────────────────────────────────
with tab3:
    st.subheader("All Friends")

    if not st.session_state.friends:
        st.info("No friends loaded yet. Go to the **Load Friends** tab.")
    else:
        today = date.today()

        search = st.text_input("🔍 Search by name or email", placeholder="Type to filter...")

        rows = []
        for f in st.session_state.friends:
            days_until = days_until_birthday(f, today)
            is_today = days_until == 0

            rows.append({
                "🎂": "🎂" if is_today else "",
                "Name": f.name,
                "Nickname": f.nickname or "—",
                "Email": f.email,
                "Birthday": f.birthday.strftime("%b %d"),
                "Days Until": "Today! 🎉" if is_today else f"{days_until} days",
            })

        df = pd.DataFrame(rows)

        if search:
            mask = df["Name"].str.contains(search, case=False) | df["Email"].str.contains(search, case=False)
            df = df[mask]

        st.dataframe(df, use_container_width=True, hide_index=True)
        st.caption(f"Total: {len(st.session_state.friends)} friend(s)")


# ─────────────────────────────────────────────────────────────────────────────
# TAB 4 — Activity Log
# ─────────────────────────────────────────────────────────────────────────────
with tab4:
    st.subheader("Activity Log")

    col_a, col_b = st.columns([4, 1])
    with col_b:
        if st.button("🗑️ Clear Log"):
            st.session_state.logs = []
            st.rerun()

    if not st.session_state.logs:
        st.info("No activity yet. Load friends or send emails to see logs here.")
    else:
        for entry in reversed(st.session_state.logs):
            st.markdown(entry)
