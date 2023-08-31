import time


import jmespath
import requests
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import undetected_chromedriver as uc
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from openpyxl import Workbook

from parser_ozon_wb.utils.google_sheets import get_sheet_values


def parse_data_wb(url, file_name, counter):
    try:
        wb_workbook = Workbook()
        ws = wb_workbook.active

        ws.append(['Артикул', 'Брэнд', 'Ссылка', 'Статус', 'Цена', 'Цена без скидки', 'Первая скидка цена',
                   'Вторая скидка цена', 'Оценка за товар', 'Отзыв 1', 'Отзыв 2', 'Отзыв 3', 'Отзыв 4', 'Отзыв 5',
                   'Отзыв 6', 'Отзыв 7', 'Отзыв 8', 'Отзыв 9', 'Отзыв 10'])

        options = webdriver.ChromeOptions()
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--start-maximized")
        service = Service()
        options.add_argument("--headless=new")
        driver = uc.Chrome(service=service, driver_executable_path='chromedriver', options=options)

        # Парсинг данных с ВБ
        wb_articles = get_sheet_values(url, 'Вб').iloc[:, 0]
        counter.quantity = len(wb_articles)
        for article in wb_articles:
            try:
                data = parse_wb(article, driver)
                ws.append(data)
            except Exception as ex:
                print(ex, 'Артикул')
            counter.count += 1
            counter.save()

        driver.close()
        driver.quit()

        wb_workbook.save(file_name)

        print("Парсинг завершен")
    except Exception as ex:
        wb_workbook.save(file_name)
        print(ex)


def parse_wb(article: str, driver):
    """
        Парсит данные о продукте с веб-сайта Вайлдберриз

        Args:
            article (str): Артикул продукта
            driver: Драйвер Selenium для взаимодействия с веб-страницей

        Returns:
            list: Список с данными о продукте
        """
    response = requests.get(
        f'https://card.wb.ru/cards/detail?appType=1&curr=rub&dest=-1257786&regions=80,38,4,64,83,33,68,70,69,30,86,75,40,1,66,110,22,31,48,71,114&spp=31&nm={article}',
    )
    link = f'https://www.wildberries.ru/catalog/{article}/detail.aspx'
    price = jmespath.search("data.products[0].salePriceU", response.json()) // 100
    imtId = jmespath.search("data.products[0].root", response.json())
    total_valuation = jmespath.search("data.products[0].reviewRating", response.json())
    brand = jmespath.search("data.products[0].brand", response.json())
    price_without_discount = jmespath.search("data.products[0].priceU", response.json()) // 100

    discount1 = jmespath.search('data.products[0].extended.basicPriceU', response.json()) // 100

    discount2 = jmespath.search('data.products[0].extended.clientPriceU', response.json()) // 100

    wait = WebDriverWait(driver, 10)

    driver.get(f'https://www.wildberries.ru/catalog/{article}/feedbacks?imtId={imtId}')
    time.sleep(2)
    element = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'product-line__price-now')))

    if driver.find_elements(By.CLASS_NAME, 'product-line__price-now')[-1].get_attribute(
            'textContent') == 'Нет в наличии':
        availability = driver.find_elements(By.CLASS_NAME, 'product-line__price-now')[-1].text
    else:
        availability = 'В наличии'

    rating_elements = driver.find_elements(By.CLASS_NAME, 'feedback__rating')

    feedbacks = [int(class_value.get_attribute('class')[-1]) for class_value in rating_elements][:10]

    return [article, brand, link, availability, price, price_without_discount, discount1, discount2,
            total_valuation] + feedbacks
