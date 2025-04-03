import datetime
import logging
import os
from pathlib import Path

import pandas as pd


def get_pricedb_path() -> Path:
    pth = os.environ.get("LEDGER_PRICE_DB")
    if pth is None:
        exit("You need to define LEDGER_PRICE_DB to use this program.")
    return Path(pth)


class PriceDB:
    _CURR = {"gau": "GRAU", "qau": "QRAU", "try": "₺", "eur": "€"}

    def __init__(self, src_curr: str, dst_curr: str) -> None:
        self.curr = src_curr
        self.dest_curr = dst_curr
        self._dir = get_pricedb_path().parent.joinpath("prices")
        self.fpath = self._dir.joinpath(f"{src_curr}2{dst_curr}.ledger")

    def read(self) -> pd.Series:
        if not self.fpath.exists() or self.fpath.stat().st_size == 0:
            return pd.Series([], dtype=float)
        _db = pd.read_csv(self.fpath, sep=" ", header=None)
        _db[1] = pd.to_datetime(_db[1])
        db = _db.set_index(1)[3]
        db = db.str.slice(1).astype(float)
        return db

    def write(self, df: pd.Series) -> None:
        df = PriceDB._CURR[self.dest_curr] + df.astype(str)
        _df = df.rename("p").to_frame()
        _df[0], _df[1] = "P", PriceDB._CURR[self.curr]
        _df = _df.reset_index(names="d").reindex(columns=[0, "d", 1, "p"])
        _df.to_csv(self.fpath, sep=" ", header=False, index=False)

    def update(self, new_db: pd.Series) -> None:
        curr_db = self.read()
        new_ind = pd.concat(
            x.index.to_series() for x in [curr_db, new_db] if not x.empty
        )
        new_ind = new_ind[~new_ind.duplicated()].sort_values()
        updated_db = curr_db.reindex(new_ind)
        updated_db.update(new_db)
        self.write(updated_db)

    def check(self, dates: list[datetime.date]) -> pd.Series:
        logging.info(f"Checking db for: {dates[0]} - {dates[1]}")
        period = pd.date_range(dates[0], dates[1], freq="d")
        db_query = self.read().reindex(period)
        missing_db = db_query[db_query.isna()].index.to_series()
        return missing_db

    def __str__(self) -> str:
        msg = f"Price database of {self.curr} to {self.dest_curr}"
        db = self.read()
        if db.empty:
            return msg + " is empty."
        return (
            msg + f" between {db.index.min().date()} - {db.index.max().date()}"
        )
