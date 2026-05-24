import requests

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db import IntegrityError, transaction

from .models import Usuario, Paciente, Cita, Consulta, Historial
from .forms import (
    LoginForm,
    PacienteForm,
    PacienteEditForm,
    CitaMedicoForm,
    CitaPacienteForm,
    ConsultaHistorialForm,
)


def es_medico(user):
    return user.is_staff or user.is_superuser or getattr(user, "rol", "") == "MEDICO"


def obtener_paciente_usuario(user):
    return get_object_or_404(Paciente, usuario=user)


def login_view(request):
    form = LoginForm(request.POST or None)
    error = None

    if request.method == "POST" and form.is_valid():
        user = authenticate(
            request,
            username=form.cleaned_data["username"],
            password=form.cleaned_data["password"],
        )

        if user is not None:
            login(request, user)
            return redirect("dashboard")

        error = "Usuario o contraseña incorrectos."

    return render(request, "VistaLogin.html", {
        "form": form,
        "error": error,
    })


def logout_view(request):
    logout(request)
    return redirect("login")


@login_required
def dashboard_view(request):
    if es_medico(request.user):
        total_pacientes = Paciente.objects.count()
        citas = Cita.objects.select_related("paciente").all()
    else:
        paciente = obtener_paciente_usuario(request.user)
        total_pacientes = 1
        citas = Cita.objects.select_related("paciente").filter(paciente=paciente)

    return render(request, "VistaDashboard.html", {
        "es_medico": es_medico(request.user),
        "total_pacientes": total_pacientes,
        "total_citas": citas.count(),
        "citas_programadas": citas.filter(estado="programada").count(),
        "citas_recientes": citas[:5],
    })


@login_required
@user_passes_test(es_medico)
def pacientes_view(request):
    pacientes = Paciente.objects.all().order_by("nombre")
    return render(request, "VistaPacientes.html", {"pacientes": pacientes})


@login_required
@user_passes_test(es_medico)
def crear_paciente_view(request):
    form = PacienteForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = Usuario.objects.create_user(
            username=form.cleaned_data["username"],
            password=form.cleaned_data["password"],
            email=form.cleaned_data["correo"],
            rol="PACIENTE",
        )

        paciente = form.save(commit=False)
        paciente.usuario = user
        paciente.save()

        messages.success(request, "Paciente registrado correctamente.")
        return redirect("pacientes")

    return render(request, "VistaRegistroPaciente.html", {
        "form": form,
        "titulo": "Registrar paciente",
        "descripcion": "Captura los datos generales del paciente y sus credenciales de acceso.",
    })


@login_required
@user_passes_test(es_medico)
def editar_paciente_view(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)
    form = PacienteEditForm(request.POST or None, instance=paciente)

    if request.method == "POST" and form.is_valid():
        form.save()
        paciente.usuario.email = form.cleaned_data["correo"]
        paciente.usuario.save()

        messages.success(request, "Paciente actualizado correctamente.")
        return redirect("pacientes")

    return render(request, "VistaRegistroPaciente.html", {
        "form": form,
        "titulo": "Editar paciente",
        "descripcion": "Actualiza la información general del paciente.",
    })


@login_required
@user_passes_test(es_medico)
def eliminar_paciente_view(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)

    if request.method == "POST":
        paciente.usuario.delete()
        messages.success(request, "Paciente eliminado correctamente.")

    return redirect("pacientes")


@login_required
def citas_view(request):
    if es_medico(request.user):
        citas = Cita.objects.select_related("paciente").all()
    else:
        paciente = obtener_paciente_usuario(request.user)
        citas = Cita.objects.select_related("paciente").filter(paciente=paciente)

    return render(request, "VistaCitas.html", {
        "citas": citas,
        "es_medico": es_medico(request.user),
    })

@login_required
def crear_cita_view(request):
    if es_medico(request.user):
        FormularioCita = CitaMedicoForm
    else:
        FormularioCita = CitaPacienteForm

    form = FormularioCita(request.POST or None)

    if request.method == "POST":
        if(form.is_valid()):
            fecha = form.cleaned_data['fecha'].strftime('%Y-%m-%d')
            hora = form.cleaned_data['hora'].strftime('%H:%M:%S')

            try:    # solicitar token
                url_servidor = "http://127.0.0.1:5001/solicitar_token"
                respuesta = requests.post(url_servidor, json={'fecha': fecha, 'hora': hora}, timeout=3)
                
                if respuesta.status_code == 409:
                    messages.error(request, "El horario está siendo procesado por otro usuario. Intenta de nuevo.")
                    return render(request, "VistaRegistrarCita.html", {"form": form})
                    
            except requests.exceptions.RequestException:
                messages.error(request, "Error de comunicación con el servidor de exclusión mutua.")
                return render(request, "VistaRegistrarCita.html", {"form": form})
            
            try:    # entrar a sección crítica
                with transaction.atomic():
                    cita = form.save(commit=False)
                    if not es_medico(request.user):
                        cita.paciente = obtener_paciente_usuario(request.user)

                    cita.estado = "programada"
                    cita.save()
                    messages.success(request, "Cita reservada exitosamente.")
            except IntegrityError as error:
                messages.error(request, f"No se pudo guardar la cita. Error: {error}")
                
            finally:    # liberar token
                try:
                    url_liberacion = "http://127.0.0.1:5001/liberar_token"
                    requests.post(url_liberacion, json={'fecha': fecha, 'hora': hora}, timeout=3)
                except requests.exceptions.RequestException:
                    pass 
            return redirect('citas')
    return render(request, "VistaRegistroCita.html", {
        "form": form,
        "titulo": "Registrar cita",
        "es_medico": es_medico(request.user),
    })


