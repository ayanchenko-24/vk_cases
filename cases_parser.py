!pip install -q beautifulsoup4 lxml

from pathlib import Path
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import json

BASE_URL = "https://ads.vk.com"

MONTHS_RU = {
    "января": 1, "февраля": 2, "марта": 3, "апреля": 4, "мая": 5, "июня": 6,
    "июля": 7, "августа": 8, "сентября": 9, "октября": 10, "ноября": 11, "декабря": 12,
}

def two(n: int) -> str:
    return f"{n:02d}"

def normalize_date(raw: str):
    import re
    if not raw:
        return None
    raw = " ".join(raw.strip().split())

    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", raw)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"

    m = re.search(r"(\d{4})[./-](\d{1,2})[./-](\d{1,2})", raw)
    if m:
        y, mo, d = map(int, m.groups())
        return f"{y}-{two(mo)}-{two(d)}"

    m = re.search(r"(\d{1,2})[./](\d{1,2})[./](\d{4})", raw)
    if m:
        d, mo, y = map(int, m.groups())
        return f"{y}-{two(mo)}-{two(d)}"

    tokens = raw.lower().split()
    for i, token in enumerate(tokens):
        if token in MONTHS_RU:
            try:
                day = int(tokens[i - 1])
            except (IndexError, ValueError):
                day = None
            year = None
            for j in range(i + 1, len(tokens)):
                m2 = re.search(r"\d{4}", tokens[j])
                if m2:
                    year = int(m2.group(0))
                    break
            if day and year:
                month = MONTHS_RU[token]
                return f"{year}-{two(month)}-{two(day)}"
    return None

html_path = Path("cases.html")

if not html_path.is_file():
    raise SystemExit("Файл cases.html не найден плак плак")

html = html_path.read_text(encoding="utf-8", errors="ignore")
soup = BeautifulSoup(html, "lxml")


cards = soup.find_all("a", class_=lambda c: c and "case-card_wrapper" in c)
print("Найдено тегов карточек:", len(cards))

cases = []

for card in cards:
    # ищем заголовки
    title_div = card.find("div", class_=lambda c: c and "case-card_title" in c)
    if title_div:
        title = title_div.get_text(" ", strip=True)
    else:
        title = card.get_text(" ", strip=True)
    if not title:
        continue

    # ищем ссылочки
    href = card.get("href", "").strip()
    if not href:
        continue
    url = urljoin(BASE_URL, href)

    # ищем даты
    time_tag = card.find("time", attrs={"itemprop": "datePublished"}) or card.find("time")
    if time_tag:
        raw_date = time_tag.get("datetime") or time_tag.get_text(strip=True)
        published_at = normalize_date(raw_date)
    else:
        published_at = None

    cases.append({
        "title": title,
        "url": url,
        "published_at": published_at,
    })



print(json.dumps(cases, ensure_ascii=False, indent=2))
print("\nВсего кейсов:", len(cases))

out_path = Path("cases.json")
out_path.write_text(json.dumps(cases, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\n[INFO] Результат сохранён в {out_path}")
