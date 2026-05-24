from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, Paciente, Cita, Consulta, Historial


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Rol del sistema", {"fields": ("rol",)}),
    )


admin.site.register(Paciente)
admin.site.register(Cita)
admin.site.register(Consulta)
admin.site.register(Historial)