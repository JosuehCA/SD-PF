from django.db import models
from django.contrib.auth.models import AbstractUser

class Usuario(AbstractUser):
    """
    Entidad usuario. Define a cualquier usuario en el sistema.

    Características:
        Nombre de usuario
        Contraseña
    """
    
    pass

class Paciente(Usuario):
    """
    Entidad paciente

    Características:
        Nombre
        Dirección
        Correo Electrónico
        Teléfono
        Edad
        Sexo

    Se debe permitir la consulta de sus datos por parte del paciente mismo y del médico, y la modificación y eliminación por parte del
    médico
    """

    pass

class Cita(models.Model):
    """
    Entidad cita

    Características:
        Día
        Hora
    
    Se debe permitir su consulta, modificación y eliminación, tanto por parte del paciente como del médico

    Se manejan notificaciones para el paciente en caso de tener
    una nueva cita o haber sido eliminada
    """

    pass

class Consulta(models.Model):
    """
    Entidad consulta. Representa una consulta realizada sobre un paciente

    Características:
        Temperatura Corporal
        Peso
        Altura
        Presión arterial

    INFORMACIÓN ENCRIPTADA
    """

    pass

class Historial(models.Model):
    """
    Entidad historial, generada por el médico sobre lo que ocurre en la consulta con el paciente

    Características:
        ???
    """

    pass