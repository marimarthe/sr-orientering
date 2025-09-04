import re, json, os, requests
from bs4 import BeautifulSoup

URL = "https://rogaland.bedriftsidretten.no/next/p/35675/sor-rogaland"
TOPIC = "sr-orientering-varsler"
STATE_FILE = "seen.json"

DATE_RE = re.compile(r"(\d{1,2}\.\s*[a-zæøåA-ZÆØÅ]+\.?\s*\d{4})")

def load_seen():
    return set(json.load(open(STATE_FILE))) if os.path.exists(STATE_FILE) else set()

def save_seen(seen):
    with open(STATE_FILE, "w") as f:
        json.dump(sorted(list(seen)), f, ensure_ascii=False, indent=2)

def fetch_news_block():
    html = requests.get(URL, timeout=20, headers={"User-Agent": "news-watcher"}).text
    soup = BeautifulSoup(html, "html.parser")
    full_text = soup.get_text("\n", strip=True)
    start_marker = "All informasjon fra o-styret til løpere og oppmenn presenteres her."
    end_marker = "Terminliste 2025"
    start = full_text.find(start_marker)
    end = full_text.find(end_marker)
    block = full_text[start:end] if start != -1 and end != -1 and end > start else full_text
    return block

def parse_items(block):
    items = []
    for chunk in [p.strip() for p in block.split("\n\n") if p.strip()]:
        m = DATE_RE.search(chunk)
        if m:
            date = m.group(1)
            title = chunk.split("\n", 1)[0].strip()
            ident = f"{date} | {title[:90]}"
            items.append({"id": ident, "date": date, "title": title})
    return items

def notify(item):
    msg = f"[Ny melding] {item['title']} ({item['date']})"
    requests.post(f"https://ntfy.sh/{TOPIC}", data=msg.encode("utf-8"))

def main():
    seen = load_seen()
    block = fetch_news_block()
    items = parse_items(block)
    new_items = [it for it in items if it["id"] not in seen]
    new_items.sort(key=lambda x: x["date"])
    for it in new_items:
        notify(it)
        seen.add(it["id"])
    save_seen(seen)

if __name__ == "__main__":
    main()
