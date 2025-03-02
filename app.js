// WebSocket URL
const WEBSOCKET_URL = 'ws://localhost:8000/ws'; // Update with your server address

// UI Elements
const statusEl = document.getElementById('status');
const canvas = document.getElementById('waveform');
const canvasCtx = canvas.getContext('2d');

// Audio and WebSocket Variables
let mediaRecorder;
let audioStream;
let audioContext;
let analyser;
let dataArray;
let websocket;
let animationId;

// Function to initialize MediaRecorder
function initializeMediaRecorder(stream) {
let options = { mimeType: 'audio/webm;codecs=opus' };

if (!MediaRecorder.isTypeSupported(options.mimeType)) {
    if (MediaRecorder.isTypeSupported('audio/ogg;codecs=opus')) {
        options.mimeType = 'audio/ogg;codecs=opus';
    } else if (MediaRecorder.isTypeSupported('audio/webm')) {
        options.mimeType = 'audio/webm';
    } else if (MediaRecorder.isTypeSupported('audio/ogg')) {
        options.mimeType = 'audio/ogg';
    } else {
        options = {}; // Let the browser choose the default
    }
}

try {
    return new MediaRecorder(stream, options);
} catch (e) {
    console.error('Exception while creating MediaRecorder:', e);
    throw e;
}
}

// Initialize WebSocket connection
function connectWebSocket() {
websocket = new WebSocket(WEBSOCKET_URL);

websocket.onopen = () => {
    console.log("WebSocket connected.");
    statusEl.textContent = 'Connected to WebSocket!';
    statusEl.style.color = '#28a745';
};

websocket.onerror = (error) => {
    console.error("WebSocket error:", error);
    statusEl.textContent = 'WebSocket error!';
    statusEl.style.color = '#dc3545';
};

websocket.onclose = () => {
    console.warn("WebSocket closed. Attempting to reconnect...");
    statusEl.textContent = 'Reconnecting...';
    statusEl.style.color = '#ff0000';
    setTimeout(connectWebSocket, 3000);
};
}

// Initialize the application
async function init() {
try {
    // Connect to WebSocket
    connectWebSocket();

    // Request microphone access
    audioStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    statusEl.textContent = 'Recording now!';
    statusEl.style.color = '#28a745';

    // Setup Audio Context for waveform visualization
    setupAudioContext(audioStream);

    // Start Visualizing
    visualize();

    // Setup MediaRecorder
    setupMediaRecorder(audioStream);

} catch (err) {
    console.error('Error accessing microphone:', err);
    statusEl.textContent = 'Microphone access denied.';
    statusEl.style.color = '#dc3545';
}
}

// Setup Audio Context and Analyser for waveform
function setupAudioContext(stream) {
audioContext = new (window.AudioContext || window.webkitAudioContext)();
const source = audioContext.createMediaStreamSource(stream);
analyser = audioContext.createAnalyser();
analyser.fftSize = 2048;
dataArray = new Uint8Array(analyser.fftSize);
source.connect(analyser);

// Resize canvas
resizeCanvas();
window.addEventListener('resize', resizeCanvas);
}

function resizeCanvas() {
canvas.width = window.innerWidth * 0.8;
canvas.height = 200;
}

function visualize() {
function draw() {
    animationId = requestAnimationFrame(draw);

    analyser.getByteTimeDomainData(dataArray);

    canvasCtx.fillStyle = '#ffffff';
    canvasCtx.fillRect(0, 0, canvas.width, canvas.height);

    canvasCtx.lineWidth = 2;
    canvasCtx.strokeStyle = '#007bff';

    canvasCtx.beginPath();

    const sliceWidth = canvas.width / dataArray.length;
    let x = 0;

    for (let i = 0; i < dataArray.length; i++) {
        const v = dataArray[i] / 128.0;
        const y = v * canvas.height / 2;

        if (i === 0) {
            canvasCtx.moveTo(x, y);
        } else {
            canvasCtx.lineTo(x, y);
        }

        x += sliceWidth;
    }

    canvasCtx.lineTo(canvas.width, canvas.height / 2);
    canvasCtx.stroke();
}

draw();
}

function setupMediaRecorder(stream) {
try {
    mediaRecorder = initializeMediaRecorder(stream);
} catch (e) {
    statusEl.textContent = 'MediaRecorder not supported.';
    statusEl.style.color = '#dc3545';
    return;
}

mediaRecorder.ondataavailable = (event) => {
    if (event.data && event.data.size > 0 && websocket.readyState === WebSocket.OPEN) {
        websocket.send(event.data);
        console.log("Sent audio chunk to WebSocket");
    }
};

mediaRecorder.onstart = () => {
    console.log('MediaRecorder started');
};

mediaRecorder.onstop = () => {
    console.log('MediaRecorder stopped');
};

mediaRecorder.onerror = (event) => {
    console.error('MediaRecorder error:', event.error);
    statusEl.textContent = 'Recording error.';
    statusEl.style.color = '#dc3545';
};

// Start recording and send data every 250 ms
mediaRecorder.start(250);
console.log('Recording started in 250ms chunks.');
}

// Start the application
window.addEventListener('load', init);

// Handle cleanup on page unload
window.addEventListener('beforeunload', () => {
if (mediaRecorder && mediaRecorder.state !== 'inactive') {
    mediaRecorder.stop();
}
if (animationId) {
    cancelAnimationFrame(animationId);
}
if (audioContext) {
    audioContext.close();
}
if (websocket) {
    websocket.close();
}
});

// Get the disconnect button
const disconnectBtn = document.getElementById("disconnectBtn");

disconnectBtn.addEventListener("click", () => {
    console.log("Disconnect button clicked.");

    // Stop media recording to ensure the last chunk is captured
    if (mediaRecorder && mediaRecorder.state !== "inactive") {
        mediaRecorder.stop();
    }

   // Wait briefly before closing WebSocket to ensure final chunk is sent
    setTimeout(() => {
        if (websocket && websocket.readyState === WebSocket.OPEN) {
            websocket.send("FINAL_CHUNK"); // Signal backend to finalize upload
            websocket.close();
        }
    }, 300); // Small delay ensures final data is sent before closing

    // Stop visualization
    if (animationId) {
        cancelAnimationFrame(animationId);
    }

    // Close audio context
    if (audioContext) {
        audioContext.close();
    }

    // Update UI
    statusEl.textContent = "Disconnected.";
    statusEl.style.color = "#dc3545";
});
