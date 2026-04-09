from __future__ import annotations

import os
from datetime import date, timedelta

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from sqlalchemy import create_engine, text

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Habit Tracker",
    page_icon="📊",
    layout="wide",
)

# ── DB connection ─────────────────────────────────────────────────────────────

@st.cache_resource
def get_engine():
    url = os.environ["DATABASE_URL"]
    url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return create_engine(
        url,
        pool_pre_ping=True,
        connect_args={"sslmode": "require"},
    )


@st.cache_data(ttl=60)
def load_habits() -> pd.DataFrame:
    with get_engine().connect() as conn:
        return pd.read_sql(
            "SELECT id::text, name, type, is_active FROM habits ORDER BY created_at",
            conn,
        )


@st.cache_data(ttl=60)
def load_logs(habit_id: str, start: date, end: date) -> pd.DataFrame:
    with get_engine().connect() as conn:
        return pd.read_sql(
            text(
                "SELECT date, value FROM habit_logs "
                "WHERE habit_id = :hid AND date BETWEEN :start AND :end "
                "ORDER BY date"
            ),
            conn,
            params={"hid": habit_id, "start": start, "end": end},
        )


# ── Value helpers ─────────────────────────────────────────────────────────────

TERNARY_COLOR = {0: "#2ecc71", 1: "#f1c40f", 2: "#e74c3c"}
BOOLEAN_COLOR = {0: "#e74c3c", 1: "#2ecc71"}

TERNARY_LABEL = {0: "🟢 Норм", 1: "🟡 Немного", 2: "🔴 Много"}
BOOLEAN_LABEL = {0: "❌ Пропустил", 1: "✅ Сделал"}


def value_label(habit_type: str, value: int) -> str:
    if habit_type == "ternary":
        return TERNARY_LABEL.get(value, str(value))
    return BOOLEAN_LABEL.get(value, str(value))


# ── Streak calculation ────────────────────────────────────────────────────────

def compute_streaks(df: pd.DataFrame) -> tuple[int, int]:
    if df.empty:
        return 0, 0

    filled = sorted(pd.to_datetime(df["date"]).dt.date.tolist())
    date_set = set(filled)

    current = 0
    d = date.today()
    while d in date_set:
        current += 1
        d -= timedelta(days=1)

    best = 1
    streak = 1
    for i in range(1, len(filled)):
        if (filled[i] - filled[i - 1]).days == 1:
            streak += 1
            best = max(best, streak)
        else:
            streak = 1
    best = max(best, streak, current)

    return current, best


# ── Calendar heatmap ──────────────────────────────────────────────────────────

def calendar_heatmap(df: pd.DataFrame, habit_type: str, title: str) -> go.Figure:
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["week"] = df["date"].dt.isocalendar().week.astype(int)
    df["year"] = df["date"].dt.year
    df["dow"] = df["date"].dt.dayofweek  # 0=Mon
    df["yw"] = df["year"].astype(str) + "-W" + df["week"].astype(str).str.zfill(2)

    pivot = df.pivot_table(index="dow", columns="yw", values="value", aggfunc="first")
    pivot = pivot.reindex(index=list(range(7)))

    if habit_type == "ternary":
        colorscale = [[0, "#2ecc71"], [0.5, "#f1c40f"], [1.0, "#e74c3c"]]
        zmin, zmax = 0, 2
    else:
        colorscale = [[0, "#e74c3c"], [1.0, "#2ecc71"]]
        zmin, zmax = 0, 1

    day_names = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

    fig = go.Figure(
        go.Heatmap(
            z=pivot.values,
            x=pivot.columns.tolist(),
            y=day_names,
            colorscale=colorscale,
            zmin=zmin,
            zmax=zmax,
            showscale=False,
            xgap=2,
            ygap=2,
        )
    )
    fig.update_layout(
        title=title,
        height=200,
        margin=dict(l=0, r=0, t=40, b=0),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(autorange="reversed"),
    )
    return fig


# ── Trend line ────────────────────────────────────────────────────────────────

