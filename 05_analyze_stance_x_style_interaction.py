"""
Compute TrueSkill ratings for all UFC fighters from match-level data.

Input : ufc_fights_raw.csv  (UFC-DataLab stats_raw.csv, ';'-separated, 1 row = 1 fight)
        alt_fighters_stats.csv (fighter profiles: dob, stance)
Output: trueskill_history.csv  (1 row = 1 fighter-fight observation: date, age, mu, sigma)
        trueskill_final.csv    (1 row = 1 fighter: final rating + profile attrs)
"""
import pandas as pd
import numpy as np
from datetime import datetime
import trueskill

# ---- load fights ----
fights = pd.read_csv("ufc_fights_raw.csv", sep=";", low_memory=False)
fights["date"] = pd.to_datetime(fights["event_date"], format="%d/%m/%Y", errors="coerce")
fights = fights.dropna(subset=["date"])
fights = fights[fights["fight_outcome"].isin(["red_win", "blue_win", "draw"])]
fights = fights.sort_values("date").reset_index(drop=True)
print(f"usable fights (decisive + draws): {len(fights)}")

# ---- load profiles ----
prof = pd.read_csv("alt_fighters_stats.csv")

def parse_dob(s):
    if not isinstance(s, str) or s.strip() == "--":
        return pd.NaT
    try:
        return pd.to_datetime(datetime.strptime(s.strip(), "%b%d,%Y"))
    except Exception:
        return pd.NaT

prof["dob_dt"] = prof["dob"].apply(parse_dob)
prof["key"] = prof["name"].str.strip().str.upper()
# drop duplicate names (ambiguous join) keeping first
dup = prof["key"].duplicated(keep=False).sum()
print(f"duplicate-name profile rows (kept first): {dup}")
prof_u = prof.drop_duplicates("key", keep="first").set_index("key")

# ---- run TrueSkill ----
env = trueskill.TrueSkill(draw_probability=0.02)
ratings = {}   # name_key -> Rating
history = []

def get(name):
    return ratings.get(name, env.create_rating())

for row in fights.itertuples():
    r_key = row.red_fighter_name.strip().upper()
    b_key = row.blue_fighter_name.strip().upper()
    r, b = get(r_key), get(b_key)
    if row.fight_outcome == "red_win":
        r_new, b_new = trueskill.rate_1vs1(r, b, env=env)
    elif row.fight_outcome == "blue_win":
        b_new, r_new = trueskill.rate_1vs1(b, r, env=env)
    else:
        r_new, b_new = trueskill.rate_1vs1(r, b, drawn=True, env=env)
    ratings[r_key], ratings[b_key] = r_new, b_new
    for key, rating, opp in ((r_key, r_new, b_key), (b_key, b_new, r_key)):
        history.append({"fighter": key, "date": row.date, "mu": rating.mu,
                        "sigma": rating.sigma, "opponent": opp})

hist = pd.DataFrame(history)
# fight number per fighter
hist["fight_no"] = hist.groupby("fighter").cumcount() + 1

# attach profile attrs
hist = hist.join(prof_u[["dob_dt", "stance"]], on="fighter")
hist["age"] = (hist["date"] - hist["dob_dt"]).dt.days / 365.25
print(f"history rows: {len(hist)}, with age: {hist['age'].notna().sum()}")

hist.to_csv("trueskill_history.csv", index=False)

# ---- final ratings per fighter ----
final = hist.sort_values("date").groupby("fighter").tail(1).copy()
final["n_fights"] = final["fighter"].map(hist.groupby("fighter").size())
final["conservative"] = final["mu"] - 3 * final["sigma"]
final.to_csv("trueskill_final.csv", index=False)

# ---- sanity check: top fighters by conservative rating (min 10 fights) ----
top = final[final["n_fights"] >= 10].nlargest(15, "conservative")
print("\nTop 15 (mu - 3*sigma, >=10 fights):")
for t in top.itertuples():
    print(f"  {t.fighter:30s} mu={t.mu:6.2f} sigma={t.sigma:5.3f} cons={t.conservative:6.2f} fights={t.n_fights}")
