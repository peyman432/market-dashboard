# -*- coding: utf-8 -*-
"""
web_sync.py
------------
این اسکریپت رو روی همون سیستمی که الان MySQL و برنامه‌های تحلیلی
(tahlil-hot2 , tahlil_daily_hot3) رو اجرا می‌کنید قرار بدید.

کارش اینه که بعد از هر بار اجرای برنامه‌های تحلیلی:
  1) فایل‌های CSV و PNG خروجی رو از پوشه‌های خودشون جمع می‌کنه
  2) توی یک پوشه یکپارچه به اسم web_export می‌ریزه
  3) یک فایل last_update.json با زمان آخرین آپدیت می‌سازه
  4) با git، این پوشه رو commit و push می‌کنه به گیت‌هاب

نکته امنیتی مهم: هیچ پسورد دیتابیسی توی این فایل یا در ریپوی گیت‌هاب
قرار نمی‌گیره. فقط خروجی نهایی (CSV/PNG) منتقل می‌شه، نه خود دیتابیس.
اتصال دیتابیس همچنان فقط روی سیستم محلی شما باقی می‌مونه.
"""

import os
import shutil
import json
import subprocess
from datetime import datetime

# ---------------------------------------------------------------------------
# تنظیمات - این بخش رو با مسیرهای واقعی سیستم خودتون تطبیق بدید
# ---------------------------------------------------------------------------

# پوشه‌ی ریپوی گیت‌هاب که قبلاً clone کردید (شامل app.py هم هست)
REPO_DIR = r"C:\market-dashboard"          # ویندوز: مسیر پوشه ریپو
# REPO_DIR = "/home/user/market-dashboard" # لینوکس: مسیر پوشه ریپو

# پوشه‌ی داخل ریپو که فایل‌های وب توش قرار می‌گیره (نباید تغییر بدید مگر app.py رو هم عوض کنید)
WEB_EXPORT_DIR = os.path.join(REPO_DIR, "web_export")

# منبع فایل‌های خروجی دو برنامه تحلیلی شما (طبق کدهای اصلی‌شون)
SOURCES = {
    "hot2": {
        "folder": "advanced_market_analysis_comprehensive",
        "csv_files": ["hot_money2_export.csv"],   # این CSV رو باید به tahlil-hot2 اضافه کنید (راهنما در README)
        "png_files": [
            "comprehensive_dashboard.png",
            "money_flow_analysis.png",
            "market_sentiment.png",
            "technical_analysis.png",
            "custom_colored_chart.png",
            "multi_chart_analysis.png",
            "institutional_analysis.png",
            "dashboard_summary.png",
        ],
        "text_files": ["detailed_report.txt"],
    },
    "hot3": {
        "folder": "advanced_stock_analysis",
        "csv_files": ["trading_signals_data_current.csv", "top_trading_signals_current.csv"],
        "png_files": ["trading_signals_analysis_current.png", "advanced_trading_analysis_current.png"],
        "text_files": ["trading_analysis_report_current.txt"],
    },
}


def collect_files():
    """کپی همه‌ی خروجی‌های موجود به web_export"""
    os.makedirs(WEB_EXPORT_DIR, exist_ok=True)
    copied = []
    missing = []

    for source_name, cfg in SOURCES.items():
        dest_dir = os.path.join(WEB_EXPORT_DIR, source_name)
        os.makedirs(dest_dir, exist_ok=True)

        all_files = cfg["csv_files"] + cfg["png_files"] + cfg["text_files"]
        for fname in all_files:
            src_path = os.path.join(cfg["folder"], fname)
            dest_path = os.path.join(dest_dir, fname)
            if os.path.exists(src_path):
                shutil.copy2(src_path, dest_path)
                copied.append(f"{source_name}/{fname}")
            else:
                missing.append(f"{source_name}/{fname}")

    return copied, missing


def write_manifest(copied, missing):
    manifest = {
        "last_update": datetime.now().isoformat(timespec="seconds"),
        "copied_files": copied,
        "missing_files": missing,
    }
    with open(os.path.join(WEB_EXPORT_DIR, "last_update.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)


def git_push():
    """commit و push خودکار به گیت‌هاب"""
    try:
        subprocess.run(["git", "add", "web_export"], cwd=REPO_DIR, check=True)
        commit_msg = f"update dashboard data {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        # اگر تغییری نباشه git commit خطا می‌ده، بی‌خطر از آن عبور می‌کنیم
        subprocess.run(["git", "commit", "-m", commit_msg], cwd=REPO_DIR, check=False)
        subprocess.run(["git", "push"], cwd=REPO_DIR, check=True)
        print("✅ داده‌ها با موفقیت به گیت‌هاب push شدند.")
    except subprocess.CalledProcessError as e:
        print(f"⚠️ خطا در push به گیت‌هاب: {e}")


def main():
    copied, missing = collect_files()
    write_manifest(copied, missing)
    print(f"📦 {len(copied)} فایل کپی شد.")
    if missing:
        print("فایل‌های زیر پیدا نشدند (شاید برنامه هنوز اجرا نشده):")
        for m in missing:
            print("  -", m)
    git_push()


if __name__ == "__main__":
    main()
