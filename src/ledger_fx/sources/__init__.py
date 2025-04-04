import logging
from abc import ABC
from datetime import date, timedelta

import pandas as pd


class Source(ABC):
    def __init__(self, src, dst):
        assert src in self.RATES.keys()
        assert dst in self.RATES[src]
        self.src = src
        self.dst = dst

    def query_data(self, missing):
        result = pd.Series([], dtype=float)
        for period in self.chunk(missing):
            logging.info(
                f"Asking {self} for {period[0].date()} - {period[1].date()}"
            )
            ret = self._query_data(*period)
            result = pd.concat(x for x in [result, ret] if not x.empty)
        return result

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.src},{self.dst})"


class SourceFactory:
    from .altinkaynak import Altinkaynak
    from .ecb import ECB

    LIST = [Altinkaynak, ECB]

    def get(self, src, dst):
        available_sources = []
        for source in self.LIST:
            if src in source.RATES.keys() and dst in source.RATES[src]:
                available_sources.append(source(src, dst))
        return available_sources
