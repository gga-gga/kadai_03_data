"""
UFC Fighter Stats Scraper
=========================
データソース : http://ufcstats.com  (静的HTML / スクレイピング可)
対象選手数   : 約 3,000〜3,500 人 (全 UFC 登録選手)
実行時間目安 : 全件取得で 90〜120 分 (rate limit 0.8s/req)

取得フィールド:
  基本情報  - 名前, 身長(cm), 体重(lbs), リーチ(cm), スタンス, 生年月日
  体重クラス - 自動分類 (Flyweight〜Heavyweight)
  戦績      - 勝/負/引分, 勝率(%)
  打撃統計  - SLpM(分当打撃数), 命中率(%), SApM(被弾数), 回避率(%)
  組技統計  - TD平均, TD命中率(%), TD阻止率(%), サブミッション平均
  独自指標  - エイプ・インデックス = リーチ(cm) ÷ 身長(cm)

使い方:
  # 動作確認 (a始まり 50人, 約1分)
  python ufc_scraper.py --chars a --limit 50

  # 特定階級を絞る例 (c始まりのみ)
  python ufc_scraper.py --chars c

  # 全選手取得 (約2時間)
  python ufc_scraper.py
"""

import re
import time
import string
import logging
import argparse

import requests
from bs4 import BeautifulSoup
import pandas as pd

# ── 設定 ──────────────────────────────────────────────────────────────────────
BASE_URL      = "http://ufcstats.com"
LIST_URL      = BASE_URL + "/statistics/fighters?char={char}&page=all"
OUTPUT_CSV    = "ufc_fighters_raw.csv"
REQUEST_DELAY = 0.8          # サーバー負荷軽減 (秒)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


# ── ユーティリティ関数 ─────────────────────────────────────────────────────────

def parse_height_cm(raw: str) -> float | None:
    """フィート・インチ表記 → cm 変換。例: "5' 11\"" → 180.3"""
    m = re.match(r"(\d+)'\s*(\d+)\"", raw.strip())
    if m:
        return round((int(m.group(1)) * 12 + int(m.group(2))) * 2.54, 1)
    return None


def parse_reach_cm(raw: str) -> float | None:
    """インチ表記 → cm 変換。例: "72.0\"" → 182.9"""
    raw = raw.strip().replace('"', "")
    if not raw or raw == "--":
        return None
    try:
        return round(float(raw) * 2.54, 1)
    except ValueError:
        return None


def parse_weight_lbs(raw: str) -> float | None:
    """例: "155 lbs." → 155.0"""
    m = re.search(r"([\d.]+)", raw)
    return float(m.group(1)) if m else None


def parse_pct(raw: str) -> float | None:
    """例: "64%" → 64.0"""
    raw = raw.strip().replace("%", "")
    if not raw or raw == "--":
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def parse_float(raw: str) -> float | None:
    raw = raw.strip()
    if not raw or raw == "--":
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def classify_weight_class(lbs: float | None) -> str:
    """体重(lbs)から階級名を返す"""
    if lbs is None:
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


# ── Step 1: 選手 URL リスト取得 ────────────────────────────────────────────────

def get_fighter_urls(char: str) -> list[str]:
    """
    アルファベット 1 文字に対応する選手一覧ページから
    全選手の詳細ページ URL を収集する。

    例: char='a' → 約230人分の URL リストを返す
    """
    url = LIST_URL.format(char=char)
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        log.warning(f"リスト取得失敗 (char={char}): {e}")
        return []

    soup  = BeautifulSoup(resp.text, "html.parser")
    table = soup.find("table", class_="b-statistics__table")
    if not table:
        log.warning(f"テーブルが見つかりません (char={char})")
        return []

    urls = []
    for row in table.find_all("tr")[1:]:   # 先頭ヘッダー行をスキップ
        link = row.find("a", href=True)
        if link and "/fighter-details/" in link["href"]:
            urls.append(link["href"])
    return urls


# ── Step 2: 個別選手ページのスクレイピング ─────────────────────────────────────

