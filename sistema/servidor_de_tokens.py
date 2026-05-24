from flask import Flask, request, jsonify
import threading
import time

app = Flask(__name__)

horarios_bloqueados = {}
lock = threading.Lock()

@app.route('/solicitar_token', methods=['POST'])
def solicitar_token():
    data = request.json
    fecha = data.get('fecha')
    hora = data.get('hora')

    if not fecha or not hora:
        return jsonify({'status': 'error'}, 'message: Faltan parámetros')
    
    id_slot = f"{fecha}_{hora}"

    with lock:
        if horarios_bloqueados.get(id_slot, False):
            return jsonify({
                'status': 'denied',
                'message': 'Token para este horario retenido por otro proceso'
            }), 409
        
        horarios_bloqueados[id_slot] = True
        token_acceso = f"TOKEN_{id_slot}_{int(time.time())}"
        return jsonify({
            'status': 'granted',
            'token': token_acceso
        }), 200

@app.route('/liberar_token', methods=['POST'])
def liberar_token():
    data = request.json
    fecha = data.get('fecha')
    hora = data.get('hora')
    id_slot = f"{fecha}_{hora}"

    with lock:
        if id_slot in horarios_bloqueados:
            horarios_bloqueados[id_slot] = False
        return jsonify({'status': 'released'}), 200
    
if __name__ == '__main__':
    app.run(port=5001, debug=True)