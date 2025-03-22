from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import render, get_object_or_404
from django.utils.timezone import now, timedelta
from django.db.models import Sum
from django.db.models.functions import TruncMinute
from .models import Device, PulseLog

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
    data = []
    one_minute_ago = now() - timedelta(minutes=1)
    for device in Device.objects.all():
        total_pulses = PulseLog.objects.filter(
            device=device,
            timestamp__gte=one_minute_ago
        ).aggregate(total=Sum('pulse_count'))['total'] or 0

        # بررسی آخرین پکت
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
            "is_online": is_online
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
