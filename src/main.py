#!/usr/bin/env python
import logging
import os
from pathlib import Path

import httpx
import pandas as pd
from selectolax.parser import HTMLParser

URL = "https://www.altinkaynak.com/Altin/Arsiv"
API_DATEF = "%d-%m-%Y"
API_CURRN = {"gau": "Gram Altın", "qau": "Çeyrek Altın"}

# - If databse is empty
# - Handle duplicates on database
# Merge with other price query script
# - That script also should update top to bottom


def convert_deu_nr(nr: str):
    return float(nr.replace(".", "").replace(",", "."))


class PriceDB:
    _DIR = Path(os.environ.get("LEDGER_PRICE_DB")).parent
    _CURR = {"gau": "GRAU", "qau": "QRAU"}

    def __init__(self, src_curr, dst_curr):
        self.curr = src_curr
        self.fpath = PriceDB._DIR.joinpath(f"{src_curr}2{dst_curr}.ledger")

    def read(self):
        db = pd.read_csv(self.fpath, sep=" ", header=None)
        db[1] = pd.to_datetime(db[1])
        db = db.set_index(1)[3]
        db = db.str.slice(1).astype(float)
        return db

    def write(self, df: pd.DataFrame):
        df = "₺" + df.astype(str)
        df = df.rename("p").to_frame()
        df[0], df[1] = "P", PriceDB._CURR[self.curr]
        df = df.reset_index(names="d").reindex(columns=[0, "d", 1, "p"])
        df.to_csv(self.fpath, sep=" ", header=False, index=False)

    def update(self, new_db):
        curr_db = self.read()
        new_ind = pd.concat(x.index.to_series() for x in [curr_db, new_db])
        new_ind = new_ind[~new_ind.duplicated()].sort_values()
        updated_db = curr_db.reindex(new_ind)
        updated_db.update(new_db)
        self.write(updated_db)

    def check(self, dates):
        logging.info(f"Checking db for: {dates[0]} - {dates[1]}")
        period = pd.date_range(*dates, freq="d")
        db_query = self.read().reindex(period)
        missing_db = db_query[db_query.isna()].index
        return missing_db


def chunk_query_period(missing_db):
    # Separate into missing windows ones rather than min max
    # Separate this query into 30 day groups
    yield [x.to_pydatetime() for x in [missing_db.min(), missing_db.max()]]


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
