import os, re, json, time, hashlib, requests
from bs4 import BeautifulSoup

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
MAX_PRICE = 150
HISTORY_FILE = "sent_deals.json"

KEYWORDS = [
    "loot", "glitch", "free delivery", "no extra", "0 delivery",
    "coupon", "code", "₹1", "₹9", "₹19", "₹29", "₹30", "₹49", "₹99",
    "rs 1", "rs 9", "rs 29", "rs 30", "rs 49", "rs 99", "freebie", "100% off"
]

FEEDS = [
    ("DesiDime Hot Deals", "https://www.desidime.com/deals.rss"),
    ("IndiaDesire Loot", "https://www.indiadesire.com/feed"),
]

def load_sent():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_sent(sent):
    with open(HISTORY_FILE, "w") as f:
        json.dump(list(sent)[-500:], f)

def get_price(text):
    m = re.search(r'(?:₹|rs\.?|inr)\s*(\d+)', text.lower())
    return int(m.group(1)) if m else None

def send_tg(title, link, source, price):
    tag = f"₹{price} Only!" if price else "Coupon / Free Delivery Loot"
    msg = (
        f"🚨 <b>LIVE LOOT ALERT ({tag})</b> 🚨\n\n"
        f"🛍 <b>Deal:</b> {title[:220]}\n"
        f"🚚 <b>Shipping:</b> ₹0 / Coupon Applied\n"
        f"📡 <b>Source:</b> {source}\n\n"
        f"👉 <b>Direct Link:</b> {link}\n\n"
        f"⚡ <i>Jaldi order karein!</i>"
    )
    r = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={"chat_id": CHANNEL_ID, "text": msg, "parse_mode": "HTML"},
        timeout=15
    )
    return r.status_code == 200

def main():
    sent = load_sent()
    headers = {"User-Agent": "Mozilla/5.0"}
    count = 0

    for source, url in FEEDS:
        try:
            res = requests.get(url, headers=headers, timeout=15)
            soup = BeautifulSoup(res.text, "xml")
            for item in soup.find_all("item")[:20]:
                title = item.title.get_text(strip=True) if item.title else ""
                link = item.link.get_text(strip=True) if item.link else ""
                if not title or not link:
                    continue

                uid = hashlib.md5(link.encode()).hexdigest()
                if uid in sent:
                    continue

                price = get_price(title)
                is_loot = any(k in title.lower() for k in KEYWORDS) or (price is not None and price <= MAX_PRICE)

                if is_loot and (price is None or price <= MAX_PRICE):
                    if send_tg(title, link, source, price):
                        sent.add(uid)
                        count += 1
                        time.sleep(2)
        except Exception as e:
            print(f"Feed error ({source}): {e}")

    save_sent(sent)
    print(f"Sent {count} new loot deals.")

if __name__ == "__main__":
    main()
