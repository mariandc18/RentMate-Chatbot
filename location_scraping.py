from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


driver = webdriver.Chrome()
driver.get('https://callejero-cuba.openalfa.com/la-habana')  

provinces_info = {}
provinces_links = driver.find_elements(By.XPATH, "//*[@id='regions']/div[1]/ul/li/a")
for province in range(len(provinces_links)):
    # Recargar los enlaces en cada iteración para evitar el error StaleElementReferenceException
    provinces_links = driver.find_elements(By.XPATH, "//*[@id='regions']/div[1]/ul/li/a")
    provincia = provinces_links[province]
    name = provincia.text
    link = provincia.get_attribute('href')
    print(f"Provincia: {name}")

    driver.get(link)
    time.sleep(2)
    try:
        barrios_elements = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, '//*[@id="regions"]//li'))
        )
        # Eliminar duplicados
        barrios = list(set([b.text.strip().replace('\n', '') for b in barrios_elements if b.text.strip()]))
    except Exception as e:
        print(f"No se pudieron obtener barrios para {name}. Error: {e}")
        barrios = []

    provinces_info[name] = barrios
    print(f"Provincia: {name}, Barrios: {barrios}")
    driver.get('https://callejero-cuba.openalfa.com/la-habana')
    time.sleep(2)

driver.quit()

  