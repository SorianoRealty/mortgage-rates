"""Fetch Connecticut DOB Excel rates and atomically update a public JSON feed."""
from datetime import datetime, timezone
from html.parser import HTMLParser
from io import BytesIO
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen
import json
import re
import xlrd
import openpyxl

SOURCE = 'https://portal.ct.gov/dob/rental-security-deposits/rental-security-deposits/deposit-index-and-interest-rates'
OUTPUT = Path(__file__).resolve().parents[1] / 'security-deposit-rates.json'

class Links(HTMLParser):
    def __init__(self):
        super().__init__(); self.links = []
    def handle_starttag(self, tag, attrs):
        if tag.lower() == 'a':
            for key, value in attrs:
                if key.lower() == 'href' and value:
                    self.links.append(value)

def get(url):
    request = Request(url, headers={'User-Agent': 'SorianoRealty-RateUpdater/1.0'})
    with urlopen(request, timeout=30) as response:
        if urlparse(response.url).hostname != 'portal.ct.gov':
            raise ValueError('Unexpected source redirect host')
        data = response.read(5_000_001)
        if len(data) > 5_000_000:
            raise ValueError('Source exceeds size limit')
        return data

def discover_link(page):
    parser = Links(); parser.feed(page)
    excel = [link for link in parser.links if re.search(r'\.(?:xls|xlsx)(?:\?|$)', link, re.I)]
    preferred = [link for link in excel if re.search(r'interest.*calculation', link, re.I)]
    if not excel: raise ValueError('Official page no longer links an Excel file')
    url = urljoin(SOURCE, (preferred or excel)[0])
    if urlparse(url).scheme != 'https' or urlparse(url).hostname != 'portal.ct.gov':
        raise ValueError('Unexpected Excel source host')
    return url

def parse_rows(sheets):
    rates = {}
    for rows in sheets:
        annual = next((i for row in rows for i, cell in enumerate(row)
                       if isinstance(cell, str) and re.fullmatch(r'annual(?:\s+rate)?', cell.strip(), re.I)), None)
        if annual is None: continue
        for row in rows:
            if len(row) <= annual: continue
            label = row[0]
            if isinstance(label, (int, float)) and not isinstance(label, bool) and float(label).is_integer():
                label = str(int(label))
            else: label = str(label).strip()
            match = re.fullmatch(r'(\d{4})(?:\s*[-–]\s*(\d{4}))?', label)
            if not match: continue
            start, end = int(match[1]), int(match[2] or match[1])
            if start < 1994 or end > datetime.now(timezone.utc).year + 1 or end < start or end-start > 30: continue
            rate = row[annual]
            if isinstance(rate, bool) or not isinstance(rate, (int, float)) or not 0 <= rate <= .20:
                raise ValueError(f'Invalid decimal annual rate in {label}')
            for year in range(start, end+1):
                if str(year) in rates and rates[str(year)] != float(rate):
                    raise ValueError(f'Conflicting rates for {year}')
                rates[str(year)] = float(rate)
    if not rates or max(map(int, rates)) < 2026: raise ValueError('Incomplete or outdated workbook')
    for year in range(1994, max(map(int, rates))+1):
        if str(year) not in rates: raise ValueError(f'Missing historical rate: {year}')
    return dict(sorted(rates.items()))

def parse_workbook(data):
    if data[:2] == b'PK':
        workbook = openpyxl.load_workbook(BytesIO(data), data_only=True, read_only=True)
        try: return parse_rows([list(sheet.values) for sheet in workbook.worksheets])
        finally: workbook.close()
    workbook = xlrd.open_workbook(file_contents=data)
    return parse_rows([[sheet.row_values(i) for i in range(sheet.nrows)] for sheet in workbook.sheets()])

def main():
    excel_url = discover_link(get(SOURCE).decode('utf-8'))
    rates = parse_workbook(get(excel_url))
    if OUTPUT.exists():
        old = json.loads(OUTPUT.read_text())
        if max(map(int, rates)) < max(map(int, old['rates'])):
            raise ValueError('Rejecting a workbook older than the saved feed')
    payload = {'rates': rates, 'checkedAt': datetime.now(timezone.utc).isoformat(),
               'sourceUrl': SOURCE, 'excelUrl': excel_url}
    temp = OUTPUT.with_suffix('.tmp')
    temp.write_text(json.dumps(payload, indent=2) + '\n'); temp.replace(OUTPUT)
    print(f'Official Excel verified. Rates through {max(map(int, rates))}.')

if __name__ == '__main__': main()
