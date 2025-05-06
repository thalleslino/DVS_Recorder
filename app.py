import os
import time
import threading
import subprocess
from datetime import date
from flask import Flask, render_template
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sua_chave_secreta_aqui'
socketio = SocketIO(app, async_mode='threading')

UPLOAD_FOLDER = 'gravacoes'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

recording_envs = {
    'Plenário': {'process': None, 'device_name': 'DVS Receive  1-2 (Dante Virtual Soundcard)', 'start_time': None},
    'CCJ': {'process': None, 'device_name': 'DVS Receive  3-4 (Dante Virtual Soundcard)', 'start_time': None},
    'Auditório-02': {'process': None, 'device_name': 'DVS Receive  5-6 (Dante Virtual Soundcard)', 'start_time': None},
    'Auditório-01': {'process': None, 'device_name': 'DVS Receive  7-8 (Dante Virtual Soundcard)', 'start_time': None}
}

@app.route('/')
def index():
    return render_template('index.html', environments=list(recording_envs.keys()))

@socketio.on('start_recording')
def start_recording(data):
    env = data['environment']
    if env not in recording_envs:
        return

    if recording_envs[env]['process']:
        emit('recording_error', {'environment': env, 'message': 'Já está gravando'})
        return

    today = date.today().strftime("%Y%m%d")
    os.makedirs(os.path.join(UPLOAD_FOLDER, today), exist_ok=True)
    filename = f"{env}_{time.strftime('%H%M%S')}.mp3"
    filepath = os.path.join(UPLOAD_FOLDER, today, filename)

    try:
        command = [
            'ffmpeg',
            '-f', 'dshow',
            '-i', f'audio={recording_envs[env]["device_name"]}',
            '-ac', '2',
            '-ar', '44100',
            filepath
        ]
        process = subprocess.Popen(command)
        recording_envs[env] = {
            'process': process,
            'device_name': recording_envs[env]['device_name'],
            'start_time': time.time(),
            'filename': filename
        }
        emit('recording_started', {'environment': env})
    except Exception as e:
        emit('recording_error', {'environment': env, 'message': str(e)})

@socketio.on('stop_recording')
def stop_recording(data):
    env = data['environment']
    if env not in recording_envs:
        return

    process = recording_envs[env]['process']
    if process:
        try:
            process.terminate()
            process.wait(timeout=5)
            filename = recording_envs[env].get('filename', '')
            recording_envs[env]['process'] = None
            recording_envs[env]['start_time'] = None
            emit('recording_stopped', {
                'environment': env,
                'filename': filename
            })
        except Exception as e:
            emit('recording_error', {
                'environment': env,
                'message': f"Erro ao parar: {str(e)}"
            })

def timer_updater():
    while True:
        for env, data in recording_envs.items():
            if data['start_time']:
                elapsed = int(time.time() - data['start_time'])
                socketio.emit('timer_update', {
                    'environment': env,
                    'minutes': f'{elapsed // 60:02d}',
                    'seconds': f'{elapsed % 60:02d}'
                })
        time.sleep(1)

threading.Thread(target=timer_updater, daemon=True).start()

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0')