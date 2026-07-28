# MMA（総合格闘技）における選手の戦闘スタイルが強さにもたらす影響の分析

UFC選手データを用いて、スタンス（構え）と得意分野（打撃系／組み技系）が選手の「強さ」にどう影響するかを検証したプロジェクトです。2025年度（前期）データサイエンス特論1 のポスター発表用に行った分析一式のコードをまとめています。

## 目次

- [背景・目的](#背景目的)
- [分析の全体像](#分析の全体像)
- [ディレクトリ構成](#ディレクトリ構成)
- [セットアップ](#セットアップ)
- [実行方法](#実行方法)
- [主な結果](#主な結果)
- [データソース・参考文献](#データソース参考文献)
- [分析の変遷（補足）](#分析の変遷補足)

## 背景・目的

MMAでは選手ごとに「スタンス」や「得意分野（ストライカー／グラップラー等）」といった多様な戦闘スタイルが存在するが、これらが実際に選手の強さとどの程度関係しているかは体系的に検証されていない。

従来の分析でよく使われる勝率（win_rate）は、すべての勝敗を等価に扱うため対戦相手の強さを考慮できないという構造的な限界がある。本プロジェクトでは、対戦相手の強さを考慮したベイズ推定指標 **TrueSkill**（Herbrich et al., 2006）を用いて選手の「強さ」を再定義した上で、スタンスと得意分野が強さに与える影響を統計的に検証した。

## 分析の全体像

1. **TrueSkillレーティングの算出**：UFC全試合（8,646試合、1994〜2026年）を時系列順に `rate_1vs1` で処理し、対戦相手の強さを考慮した強さの指標（μ, σ）を算出。
2. **得意分野の分類**：打撃・組み技の技術統計（slpm, td_avg, sub_avg 等）を主成分分析（PCA）で縮約し、k-meansクラスタリングでストライカー／グラップラー／オールラウンダーの3タイプに分類。
3. **スタンス・得意分野 × 強さの群間比較**：それぞれ一元配置分散分析（ANOVA）で平均TrueSkillの差を検定。
4. **スタンス × 得意分野の交互作用分析**：二元配置分散分析で、両者が独立に作用するか（加算的か）を検証（探索的分析。詳細は [分析の変遷](#分析の変遷補足) 参照）。

## ディレクトリ構成

```
.
├── data/                              データ取得・整形、および生データ
│   ├── ufc_scraper.py                 UFCStats.com 選手データスクレイパー
│   ├── collect_urls.py                選手詳細ページURL収集
│   ├── get_sample.py                  スクレイピングのサンプル実行
│   ├── prepare_dataset.py             外部データを本プロジェクトのスキーマに整形
│   ├── alt_fighters_stats.csv         選手プロフィール（生データ、外部ソース由来）
│   ├── ufc_analysis_data.csv          クリーニング済み選手データ（2,053名）
│   └── ufc_fights_raw.csv             試合単位データ（8,737試合、外部ソース由来）
│
├── analysis/
│   ├── 01_hypotheses_exploratory/     プロジェクト初期の探索的仮説検証（3件）
│   ├── 02_age_hypothesis/             年齢仮説の検証（後にTrueSkillへ発展・ポスターからは除外）
│   └── 03_fighting_style_trueskill/   本ポスターの中核分析（TrueSkill・スタイル分類・統計検定）
│
├── poster/
│   └── build_ufc_poster.js            A0ポスター（pptx）生成スクリプト（pptxgenjs）
│
├── results/
│   ├── trueskill_final.csv            選手ごとの最終TrueSkillレーティング
│   ├── fighters_with_style_cluster.csv 得意分野クラスタリング結果
│   ├── style_trueskill_merged.csv     得意分野×TrueSkill 突合済みデータ
│   └── figures/                       ポスター掲載図（PNG）
│
├── requirements.txt
└── README.md
```

## セットアップ

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 実行方法

`analysis/03_fighting_style_trueskill/` 内のスクリプトは、`data/` 直下のCSVを参照する前提のパス（相対パスなし・カレントディレクトリ実行）で書かれています。実行する際は該当ディレクトリにCSVをコピーするか、スクリプト冒頭の読み込みパスを書き換えてください。

```bash
cd analysis/03_fighting_style_trueskill

# 1. TrueSkillレーティングを算出（trueskill_history.csv / trueskill_final.csv を生成）
python 01_compute_trueskill.py

# 2. 得意分野を分類（fighters_with_style_cluster.csv を生成）
python 03_cluster_fight_style.py

# 3. 得意分野×TrueSkillを分析
python 04_analyze_style_x_trueskill.py

# 4. スタンス×得意分野の交互作用を分析
python 05_analyze_stance_x_style_interaction.py

# 5. 図表を生成
python plot_all_style_analyses.py
python plot_style_cluster_scatter.py
python plot_interaction_stance_style.py
python plot_trueskill_validation.py
python plot_trueskill_formula.py
```

ポスター（pptx）を生成する場合：

```bash
cd poster
npm install pptxgenjs
node build_ufc_poster.js
```

## 主な結果

| 検証 | 結果 |
|---|---|
| TrueSkillの妥当性 | 上位選手にJon Jones, Islam Makhachev, Georges St-Pierre等、実際のUFC史上最強クラスの選手が並び、指標としての妥当性を確認 |
| スタンス × 強さ | Southpawの選手が有意に優位（ANOVA, p=0.005） |
| 得意分野 × 強さ | 純粋なストライカーが有意に劣位（ANOVA, p=0.006）。グラップラー・オールラウンダーとの間に有意差、グラップラーとオールラウンダーの間には有意差なし |
| スタンス×得意分野の交互作用 | 交互作用は非有意（p=0.283）。両者は独立に作用する可能性が示唆された（探索的分析） |

先行研究（Baker & Schorer, 2013, *PLOS ONE*）では勝率を指標とした場合スタンスによる有意差は報告されていないが、本研究では対戦相手の質を考慮したTrueSkillを用いることでサウスポーの優位性を検出した。これは、勝率という粗い指標では捉えられない効果を、より妥当な強さの指標によって明らかにできる可能性を示している。

## データソース・参考文献

- 選手プロフィールデータ：[sagi778/UFC-Data-Extractor](https://github.com/sagi778) （UFCStats.com 由来のオープンデータ）／本プロジェクト独自スクレイパー（`data/ufc_scraper.py`）
- 試合単位データ：[komaksym/UFC-DataLab](https://github.com/komaksym/UFC-DataLab)（UFCStats.com 由来、MIT License）
- Herbrich, R., Minka, T., & Graepel, T. (2007). TrueSkill™: A Bayesian Skill Rating System. *Advances in Neural Information Processing Systems 19*（NIPS 2006）, pp. 569–576.
- Baker, J., & Schorer, J. (2013). The Southpaw Advantage? Lateral Preference in Mixed Martial Arts. *PLOS ONE*, 8(11), e79793. https://doi.org/10.1371/journal.pone.0079793

## 分析の変遷（補足）

このプロジェクトは以下の順で発展した。

1. **`01_hypotheses_exploratory/`**：攻撃vs防御、体重階級別サウスポー優位、Ape Indexの3つの探索的仮説を検証（プロジェクト初期）。
2. **`02_age_hypothesis/`**：年齢と勝率の関係を相関分析・偏相関分析・二次回帰分析で検証。年齢と勝率に有意な負の相関を確認したが、指導教員より「勝率は対戦相手の強さを考慮しない指標であり、この種の分析にはTrueSkillが適する」との助言を受け、指標をTrueSkillへ転換。
3. **`03_fighting_style_trueskill/`**：TrueSkillを導入し、テーマを「年齢」から「戦闘スタイル（スタンス・得意分野）」に再設定。最終的にポスターに掲載した分析。

年齢に関する分析（`02_age_hypothesis/`）は、最終的なポスターのテーマからは除外されているが、TrueSkill導入の経緯を示す資料として残してある。
