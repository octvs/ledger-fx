import argparse
import logging
from datetime import datetime

from main import PriceDB, chunk_query_period, query_data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c",
        "--currency",
        type=str,
        default="gau",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="verbose output"
    )
    parser.add_argument("dates", type=str, help="start date", nargs=2)
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, force=True)

    dates = [datetime.strptime(x, "%Y-%m-%d").date() for x in args.dates]

    if dates[0] >= dates[1]:
        print("First date should be the start (earlier) date!")
        print("Switching them for you...")
        dates = dates[::-1]

    db = PriceDB(args.currency)
    missing = db.check(dates)

    if missing.empty:
        print("Database is already up to date.")
        exit()

    for d0, d1 in chunk_query_period(missing):
        logging.info(f"Querying data source for: {d0.date()} - {d1.date()}...")
        new_db = query_data(args.currency, d0, d1)
        if new_db is not None:
            logging.info("Updating the db...")
            db.update(new_db)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
