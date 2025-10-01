
import csv
import re
import sys
from html.parser import HTMLParser
from typing import List, Tuple
from urllib.request import Request, build_opener

URL = "https://pokemon-irasuto-taizen.com/pokemon-list/"


def fetch_html(url: str = URL) -> str:
    """Fetch HTML from the illustration encyclopedia website.

    A desktop browser user-agent and referer are attached because the site blocks
    plain Python user agents with HTTP 403.
    """

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
        "Referer": "https://pokemon-irasuto-taizen.com/",
        "Accept-Language": "ja-JP,ja;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    req = Request(url, headers=headers)
    opener = build_opener()
    with opener.open(req, timeout=30) as resp:
        charset = resp.headers.get_content_charset() or "utf-8"
        return resp.read().decode(charset, errors="ignore")


class _TableCollector(HTMLParser):
    """Collect all table rows as plain-text matrices."""

    def __init__(self) -> None:
        super().__init__()
        self._tables: List[List[List[str]]] = []
        self._in_table = False
        self._current_table: List[List[str]] = []
        self._current_row: List[str] = []
        self._in_cell = False
        self._cell_parts: List[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:  # type: ignore[override]
        if tag == "table":
            self._in_table = True
            self._current_table = []
        elif self._in_table and tag == "tr":
            self._current_row = []
        elif self._in_table and tag in {"td", "th"}:
            self._in_cell = True
            self._cell_parts = []

    def handle_endtag(self, tag: str) -> None:  # type: ignore[override]
        if tag == "table" and self._in_table:
            if self._current_table:
                self._tables.append(self._current_table)
            self._in_table = False
            self._current_table = []
        elif self._in_table and tag == "tr":
            if self._current_row:
                self._current_table.append(self._current_row)
            self._current_row = []
        elif self._in_table and tag in {"td", "th"} and self._in_cell:
            text = re.sub(r"\s+", " ", "".join(self._cell_parts)).strip()
            self._current_row.append(text)
            self._in_cell = False
            self._cell_parts = []

    def handle_data(self, data: str) -> None:  # type: ignore[override]
        if self._in_cell:
            self._cell_parts.append(data)

    @property
    def tables(self) -> List[List[List[str]]]:
        return self._tables


def parse_pokemon_table(html: str) -> List[Tuple[int, str]]:
    """Extract (dex, japanese_name) pairs from the target table."""

    parser = _TableCollector()
    parser.feed(html)

    for table in parser.tables:
        if not table:
            continue
        header = table[0]
        if len(header) < 2:
            continue
        if "図鑑" not in header[0] or "ポケモン" not in header[1]:
            continue

        results: List[Tuple[int, str]] = []
        for row in table[1:]:
            if len(row) < 2:
                continue
            num_match = re.search(r"\d+", row[0])
            if not num_match:
                continue
            dex = int(num_match.group())
            name = row[1].strip()
            if not name:
                continue
            results.append((dex, name))

        if results:
            results.sort(key=lambda x: x[0])
            return results

    raise SystemExit("Could not locate the ポケモン一覧 table with 図鑑No and ポケモン名 columns.")


def main(out_path: str = "pokemon_irasuto_taizen.csv") -> None:
    html = fetch_html()
    pairs = parse_pokemon_table(html)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["図鑑No", "ポケモン名"])
        writer.writerows(pairs)
    print(f"Wrote {len(pairs)} entries to {out_path}")


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "pokemon_irasuto_taizen.csv"
    main(out)
