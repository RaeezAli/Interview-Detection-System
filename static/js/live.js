/* ============================================================
   InterviewAI — Live Video Page JS  (static/js/live.js)
   Handles webcam access, recording via MediaRecorder, and fake indicators.
   ============================================================ */
(function () {
    const socket = io({ transports: ["websocket", "polling"] });

    var mediaRecorder;
    var recordedChunks = [];
    var stream;
    var timerInterval;
    var seconds = 0;

    // Start Interview Button
    document.getElementById("start-btn").addEventListener("click", async function() {
        try {
            // Request webcam and microphone with high-quality audio settings
            stream = await navigator.mediaDevices.getUserMedia({
                video: { width: 640, height: 480 },
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    sampleRate: 44100,
                    channelCount: 1
                }
            });
            
            // Show video feed
            var videoEl = document.getElementById("webcam");
            videoEl.srcObject = stream;
            videoEl.play();
            
            // Show LIVE indicator
            document.getElementById("live-badge").style.display = "flex";
            
            // Start recording using MediaRecorder - explicitly prefer high-quality audio
            recordedChunks = [];
            
            var options;
            if (MediaRecorder.isTypeSupported("video/webm;codecs=vp8,opus")) {
                options = { 
                    mimeType: "video/webm;codecs=vp8,opus",
                    audioBitsPerSecond: 128000
                };
            } else if (MediaRecorder.isTypeSupported("video/webm")) {
                options = { mimeType: "video/webm" };
            } else {
                options = {};
            }

            mediaRecorder = new MediaRecorder(stream, options);
            
            mediaRecorder.ondataavailable = function(e) {
                if (e.data.size > 0) {
                    recordedChunks.push(e.data);
                }
            };
            
            mediaRecorder.onstop = function() {
                // When recording stops, create blob and upload
                var blob = new Blob(recordedChunks, { type: "video/webm" });
                uploadRecordedVideo(blob);
            };
            
            // Collect data every 1 second
            mediaRecorder.start(1000);
            
            // Start timer
            seconds = 0;
            updateTimer();
            timerInterval = setInterval(updateTimer, 1000);
            
            // Start lightweight client-side indicators
            startClientSideIndicators();
            
            // Update UI
            document.getElementById("start-btn").disabled = true;
            document.getElementById("start-btn").style.opacity = "0.5";
            document.getElementById("end-btn").disabled = false;
            
            // Emit session start to Flask
            socket.emit("start_live_analysis");
            
        } catch(err) {
            alert("Camera access denied or not available: " + err.message);
        }
    });

    // End Interview Button
    document.getElementById("end-btn").addEventListener("click", function() {
        // Stop timer
        clearInterval(timerInterval);
        
        // Stop all webcam tracks
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
        }
        
        // Stop MediaRecorder - this triggers onstop which uploads video
        if (mediaRecorder && mediaRecorder.state !== "inactive") {
            mediaRecorder.stop();
        }
        
        // Show processing overlay on video
        document.getElementById("processingOverlay").style.display = "flex";
        
        // Update UI
        document.getElementById("end-btn").disabled = true;
        document.getElementById("start-btn").disabled = true;
    });

    // Upload recorded video to Flask
    function uploadRecordedVideo(blob) {
        var formData = new FormData();
        var filename = "live_interview_" + Date.now() + ".webm";
        formData.append("video", blob, filename); 
        
        // Show uploading status
        updateOverlayText("Uploading recording...");
        
        fetch("/upload", {
            method: "POST",
            body: formData,
            headers: { "Accept": "application/json" }
        })
        .then(response => {
            if (response.redirected) {
                updateOverlayText("Processing interview...");
                window.location.href = response.url;
            } else {
                return response.json().then(data => {
                    if (data.redirect) {
                        window.location.href = data.redirect;
                    } else if (data.error) {
                        updateOverlayText("Error: " + data.error);
                    }
                }).catch(err => {
                    console.log("Upload response parsing error:", err);
                    window.location.href = "/loading";
                });
            }
        })
        .catch(err => {
            console.error("Upload error:", err);
            updateOverlayText("Upload failed. Please try again.");
            setTimeout(() => { window.location.href = "/"; }, 3000);
        });
    }

    function updateOverlayText(text) {
        var el = document.getElementById("overlayText");
        if (el) el.textContent = text;
    }

    function updateTimer() {
        seconds++;
        var h = String(Math.floor(seconds / 3600)).padStart(2, "0");
        var m = String(Math.floor((seconds % 3600) / 60)).padStart(2, "0");
        var s = String(seconds % 60).padStart(2, "0");
        document.getElementById("timer").textContent = `${h}:${m}:${s}`;
    }

    // Lightweight client-side only indicators
    function startClientSideIndicators() {
        var eyeLabels = ["Looking at Camera", "Looking at Camera", "Looking at Camera", "Looking Left", "Looking Right"];
        var exprLabels = ["Calm & Composed", "Confident & Friendly", "Calm & Composed", "Engaged", "Calm & Composed"];
        var postLabels = ["Good Posture", "Good Posture", "Mild Slouching", "Good Posture", "Excellent Posture"];
        var tips = [
            "Maintain eye contact with the camera",
            "Speak clearly and at a steady pace",
            "Keep your shoulders back and sit upright",
            "Smile naturally to appear confident",
            "Take a breath before answering questions"
        ];
        
        var confidence = 75;
        
        setInterval(function() {
            // Randomly update indicators to show activity
            var eyeEl = document.getElementById("stat-gaze");
            var dotGaze = document.getElementById("dot-gaze");
            var exprEl = document.getElementById("stat-emotion");
            var postEl = document.getElementById("stat-posture");
            var confEl = document.getElementById("score-text");
            var confBar = document.getElementById("score-fill");
            var tipEl = document.getElementById("tip-text");
            
            if (eyeEl) {
                var eyeVal = eyeLabels[Math.floor(Math.random() * eyeLabels.length)];
                eyeEl.textContent = eyeVal;
            }
            if (dotGaze) {
                var isLooking = (eyeEl && eyeEl.textContent === "Looking at Camera");
                dotGaze.className = "indicator-dot " + (isLooking ? "dot-green" : "dot-red");
            }
            
            if (exprEl) exprEl.textContent = exprLabels[Math.floor(Math.random() * exprLabels.length)];
            if (postEl) postEl.textContent = postLabels[Math.floor(Math.random() * postLabels.length)];
            
            // Smoothly animate confidence score between 70-95
            confidence += (Math.random() - 0.5) * 5;
            confidence = Math.max(70, Math.min(95, confidence));
            var confRounded = Math.round(confidence);
            
            if (confEl) confEl.textContent = confRounded + "%";
            if (confBar) confBar.style.width = confRounded + "%";
            
            if (tipEl) tipEl.textContent = tips[Math.floor(Math.random() * tips.length)];
            
        }, 2000); // Update every 2 seconds
    }
})();
