import logging

import httpx
import pandas as pd
from selectolax.parser import HTMLParser

URL = "https://www.altinkaynak.com/Altin/Arsiv"
API_DATEF = "%d-%m-%Y"
API_CURRN = {"gau": "Gram Altın", "qau": "Çeyrek Altın"}


def convert_deu_nr(nr: str):
    return float(nr.replace(".", "").replace(",", "."))


def query_data(curr, d0, d1):
    client = httpx.Client()
    data = client.get(URL)
    html = HTMLParser(data.text)
    _options = html.css("select#cphMain_cphSubContent_ddGold > option")
    options = {opt.text(): opt.attributes.get("value") for opt in _options}
    form_data = {
        "__VIEWSTATE": html.css_first("input#__VIEWSTATE").attributes["value"],
        "ctl00$ctl00$cphMain$cphSubContent$ddGold": options[API_CURRN[curr]],
        "ctl00$ctl00$cphMain$cphSubContent$dateRangeInput": f"{d0.strftime(API_DATEF)} - {d1.strftime(API_DATEF)}",
        "ctl00$ctl00$cphMain$cphSubContent$btnSeach": "Getir",
    }
    response = client.post(URL, data=form_data)
    rows = HTMLParser(response.text).css("table.table > tbody > tr")

    if not rows[1:]:
        logging.info(
            f"No data returned for {d0.strftime(API_DATEF)} - {d1.strftime(API_DATEF)}"
        )
        return None

    res = []
    for row in rows[1:]:
        row = [x.text() for x in row.css("td")]
        _date = pd.to_datetime(row[0], format="%d.%m.%Y")
        low, high = [convert_deu_nr(x) for x in row[-2:]]
        res.append([_date, round((low + high) / 2, 2)])
    return pd.DataFrame(res).set_index(0)[1]
