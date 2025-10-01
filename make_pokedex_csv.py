
import re
import csv
import sys
from html import unescape
from html.parser import HTMLParser
from urllib.request import urlopen

URL = "https://ja.wikipedia.org/w/index.php?printable=yes&title=%E5%85%A8%E5%9B%BD%E3%83%9D%E3%82%B1%E3%83%A2%E3%83%B3%E5%9B%B3%E9%91%91%E9%A0%86%E3%81%AE%E3%83%9D%E3%82%B1%E3%83%A2%E3%83%B3%E4%B8%80%E8%A6%A7"

def fetch_text(url=URL):
    with urlopen(url) as resp:
        return resp.read().decode("utf-8", errors="ignore")

class WikiTableParser(HTMLParser):
    TARGET_CLASSES = {"wikitable"}

    def __init__(self):
        super().__init__()
        self.collecting = False
        self.finished = False
        self.table_depth = 0
        self.in_cell = False
        self.skip_depth = 0
        self.current_cells = []
        self.rows = []
        self.current_cell_index = None

    def handle_starttag(self, tag, attrs):
        if self.finished:
            return

        attr_map = dict(attrs)
        if tag == "table":
            if self.collecting:
                self.table_depth += 1
            elif self._has_target_class(attr_map.get("class", "")):
                self.collecting = True
                self.table_depth = 0
        elif self.collecting:
            if tag == "tr":
                self.current_cells = []
                self.current_cell_index = None
            elif tag == "td":
                self.in_cell = True
                self.current_cells.append("")
                self.current_cell_index = len(self.current_cells) - 1
            elif tag in {"sup", "rt"} and self.in_cell:
                self.skip_depth += 1
            elif tag == "br" and self.in_cell and self.skip_depth == 0:
                self._append_to_cell("\n")

    def handle_endtag(self, tag):
        if self.finished:
            return

        if tag == "table" and self.collecting:
            if self.table_depth > 0:
                self.table_depth -= 1
            else:
                self.collecting = False
                self.finished = True
        elif not self.collecting:
            return
        elif tag == "td" and self.in_cell:
            self.in_cell = False
            self.current_cell_index = None
        elif tag == "tr":
            if self.current_cells:
                self.rows.append(self.current_cells)
            self.current_cells = []
            self.current_cell_index = None
        elif tag in {"sup", "rt"} and self.skip_depth > 0:
            self.skip_depth -= 1

    def handle_data(self, data):
        if self.collecting and self.in_cell and self.skip_depth == 0 and self.current_cell_index is not None:
            self._append_to_cell(data)

    def handle_entityref(self, name):
        self._append_to_cell(unescape(f"&{name};"))

    def handle_charref(self, name):
        self._append_to_cell(unescape(f"&#{name};"))

    def _append_to_cell(self, data):
        if self.collecting and self.in_cell and self.skip_depth == 0 and self.current_cell_index is not None:
            self.current_cells[self.current_cell_index] += data

    @staticmethod
    def _has_target_class(class_attr: str) -> bool:
        classes = set(class_attr.split()) if class_attr else set()
        return bool(WikiTableParser.TARGET_CLASSES & classes)


def parse_pairs(text: str):
    parser = WikiTableParser()
    parser.feed(text)

    pairs = {}
    for row in parser.rows:
        if len(row) < 2:
            continue
        raw_num = row[0].strip()
        if not raw_num:
            continue
        digits = re.sub(r"[^0-9]", "", raw_num)
        if not digits:
            continue
        num = int(digits)

        name = re.sub(r"\[[^\]]*\]", "", row[1]).strip()
        name = re.sub(r"\s+", " ", name)
        if not name:
            continue

        pairs[num] = name

    if not pairs:
        raise SystemExit("No pokedex entries were extracted")

    numbers = sorted(pairs)
    expected = list(range(numbers[0], numbers[-1] + 1))
    missing = [n for n in expected if n not in pairs]
    if missing:
        raise SystemExit(f"Missing entries: {missing[:10]}... total={len(missing)}")

    return [(n, pairs[n]) for n in expected]

def main(out_path=None):
    text = fetch_text()
    pairs = parse_pairs(text)

    if out_path is None:
        start_id = pairs[0][0]
        end_id = pairs[-1][0]
        out_path = f"pokedex_{start_id:03d}_{end_id:03d}.csv"

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "name"])
        for i, name in pairs:
            w.writerow([i, name])
    print(f"Wrote {len(pairs)} entries to {out_path}")

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else None
    main(out)
