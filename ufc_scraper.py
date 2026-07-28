import requests
from bs4 import BeautifulSoup
import time

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
chars = "abcde"
limit = 500
urls = []
for c in chars:
    resp = requests.get(f'http://ufcstats.com/statistics/fighters?char={c}&page=all', headers=HEADERS, timeout=15)
    soup = BeautifulSoup(resp.text, 'html.parser')
    table = soup.find('table', class_='b-statistics__table')
    if table:
        for row in table.find_all('tr')[1:]:
            a = row.find('a', href=True)
            if a and '/fighter-details/' in a['href']:
                urls.append(a['href'])
    time.sleep(0.3)

urls = urls[:limit]
with open('urls.txt', 'w') as f:
    f.write('\n'.join(urls))
print(f"収集完了: {len(urls)} URL -> urls.txt")
