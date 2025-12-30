from django.contrib import admin
from .models import (
    Reservation,
    ReservationService,
    ReservationStatusHistory,
    ServiceProvider,
    ServiceProviderAvailability,
    WaitingList,
)

# Register your models here.

admin.site.register(Reservation)
admin.site.register(ReservationService)
admin.site.register(ReservationStatusHistory)
admin.site.register(ServiceProvider)
admin.site.register(ServiceProviderAvailability)
admin.site.register(WaitingList)
