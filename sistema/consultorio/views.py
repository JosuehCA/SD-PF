from django.http import HttpResponse
from . import models

def index(request):
    return HttpResponse("Hello, world. You're at the consultorio index.")

def generarReporte(request):
    # Autentifación requerida
    pass

def generarHistorial(request):
    pass

def crearPaciente(request):
    pass

def consultarDatosDePaciente(request):
    pass

def crearCita(request):
    pass

def consultarDatosDeCita(request):
    pass

def crearConsulta(request):
    pass

def consultarDatosDeConsulta(request):
    pass