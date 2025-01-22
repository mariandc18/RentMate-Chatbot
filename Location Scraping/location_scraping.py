from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import re  

options = webdriver.ChromeOptions()
options.add_argument('--ignore-certificate-errors')  # Evitar errores SSL
driver = webdriver.Chrome(options=options)
driver.get('https://callejero-cuba.openalfa.com/la-habana')  

municipalities_info = {}
# Obtener enlaces a los municipios
municipalities_links = driver.find_elements(By.XPATH, "//*[@id='regions']/div[1]/ul/li/a")

for province in range(len(municipalities_links)):
    # Recargar los enlaces para evitar StaleElementReferenceException
    municipalities_links = driver.find_elements(By.XPATH, "//*[@id='regions']/div[1]/ul/li/a")
    municipality = municipalities_links[province]
    name = municipality.text
    link = municipality.get_attribute('href')
    print(f"Provincia: {name}")

    driver.get(link)
    time.sleep(2)

    # Extraer barrios
    try:
        neighborhoods_elements = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, '//*[@id="regions"]//li/a'))
        )
        neighborhoods = list(set([b.text.strip().replace('\n', ' ') for b in neighborhoods_elements if b.text.strip()]))
    except Exception as e:
        print(f"No se pudieron obtener barrios para {name}. Error: {e}")
        neighborhoods = []

    neighborhoods_info = {}
    for neighborhood in range(len(neighborhoods_elements)):
        neighborhoods_elements = driver.find_elements(By.XPATH, '//*[@id="regions"]//li/a')
        neighborhood_element = neighborhoods_elements[neighborhood]
        neighborhood_name = neighborhood_element.text
        neighborhoods_link = neighborhood_element.get_attribute('href')
        print(f"  Barrio: {neighborhood_name}")

        driver.get(neighborhoods_link)
        time.sleep(2)

        #extraer calles 
        try:
            streets_elements = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.XPATH, '//*[@id="divcalles"]//ul/li'))
            )
            # Filtrar encabezados, números, paréntesis y saltos de línea
            streets = []
            for c in streets_elements:
                street = c.text.strip().replace('\n', ' ') 
                if not street.isupper():  
                    street = re.sub(r'\(.*?\)', '', street).strip()
                    if not street.isdigit():  
                        if street: 
                            streets.append(street)

        except Exception as e:
            print(f"    No se pudieron obtener calles para {neighborhood_name}. Error: {e}")
            streets = []

        neighborhoods_info[neighborhood_name] = streets
        print(f"    Calles: {streets}")
        driver.get(link)
        time.sleep(2)

    municipalities_info[name] = neighborhoods_info
    driver.get('https://callejero-cuba.openalfa.com/la-habana')
    time.sleep(2)

driver.quit()

#guardar en un json 
with open('barrios_calles_habana.json', 'w', encoding='utf-8') as f: 
    json.dump(municipalities_info, f, ensure_ascii=False, indent=4)
 