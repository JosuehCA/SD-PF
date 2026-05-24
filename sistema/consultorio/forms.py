import re
from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Usuario, Paciente, Cita


DOMINIOS_CORREO_PERMITIDOS = [
    "gmail.com",
    "hotmail.com",
    "outlook.com",
    "icloud.com",
    "yahoo.com",
    "live.com",
    "uady.mx",
]


def validar_texto_nombre(valor):
    valor = valor.strip()

    if len(valor) < 3:
        raise ValidationError("El nombre debe tener al menos 3 caracteres.")

    if not re.match(r"^[A-Za-zÁÉÍÓÚáéíóúÑñÜü\s.'-]+$", valor):
        raise ValidationError("El nombre solo puede contener letras, espacios, puntos, apóstrofes o guiones.")

    if "  " in valor:
        raise ValidationError("El nombre no debe contener espacios dobles.")

    return " ".join(valor.split()).title()


def validar_correo(correo):
    correo = correo.strip().lower()
    dominio = correo.split("@")[-1]

    if dominio not in DOMINIOS_CORREO_PERMITIDOS:
        raise ValidationError(
            "Ingresa un correo con un dominio válido, Ej. Gmail, Outlook, Hotmail, iCloud."
        )

    return correo


def validar_telefono(telefono):
    telefono_limpio = re.sub(r"\D", "", telefono)

    if len(telefono_limpio) != 10:
        raise ValidationError("El teléfono debe tener 10 dígitos.")

    if telefono_limpio.startswith("0"):
        raise ValidationError("El teléfono no debe iniciar con 0.")

    return telefono_limpio


def validar_password(password):
    if len(password) < 8:
        raise ValidationError("La contraseña debe tener al menos 8 caracteres.")

    if not re.search(r"[A-Z]", password):
        raise ValidationError("La contraseña debe incluir al menos una letra mayúscula.")

    if not re.search(r"[a-z]", password):
        raise ValidationError("La contraseña debe incluir al menos una letra minúscula.")

    if not re.search(r"\d", password):
        raise ValidationError("La contraseña debe incluir al menos un número.")

    if not re.search(r"[^\w\s]", password):
        raise ValidationError("La contraseña debe incluir al menos un carácter especial.")

    return password


class LoginForm(forms.Form):
    username = forms.CharField(
        label="Usuario",
        min_length=4,
        max_length=30,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Ej. aurora.cetina",
            "autocomplete": "username",
        })
    )

    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Ingresa tu contraseña",
            "autocomplete": "current-password",
        })
    )


