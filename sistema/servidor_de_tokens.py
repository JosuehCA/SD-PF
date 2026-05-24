import os
import threading
import time

from flask import Flask, request, jsonify

app = Flask(__name__)

horarios_bloqueados = {}
lock = threading.Lock()

TOKEN_TTL_SECONDS = 10  # Auto-release tokens after this many seconds
SHARED_SECRET = os.environ.get("TOKEN_SERVER_SECRET", "dev-secret-change-in-production")


@app.before_request
def verify_auth():
    """Validate shared secret on all requests."""
    token = request.headers.get("X-Internal-Auth")
    if token != SHARED_SECRET:
        return jsonify({"status": "error", "message": "No autorizado"}), 401


def cleanup_expired_tokens():
    """Remove tokens that have exceeded their TTL."""
    now = time.time()
    expired = [
        slot for slot, entry in horarios_bloqueados.items()
        if isinstance(entry, dict) and (now - entry["timestamp"]) > TOKEN_TTL_SECONDS
    ]
    for slot in expired:
        del horarios_bloqueados[slot]


@app.route('/solicitar_token', methods=['POST'])
def solicitar_token():
    data = request.json
    fecha = data.get('fecha')
    hora = data.get('hora')

    if not fecha or not hora:
        return jsonify({"status": "error", "message": "Faltan parámetros"}), 400

    id_slot = f"{fecha}_{hora}"

    with lock:
        cleanup_expired_tokens()

        entry = horarios_bloqueados.get(id_slot)
        if entry:
            return jsonify({
                "status": "denied",
                "message": "Token para este horario retenido por otro proceso"
            }), 409

        horarios_bloqueados[id_slot] = {"timestamp": time.time()}
        token_acceso = f"TOKEN_{id_slot}_{int(time.time())}"
        return jsonify({
            "status": "granted",
            "token": token_acceso
        }), 200


@app.route('/liberar_token', methods=['POST'])
def liberar_token():
    data = request.json
    fecha = data.get('fecha')
    hora = data.get('hora')
    id_slot = f"{fecha}_{hora}"

    with lock:
        if id_slot in horarios_bloqueados:
            del horarios_bloqueados[id_slot]
        return jsonify({"status": "released"}), 200


if __name__ == '__main__':
    print(f"[Token Server] TTL: {TOKEN_TTL_SECONDS}s | Auth: {'ENABLED' if SHARED_SECRET != 'dev-secret-change-in-production' else 'DEV MODE'}")
    app.run(port=5001, debug=True)