def scrape_fighter(url: str) -> dict | None:
    """
    選手詳細ページ (http://ufcstats.com/fighter-details/XXXXXXXX)
    から全スタッツを取得して dict で返す。

    Returns None if the request fails.
    """
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        log.warning(f"取得失敗 {url}: {e}")
        return None

    soup = BeautifulSoup(resp.text, "html.parser")

    # ── 名前 ──────────────────────────────────────────────────
    name_tag = soup.find("span", class_="b-content__title-highlight")
    name = name_tag.text.strip() if name_tag else ""

    # ── 戦績 (W-L-D) ───────────────────────────────────────────
    record_tag = soup.find("span", class_="b-content__title-record")
    wins = losses = draws = 0
    if record_tag:
        m = re.search(r"(\d+)-(\d+)-(\d+)", record_tag.text)
        if m:
            wins, losses, draws = int(m.group(1)), int(m.group(2)), int(m.group(3))

    total    = wins + losses + draws
    win_rate = round(wins / total * 100, 1) if total > 0 else None

    # ── 基本情報 (身長/体重/リーチ/スタンス/生年月日) ─────────────
    info = {}
    info_box = soup.find("div", class_="b-list__info-box")
    if info_box:
        for li in info_box.find_all("li", class_="b-list__box-list-item"):
            title_tag = li.find("i", class_="b-list__box-item-title")
            if title_tag:
                label = title_tag.text.strip().rstrip(":").lower()
                value = li.text.replace(title_tag.text, "").strip()
                info[label] = value

    height_cm  = parse_height_cm(info.get("height", ""))
    weight_lbs = parse_weight_lbs(info.get("weight", ""))
    reach_cm   = parse_reach_cm(info.get("reach", ""))
    stance     = info.get("stance", "").strip() or None
    dob        = info.get("dob", "").strip() or None

    # ── パフォーマンス統計 ────────────────────────────────────────
    # ページ左右の stat box を両方スキャン
    stats = {}
    for box in soup.find_all("div", class_=re.compile(r"b-list__info-box-(left|right)")):
        for li in box.find_all("li", class_="b-list__box-list-item"):
            title_tag = li.find("i", class_="b-list__box-item-title")
            if title_tag:
                label = title_tag.text.strip().rstrip(":").lower()
                value = li.text.replace(title_tag.text, "").strip()
                stats[label] = value

    slpm    = parse_float(stats.get("slpm",      ""))   # Significant Strikes Landed /min
    str_acc = parse_pct(stats.get("str. acc.",   ""))   # 打撃命中率 (%)
    sapm    = parse_float(stats.get("sapm",      ""))   # Significant Strikes Absorbed /min
    str_def = parse_pct(stats.get("str. def",    ""))   # 打撃回避率 (%)
    td_avg  = parse_float(stats.get("td avg.",   ""))   # テイクダウン平均 /15min
    td_acc  = parse_pct(stats.get("td acc.",     ""))   # テイクダウン命中率 (%)
    td_def  = parse_pct(stats.get("td def.",     ""))   # テイクダウン阻止率 (%)
    sub_avg = parse_float(stats.get("sub. avg.", ""))   # サブミッション平均 /15min

    # ── 独自指標: エイプ・インデックス ───────────────────────────
    # 定義: リーチ(cm) ÷ 身長(cm)
    # 1.00 超 = リーチが身長を上回る → 打撃レンジに優位性あり
    ape_index = None
    if height_cm and reach_cm and height_cm > 0:
        ape_index = round(reach_cm / height_cm, 4)

    return {
        # 識別情報
        "name":         name,
        "url":          url,
        # 基本情報
        "weight_class": classify_weight_class(weight_lbs),
        "height_cm":    height_cm,
        "weight_lbs":   weight_lbs,
        "reach_cm":     reach_cm,
        "stance":       stance,
        "dob":          dob,
        # 戦績
        "wins":         wins,
        "losses":       losses,
        "draws":        draws,
        "win_rate":     win_rate,
        # 打撃統計
        "slpm":         slpm,
        "str_acc":      str_acc,
        "sapm":         sapm,
        "str_def":      str_def,
        # 組技統計
        "td_avg":       td_avg,
        "td_acc":       td_acc,
        "td_def":       td_def,
        "sub_avg":      sub_avg,
        # 独自派生指標
        "ape_index":    ape_index,
    }


# ── メイン処理 ─────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="UFC Fighter Stats Scraper")
    parser.add_argument(
        "--chars",  default="",
        help="対象アルファベット文字列 例: abc  (省略時=全26文字)"
    )
    parser.add_argument(
        "--limit", type=int, default=0,
        help="取得上限人数 0=無制限"
    )
    parser.add_argument(
        "--output", default=OUTPUT_CSV,
        help="出力CSVファイルパス"
    )
    args = parser.parse_args()

    chars = args.chars.lower() if args.chars else string.ascii_lowercase

    # ── Step 1: 全選手 URL を収集 ──────────────────────────────────
    log.info("Step 1: 選手 URL リストを収集中...")
    all_urls: list[str] = []
    for char in chars:
        urls = get_fighter_urls(char)
        all_urls.extend(urls)
        log.info(f"  '{char}' → {len(urls)} 人")
        time.sleep(REQUEST_DELAY)

    if args.limit:
        all_urls = all_urls[: args.limit]

    log.info(f"収集 URL 合計: {len(all_urls)} 人分")

    # ── Step 2: 各選手ページをスクレイピング ───────────────────────
    log.info("Step 2: 各選手の詳細スタッツを取得中...")
    records: list[dict] = []

    for i, url in enumerate(all_urls, 1):
        data = scrape_fighter(url)
        if data:
            records.append(data)
        if i % 100 == 0:
            log.info(f"  進捗: {i}/{len(all_urls)} 人完了 ({len(records)} 件成功)")
        time.sleep(REQUEST_DELAY)

    # ── Step 3: DataFrame に変換・保存 ─────────────────────────────
    log.info("Step 3: CSV 保存中...")
    df = pd.DataFrame(records)
    df.to_csv(args.output, index=False, encoding="utf-8-sig")
    log.info(f"保存完了: {args.output}  ({len(df)} 行 × {len(df.columns)} 列)")

    # ── サマリー表示 ──────────────────────────────────────────────
    print("\n" + "=" * 65)
    print("  取得データ サンプル (先頭10件)")
    print("=" * 65)
    display_cols = [
        "name", "weight_class", "wins", "losses",
        "win_rate", "str_acc", "str_def", "td_def", "ape_index"
    ]
    print(df[display_cols].head(10).to_string(index=False))

    print("\n欠損値の割合:")
    print(df.isnull().mean().round(3).to_string())


if __name__ == "__main__":
    main()
