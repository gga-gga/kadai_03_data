"""
データ整形スクリプト
====================
alt_fighters_stats.csv（UFCStats.com 由来のオープンデータ、出典:
GitHub: sagi778/UFC-Data-Extractor）を、本プロジェクト独自のスキーマ
（ufc_scraper.py の出力形式と同一）に変換する。

変換内容:
  height "5'6\""        → height_cm (float)
  weight "135lbs."      → weight_lbs (float)
  reach  "71\""         → reach_cm (float)
  wins/losses/draws     → win_rate (%)
  height_cm, reach_cm   → ape_index = reach_cm / height_cm
  weight_lbs            → weight_class (自動分類)

reach が欠損("--")の選手は ape_index を計算できないため除外する。
"""

import re
import pandas as pd


def parse_height_cm(raw: str):
    if not isinstance(raw, str):
        return None
    m = re.match(r"(\d+)'\s*(\d+)\"", raw.strip())
    if m:
        return round((int(m.group(1)) * 12 + int(m.group(2))) * 2.54, 1)
    return None


def parse_reach_cm(raw: str):
    if not isinstance(raw, str):
        return None
    raw = raw.strip().replace('"', "")
    if not raw or raw == "--":
        return None
    try:
        return round(float(raw) * 2.54, 1)
    except ValueError:
        return None


def parse_weight_lbs(raw: str):
    if not isinstance(raw, str):
        return None
    m = re.search(r"([\d.]+)", raw)
    return float(m.group(1)) if m else None


def parse_pct(raw):
    if pd.isna(raw):
        return None
    if isinstance(raw, str):
        raw = raw.strip().replace("%", "")
        if not raw or raw == "--":
            return None
        try:
            return float(raw)
        except ValueError:
            return None
    return float(raw)


def classify_weight_class(lbs):
    if lbs is None or pd.isna(lbs):
        return "Unknown"
    if lbs <= 115: return "Strawweight"
    if lbs <= 125: return "Flyweight"
    if lbs <= 135: return "Bantamweight"
    if lbs <= 145: return "Featherweight"
    if lbs <= 155: return "Lightweight"
    if lbs <= 170: return "Welterweight"
    if lbs <= 185: return "Middleweight"
    if lbs <= 205: return "Light Heavyweight"
    return "Heavyweight"


def main():
    df = pd.read_csv("alt_fighters_stats.csv")
    print(f"元データ: {len(df)} 行")

    out = pd.DataFrame()
    out["name"] = df["name"]
    out["height_cm"] = df["height"].apply(parse_height_cm)
    out["weight_lbs"] = df["weight"].apply(parse_weight_lbs)
    out["reach_cm"] = df["reach"].apply(parse_reach_cm)
    out["weight_class"] = out["weight_lbs"].apply(classify_weight_class)
    out["stance"] = df["stance"]
    out["dob"] = df["dob"]
    def parse_leading_int(raw):
        if pd.isna(raw):
            return 0
        m = re.match(r"\s*(\d+)", str(raw))
        return int(m.group(1)) if m else 0

    out["wins"] = df["wins"].apply(parse_leading_int)
    out["losses"] = df["losses"].apply(parse_leading_int)
    out["draws"] = df["draws"].apply(parse_leading_int)  # "0 (1 NC)" 等のNCは無視

    total = out["wins"] + out["losses"] + out["draws"]
    out["win_rate"] = (out["wins"] / total * 100).round(1)

    out["slpm"] = df["slpm"]
    out["str_acc"] = df["str_acc"].apply(parse_pct)
    out["sapm"] = df["sapm"]
    out["str_def"] = df["str_def"].apply(parse_pct)
    out["td_avg"] = df["td_avg"]
    out["td_acc"] = df["td_acc"].apply(parse_pct)
    out["td_def"] = df["td_def"].apply(parse_pct)
    out["sub_avg"] = df["sub_avg"]

    out["ape_index"] = (out["reach_cm"] / out["height_cm"]).round(4)
    out["url"] = df["url"]

    before = len(out)
    out = out.dropna(subset=["height_cm", "reach_cm"]).reset_index(drop=True)
    print(f"height_cm / reach_cm has missing values, excluded: {before} -> {len(out)} rows")

    out.to_csv("ufc_analysis_data.csv", index=False, encoding="utf-8-sig")
    print(f"saved: ufc_analysis_data.csv ({len(out)} rows x {len(out.columns)} cols)")
    print(out.head(5).to_string(index=False))


if __name__ == "__main__":
    main()
