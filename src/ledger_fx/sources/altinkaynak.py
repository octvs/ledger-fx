import logging
import subprocess
import time

import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from .base import Source

# ── helpers ────────────────────────────────────────────────────────────────────


def _get_binary(name: str) -> str:
    result = subprocess.run(["which", name], capture_output=True, text=True)
    path = result.stdout.strip()
    if not path:
        raise FileNotFoundError(
            f"'{name}' not found in PATH. Are you inside `nix develop`?"
        )
    return path


def _convert_tr_number(nr: str) -> float:
    """'2.021,76' → 2021.76"""
    return float(nr.replace(".", "").replace(",", "."))


# ── Selenium driver ────────────────────────────────────────────────────────────


def _build_driver() -> webdriver.Chrome:
    options = Options()
    options.binary_location = _get_binary("chromium")
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280,900")
    options.add_argument("--lang=tr-TR")
    options.add_argument(
        "--user-agent=Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
    service = Service(executable_path=_get_binary("chromedriver"))
    return webdriver.Chrome(service=service, options=options)


# ── page interaction ───────────────────────────────────────────────────────────


def _select_gold_type(
    driver: webdriver.Chrome, wait: WebDriverWait, label: str
):
    el = wait.until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, ".dataitem-select select")
        )
    )
    Select(el).select_by_visible_text(label)
    time.sleep(0.4)


def _open_date_picker(wait: WebDriverWait):
    btn = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "button.date-input"))
    )
    btn.click()
    wait.until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "table.rdp-month_grid")
        )
    )
    time.sleep(0.5)


def _navigate_to_month(
    driver: webdriver.Chrome, wait: WebDriverWait, target: pd.Timestamp
):
    month_sel = wait.until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "select.rdp-months_dropdown")
        )
    )
    Select(month_sel).select_by_value(str(target.month - 1))  # 0-indexed
    time.sleep(0.3)

    year_sel = driver.find_element(
        By.CSS_SELECTOR, "select.rdp-years_dropdown"
    )
    Select(year_sel).select_by_value(str(target.year))
    time.sleep(0.4)


def _click_day(
    driver: webdriver.Chrome, wait: WebDriverWait, target: pd.Timestamp
):
    iso = target.strftime("%Y-%m-%d")
    xpath = (
        f"//td[@data-day='{iso}' and not(@data-disabled='true')]"
        f"//button[@class='rdp-day_button']"
    )
    try:
        btn = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
        btn.click()
        time.sleep(0.4)
    except TimeoutException:
        logging.warning(
            f"Day {iso} not clickable (weekend/holiday) — skipping"
        )


def _submit(driver: webdriver.Chrome):
    driver.execute_script(
        "document.querySelector('.date-form-actions button[type=submit]').click()"
    )
    time.sleep(2)


# ── parser ─────────────────────────────────────────────────────────────────────


def _parse_rows(driver: webdriver.Chrome, wait: WebDriverWait) -> list[dict]:
    try:
        wait.until(
            EC.presence_of_element_located(
                (
                    By.CSS_SELECTOR,
                    ".rates-inner .rates-row, "
                    ".rates-inner [class*='row']:not(.rates-head)",
                )
            )
        )
    except TimeoutException:
        time.sleep(3)

    soup = BeautifulSoup(driver.page_source, "lxml")
    rates_inner = soup.select_one(".rates-inner")

    if not rates_inner:
        logging.error(".rates-inner not found in page source.")
        return []

    header_div = rates_inner.select_one(".rates-head")
    raw_headers = (
        [
            d.get_text(strip=True)
            for d in header_div.find_all("div", recursive=False)
        ]
        if header_div
        else ["Tarih", "_change", "Gişe Alış", "Gişe Satış"]
    )
    headers = [h if h else "_change" for h in raw_headers]

    rows = []
    for row_div in rates_inner.find_all("div", recursive=False):
        if "rates-head" in row_div.get("class", []):
            continue
        cells = [
            d.get_text(strip=True)
            for d in row_div.find_all("div", recursive=False)
        ]
        if not cells:
            continue
        padded = cells + [""] * (len(headers) - len(cells))
        rows.append(dict(zip(headers, padded[: len(headers)])))

    return rows


# ── Source implementation ──────────────────────────────────────────────────────


class Altinkaynak(Source):
    URL = "https://www.altinkaynak.com/Altin/Arsiv"
    RATES = {"gau": ["try"], "qau": ["try"]}
    API_CURR_NAME = {"gau": "Gram Altın", "qau": "Çeyrek Altın"}

    # Earliest date available in the year dropdown
    MIN = pd.Timestamp(1926, 1, 1)

    def chunk(self, missing):
        """Single chunk — the site supports arbitrary date ranges."""
        missing = missing[missing >= self.MIN]
        missing = missing[missing <= pd.Timestamp.today()]
        if not missing.empty:
            yield missing.min(), missing.max()

    def _query_data(self, d0, d1) -> pd.Series:
        label = self.API_CURR_NAME[self.src]
        driver = _build_driver()
        wait = WebDriverWait(driver, 15)

        try:
            driver.get(self.URL)
            time.sleep(2)

            _select_gold_type(driver, wait, label)
            _open_date_picker(wait)
            _navigate_to_month(driver, wait, d0)
            _click_day(driver, wait, d0)
            _navigate_to_month(driver, wait, d1)
            _click_day(driver, wait, d1)
            _submit(driver)

            rows = _parse_rows(driver, wait)

        except TimeoutException as e:
            logging.error(
                f"Selenium timeout for {label} {d0}–{d1}: {e.msg or e}"
            )
            rows = []

        finally:
            driver.quit()

        if not rows:
            logging.info(f"No data returned for {d0.date()} - {d1.date()}")
            return pd.Series([], dtype=float)

        records = []
        for row in rows:
            try:
                dt = pd.to_datetime(row["Tarih"], format="%d.%m.%Y")
                low = _convert_tr_number(row["Gişe Alış"])
                high = _convert_tr_number(row["Gişe Satış"])
                records.append((dt, round((low + high) / 2, 2)))
            except (KeyError, ValueError) as e:
                logging.warning(f"Skipping malformed row {row}: {e}")
                continue

        if not records:
            return pd.Series([], dtype=float)

        index, values = zip(*records)
        series = pd.Series(data=values, index=pd.DatetimeIndex(index))

        # Deduplicate: average prices on the same date rather than
        # arbitrarily keeping one — this is the safest approach for
        # a price series that will be used in financial calculations.
        if series.index.duplicated().any():
            dupes = series.index[series.index.duplicated(keep=False)].unique()
            logging.warning(
                f"Duplicate dates in response (will average): "
                f"{[d.date() for d in dupes]}"
            )
            series = series.groupby(level=0).mean().round(2)

        return series
