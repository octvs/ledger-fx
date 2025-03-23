import logging
import os
from pathlib import Path

import pandas as pd


class PriceDB:
    _DIR = Path(os.environ.get("LEDGER_PRICE_DB")).parent
    _CURR = {"gau": "GRAU", "qau": "QRAU", "try": "₺", "eur": "€"}

    def __init__(self, src_curr, dst_curr):
        self.curr = src_curr
        self.dest_curr = dst_curr
        self.fpath = PriceDB._DIR.joinpath(f"{src_curr}2{dst_curr}.ledger")

    def read(self):
        db = pd.read_csv(self.fpath, sep=" ", header=None)
        db[1] = pd.to_datetime(db[1])
        db = db.set_index(1)[3]
        db = db.str.slice(1).astype(float)
        return db

    def write(self, df: pd.DataFrame):
        df = PriceDB._CURR[self.dest_curr] + df.astype(str)
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
