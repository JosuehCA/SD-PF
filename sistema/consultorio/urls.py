from django.urls import path
from . import views

urlpatterns = [
    path("", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("pacientes/", views.pacientes_view, name="pacientes"),
    path("registrar_paciente/", views.crear_paciente_view, name="crear_paciente"),
    path("pacientes/<int:paciente_id>/editar/", views.editar_paciente_view, name="editar_paciente"),
    path("pacientes/<int:paciente_id>/eliminar/", views.eliminar_paciente_view, name="eliminar_paciente"),
    path("citas/", views.citas_view, name="citas"),
    path("registrar_cita/", views.crear_cita_view, name="crear_cita"),
    path("citas/<int:cita_id>/editar/", views.editar_cita_view, name="editar_cita"),
    path("citas/<int:cita_id>/eliminar/", views.eliminar_cita_view, name="eliminar_cita"),
    path("historial/", views.historial_view, name="historial"),
    path("registrar_historial/<int:cita_id>/", views.crear_historial_view, name="crear_historial"),
    path("reportes/", views.reportes_view, name="reportes"),
]