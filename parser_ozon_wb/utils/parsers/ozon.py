import json
import time

import jmespath
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import undetected_chromedriver as uc
from openpyxl import Workbook

from parser_ozon_wb.utils.google_sheets import get_sheet_values


def parse_data_ozon(url, file_name, counter) -> None:
    """
    Парсит данные с Вайлдберриз и Озон, сохраняет результаты в файлы Excel и выводит сообщение о завершении парсинга
    """
    try:
        ozon_workbook = Workbook()

        ws = ozon_workbook.active

        ws.append(['Артикул', 'Брэнд', 'Ссылка', 'Статус', 'Цена', 'Цена с озоной картой', 'Цена без скидки',
                   'Оценка за товар', 'Отзыв 1', 'Отзыв 2', 'Отзыв 3', 'Отзыв 4', 'Отзыв 5', 'Отзыв 6', 'Отзыв 7',
                   'Отзыв 8', 'Отзыв 9', 'Отзыв 10'])

        options = webdriver.ChromeOptions()
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--start-maximized")
        driver = uc.Chrome(driver_executable_path='/home/chromedriver', options=options, headless=True, sandbox=False)

        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            'source': '''
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
        '''
        })
        # Парсинг данных с OZON
        ozon_articles = get_sheet_values(url, 'Озон').iloc[:, 0]

        driver.get('https://www.ozon.ru/')
        time.sleep(7)
        counter.quantity = len(ozon_articles)
        for article in ozon_articles:
            try:
                data = parse_ozon(article, driver)
                ws.append(data)
            except Exception as ex:
                print(ex, 'Артикул')

            counter.count += 1
            counter.save()

        driver.close()
        driver.quit()

        ozon_workbook.save(file_name)

        print("Парсинг завершен")
    except Exception as ex:
        ozon_workbook.save(file_name)
        print(ex)


def parse_ozon(article: str, driver) -> list:
    """
    Парсит данные о продукте с веб-сайта Озон

    Args:
        article (str): Артикул продукта
        driver: Драйвер Selenium для взаимодействия с веб-страницей

    Returns:
        list: Список с данными о продукте
    """
    driver.get(f'https://www.ozon.ru/search/?text={article}&from_global=true')

    time.sleep(3)

    try:
        link = driver.find_elements(By.CLASS_NAME, 'tile-hover-target')[-1].get_attribute('href')

        link_json = link.split('https://www.ozon.ru')[1]

        driver.get(
            f'https://www.ozon.ru/api/entrypoint-api.bx/page/json/v2?url={link_json}&layout_container=pdpReviews&layout_page_index=2')
        time.sleep(1)
        json_data_html = driver.find_element(By.TAG_NAME, 'pre').text
        json_data = json.loads(json_data_html)

        valuation = []

        for key in json_data['widgetStates']:
            if key.startswith('webListReviews'):
                value = json_data['widgetStates'][key]
                json_feedbacks = json.loads(value)
                valuation = jmespath.search('reviews[:10].content.score', json_feedbacks)
        driver.get(link)

        json_price_original = json.loads(
            driver.find_element(By.XPATH, "//*[starts-with(@id, 'state-webPrice')]").get_attribute('data-state'))

        price_original = jmespath.search('originalPrice', json_price_original).replace('₽', '')
        price_with_card = jmespath.search('cardPrice', json_price_original).replace('₽', '')

        json_product = json.loads(
            driver.find_element(By.CSS_SELECTOR, '[type="application/ld+json"]').get_attribute('textContent'))

        price = jmespath.search('offers.price', json_product)
        brand = jmespath.search('brand', json_product)

        try:
            total_valuation = jmespath.search('aggregateRating.ratingValue', json_product)
        except:
            total_valuation = 0
        availability = 'В наличии'
    except Exception as ex:
        print(ex)
        brand = None
        link = None
        price = None
        availability = 'Нет в наличии'
        price_with_card = None
        price_original = None
        total_valuation = None
        valuation = ['']

    return [article, brand, link, availability, price, price_with_card, price_original, total_valuation] + valuation
