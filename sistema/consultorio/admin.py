from django.contrib import admin

from .models import Usuario, Paciente, Cita, Consulta, Historial

admin.site.register(Usuario)
admin.site.register(Paciente)
admin.site.register(Cita)
admin.site.register(Consulta)
admin.site.register(Historial)