class PacienteForm(forms.ModelForm):
    username = forms.CharField(
        label="Usuario",
        min_length=4,
        max_length=30,
        help_text="Usa letras, números, punto o guion bajo. Ejemplo: aurora.cetina",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Ej. aurora.cetina",
            "autocomplete": "username",
        })
    )

    password = forms.CharField(
        label="Contraseña",
        help_text="Mínimo 8 caracteres, con mayúscula, minúscula, número y símbolo.",
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Ej. Paciente#2026",
            "autocomplete": "new-password",
        })
    )

    password_confirm = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Repite la contraseña",
            "autocomplete": "new-password",
        })
    )

    class Meta:
        model = Paciente
        fields = ["nombre", "direccion", "correo", "telefono", "edad", "sexo"]

        widgets = {
            "nombre": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ej. Aurora Cetina López",
                "autocomplete": "name",
            }),
            "direccion": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ej. Calle 60 #123, Col. Centro",
                "autocomplete": "street-address",
            }),
            "correo": forms.EmailInput(attrs={
                "class": "form-control",
                "placeholder": "Ej. paciente@gmail.com",
                "autocomplete": "email",
            }),
            "telefono": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ej. 9991234567",
                "maxlength": "10",
                "inputmode": "numeric",
                "autocomplete": "tel",
            }),
            "edad": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Ej. 28",
                "min": "1",
                "max": "120",
            }),
            "sexo": forms.Select(attrs={
                "class": "form-control",
            }),
        }

    def clean_username(self):
        username = self.cleaned_data["username"].strip().lower()

        if not re.match(r"^[a-zA-Z0-9._]+$", username):
            raise forms.ValidationError("El usuario solo puede contener letras, números, punto o guion bajo.")

        if Usuario.objects.filter(username=username).exists():
            raise forms.ValidationError("Este nombre de usuario ya está registrado.")

        return username

    def clean_password(self):
        return validar_password(self.cleaned_data["password"])

    def clean_nombre(self):
        return validar_texto_nombre(self.cleaned_data["nombre"])

    def clean_correo(self):
        correo = validar_correo(self.cleaned_data["correo"])

        if Paciente.objects.filter(correo=correo).exists():
            raise forms.ValidationError("Este correo ya está registrado.")

        return correo

    def clean_telefono(self):
        telefono = validar_telefono(self.cleaned_data["telefono"])

        if Paciente.objects.filter(telefono=telefono).exists():
            raise forms.ValidationError("Este teléfono ya está registrado.")

        return telefono

    def clean_direccion(self):
        direccion = self.cleaned_data["direccion"].strip()

        if len(direccion) < 8:
            raise forms.ValidationError("Ingresa una dirección más completa.")

        return " ".join(direccion.split())

    def clean_edad(self):
        edad = self.cleaned_data["edad"]

        if edad < 1 or edad > 120:
            raise forms.ValidationError("La edad debe estar entre 1 y 120 años.")

        return edad

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password and password_confirm and password != password_confirm:
            self.add_error("password_confirm", "Las contraseñas no coinciden.")

        return cleaned_data


class PacienteEditForm(forms.ModelForm):
    class Meta:
        model = Paciente
        fields = ["nombre", "direccion", "correo", "telefono", "edad", "sexo"]

        widgets = {
            "nombre": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ej. Aurora Cetina López",
            }),
            "direccion": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ej. Calle 60 #123, Col. Centro",
            }),
            "correo": forms.EmailInput(attrs={
                "class": "form-control",
                "placeholder": "Ej. paciente@gmail.com",
            }),
            "telefono": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ej. 9991234567",
                "maxlength": "10",
                "inputmode": "numeric",
            }),
            "edad": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Ej. 28",
                "min": "1",
                "max": "120",
            }),
            "sexo": forms.Select(attrs={
                "class": "form-control",
            }),
        }

    def clean_nombre(self):
        return validar_texto_nombre(self.cleaned_data["nombre"])

    def clean_correo(self):
        correo = validar_correo(self.cleaned_data["correo"])

        existe = Paciente.objects.filter(correo=correo).exclude(pk=self.instance.pk).exists()

        if existe:
            raise forms.ValidationError("Este correo ya está registrado por otro paciente.")

        return correo

    def clean_telefono(self):
        telefono = validar_telefono(self.cleaned_data["telefono"])

        existe = Paciente.objects.filter(telefono=telefono).exclude(pk=self.instance.pk).exists()

        if existe:
            raise forms.ValidationError("Este teléfono ya está registrado por otro paciente.")

        return telefono

    def clean_direccion(self):
        direccion = self.cleaned_data["direccion"].strip()

        if len(direccion) < 8:
            raise forms.ValidationError("Ingresa una dirección más completa.")

        return " ".join(direccion.split())

    def clean_edad(self):
        edad = self.cleaned_data["edad"]

        if edad < 1 or edad > 120:
            raise forms.ValidationError("La edad debe estar entre 1 y 120 años.")

        return edad


