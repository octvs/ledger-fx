from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select

options = webdriver.FirefoxOptions()
options.add_argument("--headless")
driver = webdriver.Firefox(options=options)
driver.get("https://www.altinkaynak.com/Altin/Arsiv")
driver.implicitly_wait(0.5)

type_element = driver.find_element(By.ID, "cphMain_cphSubContent_ddGold")
type_select = Select(type_element)
print(type_select.options)

driver.implicitly_wait(0.5)
# type_select.select_by_visible_text("Gram Altın")

# date_element = driver.find_element(By.ID, "cphMain_cphSubContent_ddGold")
# type_select = Select(type_element)
# input id cphMain_cphSubContent_dateRangeInput

driver.quit()
