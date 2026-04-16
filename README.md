# Habit Tracker Bot

A personal Telegram bot for tracking daily habits, with a Streamlit dashboard for visualizing progress.

> **Single-user by design.** The bot only responds to one configured Telegram account (`OWNER_ID`). There is no multi-user support.

## Features

- Two habit types: **boolean** (yes/no) and **ternary** (0 / a bit / a lot)
- Log habits for today or any past date
- Daily reminder at a configurable time
- Archive habits without losing historical data
- Streamlit dashboard with calendar heatmaps and trend charts

## Stack

- **Bot:** Python 3.12, [aiogram 3](https://docs.aiogram.dev/), APScheduler
- **Dashboard:** Streamlit, Plotly, pandas, SQLAlchemy
- **Database:** PostgreSQL (tested with [Supabase](https://supabase.com) free tier)
- **Hosting:** [Fly.io](https://fly.io)

## Setup

### 1. Prerequisites

- Python 3.12+
- A PostgreSQL database (Supabase free tier works well)
- A Telegram bot token from [@BotFather](https://t.me/BotFather)
- Your Telegram numeric user ID (get it from [@userinfobot](https://t.me/userinfobot))

### 2. Database

Run the schema against your PostgreSQL instance:

```bash
psql "$DATABASE_URL" -f db/schema.sql
```

### 3. Environment variables

Create a `.env` file in the project root:

```env
BOT_TOKEN=your_telegram_bot_token
DATABASE_URL=postgresql://user:password@host:5432/dbname
OWNER_ID=123456789

# Optional — defaults shown
REMINDER_HOUR=23
REMINDER_MINUTE=0
TIMEZONE=Europe/Warsaw
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Run locally

**Bot:**
```bash
python -m bot.main
```

**Dashboard** (in a separate terminal):
```bash
cd dashboard
streamlit run app.py
```

## Deploy to Fly.io

### Bot

```bash
# Install flyctl: https://fly.io/docs/hands-on/install-flyctl/
fly launch          # first time only — creates fly.toml
fly secrets set BOT_TOKEN=... DATABASE_URL=... OWNER_ID=...
fly deploy
```

Edit `fly.toml` to change the reminder time or timezone:

```toml
[env]
  REMINDER_HOUR   = "23"
  REMINDER_MINUTE = "0"
  TIMEZONE        = "Europe/Warsaw"
```

### Dashboard

The dashboard is a separate Streamlit app. The easiest free option is [Streamlit Community Cloud](https://streamlit.io/cloud):

1. Push the repo to GitHub
2. Connect the repo in Streamlit Cloud, set the main file to `dashboard/app.py`
3. Add `DATABASE_URL` in the Streamlit Cloud secrets

## Bot commands

| Command | Description |
|---------|-------------|
| `/log` | Log habits for today or a past date |
| `/status` | See what's already filled in today |
| `/habits` | List all habits |
| `/add_habit` | Add a new habit |
| `/archive_habit` | Archive a habit (data is preserved) |
| `/cancel` | Cancel the current action |

## Project structure

```
├── bot/
│   ├── handlers/        # Telegram command/callback handlers
│   │   ├── general.py   # /start, /help, /cancel
│   │   ├── habits.py    # /add_habit, /archive_habit, /habits
│   │   ├── log.py       # /log
│   │   └── status.py    # /status
│   ├── config.py        # Settings via pydantic-settings
│   ├── database.py      # Async DB queries
│   ├── keyboards.py     # Inline keyboard builders
│   ├── middleware.py    # Owner-only access guard
│   ├── scheduler.py     # Daily reminder job
│   └── main.py          # Entry point
├── dashboard/
│   └── app.py           # Streamlit dashboard
├── db/
│   └── schema.sql       # PostgreSQL schema
├── Dockerfile
├── fly.toml
└── requirements.txt
```

## License

MIT