class CitaMedicoForm(forms.ModelForm):
    class Meta:
        model = Cita
        fields = ["paciente", "fecha", "hora"]

        widgets = {
            "paciente": forms.Select(attrs={
                "class": "form-control",
            }),
            "fecha": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date",
            }),
            "hora": forms.TimeInput(attrs={
                "class": "form-control",
                "type": "time",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["paciente"].empty_label = "Selecciona un paciente"

    def clean(self):
        cleaned_data = super().clean()
        fecha = cleaned_data.get("fecha")
        hora = cleaned_data.get("hora")

        validar_fecha_hora_cita(self, fecha, hora)

        return cleaned_data


class CitaPacienteForm(forms.ModelForm):
    class Meta:
        model = Cita
        fields = ["fecha", "hora"]

        widgets = {
            "fecha": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date",
            }),
            "hora": forms.TimeInput(attrs={
                "class": "form-control",
                "type": "time",
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        fecha = cleaned_data.get("fecha")
        hora = cleaned_data.get("hora")

        validar_fecha_hora_cita(self, fecha, hora)

        return cleaned_data


def validar_fecha_hora_cita(form, fecha, hora):
    if not fecha or not hora:
        return

    ahora = timezone.localtime()
    fecha_actual = ahora.date()
    hora_actual = ahora.time().replace(second=0, microsecond=0)

    if fecha < fecha_actual:
        form.add_error(
            "fecha",
            "No es posible agendar citas en fechas anteriores al día actual."
        )
        return

    if fecha == fecha_actual and hora <= hora_actual:
        form.add_error(
            "hora",
            "No es posible agendar citas en ese horario. Selecciona un horario posterior a la hora actual."
        )
        return

    cita_existente = Cita.objects.filter(
        fecha=fecha,
        hora=hora,
        estado= "programada",
    )

    if form.instance.pk:
        cita_existente = cita_existente.exclude(pk=form.instance.pk)

    if cita_existente.exists():
        form.add_error(
            "hora",
            "Ese horario ya fue reservado. Selecciona otro horario."
        )

class ConsultaHistorialForm(forms.Form):
    temperatura = forms.DecimalField(
        label="Temperatura corporal",
        max_digits=4,
        decimal_places=1,
        min_value=Decimal("30.0"),
        max_value=Decimal("45.0"),
        widget=forms.NumberInput(attrs={
            "class": "form-control",
            "step": "0.1",
            "placeholder": "Ej. 36.5",
        })
    )

    peso = forms.DecimalField(
        label="Peso",
        max_digits=5,
        decimal_places=2,
        min_value=Decimal("1.00"),
        max_value=Decimal("300.00"),
        widget=forms.NumberInput(attrs={
            "class": "form-control",
            "step": "0.01",
            "placeholder": "Ej. 65.50",
        })
    )

    altura = forms.DecimalField(
        label="Altura",
        max_digits=4,
        decimal_places=2,
        min_value=Decimal("0.30"),
        max_value=Decimal("2.50"),
        widget=forms.NumberInput(attrs={
            "class": "form-control",
            "step": "0.01",
            "placeholder": "Ej. 1.65",
        })
    )

    presion_arterial = forms.CharField(
        label="Presión arterial",
        max_length=7,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Ej. 120/80",
        })
    )

    diagnostico = forms.CharField(
        label="Diagnóstico",
        min_length=5,
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 4,
            "placeholder": "Describe el diagnóstico del paciente.",
        })
    )

    resultados = forms.CharField(
        label="Resultados",
        required=False,
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 4,
            "placeholder": "Agrega observaciones o resultados relevantes.",
        })
    )

    prescripciones = forms.CharField(
        label="Prescripciones",
        required=False,
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 4,
            "placeholder": "Indica medicamentos, dosis o recomendaciones.",
        })
    )

    def clean_presion_arterial(self):
        presion = self.cleaned_data["presion_arterial"].strip()

        if not re.match(r"^\d{2,3}/\d{2,3}$", presion):
            raise forms.ValidationError("Usa el formato correcto. Ejemplo: 120/80.")

        sistolica, diastolica = map(int, presion.split("/"))

        if sistolica < 70 or sistolica > 250:
            raise forms.ValidationError("La presión sistólica debe estar entre 70 y 250.")

        if diastolica < 40 or diastolica > 150:
            raise forms.ValidationError("La presión diastólica debe estar entre 40 y 150.")

        if diastolica >= sistolica:
            raise forms.ValidationError("La presión diastólica debe ser menor que la sistólica.")

        return presion

    def clean_diagnostico(self):
        diagnostico = self.cleaned_data["diagnostico"].strip()

        if len(diagnostico) < 5:
            raise forms.ValidationError("El diagnóstico debe ser más descriptivo.")

        return diagnostico

    def clean_resultados(self):
        resultados = self.cleaned_data.get("resultados", "").strip()
        return resultados

    def clean_prescripciones(self):
        prescripciones = self.cleaned_data.get("prescripciones", "").strip()
        return prescripciones


