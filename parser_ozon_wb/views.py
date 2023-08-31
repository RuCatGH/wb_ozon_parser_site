import datetime
import os
import threading
import time

from django.http import JsonResponse, FileResponse
from django.shortcuts import render

from parser_ozon_wb.models import Counter
from parser_ozon_wb.utils.parsers.ozon import parse_data_ozon
from parser_ozon_wb.utils.parsers.wb import parse_data_wb
from parser_ozon_wb.utils.utils import cross_reference_data

files_for_delete = []


def index(request):
    return render(request, 'parser_ozon_wb/index.html')


def parse_wb_view(request):
    counter = Counter.objects.create()

    for file in files_for_delete:
        try:
            os.remove(file)
        except:
            pass
        files_for_delete.remove(file)
    url = request.GET.get('url')
    file_name_start = request.GET.get('file_name')
    counter.name = file_name_start
    counter.save()
    file_name = f'files/{file_name_start.replace(" ", "-").replace(".", "_").replace(":", "")}.xlsx'

    t1 = threading.Thread(target=parse_data_wb, args=(url, file_name, counter,), daemon=True)
    t1.start()
    t1.join()

    response = FileResponse(open(file_name, 'rb'),
                            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    files_for_delete.append(file_name)
    counter.delete()
    return response


def parse_ozon_view(request):
    counter = Counter.objects.create()

    for file in files_for_delete:
        try:
            os.remove(file)
        except:
            pass
        files_for_delete.remove(file)
    url = request.GET.get('url')
    file_name_start = request.GET.get('file_name')
    counter.name = file_name_start
    counter.save()
    file_name = f'files/{file_name_start.replace(" ", "-").replace(".", "_").replace(":", "")}.xlsx'
    t1 = threading.Thread(target=parse_data_ozon, args=(url, file_name, counter,), daemon=True)
    t1.start()
    t1.join()

    response = FileResponse(open(file_name, 'rb'),
                            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    files_for_delete.append(file_name)
    counter.delete()
    return response


def compare_files_view(request):
    if request.method == 'POST':
        for file in files_for_delete:
            try:
                os.remove(file)
            except:
                pass
            files_for_delete.remove(file)
        file1 = request.FILES['file1']
        file2 = request.FILES['file2']
        file_name_start = request.POST.get('file_name')
        file_name = f'files/{file_name_start.replace(" ", "-").replace(".", "_").replace(":", "")}.xlsx'
        url = request.POST.get('url')  # Получаем значение ссылки

        t1 = threading.Thread(target=cross_reference_data, args=(url, file2, file1, file_name,), daemon=True)
        t1.start()
        t1.join()

        response = FileResponse(open(file_name, 'rb'),
                                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        files_for_delete.append(file_name)
        return response


def get_counter(request):
    try:
        file_name = request.GET.get('file_name')

        count = Counter.objects.get(name=file_name).count
        quantity = Counter.objects.get(name=file_name).quantity
        return JsonResponse({'count': count, 'quantity': quantity})
    except:
        return JsonResponse({'count': '0', 'quantity': '0'})
