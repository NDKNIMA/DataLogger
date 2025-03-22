from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import render, get_object_or_404
from django.utils.timezone import now, timedelta
from django.db.models import Sum
from django.db.models.functions import TruncMinute
from .models import Device, PulseLog
from .models import Hall, Station
from django.http import HttpResponse
import csv
from datetime import datetime
@api_view(['GET'])
def export_trend_csv(request, device_id):
    device = get_object_or_404(Device, id=device_id)
    hours = float(request.GET.get('hours', 1))
    since = now() - timedelta(hours=hours)

    logs = (
        PulseLog.objects.filter(device=device, timestamp__gte=since)
        .annotate(minute=TruncMinute('timestamp'))
        .values('minute')
        .annotate(total_pulse=Sum('pulse_count'))
        .order_by('minute')
    )

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response.write('\ufeff')  # UTF-8 BOM for Excel

    timestamp_str = datetime.now().strftime('%Y-%m-%d_%H-%M')
    filename = f"trend_{timestamp_str}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow(['زمان', 'تعداد پالس', 'میزان تولید (متر)'])

    for entry in logs:
        minute = entry['minute'].strftime('%Y/%m/%d - %H:%M')
        total_pulse = entry['total_pulse']
        meters = round(total_pulse * device.pulse_to_meter_factor, 2)
        writer.writerow([minute, total_pulse, meters])


    return response

@api_view(['GET'])
def halls_and_stations(request):
    halls = Hall.objects.all()
    data = []
    for hall in halls:
        stations = hall.stations.all()
        data.append({
            'hall': hall.name,
            'stations': [{'id': s.id, 'name': s.name} for s in stations]
        })
    return Response(data)

@api_view(['POST'])
def receive_pulse(request):
    mac = request.data.get('mac')
    pulse_count = request.data.get('pulse_count')
    if not mac or pulse_count is None:
        return Response({'error': 'Missing data'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        device = Device.objects.get(mac_address=mac)
    except Device.DoesNotExist:
        return Response({'error': 'Unknown device'}, status=status.HTTP_404_NOT_FOUND)
    PulseLog.objects.create(device=device, pulse_count=pulse_count, timestamp=now())
    return Response({'message': 'Data received'}, status=status.HTTP_201_CREATED)

@api_view(['GET'])
def device_efficiency(request):
    from django.utils.timezone import now
    from .models import Device, PulseLog
    from django.db.models import Sum
    from datetime import timedelta

    hall_name = request.GET.get('hall')
    station_id = request.GET.get('station')

    devices = Device.objects.all()

    if station_id:
        devices = devices.filter(station_id=station_id)
    elif hall_name:
        devices = devices.filter(station__hall__name=hall_name)

    one_minute_ago = now() - timedelta(minutes=1)
    data = []

    for device in devices:
        total_pulses = PulseLog.objects.filter(
            device=device,
            timestamp__gte=one_minute_ago
        ).aggregate(total=Sum('pulse_count'))['total'] or 0

        latest_log = PulseLog.objects.filter(device=device).order_by('-timestamp').first()
        is_online = False
        if latest_log and (now() - latest_log.timestamp).total_seconds() <= 60:
            is_online = True

        production = total_pulses * device.pulse_to_meter_factor
        efficiency = (production / device.optimal_production_per_min) * 100 if device.optimal_production_per_min > 0 else 0

        data.append({
            "device": device.name,
            "efficiency": round(efficiency, 1),
            "id": device.id,
            "is_online": is_online,
            "station": device.station.name if device.station else "نامشخص",
            "hall": device.station.hall.name if device.station and device.station.hall else "نامشخص"
        })

    return Response(data)


def dashboard(request):
    return render(request, 'devices/dashboard.html')

def device_trend_view(request, device_id):
    device = get_object_or_404(Device, id=device_id)
    return render(request, 'devices/device_trend.html', {'device': device})

@api_view(['GET'])
def get_device_trend_data(request, device_id):
    device = get_object_or_404(Device, id=device_id)
    hours = float(request.GET.get('hours', 1))
    since = now() - timedelta(hours=hours)
    logs = (
        PulseLog.objects.filter(device=device, timestamp__gte=since)
        .annotate(minute=TruncMinute('timestamp'))
        .values('minute')
        .annotate(total_pulse=Sum('pulse_count'))
        .order_by('minute')
    )
    data = []
    for entry in logs:
        meters = entry['total_pulse'] * device.pulse_to_meter_factor
        data.append({'minute': entry['minute'], 'production': round(meters, 2)})
    return Response(data)
