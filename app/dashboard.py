from __future__ import annotations

from datetime import datetime
import sys
from pathlib import Path

import pandas as pd
import streamlit as st
from sqlalchemy import select

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.db import get_session, init_db
from app.digest import generate_daily_digest
from app.manual_intake import save_manual_input
from app.models import Lead
from app.run_collectors import run_all_collectors

st.set_page_config(page_title="LensLead UK", page_icon="📸", layout="wide")

CUSTOM_CSS = """
<style>
.stApp { background: #f7f7f5; color: #111; }
.block-container { padding-top: 2rem; max-width: 1200px; }
.card { background: #f1f1ef; border: 1px solid #e1e1dd; border-radius: 18px; padding: 16px; margin-bottom: 12px; }
.pill { display:inline-block; border-radius:999px; padding:2px 10px; font-size:12px; border:1px solid #d8d8d5; background:#fff; }
.title { font-size: 2rem; font-weight: 600; letter-spacing: -0.02em; margin-bottom: 1rem; }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
st.markdown('<div class="title">LensLead UK</div>', unsafe_allow_html=True)

init_db()


def load_leads() -> list[Lead]:
    with get_session() as session:
        return session.scalars(select(Lead).order_by(Lead.relevance_score.desc(), Lead.created_at.desc())).all()


def to_df(leads: list[Lead]) -> pd.DataFrame:
    rows = []
    for lead in leads:
        rows.append(
            {
                "id": lead.id,
                "title": lead.title,
                "company": lead.company,
                "location": lead.location,
                "category": lead.category,
                "media_type": lead.media_type,
                "role_type": lead.role_type,
                "score": lead.relevance_score,
                "pay": lead.pay_text,
                "status": lead.status,
                "source": lead.source,
                "posted_date": lead.posted_date,
                "apply_url": lead.apply_url,
                "why_high": lead.score_reasons,
                "red_flags": lead.red_flags,
            }
        )
    return pd.DataFrame(rows)


def render_filters(df: pd.DataFrame) -> pd.DataFrame:
    cols = st.columns(5)
    categories = cols[0].multiselect("Category", sorted(df["category"].dropna().unique()), default=list(df["category"].dropna().unique()))
    sources = cols[1].multiselect("Source", sorted(df["source"].dropna().unique()), default=list(df["source"].dropna().unique()))
    media = cols[2].multiselect("Media", sorted(df["media_type"].dropna().unique()), default=list(df["media_type"].dropna().unique()))
    role = cols[3].multiselect("Role", sorted(df["role_type"].dropna().unique()), default=list(df["role_type"].dropna().unique()))
    statuses = cols[4].multiselect("Status", sorted(df["status"].dropna().unique()), default=list(df["status"].dropna().unique()))
    score_min = st.slider("Minimum score", 0, 100, 0)
    filtered = df[
        (df["category"].isin(categories))
        & (df["source"].isin(sources))
        & (df["media_type"].isin(media))
        & (df["role_type"].isin(role))
        & (df["status"].isin(statuses))
        & (df["score"] >= score_min)
    ]
    sort_col = st.selectbox("Sort by", ["score", "posted_date", "pay", "category"])
    return filtered.sort_values(sort_col, ascending=False)


def render_leads_table(df: pd.DataFrame, category: str | None = None) -> None:
    view = df if category is None else df[df["category"] == category]
    st.dataframe(view, use_container_width=True, hide_index=True)
    lead_id = st.number_input("Lead ID to update status", min_value=0, step=1)
    new_status = st.selectbox("New status", ["new", "shortlisted", "applied", "contacted", "ignored", "expired"])
    if st.button("Update status"):
        with get_session() as session:
            lead = session.get(Lead, int(lead_id))
            if lead:
                lead.status = new_status
                lead.updated_at = datetime.utcnow()
                st.success(f"Lead {lead_id} updated to {new_status}")
            else:
                st.warning("Lead not found.")


leads = load_leads()
df = to_df(leads) if leads else pd.DataFrame(
    columns=["id", "title", "company", "location", "category", "media_type", "role_type", "score", "pay", "status", "source", "posted_date", "apply_url", "why_high", "red_flags"]
)

tab_overview, tab_wedding, tab_events, tab_general, tab_manual, tab_settings = st.tabs(
    ["Overview", "Wedding", "Events", "General", "Manual Intake", "Settings"]
)

with tab_overview:
    if st.button("Run collectors now"):
        summary = run_all_collectors()
        st.json(summary)
        st.rerun()
    if not df.empty:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.write(f"Total new leads: {len(df[df['status'] == 'new'])}")
        st.write(f"Top wedding leads: {len(df[df['category'] == 'wedding'])}")
        st.write(f"Top event leads: {len(df[df['category'] == 'event'])}")
        st.write(f"Top general leads: {len(df[df['category'] == 'general'])}")
        st.markdown("</div>", unsafe_allow_html=True)
        st.bar_chart(df.groupby("source")["id"].count())
        st.bar_chart(df.groupby("category")["id"].count())
        filtered = render_filters(df)
        render_leads_table(filtered)

with tab_wedding:
    if not df.empty:
        render_leads_table(render_filters(df), "wedding")

with tab_events:
    if not df.empty:
        render_leads_table(render_filters(df), "event")

with tab_general:
    if not df.empty:
        render_leads_table(render_filters(df), "general")

with tab_manual:
    pasted_text = st.text_area("Paste a post, email, WhatsApp message, Instagram caption, or advert", height=220)
    if st.button("Classify and save manual lead"):
        if pasted_text.strip():
            with get_session() as session:
                lead = save_manual_input(session, pasted_text)
                if lead:
                    st.success(f"Saved lead #{lead.id} ({lead.category}) score {int(lead.relevance_score)}")
                    st.caption(f"Why this scored highly: {lead.score_reasons or 'N/A'}")
                    st.caption(f"Possible red flags: {lead.red_flags or 'None'}")
                else:
                    st.info("Looks like a duplicate lead, so it was skipped.")
        else:
            st.warning("Please paste some text.")

with tab_settings:
    st.write("API Key status")
    import os
    st.write(f"REED_API_KEY: {'✅ set' if os.getenv('REED_API_KEY') else '❌ missing'}")
    st.write(f"ADZUNA_APP_ID: {'✅ set' if os.getenv('ADZUNA_APP_ID') else '❌ missing'}")
    st.write(f"ADZUNA_APP_KEY: {'✅ set' if os.getenv('ADZUNA_APP_KEY') else '❌ missing'}")
    st.write(f"SERPAPI_API_KEY: {'✅ set' if os.getenv('SERPAPI_API_KEY') else '❌ missing'}")
    st.write(f"OPENAI_API_KEY: {'✅ set' if os.getenv('OPENAI_API_KEY') else '❌ missing'}")
    st.download_button("Export CSV", data=df.to_csv(index=False).encode("utf-8"), file_name="lenslead_uk_leads.csv")
    if st.button("Generate daily digest markdown"):
        with get_session() as session:
            digest = generate_daily_digest(session)
        st.code(digest, language="markdown")
