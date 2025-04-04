# dotfiles

## Inbox

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
- [ ] Verbosity level support on Argparser
  - [ ] `-v` for INFO and `-vv` for DEBUG

## Backlog

- [-] Add type hints for
  - [x] ./src/pricedb.py
  - [ ] ./src/cli.py
  - [ ] ./src/sources/altinkaynak.py
- [ ] Rewrite using data service
  - [ ] Rewrite using the data service given by altinkaynak as seen in
        github:mustafa-mercanli/altinkaynak

## Implementation

## Done

- [x] Generalize to EUR2TRY conversion
  - Merge with other price query script
    - That script also should update top to bottom
