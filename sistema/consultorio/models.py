from django.db import models as m
from django.contrib.auth.models import AbstractUser

class Usuario(AbstractUser):
    """
    Entidad usuario. Define a cualquier usuario en el sistema.

    Características:
        Nombre de usuario (heredado)
        Contraseña (heredado)
    """

    pass

class Paciente(Usuario):
    """
    Entidad paciente

    Características:
        Nombre  (heredado)
        Dirección   
        Correo Electrónico (heredado)
        Teléfono
        Edad
        Sexo

    Se debe permitir la consulta de sus datos por parte del paciente mismo y del médico, y la modificación y eliminación por parte del
    médico
    """

    direccion = m.CharField(max_length=200)
    telefono = m.CharField(max_length=50)
    edad = m.PositiveBigIntegerField()
    sexo = m.CharField(
        max_length=1,
        choices = [
            ('H', 'Hombre'),
            ('M', 'Mujer')
        ]
    )


class Cita(m.Model):
    """
    Entidad cita

    Características:
        Día
        Hora
    
    Se debe permitir su consulta, modificación y eliminación, tanto por parte del paciente como del médico

    Se manejan notificaciones para el paciente en caso de tener
    una nueva cita o haber sido eliminada
    """

    paciente = m.ForeignKey('Paciente', on_delete=m.CASCADE, related_name="paciente_cita")
    dia = m.DateField(auto_now_add=True)
    hora = m.TimeField()

class Consulta(m.Model):
    """
    Entidad consulta. Representa una consulta realizada sobre un paciente

    Características:
        Temperatura Corporal
        Peso
        Altura
        Presión arterial

    INFORMACIÓN ENCRIPTADA
    """

    paciente = m.ForeignKey('Paciente', on_delete=m.CASCADE, related_name="paciente_consulta")
    temperatura_corporal = m.DecimalField(max_digits=5, decimal_places=2)
    peso = m.DecimalField(max_digits=5, decimal_places=2)
    altura = m.IntegerField() # Altura en centímetros
    presion_arterial = m.DecimalField(max_digits=5, decimal_places=2)

class Historial(m.Model):
    """
    Entidad historial, generada por el médico sobre lo que ocurre en la consulta con el paciente

    Características:
        Diagnóstico del paciente
        Resultados de análisis previos del paciente
        Prescripciones del paciente
    """

    diagnostico = m.TextField()
    resultados = m.TextField()
    prescripciones = m.TextField()

    class Meta:
        verbose_name = "Historial"
        verbose_name_plural = "Historiales"