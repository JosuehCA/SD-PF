import os
import requests
import threading
import time

URL_SERVER = "http://127.0.0.1:5001/solicitar_token"
DATOS_CITA = {
    "fecha": "2026-06-01",
    "hora": "10:00:00"
}

# Auth header must match TOKEN_SERVER_SECRET env var
AUTH_HEADERS = {
    "X-Internal-Auth": os.environ.get("TOKEN_SERVER_SECRET", "dev-secret-change-in-production")
}

def enviar_peticion(nombre_paciente, resultados):
    print(f"[{nombre_paciente}] Solicitando token para {DATOS_CITA['fecha']} a las {DATOS_CITA['hora']}...")
    try:
        respuesta = requests.post(URL_SERVER, json=DATOS_CITA, headers=AUTH_HEADERS, timeout=3)
        resultados[nombre_paciente] = (respuesta.status_code, respuesta.json())
    except Exception as e:
        resultados[nombre_paciente] = ("Error", str(e))

if __name__ == "__main__":
    print("--- INICIANDO PRUEBA DE CONCURRENCIA DISTRIBUIDA ---")
    resultados_prueba = {}

    hilo_paciente_a = threading.Thread(target=enviar_peticion, args=("Paciente A", resultados_prueba))
    hilo_paciente_b = threading.Thread(target=enviar_peticion, args=("Paciente B", resultados_prueba))

    hilo_paciente_a.start()
    hilo_paciente_b.start()

    hilo_paciente_a.join()
    hilo_paciente_b.join()

    print("\n--- RESULTADOS DE LA EVALUACIÓN ---")
    for paciente, datos in resultados_prueba.items():
        status, json_res = datos
        print(f"{paciente} -> Código HTTP: {status} | Respuesta: {json_res}")

    requests.post("http://127.0.0.1:5001/liberar_token", json=DATOS_CITA, headers=AUTH_HEADERS)