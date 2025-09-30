# scrape_gamewith_pokemon_csv.py
import csv, re, time, requests
from bs4 import BeautifulSoup

URL = "https://gamewith.jp/pokemon-sv/article/show/375426"
OUT_CSV = "pokemon_1_1023_ja_from_gamewith.csv"

def main():
    html = requests.get(URL, timeout=20).text
    soup = BeautifulSoup(html, "html.parser")

    # 「No.001」「No.025」…のような表記と日本語名を拾う
    # サイト構造変更に備えて冗長に探索
    cand = []
    for el in soup.find_all(text=re.compile(r"No\.\s*\d{3,4}")):
        m = re.search(r"No\.\s*(\d{3,4})", el)
        if not m: 
            continue
        dex = int(m.group(1))
        # 近傍の要素から日本語名らしき文字列を探索
        name = None
        # 1) 同じ要素内
        if isinstance(el, str):
            # よくある「No.001 フシギダネ」型
            tail = el.split(m.group(0))[-1].strip()
            if tail and len(tail) <= 20:
                name = tail
        # 2) 親要素や兄弟要素
        if not name:
            parent = getattr(el, "parent", None)
            if parent:
                # 次兄弟テキスト
                sib_text = parent.get_text(" ", strip=True)
                # No.001 フシギダネ などから名前を抽出
                mm = re.search(r"No\.\s*\d{3,4}\s*([^\s|/|・|,|，|、]{1,20})", sib_text)
                if mm:
                    name = mm.group(1)

        if name:
            cand.append((dex, name))

    # 重複を整理 & 1..1023 に限定
    seen = {}
    for dex, name in cand:
        if 1 <= dex <= 1023 and dex not in seen:
            seen[dex] = name

    rows = [(i, seen.get(i, "")) for i in range(1, 1024)]

    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "name"])
        w.writerows(rows)

    print(f"done -> {OUT_CSV} ({sum(1 for _,n in rows if n)}/1023 filled)")

if __name__ == "__main__":
    main()
