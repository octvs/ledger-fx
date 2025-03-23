#!/usr/bin/env python

import os
from datetime import date, datetime, timedelta
from pathlib import Path

import httpx
import pandas as pd
from selectolax.parser import HTMLParser

URL = "https://www.altinkaynak.com/Altin/Arsiv"
API_DATEF = "%d-%m-%Y"
API_CURRN = {"gau": "Gram Altın", "qau": "Çeyrek Altın"}
DB_DIR = Path(os.environ.get("LEDGER_PRICE_DB")).parent


def convert_deu_nr(nr: str):
    return float(nr.replace(".", "").replace(",", "."))


def read_price_db(curr="gau"):
    db_fpath = DB_DIR.joinpath(f"{curr}2try.ledger")
    db = pd.read_csv(db_fpath, sep=" ", header=None)
    db = db.drop([0, 2], axis=1)
    db = db.set_axis(["date", "price"], axis=1)
    db["price"] = db["price"].str.slice(1).astype(float)
    db["date"] = pd.to_datetime(db["date"])
    return db


def check_database(curr, date0, date1):
    period = pd.date_range(date0, date1 - timedelta(1), freq="d")
    db_query = (
        read_price_db(curr)
        .set_index("date")
        .reindex(period)
        .reset_index(names="date")
    )
    print(db_query)
    missing_db = db_query[~db_query["price"].notna()]
    if missing_db.empty:
        exit("Already updated")
    # Separate into missing ones rather than min max
    _date0 = missing_db["date"].min()
    _date1 = missing_db["date"].max()
    update_database(curr, _date0.to_pydatetime(), _date1.to_pydatetime())


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

    res = []
    for row in rows[1:]:
        row = [x.text() for x in row.css("td")]
        _date = datetime.strptime(row[0], "%d.%m.%Y").date()
        low, high = [convert_deu_nr(x) for x in row[-2:]]
        res.append([_date, round((low + high) / 2, 2)])
    return pd.DataFrame(res, columns=["date", "price"])


def update_database(curr, d0, d1):
    # Func: Chunk to max 30 days
    new = query_data(curr, d0, d1)
    write_price_db(new, curr)
    # Func: Write back to db
    return None


def write_price_db(new_data, curr="gau"):
    curr_db = read_price_db(curr)
    new_db = pd.concat([curr_db, new_data])
    # Deduplicate?
    new_db["date"] = pd.to_datetime(new_db["date"])
    new_db = new_db.sort_values(by="date")
    new_db["price"] = "₺" + new_db["price"].astype(str)
    new_db[0] = "P"
    new_db[2] = curr.upper()[0] + "R" + curr.upper()[1:]
    new_db = new_db.reindex(columns=[0, "date", 2, "price"])
    db_fpath = DB_DIR.joinpath(f"{curr}2try.ledger")
    new_db.to_csv(db_fpath, sep=" ", header=False, index=False)


def main():
    currency = "gau"
    print(check_database(currency, date(2025, 3, 1), date(2025, 3, 21)))


if __name__ == "__main__":
    main()