def trend_chart(df: pd.DataFrame, habit_type: str, title: str) -> go.Figure:
    df = df.copy().sort_values("date")
    df["date"] = pd.to_datetime(df["date"])
    df["rolling"] = df["value"].rolling(7, min_periods=1).mean()

    if habit_type == "ternary":
        tick_vals = [0, 1, 2]
        tick_text = ["🟢 Норм", "🟡 Немного", "🔴 Много"]
        yrange = [-0.2, 2.2]
    else:
        tick_vals = [0, 1]
        tick_text = ["❌ Нет", "✅ Да"]
        yrange = [-0.2, 1.2]

    colors = [
        (TERNARY_COLOR if habit_type == "ternary" else BOOLEAN_COLOR).get(int(v), "#888")
        for v in df["value"]
    ]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["value"],
            mode="markers",
            marker=dict(color=colors, size=8),
            name="Значение",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["rolling"],
            mode="lines",
            line=dict(color="#7f8c8d", width=2, dash="dot"),
            name="Скользящее среднее (7д)",
        )
    )
    fig.update_layout(
        title=title,
        height=300,
        yaxis=dict(tickvals=tick_vals, ticktext=tick_text, range=yrange),
        margin=dict(l=0, r=0, t=40, b=0),
        legend=dict(orientation="h", y=-0.2),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


# ── Sidebar ───────────────────────────────────────────────────────────────────

habits_df = load_habits()

with st.sidebar:
    st.title("📊 Habit Tracker")

    show_archived = st.checkbox("Показать архивированные", value=False)

    st.divider()

    period = st.selectbox(
        "Период",
        ["Последние 30 дней", "Последние 90 дней", "Последние 365 дней", "Всё время"],
    )
    today = date.today()
    period_map = {
        "Последние 30 дней": today - timedelta(days=30),
        "Последние 90 дней": today - timedelta(days=90),
        "Последние 365 дней": today - timedelta(days=365),
        "Всё время": date(2000, 1, 1),
    }
    start_date = period_map[period]

    st.divider()
    chart_type = st.radio("График", ["Календарь (heatmap)", "Тренд"])

filtered = habits_df if show_archived else habits_df[habits_df["is_active"]]

if filtered.empty:
    st.warning("Нет привычек.")
    st.stop()

# ── Helper: render one habit card ─────────────────────────────────────────────

def render_habit(habit_row: pd.Series) -> None:
    habit_id = habit_row["id"]
    habit_type = habit_row["type"]
    name = habit_row["name"]

    logs = load_logs(habit_id, start_date, today)

    cur_streak, best_streak = compute_streaks(logs)
    fill_rate = round(len(logs) / max((today - start_date).days, 1) * 100, 1)
    last_val = value_label(habit_type, int(logs.iloc[-1]["value"])) if not logs.empty else "—"

    with st.container(border=True):
        st.subheader(name)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Серия", f"{cur_streak} дн.")
        m2.metric("Лучшая серия", f"{best_streak} дн.")
        m3.metric("Дней заполнено", f"{len(logs)}")
        m4.metric("Заполнено", f"{fill_rate}%")

        if logs.empty:
            st.info("Нет данных за выбранный период.")
            return

        if chart_type == "Календарь (heatmap)":
            st.plotly_chart(
                calendar_heatmap(logs, habit_type, ""),
                use_container_width=True,
            )
        else:
            st.plotly_chart(
                trend_chart(logs, habit_type, ""),
                use_container_width=True,
            )


# ── Main area: two sections by type ──────────────────────────────────────────

ternary_habits = filtered[filtered["type"] == "ternary"]
boolean_habits = filtered[filtered["type"] == "boolean"]

if not ternary_habits.empty:
    st.header("🎚️ Ternary-привычки (0 / 1 / 2)")
    cols = st.columns(min(len(ternary_habits), 2))
    for i, (_, row) in enumerate(ternary_habits.iterrows()):
        with cols[i % 2]:
            render_habit(row)

if not boolean_habits.empty:
    st.header("✅ Boolean-привычки (да / нет)")
    cols = st.columns(min(len(boolean_habits), 2))
    for i, (_, row) in enumerate(boolean_habits.iterrows()):
        with cols[i % 2]:
            render_habit(row)
