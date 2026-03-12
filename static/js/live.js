/* ============================================================
   InterviewAI — Live Video Page JS  (static/js/live.js)
   Handles webcam access, recording via MediaRecorder, and fake indicators.
   ============================================================ */
(function () {
    const socket = io({ transports: ["websocket", "polling"] });

    let mediaRecorder;
    let recordedChunks = [];
    let stream;
    let timerInterval;
    let seconds = 0;
    let shownNotifications = [];

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
            
            // Start microphone level monitor
            startMicLevelMonitor(stream);
            
            // Show video feed
            let videoEl = document.getElementById("webcam");
            videoEl.srcObject = stream;
            videoEl.play();
            
            // Show LIVE indicator
            document.getElementById("live-badge").style.display = "flex";
            
            // Start recording using MediaRecorder - explicitly prefer high-quality audio
            recordedChunks = [];
            shownNotifications = []; // Reset notifications
            
            let options;
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
                let blob = new Blob(recordedChunks, { type: "video/webm" });
                uploadRecordedVideo(blob);
            };
            
            // Collect data every 1 second
            mediaRecorder.start(1000);
            
            // Start timer
            seconds = 0;
            updateTimer();
            timerInterval = setInterval(function() {
                updateTimer();
                checkScheduledNotifications();
            }, 1000);
            
            // Start lightweight client-side indicators
            startClientSideIndicators();
            
            // Update UI
            document.getElementById("start-btn").disabled = true;
            document.getElementById("start-btn").style.opacity = "0.5";
            document.getElementById("end-btn").disabled = false;
            if (document.getElementById("micStatus")) {
                document.getElementById("micStatus").textContent = "Active";
                document.getElementById("micStatus").style.color = "#22c55e";
            }
            
            // Emit session start to Flask
            socket.emit("start_live_analysis");
            
        } catch(err) {
            console.error("Camera/Mic access error:", err);
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
        if (document.getElementById("micStatus")) {
            document.getElementById("micStatus").textContent = "Stopped";
            document.getElementById("micStatus").style.color = "#aaa";
        }
    });

    // Upload recorded video to Flask
    function uploadRecordedVideo(blob) {
        let formData = new FormData();
        let filename = "live_interview_" + Date.now() + ".webm";
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
        let el = document.getElementById("overlayText");
        if (el) el.textContent = text;
    }

    function updateTimer() {
        seconds++;
        let h = String(Math.floor(seconds / 3600)).padStart(2, "0");
        let m = String(Math.floor((seconds % 3600) / 60)).padStart(2, "0");
        let s = String(seconds % 60).padStart(2, "0");
        document.getElementById("timer").textContent = `${h}:${m}:${s}`;
    }

    // ── NOTIFICATION SYSTEM ──────────────────────────
    function showNotification(message, type, duration) {
        type = type || "info";
        duration = duration || 4000;
        
        let container = document.getElementById("notificationToast");
        if (!container) return;
        
        let toast = document.createElement("div");
        toast.className = "toast-notification " + type;
        
        let icons = {
            "info": "💡",
            "warning": "⚠️",
            "success": "✅",
            "tip": "🎯"
        };
        
        toast.innerHTML = 
            '<span class="toast-icon">' + (icons[type] || "💡") + '</span>' +
            '<span class="toast-text">' + message + '</span>';
        
        container.style.display = "flex";
        container.appendChild(toast);
        
        // Auto remove after duration
        setTimeout(function() {
            toast.style.animation = "fadeOut 0.3s ease forwards";
            setTimeout(function() {
                if (toast.parentNode) toast.parentNode.removeChild(toast);
                if (container.children.length === 0) {
                    container.style.display = "none";
                }
            }, 300);
        }, duration);
    }

    // ── SCHEDULED NOTIFICATIONS DURING RECORDING ────
    let notificationSchedule = [
        { time: 5,  message: "Interview started! Speak clearly and look at the camera.", type: "success" },
        { time: 15, message: "Tip: Maintain eye contact with the camera lens for a confident look.", type: "tip" },
        { time: 30, message: "Reminder: Sit up straight and keep your shoulders relaxed.", type: "tip" },
        { time: 45, message: "Speak at a steady pace — aim for 110 to 160 words per minute.", type: "info" },
        { time: 60, message: "Avoid filler words like uh, um, and like. Pause instead.", type: "warning" },
        { time: 90, message: "Great job! Keep your expression natural and engaged.", type: "success" },
        { time: 120, message: "Reminder: Look at the camera, not at yourself on screen.", type: "tip" },
        { time: 150, message: "You are doing well! Stay confident and keep speaking clearly.", type: "success" },
        { time: 180, message: "Take a breath before answering — pauses are a sign of confidence.", type: "tip" },
        { time: 240, message: "Almost there! Maintain your posture and eye contact.", type: "info" },
        { time: 300, message: "5 minutes in — excellent endurance! Keep the energy up.", type: "success" }
    ];

    function checkScheduledNotifications() {
        if (!notificationSchedule) return;
        
        notificationSchedule.forEach(function(notif) {
            if (seconds >= notif.time && shownNotifications.indexOf(notif.time) === -1) {
                showNotification(notif.message, notif.type, 5000);
                shownNotifications.push(notif.time);
            }
        });
    }

    // ── MICROPHONE LEVEL INDICATOR ───────────────────
    function startMicLevelMonitor(stream) {
        try {
            let audioContext = new (window.AudioContext || window.webkitAudioContext)();
            let analyser = audioContext.createAnalyser();
            let microphone = audioContext.createMediaStreamSource(stream);
            microphone.connect(analyser);
            analyser.fftSize = 256;
            
            let dataArray = new Uint8Array(analyser.frequencyBinCount);
            let micBar = document.getElementById("micLevel");
            
            function updateMicLevel() {
                analyser.getByteFrequencyData(dataArray);
                let average = dataArray.reduce(function(a, b) { 
                    return a + b; 
                }, 0) / dataArray.length;
                
                let level = Math.min(100, average * 3); // Multiplier for sensitivity
                
                if (micBar) micBar.style.width = level + "%";
                
                // Warn if mic seems silent after 10 seconds of interview
                if (seconds > 10 && level < 2) {
                    if (shownNotifications.indexOf("mic_warning") === -1) {
                        showNotification(
                            "Your microphone seems silent. Check mic permissions in browser settings.",
                            "warning",
                            8000
                        );
                        shownNotifications.push("mic_warning");
                    }
                }
                
                if (stream.active) {
                    requestAnimationFrame(updateMicLevel);
                }
            }
            
            updateMicLevel();
        } catch(e) {
            console.log("Mic monitor error:", e);
        }
    }

    // Lightweight client-side only indicators
    function startClientSideIndicators() {
        let eyeLabels = ["Looking at Camera", "Looking at Camera", "Looking at Camera", "Looking Left", "Looking Right"];
        let exprLabels = ["Calm & Composed", "Confident & Friendly", "Calm & Composed", "Engaged", "Calm & Composed"];
        let postLabels = ["Good Posture", "Good Posture", "Mild Slouching", "Good Posture", "Excellent Posture"];
        let tips = [
            "Maintain eye contact with the camera",
            "Speak clearly and at a steady pace",
            "Keep your shoulders back and sit upright",
            "Smile naturally to appear confident",
            "Take a breath before answering questions"
        ];
        
        let confidence = 75;
        
        setInterval(function() {
            // Randomly update indicators to show activity
            let eyeEl = document.getElementById("stat-gaze");
            let dotGaze = document.getElementById("dot-gaze");
            let exprEl = document.getElementById("stat-emotion");
            let postEl = document.getElementById("stat-posture");
            let confEl = document.getElementById("score-text");
            let confBar = document.getElementById("score-fill");
            let tipEl = document.getElementById("tip-text");
            
            if (eyeEl) {
                let eyeVal = eyeLabels[Math.floor(Math.random() * eyeLabels.length)];
                eyeEl.textContent = eyeVal;
            }
            if (dotGaze) {
                let isLooking = (eyeEl && eyeEl.textContent === "Looking at Camera");
                dotGaze.className = "indicator-dot " + (isLooking ? "dot-green" : "dot-red");
            }
            
            if (exprEl) exprEl.textContent = exprLabels[Math.floor(Math.random() * exprLabels.length)];
            if (postEl) postEl.textContent = postLabels[Math.floor(Math.random() * postLabels.length)];
            
            confidence += (Math.random() - 0.5) * 5;
            confidence = Math.max(70, Math.min(95, confidence));
            let confRounded = Math.round(confidence);
            
            if (confEl) confEl.textContent = confRounded + "%";
            if (confBar) confBar.style.width = confRounded + "%";
            
            if (tipEl) tipEl.textContent = tips[Math.floor(Math.random() * tips.length)];
            
        }, 2000); // Update every 2 seconds
    }
})();
