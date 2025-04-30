import pandas as pd

from .base import Source


class ECB(Source):
    URL = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.zip"
    RATES = {"eur": ["try", "jpy", "usd"]}
    MIN = pd.Timestamp(2005, 1, 3)

    def chunk(self, missing):
        missing = missing[missing >= self.MIN]
        missing = missing[missing <= pd.Timestamp.today()]
        if not missing.empty:
            yield missing.min(), missing.max()

    def _query_data(self, d0, d1):
        data = pd.read_csv(ECB.URL, parse_dates=["Date"])
        data = data[["Date", "TRY"]]
        data = data[data["Date"] >= pd.to_datetime(d0)]
        data = data[data["Date"] <= pd.to_datetime(d1)]
        data = data[data["TRY"].notna()]
        return data.set_index("Date")["TRY"]
