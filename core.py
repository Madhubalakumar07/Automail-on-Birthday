"""
core.py — Birthday checking and email sending logic for AutoMail.
"""

import csv
import smtplib
import logging
from calendar import isleap
from datetime import date, datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

log = logging.getLogger("automail")


def _birthday_for_year(birthday: date, year: int) -> date:
    if birthday.month == 2 and birthday.day == 29 and not isleap(year):
        return date(year, 2, 28)
    return birthday.replace(year=year)


@dataclass
class Friend:
    name: str
    email: str
    birthday: date
    nickname: str

    @property
    def display_name(self) -> str:
        return self.nickname if self.nickname else self.name.split()[0]

    def age_on(self, on_date: Optional[date] = None) -> int:
        on_date = on_date or date.today()
        years = on_date.year - self.birthday.year
        if on_date < _birthday_for_year(self.birthday, on_date.year):
            years -= 1
        return years

    @property
    def age(self) -> int:
        return self.age_on()


def load_friends_from_file(path: str) -> tuple[list[Friend], list[str]]:
    """Load friends from CSV. Returns (friends, errors)."""
    friends, errors = [], []
    try:
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            required = {"name", "email", "birthday"}
            if not required.issubset(set(reader.fieldnames or [])):
                missing = required - set(reader.fieldnames or [])
                return [], [f"Missing columns: {missing}"]
            for i, row in enumerate(reader, 2):
                try:
                    bday = datetime.strptime(row["birthday"].strip(), "%Y-%m-%d").date()
                    friends.append(Friend(
                        name=row["name"].strip(),
                        email=row["email"].strip(),
                        birthday=bday,
                        nickname=row.get("nickname", "").strip(),
                    ))
                except ValueError as e:
                    errors.append(f"Row {i}: {e}")
    except Exception as e:
        return [], [str(e)]
    return friends, errors


def load_friends_from_csv_text(content: str) -> tuple[list[Friend], list[str]]:
    """Load friends from raw CSV string (for uploaded files)."""
    import io
    friends, errors = [], []
    reader = csv.DictReader(io.StringIO(content))
    required = {"name", "email", "birthday"}
    if not required.issubset(set(reader.fieldnames or [])):
        return [], [f"Missing columns: {required - set(reader.fieldnames or [])}"]
    for i, row in enumerate(reader, 2):
        try:
            bday = datetime.strptime(row["birthday"].strip(), "%Y-%m-%d").date()
            friends.append(Friend(
                name=row["name"].strip(),
                email=row["email"].strip(),
                birthday=bday,
                nickname=row.get("nickname", "").strip(),
            ))
        except ValueError as e:
            errors.append(f"Row {i}: {e}")
    return friends, errors


def get_todays_birthdays(friends: list[Friend], check_date: Optional[date] = None) -> list[Friend]:
    check_date = check_date or date.today()
    return [f for f in friends if f.birthday.month == check_date.month and f.birthday.day == check_date.day]


def days_until_birthday(friend: Friend, from_date: Optional[date] = None) -> int:
    from_date = from_date or date.today()
    next_birthday = _birthday_for_year(friend.birthday, from_date.year)
    if next_birthday < from_date:
        next_birthday = _birthday_for_year(friend.birthday, from_date.year + 1)
    return (next_birthday - from_date).days


def build_email_text(friend: Friend, sender_name: str) -> str:
    return (
        f"Subject: 🎂 Happy Birthday, {friend.display_name}!\n\n"
        f"Hey {friend.display_name}!\n\n"
        f"Today is your special day and we wanted you to know you're being thought of! 🎉\n\n"
        f"Wishing you a birthday filled with joy, laughter, and everything your heart desires.\n\n"
        f"🎈 🎁 🍰 🥂 🎊\n\n"
        f"Happy Birthday!\n— {sender_name}"
    )


def send_birthday_email(
    friend: Friend,
    smtp_host: str,
    smtp_port: int,
    smtp_user: str,
    smtp_pass: str,
    sender_name: str,
) -> tuple[bool, str]:
    """Send one email. Returns (success, message)."""
    body = (
        f"Hey {friend.display_name}!\n\n"
        f"Today is your special day and we wanted you to know you're being thought of! 🎉\n\n"
        f"Wishing you a birthday filled with joy, laughter, and everything your heart desires.\n\n"
        f"🎈 🎁 🍰 🥂 🎊\n\n"
        f"Happy Birthday!\n— {sender_name}"
    )

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🎂 Happy Birthday, {friend.display_name}!"
    msg["From"] = f"{sender_name} <{smtp_user}>"
    msg["To"] = f"{friend.name} <{friend.email}>"
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, friend.email, msg.as_string())
        return True, f"Sent to {friend.name} <{friend.email}>"
    except smtplib.SMTPAuthenticationError:
        return False, "Authentication failed — check credentials or use an App Password."
    except smtplib.SMTPException as e:
        return False, str(e)
    except Exception as e:
        return False, str(e)
