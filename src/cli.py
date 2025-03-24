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


def query(db, dates):
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

    missing = db.check(dates)

    if missing.empty:
        logging.info("Database is already up to date.")
        exit()

    for d0, d1 in chunk_query_period(missing):
        logging.info(f"Querying data source for: {d0.date()} - {d1.date()}...")
        new_db = query_data(db.curr, d0, d1)
        if new_db is not None:
            logging.info("Updating db...")
            db.update(new_db)


def parse_arguments():
    parser = argparse.ArgumentParser()

    # Flags
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="verbose output",
    )
    parser.add_argument(
        "-c",
        "--src-currency",
        type=str,
        default="try",
        help="source currency",
        metavar="CURRENCY",
    )
    parser.add_argument(
        "-d",
        "--dst-currency",
        type=str,
        default="eur",
        help="destination currency",
        metavar="CURRENCY",
    )

    # Subcommands
    cmds = parser.add_subparsers(title="commands", dest="cmd")
    edit_parser = cmds.add_parser(
        "edit",
        aliases=["e"],
        help="open the db on $EDITOR",
    )
    list_parser = cmds.add_parser(
        "list",
        aliases=["l"],
        help="display the price database",
    )
    query_parser = cmds.add_parser(
        "query",
        aliases=["q"],
        help="query data from sources",
    )

    # Subcomand default actions
    edit_parser.set_defaults(cmd=lambda db: os.system(f"$EDITOR {db.fpath}"))
    list_parser.set_defaults(cmd=lambda db: print(db))
    query_parser.set_defaults(cmd=lambda db: query(db, args.dates))

    # Subcommand specific arguments
    query_parser.add_argument(
        "dates",
        type=str,
        help="start and end date in YYYYMMDD format",
        nargs=2,
        metavar="DATE",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, force=True)
    logging.debug(f"Received args from shell {args}")

    if args.cmd is None:
        args.cmd = lambda db: print(db)

    return args


def main():
    args = parse_arguments()
    db = PriceDB(args.src_currency, args.dst_currency)
    args.cmd(db)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
