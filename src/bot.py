import logging
from datetime import date, datetime, timedelta

from src.main import PriceDB, chunk_query_period, query_data


def generate_monthly_periods(date0, date1=datetime.now().date()):
    while date0 <= date(date1.year, date1.month, 1) - timedelta(days=1):
        yield date0, date(date0.year, date0.month + 1, 1) - timedelta(days=1)
        if date0.month == 11:
            date0 = date(date0.year + 1, 1, 1)
        else:
            date0 = date(date0.year, date0.month + 1, 1)


for curr in ["gau", "qau"]:
    logging.basicConfig(level=logging.INFO, force=True)

    db = PriceDB(curr)

    start_date = date(2020, 1, 1)
    for dates in generate_monthly_periods(start_date):
        missing = db.check(dates)
        if missing.empty:
            print("Database is already up to date.")
            continue

        for d0, d1 in chunk_query_period(missing):
            logging.info(
                f"Querying data source for: {d0.date()} - {d1.date()}..."
            )
            new_db = query_data(curr, d0, d1)
            if new_db is not None:
                logging.info("Updating the db...")
                db.update(new_db)
