from django.contrib import admin
from .models import Hall, Station, Device, PulseLog

admin.site.register(Hall)
admin.site.register(Station)
admin.site.register(Device)
admin.site.register(PulseLog)
