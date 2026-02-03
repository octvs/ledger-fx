# todo

## Inbox

- [ ] Query non-contiguous periods separately.
  - Example: If
    - 02.10 missing
    - 03.10-10.10 present
    - Query done on 15.10 between 01.10-15.10, this will query 02.10-15.10, but
      we should break this non-contiguous period and query them separately.
      Hence 02.10-03.10 and 10.10-15.10.
- [ ] Bug when period is fully non-existant on web
  ```sh
  ledger-fx -v -c eur -d try q 20250301 20250302
  ```
- [ ] Missing dates at upstream
  - [ ] To tackle repeated queries for lacking dates at web, sources can/should
        fill blanks upon returning a successful query so that we don't
        repeatedly query dates that don't exist
    - But this might be a wrong thing to do if we have multiple sources for
      same conversion, since some other can provide the correct value later to
      be filled

## Backlog

- [-] Add type hints for
  - [x] ./src/pricedb.py
  - [ ] ./src/cli.py
  - [ ] ./src/sources/altinkaynak.py
- [ ] Rewrite using data service
  - [ ] Rewrite using the data service given by altinkaynak as seen in
        github:mustafa-mercanli/altinkaynak
  - [ ] Drop selectolax dependency

## Implementation

## Done

- [x] Verbosity level support on Argparser
- [x] Generalize to EUR2TRY conversion
