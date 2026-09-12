# -*- coding: utf-8 -*-
"""
app.py — داشبورد آنلاین تعاملی بازار سرمایه
این فایل روی Streamlit Community Cloud اجرا می‌شه (رایگان).
داده‌ها رو از پوشه‌ی web_export (که با web_sync.py از سیستم محلی
شما همگام‌سازی می‌شه) می‌خونه — هیچ اتصال مستقیمی به MySQL شما نداره.
"""

import os
import json
from datetime import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------------------------
st.set_page_config(page_title="داشبورد بازار سرمایه", page_icon="📊", layout="wide")

# راست‌چین کردن کل صفحه برای فارسی
st.markdown(
    """
    <style>
        html, body, [class*="css"]  { direction: rtl; text-align: right; font-family: Tahoma, sans-serif; }
        .stDataFrame { direction: ltr; }
    </style>
    """,
    unsafe_allow_html=True,
)

WEB_EXPORT_DIR = "web_export"
HOT2_DIR = os.path.join(WEB_EXPORT_DIR, "hot2")
HOT3_DIR = os.path.join(WEB_EXPORT_DIR, "hot3")

st.title("📊 داشبورد آنلاین تحلیل بازار سرمایه")

# ---------------------------------------------------------------------------
# نوار وضعیت آخرین آپدیت
manifest_path = os.path.join(WEB_EXPORT_DIR, "last_update.json")
if os.path.exists(manifest_path):
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    last_update = manifest.get("last_update", "نامشخص")
    st.caption(f"🕒 آخرین به‌روزرسانی داده‌ها: {last_update}")
else:
    st.warning("هنوز هیچ داده‌ای همگام‌سازی نشده. اسکریپت web_sync.py را روی سیستم محلی اجرا کنید.")

st.button("🔄 بارگذاری مجدد داده‌ها", on_click=st.cache_data.clear)

# ---------------------------------------------------------------------------
@st.cache_data(ttl=60)
def load_csv(path):
    if os.path.exists(path):
        try:
            return pd.read_csv(path, encoding="utf-8-sig")
        except Exception:
            return pd.read_csv(path)
    return None


signals_df = load_csv(os.path.join(HOT3_DIR, "trading_signals_data_current.csv"))
top_stocks_df = load_csv(os.path.join(HOT3_DIR, "top_trading_signals_current.csv"))
hot2_df = load_csv(os.path.join(HOT2_DIR, "hot_money2_export.csv"))

tab1, tab2, tab3 = st.tabs(["📈 سیگنال‌های معاملاتی", "💰 جریان پول هوشمند", "🖼️ گالری نمودارها"])

# ---------------------------------------------------------------------------
# تب ۱: سیگنال‌های معاملاتی (تعاملی: فیلتر + زوم + جدول)
# ---------------------------------------------------------------------------
with tab1:
    if signals_df is not None and not signals_df.empty:
        with st.sidebar:
            st.header("🔎 فیلترهای سیگنال‌ها")
            text_cols = [c for c in signals_df.columns if signals_df[c].dtype == object]
            symbol_col = next((c for c in text_cols if "نماد" in c or "symbol" in c.lower()), text_cols[0] if text_cols else None)

            if symbol_col:
                symbols = sorted(signals_df[symbol_col].dropna().unique().tolist())
                selected_symbols = st.multiselect("انتخاب نماد", symbols, default=symbols[:10] if len(symbols) > 10 else symbols)
            else:
                selected_symbols = None

            numeric_cols = signals_df.select_dtypes("number").columns.tolist()
            selected_metric = st.selectbox("شاخص برای نمودار", numeric_cols) if numeric_cols else None

        filtered = signals_df.copy()
        if symbol_col and selected_symbols:
            filtered = filtered[filtered[symbol_col].isin(selected_symbols)]

        st.subheader("جدول سیگنال‌های معاملاتی (زنده)")
        st.dataframe(filtered, use_container_width=True, height=350)

        if selected_metric and symbol_col:
            st.subheader(f"نمودار مقایسه‌ای «{selected_metric}»")
            fig = px.bar(filtered, x=symbol_col, y=selected_metric, color=symbol_col)
            fig.update_layout(showlegend=False, dragmode="zoom")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("داده‌ی سیگنال‌های معاملاتی هنوز همگام‌سازی نشده است.")

    if top_stocks_df is not None and not top_stocks_df.empty:
        st.subheader("🏆 برترین سهام از نظر سیگنال")
        st.dataframe(top_stocks_df, use_container_width=True)

# ---------------------------------------------------------------------------
# تب ۲: جریان پول هوشمند (Hot Money)
# ---------------------------------------------------------------------------
with tab2:
    if hot2_df is not None and not hot2_df.empty:
        num_cols = hot2_df.select_dtypes("number").columns.tolist()
        if num_cols:
            metric = st.selectbox("شاخص برای نمایش روند زمانی", num_cols, key="hot2_metric")
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(y=hot2_df[metric], mode="lines+markers", name=metric))
            fig2.update_layout(title=f"روند {metric}", dragmode="zoom", xaxis_title="زمان (ایندکس)", yaxis_title=metric)
            st.plotly_chart(fig2, use_container_width=True)

        st.subheader("جدول کامل داده‌های جریان پول")
        st.dataframe(hot2_df, use_container_width=True, height=350)
    else:
        st.info(
            "داده‌ی جریان پول هوشمند هنوز همگام‌سازی نشده است. "
            "برای فعال‌سازی این بخش باید در tahlil-hot2 خروجی df را با "
            "`df.to_csv('advanced_market_analysis_comprehensive/hot_money2_export.csv', "
            "index=False, encoding='utf-8-sig')` ذخیره کنید."
        )

# ---------------------------------------------------------------------------
# تب ۳: گالری نمودارهای PNG تولیدشده توسط برنامه‌های اصلی (همان نمودارهای matplotlib)
# ---------------------------------------------------------------------------
with tab3:
    st.subheader("نمودارهای تولید شده توسط موتور تحلیل")
    cols = st.columns(2)
    idx = 0
    for source_dir, label in [(HOT2_DIR, "تحلیل پول هوشمند (Hot2)"), (HOT3_DIR, "سیگنال‌های معاملاتی (Hot3)")]:
        if os.path.isdir(source_dir):
            pngs = [f for f in os.listdir(source_dir) if f.lower().endswith(".png")]
            for png in sorted(pngs):
                with cols[idx % 2]:
                    st.image(os.path.join(source_dir, png), caption=f"{label} — {png}", use_container_width=True)
                idx += 1
    if idx == 0:
        st.info("هنوز تصویری همگام‌سازی نشده است.")

st.caption("این داشبورد به‌صورت خودکار هر بار که داده‌های جدید از سیستم محلی push شود، به‌روزرسانی می‌شود.")
