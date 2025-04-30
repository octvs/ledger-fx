import argparse
import logging
import os
from datetime import date, datetime, timedelta

# Make CLI runnable from source tree with `python src/package`
if not __package__:
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent.parent))

from ledger_fx import PriceDB, SourceFactory


def clean_date_input(dates):
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
    return dates


def query(db, dates) -> None:
    dates = clean_date_input(dates)
    missing = db.check(dates)
    if missing.empty:
        logging.info("Database is already up to date.")
        exit()
    logging.info(
        f"Missing: {missing.min().date()} - {missing.max().date()}..."
    )
    available_sources = SourceFactory().get(db.curr, db.dest_curr)

    if len(available_sources) > 1:
        print("Choosing a source is not implemented yet! Using first.")

    source = available_sources[0]
    new_db = source.query_data(missing)
    if not new_db.empty:
        logging.info("Updating db...")
        db.update(new_db)


def parse_arguments() -> argparse.Namespace:
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
        default="eur",
        help="source currency",
        metavar="CURRENCY",
    )
    parser.add_argument(
        "-d",
        "--dst-currency",
        type=str,
        default="try",
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
        logging.basicConfig(level=logging.INFO, force=True)
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
