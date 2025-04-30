import logging

import httpx
import pandas as pd
from selectolax.parser import HTMLParser

from .base import Source


def convert_deu_nr(nr: str):
    return float(nr.replace(".", "").replace(",", "."))


class Altinkaynak(Source):
    URL = "https://www.altinkaynak.com/Altin/Arsiv"
    DATEF = "%d-%m-%Y"
    RATES = {"gau": ["try"], "qau": ["try"]}
    API_CURR_NAME = {"gau": "Gram Altın", "qau": "Çeyrek Altın"}
    API_PERIOD_LIMIT = pd.Timedelta(30, "d")

    def chunk(self, missing):
        while missing.max() - missing.min() > self.API_PERIOD_LIMIT:
            yield missing.min(), missing.min() + self.API_PERIOD_LIMIT
            missing = missing[missing > missing.min() + self.API_PERIOD_LIMIT]
        yield missing.min(), missing.max()

    def _query_data(self, d0, d1):
        client = httpx.Client()
        data = client.get(self.URL)
        html = HTMLParser(data.text)
        _options = html.css("select#cphMain_cphSubContent_ddGold > option")
        options = {opt.text(): opt.attributes.get("value") for opt in _options}
        form_data = {
            "__VIEWSTATE": html.css_first("input#__VIEWSTATE").attributes[
                "value"
            ],
            "ctl00$ctl00$cphMain$cphSubContent$ddGold": options[
                self.API_CURR_NAME[self.src]
            ],
            "ctl00$ctl00$cphMain$cphSubContent$dateRangeInput": f"{d0.strftime(self.DATEF)} - {d1.strftime(self.DATEF)}",
            "ctl00$ctl00$cphMain$cphSubContent$btnSeach": "Getir",
        }
        response = client.post(self.URL, data=form_data)
        rows = HTMLParser(response.text).css("table.table > tbody > tr")

        if not rows[1:]:
            logging.info(
                f"No data returned for {d0.strftime(self.DATEF)} - {d1.strftime(self.DATEF)}"
            )
            return pd.Series([], dtype=float)

        res = []
        for row in rows[1:]:
            row = [x.text() for x in row.css("td")]
            _date = pd.to_datetime(row[0], format="%d.%m.%Y")
            low, high = [convert_deu_nr(x) for x in row[-2:]]
            res.append([_date, round((low + high) / 2, 2)])
        return pd.DataFrame(res).set_index(0)[1]
