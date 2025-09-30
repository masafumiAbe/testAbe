
import re
import csv
import sys
from urllib.request import urlopen

URL = "https://ja.wikipedia.org/w/index.php?printable=yes&title=%E5%85%A8%E5%9B%BD%E3%83%9D%E3%82%B1%E3%83%A2%E3%83%B3%E5%9B%B3%E9%91%91%E9%A0%86%E3%81%AE%E3%83%9D%E3%82%B1%E3%83%A2%E3%83%B3%E4%B8%80%E8%A6%A7"

def fetch_text(url=URL):
    with urlopen(url) as resp:
        return resp.read().decode("utf-8", errors="ignore")

def parse_pairs(text: str):
    # Lines look like: "0001 【84†フシギダネ】"
    # We'll capture the 4-digit number and the name between the last '†' and '】'
    pairs = {}
    for line in text.splitlines():
        m = re.search(r"(\\d{4})\\s+.*?\\u2020?([^\\]]*?)\\u3011", line)  # cautious fallback
        # Better pattern for Wikipedia printable:
        m = re.search(r"(\\d{4})\\s+.*?\\u2020?([^】]*?)】", line) or m
        if not m:
            # Specific pattern: 0001 【84†フシギダネ】
            m = re.search(r"(\\d{4})\\s+【[^†】]*?†([^】]+)】", line)
        if m:
            num = int(m.group(1))
            name = m.group(2).strip()
            if 1 <= num <= 1023:
                pairs[num] = name
    # Ensure continuous coverage
    missing = [i for i in range(1, 1024) if i not in pairs]
    if missing:
        raise SystemExit(f"Missing entries: {missing[:10]}... total={len(missing)}")
    return [(i, pairs[i]) for i in range(1, 1024)]

def main(out_path="pokedex_001_1023.csv"):
    text = fetch_text()
    pairs = parse_pairs(text)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "name"])
        for i, name in pairs:
            w.writerow([i, name])
    print(f"Wrote {len(pairs)} entries to {out_path}")

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "pokedex_001_1023.csv"
    main(out)
