from .altinkaynak import Altinkaynak
from .ecb import ECB


class SourceFactory:
    LIST = [Altinkaynak, ECB]

    def get(self, src, dst):
        available_sources = []
        for source in self.LIST:
            if src in source.RATES.keys() and dst in source.RATES[src]:
                available_sources.append(source(src, dst))
        return available_sources
