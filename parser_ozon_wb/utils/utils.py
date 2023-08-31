import pandas as pd
from openpyxl import Workbook

from parser_ozon_wb.utils.google_sheets import get_sheet_values


def cross_reference_data(url, ozon_file, wb_file, file_name) -> None:
    """
    Загружает данные из файлов Excel, объединяет их и сохраняет результаты в файл Excel
    """

    guide = get_sheet_values(url, 'Справочник')
    wb = pd.read_excel(ozon_file)
    ozon = pd.read_excel(wb_file)

    wb['Артикул'] = wb['Артикул'].astype(str)
    ozon['Артикул'] = ozon['Артикул'].astype(str)
    guide['Артикул'] = guide['Артикул'].astype(str)

    merged_df = pd.concat([wb, ozon], ignore_index=True)

    merged_df = pd.merge(guide, merged_df, on='Артикул')
    merged_df.to_excel(file_name, index=False)