class PacienteSignupForm(forms.ModelForm):
    """Form for patient self-registration."""
    username = forms.CharField(
        label="Usuario",
        min_length=4,
        max_length=30,
        help_text="Usa letras, números, punto o guion bajo.",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Ej. aurora.cetina",
            "autocomplete": "username",
        })
    )

    password = forms.CharField(
        label="Contraseña",
        help_text="Mínimo 8 caracteres, con mayúscula, minúscula, número y símbolo.",
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Ej. MiClave#2026",
            "autocomplete": "new-password",
        })
    )

    password_confirm = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Repite la contraseña",
            "autocomplete": "new-password",
        })
    )

    class Meta:
        model = Paciente
        fields = ["nombre", "direccion", "correo", "telefono", "edad", "sexo"]

        widgets = {
            "nombre": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ej. Aurora Cetina López",
            }),
            "direccion": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ej. Calle 60 #123, Col. Centro",
            }),
            "correo": forms.EmailInput(attrs={
                "class": "form-control",
                "placeholder": "Ej. paciente@gmail.com",
            }),
            "telefono": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ej. 9991234567",
                "maxlength": "10",
                "inputmode": "numeric",
            }),
            "edad": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Ej. 28",
                "min": "1",
                "max": "120",
            }),
            "sexo": forms.Select(attrs={
                "class": "form-control",
            }),
        }

    def clean_username(self):
        username = self.cleaned_data["username"].strip().lower()

        if not re.match(r"^[a-zA-Z0-9._]+$", username):
            raise forms.ValidationError("El usuario solo puede contener letras, números, punto o guion bajo.")

        if Usuario.objects.filter(username=username).exists():
            raise forms.ValidationError("Este nombre de usuario ya está registrado.")

        return username

    def clean_password(self):
        return validar_password(self.cleaned_data["password"])

    def clean_nombre(self):
        return validar_texto_nombre(self.cleaned_data["nombre"])

    def clean_correo(self):
        correo = validar_correo(self.cleaned_data["correo"])

        if Paciente.objects.filter(correo=correo).exists():
            raise forms.ValidationError("Este correo ya está registrado.")

        return correo

    def clean_telefono(self):
        telefono = validar_telefono(self.cleaned_data["telefono"])

        if Paciente.objects.filter(telefono=telefono).exists():
            raise forms.ValidationError("Este teléfono ya está registrado.")

        return telefono

    def clean_direccion(self):
        direccion = self.cleaned_data["direccion"].strip()

        if len(direccion) < 8:
            raise forms.ValidationError("Ingresa una dirección más completa.")

        return " ".join(direccion.split())

    def clean_edad(self):
        edad = self.cleaned_data["edad"]

        if edad < 1 or edad > 120:
            raise forms.ValidationError("La edad debe estar entre 1 y 120 años.")

        return edad

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password and password_confirm and password != password_confirm:
            self.add_error("password_confirm", "Las contraseñas no coinciden.")

        return cleaned_data