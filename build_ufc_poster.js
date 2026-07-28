import requests, time, re, pandas as pd
from bs4 import BeautifulSoup

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

def parse_height_cm(raw):
    m = re.match(r"(\d+)'\s*(\d+)\"", raw.strip())
    if m: return round((int(m.group(1))*12 + int(m.group(2)))*2.54, 1)
    return None

def parse_reach_cm(raw):
    raw = raw.strip().replace('"','')
    if not raw or raw=='--': return None
    try: return round(float(raw)*2.54, 1)
    except: return None

def parse_pct(raw):
    raw = raw.strip().replace('%','')
    try: return float(raw) if raw and raw!='--' else None
    except: return None

def parse_float(raw):
    raw = raw.strip()
    try: return float(raw) if raw and raw!='--' else None
    except: return None

def wc(lbs):
    if not lbs: return 'Unknown'
    if lbs<=115: return 'Strawweight'
    if lbs<=125: return 'Flyweight'
    if lbs<=135: return 'Bantamweight'
    if lbs<=145: return 'Featherweight'
    if lbs<=155: return 'Lightweight'
    if lbs<=170: return 'Welterweight'
    if lbs<=185: return 'Middleweight'
    if lbs<=205: return 'Light Heavyweight'
    return 'Heavyweight'

def scrape_fighter(url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
    except Exception as e:
        print(f"  ERROR: {e}")
        return None

    name_tag = soup.find('span', class_='b-content__title-highlight')
    name = name_tag.text.strip() if name_tag else ''
    record_tag = soup.find('span', class_='b-content__title-record')
    wins=losses=draws=0
    if record_tag:
        m = re.search(r'(\d+)-(\d+)-(\d+)', record_tag.text)
        if m: wins,losses,draws=int(m.group(1)),int(m.group(2)),int(m.group(3))

    info={}
    ib=soup.find('div',class_='b-list__info-box')
    if ib:
        for li in ib.find_all('li'):
            t=li.find('i',class_='b-list__box-item-title')
            if t: info[t.text.strip().rstrip(':').lower()]=li.text.replace(t.text,'').strip()

    stats={}
    for box in soup.find_all('div',class_=re.compile(r'b-list__info-box-(left|right)')):
        for li in box.find_all('li',class_='b-list__box-list-item'):
            t=li.find('i',class_='b-list__box-item-title')
            if t: stats[t.text.strip().rstrip(':').lower()]=li.text.replace(t.text,'').strip()

    height_cm=parse_height_cm(info.get('height',''))
    reach_cm=parse_reach_cm(info.get('reach',''))
    wm=re.search(r'([\d.]+)',info.get('weight',''))
    weight_lbs=float(wm.group(1)) if wm else None
    total=wins+losses+draws
    win_rate=round(wins/total*100,1) if total>0 else None
    ape_index=round(reach_cm/height_cm,4) if height_cm and reach_cm else None

    return {
        'name':name,'url':url,'weight_class':wc(weight_lbs),
        'height_cm':height_cm,'weight_lbs':weight_lbs,'reach_cm':reach_cm,
        'stance':info.get('stance','').strip() or None,'dob':info.get('dob','').strip() or None,
        'wins':wins,'losses':losses,'draws':draws,'win_rate':win_rate,
        'slpm':parse_float(stats.get('slpm','')),
        'str_acc':parse_pct(stats.get('str. acc.','')),
        'sapm':parse_float(stats.get('sapm','')),
        'str_def':parse_pct(stats.get('str. def','')),
        'td_avg':parse_float(stats.get('td avg.','')),
        'td_acc':parse_pct(stats.get('td acc.','')),
        'td_def':parse_pct(stats.get('td def.','')),
        'sub_avg':parse_float(stats.get('sub. avg.','')),
        'ape_index':ape_index,
    }

print("Step1: URLリスト取得...")
resp=requests.get('http://ufcstats.com/statistics/fighters?char=c&page=all',headers=HEADERS,timeout=15)
soup=BeautifulSoup(resp.text,'html.parser')
table=soup.find('table',class_='b-statistics__table')
urls=[row.find('a')['href'] for row in table.find_all('tr')[1:] if row.find('a')][:25]
print(f"対象: {len(urls)}人")

records=[]
for i,url in enumerate(urls,1):
    data=scrape_fighter(url)
    if data:
        records.append(data)
        ai_str=f"{data['ape_index']:.4f}" if data['ape_index'] else "N/A "
        wr_str=f"{data['win_rate']}%" if data['win_rate'] else "N/A"
        print(f"[{i:2d}] {data['name']:<28} {data['weight_class']:<20} 勝率:{wr_str:<7} AI:{ai_str}")
    time.sleep(0.4)

df=pd.DataFrame(records)
df.to_csv('/sessions/serene-keen-dijkstra/mnt/outputs/ufc_sample_data.csv',index=False,encoding='utf-8-sig')
print(f"\n完了: {len(df)}行 × {len(df.columns)}列")
print(df[['name','weight_class','wins','losses','win_rate','str_acc','str_def','td_def','ape_index']].to_string(index=False))
