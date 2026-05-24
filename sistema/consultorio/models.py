from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models import Q

from .fields import EncryptedTextField, EncryptedCharField


class Usuario(AbstractUser):
    ROL_CHOICES = [
        ("MEDICO", "Médico"),
        ("PACIENTE", "Paciente"),
    ]

    rol = models.CharField(max_length=20, choices=ROL_CHOICES, default="PACIENTE")

    def es_medico(self):
        return self.rol == "MEDICO" or self.is_staff or self.is_superuser


class Paciente(models.Model):
    SEXO_CHOICES = [
    ("H", "Hombre"),
    ("M", "Mujer"),
    ]  

    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=120)
    direccion = models.CharField(max_length=200)
    correo = models.EmailField(unique=True)
    telefono = models.CharField(max_length=20)
    edad = models.PositiveIntegerField()
    sexo = models.CharField(max_length=1, choices=SEXO_CHOICES)

    def __str__(self):
        return self.nombre


class Cita(models.Model):
    ESTADOS = [
        ("programada", "Programada"),
        ("cancelada", "Cancelada"),
        ("atendida", "Atendida"),
    ]

    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name="citas")
    fecha = models.DateField()
    hora = models.TimeField()
    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default="programada"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["fecha", "hora"],
                condition=Q(estado="programada"),
                name="unique_cita_programada_por_fecha_hora",
            )
        ]
        ordering = ["fecha", "hora"]

    def __str__(self):
        return f"{self.paciente.nombre} - {self.fecha} {self.hora}"


class Consulta(models.Model):
    cita = models.OneToOneField(Cita, on_delete=models.CASCADE)
    temperatura = EncryptedCharField(max_length=512)
    peso = EncryptedCharField(max_length=512)
    altura = EncryptedCharField(max_length=512)
    presion_arterial = EncryptedCharField(max_length=512)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Consulta de {self.cita.paciente.nombre}"


class Historial(models.Model):
    consulta = models.OneToOneField(Consulta, on_delete=models.CASCADE)
    diagnostico = EncryptedTextField()
    resultados = EncryptedTextField(blank=True)
    prescripciones = EncryptedTextField(blank=True)

    def __str__(self):
        return f"Historial de {self.consulta.cita.paciente.nombre}"


class AuditLog(models.Model):
    """Tracks access and modifications to sensitive clinical data."""
    ACCIONES = [
        ("crear", "Crear"),
        ("editar", "Editar"),
        ("ver", "Ver"),
        ("eliminar", "Eliminar"),
    ]

    usuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True)
    accion = models.CharField(max_length=20, choices=ACCIONES)
    modelo = models.CharField(max_length=50)
    objeto_id = models.PositiveIntegerField()
    descripcion = models.TextField(blank=True)
    fecha = models.DateTimeField(auto_now_add=True)
    ip = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.usuario} - {self.accion} {self.modelo} #{self.objeto_id}"