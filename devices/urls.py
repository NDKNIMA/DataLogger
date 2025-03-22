from django.urls import path
from .views import receive_pulse, device_efficiency, dashboard, device_trend_view, get_device_trend_data,halls_and_stations,export_trend_csv

urlpatterns = [
    path('api/pulse/', receive_pulse),
    path('api/efficiency/', device_efficiency),
    path('dashboard/', dashboard),
    path('device/<int:device_id>/trend/', device_trend_view, name='device_trend_view'),
    path('api/device/<int:device_id>/trend-data/', get_device_trend_data, name='get_device_trend_data'),
    path('api/structure/', halls_and_stations),
    path('device/<int:device_id>/export-csv/', export_trend_csv, name='export_trend_csv'),


]
