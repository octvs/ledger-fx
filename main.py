#!/usr/bin/env python

import subprocess
from xml.etree import ElementTree as ET

GOLD_TYPE_CODES = {"GRAU": "35", "QRAU": "28"}


def parse_deu_number_string(nr):
    return float(nr.replace(".", "").replace(",", "."))


def get_price_page(au_type, date0, date1):
    return subprocess.run(
        ["./query-website.sh", GOLD_TYPE_CODES[au_type], date0, date1],
        capture_output=True,
        text=True,
    ).stdout


def digest_price_html(price_html, curr0, curr1="₺"):
    ret = subprocess.run(
        ["grep", r"^\s*<tr><td>.*</td></tr>\s*$"],
        capture_output=True,
        text=True,
        input=price_html,
    ).stdout.strip()

    for row in iter(ET.XML(f"<table>{ret}</table>")):
        _date = row[0].text
        d, m, y = _date.split(".")
        date = f"{y}-{m}-{d.zfill(2)}"
        low, high = [parse_deu_number_string(x.text) for x in row[-2:]]
        line = f"P {date} {curr0} {curr1}{round((low + high) / 2, 2)}"
        print(line)


if __name__ == "__main__":
    currency = "QRAU"
    start = "01-02-2025"
    end = "28-02-2025"
    webpage = get_price_page(currency, start, end)
    digest_price_html(webpage, currency)
