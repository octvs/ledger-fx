import argparse
import logging
import os
from datetime import date, datetime, timedelta

from pricedb import PriceDB
from sources.altinkaynak import query_data


def chunk_query_period(missing_db):
    # Separate into missing windows ones rather than min max
    # Separate this query into 30 day groups
    yield [x.to_pydatetime() for x in [missing_db.min(), missing_db.max()]]


def query(src, dst, dates):
    dates = [datetime.strptime(x, "%Y%m%d").date() for x in dates]

    if dates[0] >= date.today():
        logging.info(f"Start date ({dates[0]}) is in future.")
        exit()

    if dates[1] > date.today():
        logging.info(f"End date ({dates[1]}) is in future.")
        logging.debug("Truncating to yesterday.")
        dates[1] = date.today() - timedelta(days=1)

    if dates[0] >= dates[1]:
        logging.info("First date should be the start (earlier) date!")
        logging.debug("Switching them for you...")
        dates = dates[::-1]

    db = PriceDB(src, dst)
    missing = db.check(dates)

    if missing.empty:
        logging.info("Database is already up to date.")
        exit()

    for d0, d1 in chunk_query_period(missing):
        logging.info(f"Querying data source for: {d0.date()} - {d1.date()}...")
        new_db = query_data(src, d0, d1)
        if new_db is not None:
            logging.info("Updating db...")
            db.update(new_db)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="verbose output"
    )
    parser.add_argument(
        "-c", "--currency", type=str, default="gau", help="source currency"
    )
    parser.add_argument(
        "-d",
        "--dst-currency",
        type=str,
        default="try",
        help="destination currency",
    )

    cmds = parser.add_subparsers(title="commands", dest="f")
    cmds.add_parser(
        "list", aliases=["l"], help="display the price database"
    ).set_defaults(f=lambda db: print(db))
    cmds.add_parser(
        "edit", aliases=["e"], help="open the db on $EDITOR"
    ).set_defaults(f=lambda db: os.system(f"$EDITOR {db.fpath}"))
    # cmds.add_parser(
    #     "query", aliases=["e"], help="query data from sources"
    # ).set_defaults(f=lambda cat: _edit(shopping, cat))
    # parser.add_argument("dates", type=str, help="start date", nargs=2)

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, force=True)
    logging.debug(f"Received args from shell {args}")

    if args.f is None:
        args.f = lambda db: print(db)

    db = PriceDB(args.currency, args.dst_currency)
    args.f(db)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
