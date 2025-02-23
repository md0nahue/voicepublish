// Check if the browser supports necessary APIs
if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
    console.log('getUserMedia supported.');

    // Constraints for audio recording
    const TIMESLICE = 1000; // 1000 milliseconds = 1 second
    const constraints = { audio: true };
    let chunks = []; // Array to store audio chunks
    let mediaRecorder;
    let audioCtx;
    let analyser;
    let canvas;
    let canvasCtx;
    let waveformData;

    function getSupportedMimeType() {
        const mimeTypes = [
            'audio/webm;codecs=opus',
            'audio/webm',
            'audio/ogg;codecs=opus',
            'audio/ogg',
            'audio/mp4',
            'audio/mpeg',
            'audio/wav'
        ];

        for (let mimeType of mimeTypes) {
            if (MediaRecorder.isTypeSupported(mimeType)) {
                console.log(`Selected MIME type: ${mimeType}`);
                return mimeType;
            }
        }

        console.warn('No supported MIME type found. Using default "audio/webm".');
        return 'audio/webm';
    }

    // Function to initialize audio context and canvas for waveform
    function initAudio() {
        audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        analyser = audioCtx.createAnalyser();
        analyser.fftSize = 2048; // Increase fftSize for higher resolution

        canvas = document.createElement('canvas');
        canvasCtx = canvas.getContext('2d');
        document.getElementById('audioWaveform').appendChild(canvas);
        
        //Adjust canvas dimensions if needed
        canvas.width = 600;
        canvas.height = 200;

        waveformData = new Uint8Array(analyser.frequencyBinCount);
    }

    // Function to draw the waveform
    function drawWaveform() {
        requestAnimationFrame(drawWaveform);

        analyser.getByteTimeDomainData(waveformData);

        canvasCtx.fillStyle = 'rgb(200, 200, 200)';
        canvasCtx.fillRect(0, 0, canvas.width, canvas.height);
        canvasCtx.lineWidth = 2;
        canvasCtx.strokeStyle = 'rgb(0, 0, 0)';
        canvasCtx.beginPath();

        const sliceWidth = canvas.width * 1.0 / waveformData.length;
        let x = 0;
        for (let i = 0; i < waveformData.length; i++) {
            const v = waveformData[i] / 128.0;
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

    // Request microphone permissions and start recording
    navigator.mediaDevices.getUserMedia(constraints)
        .then(function(stream) {
            initAudio(); // Initialize audio context and waveform after getting user media

            selectedMimeType = getSupportedMimeType();
            mediaRecorder = new MediaRecorder(stream, { mimeType: selectedMimeType });

            // Connect the source to be analysed
            const source = audioCtx.createMediaStreamSource(stream);
            source.connect(analyser);

            mediaRecorder.ondataavailable = function(e) {
                chunks.push(e.data);
                uploadChunk(e.data, selectedMimeType); // Upload each chunk as it becomes available
            };

            mediaRecorder.onstop = function(e) {
                console.log('Recorder stopped.');
                // You might want to do something here after all chunks have been uploaded,
                // like notifying the user or cleaning up resources.
            };

            // Button event handlers
            const startRecordButton = document.getElementById('startRecord');
            const stopRecordButton = document.getElementById('stopRecord');

            startRecordButton.onclick = function() {
                mediaRecorder.start(TIMESLICE);
                console.log('Recorder started', mediaRecorder.state);
                startRecordButton.disabled = true;
                stopRecordButton.disabled = false;
                drawWaveform(); // Start drawing the waveform
            };

            stopRecordButton.onclick = function() {
                mediaRecorder.stop();
                console.log('Recorder stopped', mediaRecorder.state);
                startRecordButton.disabled = false;
                stopRecordButton.disabled = true;
            };
        })
        .catch(function(err) {
            console.log('The following error occurred: ' + err);
        });
} else {
    console.log('getUserMedia not supported on your browser!');
    alert('Audio recording is not supported in this browser. Please use a different browser.');
}

// Function to get presigned URL from your server
async function getPresignedUrl(mimeType) {
    // Replace with your server endpoint
    const response = await fetch(`http://localhost:4567/get_presigned_url?mime_type=${encodeURIComponent(mimeType)}`);
        if (!response.ok) {
        throw new Error('Failed to get presigned URL');
    }
    const data = await response.json();
    return data.url; // Assuming your server returns { url: '...' }
}

// Function to upload audio chunk to S3
async function uploadChunk(chunk, mimeType) {
    try {
        const url = await getPresignedUrl(mimeType);
        const response = await fetch(url, {
            method: 'PUT',
            body: chunk,
            headers: {
                'Content-Type': mimeType // Adjust if you use a different audio format
            }
        });

        if (response.ok) {
            console.log('Chunk uploaded successfully.');
        } else {
            console.error('Chunk upload failed:', response.status);
        }
    } catch (error) {
        console.error('Error uploading chunk:', error);
    }
}