@login_required
def editar_cita_view(request, cita_id):
    if es_medico(request.user):
        cita = get_object_or_404(Cita, id=cita_id)
        FormularioCita = CitaMedicoForm
    else:
        paciente = obtener_paciente_usuario(request.user)
        cita = get_object_or_404(Cita, id=cita_id, paciente=paciente)
        FormularioCita = CitaPacienteForm

    if cita.estado == "atendida":
        messages.warning(request, "No se puede editar una cita que ya fue atendida.")
        return redirect("citas")

    form = FormularioCita(request.POST or None, instance=cita)

    if request.method == "POST" and form.is_valid():
        cita_editada = form.save(commit=False)

        if not es_medico(request.user):
            cita_editada.paciente = obtener_paciente_usuario(request.user)

        cita_editada.save()

        messages.success(request, "Cita actualizada correctamente.")
        return redirect("citas")

    return render(request, "VistaRegistroCita.html", {
        "form": form,
        "titulo": "Editar cita",
        "descripcion": "Modifica la fecha u hora de la cita.",
        "es_medico": es_medico(request.user),
    })


@login_required
def eliminar_cita_view(request, cita_id):
    if es_medico(request.user):
        cita = get_object_or_404(Cita, id=cita_id)
    else:
        paciente = obtener_paciente_usuario(request.user)
        cita = get_object_or_404(Cita, id=cita_id, paciente=paciente)

    if request.method == "POST":
        cita.estado = "cancelada"
        cita.save()
        messages.success(request, "Cita cancelada correctamente.")

    return redirect("citas")


@login_required
@user_passes_test(es_medico)
def crear_historial_view(request, cita_id):
    cita = get_object_or_404(Cita, id=cita_id)

    if hasattr(cita, "consulta"):
        messages.warning(request, "Esta cita ya tiene una consulta registrada.")
        return redirect("historial")

    form = ConsultaHistorialForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        consulta = Consulta.objects.create(
            cita=cita,
            temperatura=form.cleaned_data["temperatura"],
            peso=form.cleaned_data["peso"],
            altura=form.cleaned_data["altura"],
            presion_arterial=form.cleaned_data["presion_arterial"],
        )

        Historial.objects.create(
            consulta=consulta,
            diagnostico=form.cleaned_data["diagnostico"],
            resultados=form.cleaned_data["resultados"],
            prescripciones=form.cleaned_data["prescripciones"],
        )

        cita.estado = "atendida"
        cita.save()

        messages.success(request, "Historial clínico registrado correctamente.")
        return redirect("historial")

    return render(request, "VistaRegistroHistorial.html", {
        "form": form,
        "cita": cita,
        "titulo": "Registrar historial clínico",
        "descripcion": "Registra los signos vitales y la relatoría médica de la consulta.",
    })


@login_required
def historial_view(request):
    paciente_id = request.GET.get("paciente")

    if es_medico(request.user):
        pacientes = Paciente.objects.all().order_by("nombre")

        historias = Historial.objects.select_related(
            "consulta",
            "consulta__cita",
            "consulta__cita__paciente",
        ).all().order_by("-consulta__fecha_registro")

        if paciente_id:
            historias = historias.filter(consulta__cita__paciente_id=paciente_id)

    else:
        paciente = obtener_paciente_usuario(request.user)
        pacientes = None

        historias = Historial.objects.select_related(
            "consulta",
            "consulta__cita",
            "consulta__cita__paciente",
        ).filter(consulta__cita__paciente=paciente).order_by("-consulta__fecha_registro")

    return render(request, "VistaHistorial.html", {
        "historias": historias,
        "pacientes": pacientes,
        "paciente_id": paciente_id,
        "es_medico": es_medico(request.user),
    })


@login_required
@user_passes_test(es_medico)
def reportes_view(request):
    pacientes = Paciente.objects.all().order_by("nombre")
    citas = Cita.objects.select_related("paciente").all().order_by("fecha", "hora")
    historias = Historial.objects.select_related(
        "consulta",
        "consulta__cita",
        "consulta__cita__paciente",
    ).all()

    return render(request, "VistaReportes.html", {
        "pacientes": pacientes,
        "citas": citas,
        "historias": historias,
        "total_pacientes": pacientes.count(),
        "total_citas": citas.count(),
        "total_historias": historias.count(),
    })