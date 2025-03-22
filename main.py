import subprocess
from xml.etree import ElementTree as ET

GOLD_TYPE_CODES = {"GRAU": "35", "QRAU": "28"}


def parse_deu_number_string(nr):
    return float(nr.replace(".", "").replace(",", "."))


def get_prices(au_type, date0, date1):
    _ret = subprocess.run(
        ["./query-website.sh", GOLD_TYPE_CODES[au_type], date0, date1],
        capture_output=True,
        text=True,
    ).stdout
    ret = subprocess.run(
        ["grep", r"^\s*<tr><td>.*</td></tr>\s*$"],
        capture_output=True,
        text=True,
        input=_ret,
    ).stdout.strip()

    for row in iter(ET.XML(f"<table>{ret}</table>")):
        _date = row[0].text
        d, m, y = _date.split(".")
        date = f"{y}-{m}-{d.zfill(2)}"
        low, high = [parse_deu_number_string(x.text) for x in row[-2:]]
        line = f"P {date} {au_type} ₺{round((low + high) / 2, 2)}"
        print(line)


if __name__ == "__main__":
    get_prices("QRAU", "01-02-2025", "28-02-2025")
