from django.db import models

class Device(models.Model):
    name = models.CharField(max_length=100)
    mac_address = models.CharField(max_length=17, unique=True)
    pulse_to_meter_factor = models.FloatField()
    optimal_production_per_min = models.FloatField()

    def __str__(self):
        return self.name

class PulseLog(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    pulse_count = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['device']),
            models.Index(fields=['timestamp']),
        ]
