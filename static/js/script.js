const socket = io();
const recordingStates = JSON.parse(localStorage.getItem('recordingStates')) || {};

// Atualiza a UI quando a página carrega
document.addEventListener('DOMContentLoaded', () => {
    Object.keys(recordingStates).forEach(env => {
        updateUI(env, recordingStates[env]);
    });
});

// Funções principais
function startRecording(env) {
    if (confirm(`Iniciar gravação em ${env}?`)) {
        socket.emit('start_recording', { environment: env });
    }
}

function stopRecording(env) {
    if (confirm(`Parar gravação em ${env}?`)) {
        socket.emit('stop_recording', { environment: env });
    }
}

// Atualiza a interface
function updateUI(env, isRecording) {
    const card = document.getElementById(`card-${env}`);
    const startBtn = document.querySelector(`#card-${env} .btn-start`);
    const stopBtn = document.querySelector(`#card-${env} .btn-stop`);
    const statusEl = document.getElementById(`status-${env}`);
    const timerEl = document.getElementById(`timer-${env}`);
    const fileInfoEl = document.getElementById(`file-info-${env}`);

    if (isRecording) {
        // Modo gravação
        card.classList.add('recording');
        startBtn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> Gravando';
        startBtn.style.backgroundColor = 'var(--danger-color)';
        stopBtn.classList.add('active');
        statusEl.innerHTML = 'Gravando <span class="recording-status"></span>';
    } else {
        // Modo parado
        card.classList.remove('recording');
        startBtn.innerHTML = '<i class="fas fa-circle-play"></i> Iniciar';
        startBtn.style.backgroundColor = 'var(--success-color)';
        stopBtn.classList.remove('active');
        statusEl.textContent = 'Pronto para gravar';
        timerEl.textContent = '00:00';
    }

    // Atualiza o estado local
    recordingStates[env] = isRecording;
    localStorage.setItem('recordingStates', JSON.stringify(recordingStates));
}

// Listeners do Socket.IO
socket.on('recording_started', data => {
    updateUI(data.environment, true);
    showAlert(`Gravação iniciada em ${data.environment}`);
});

socket.on('recording_stopped', data => {
    updateUI(data.environment, false);
    document.getElementById(`file-info-${data.environment}`).textContent = 
        `Arquivo salvo: ${data.filename}`;
    showAlert(`Gravação em ${data.environment} finalizada`);
});

socket.on('recording_error', data => {
    updateUI(data.environment, false);
    showAlert(`ERRO em ${data.environment}: ${data.message}`, 'error');
});

socket.on('timer_update', data => {
    document.getElementById(`timer-${data.environment}`).textContent = 
        `${data.minutes}:${data.seconds}`;
});

// Função auxiliar para alertas
function showAlert(message, type = 'success') {
    const alert = document.createElement('div');
    alert.className = `alert-${type}`;
    alert.textContent = message;
    document.body.appendChild(alert);
    
    setTimeout(() => {
        alert.remove();
    }, 3000);
}