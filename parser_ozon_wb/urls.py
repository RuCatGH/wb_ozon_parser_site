from django.urls import path

from parser_ozon_wb import views

urlpatterns = [
    path('', views.index, name='index'),
    path('parse-wb/', views.parse_wb_view, name='parse_wb'),
    path('parse-ozon/', views.parse_ozon_view, name='parse_ozon'),
    path('compare-files/', views.compare_files_view, name='compare_data'),
    path('status/', views.get_counter, name='get_counter'),
]
