// ---------------- LIVE METRICS ----------------
function fetchMetrics() {
    fetch('/metrics')
        .then(response => response.json())
        .then(data => {
            document.getElementById('emotion').innerText = data.emotion;
            document.getElementById('confidence').innerText = (data.confidence * 100).toFixed(1) + '%';
            document.getElementById('blinkCount').innerText = data.blink_count;
        })
        .catch(err => console.error('Error fetching metrics:', err));
}

// Fetch metrics every 300ms
setInterval(fetchMetrics, 300);

// ---------------- CAMERA TOGGLE ----------------
document.getElementById('cameraToggleBtn').addEventListener('click', () => {
    fetch('/toggle_camera', {method: 'POST'})
        .then(response => response.json())
        .then(data => {
            document.getElementById('cameraToggleBtn').innerText = data.camera_enabled ? 'Turn Camera OFF' : 'Turn Camera ON';
        });
});

// ---------------- END INTERVIEW ----------------
document.getElementById('endInterviewBtn').addEventListener('click', () => {
    fetch('/end_interview', {method: 'POST'})
        .then(response => response.json())
        .then(data => {
            alert(data.message);
            fetch('/summary')
                .then(response => response.json())
                .then(summary => {
                    document.getElementById('summarySection').style.display = 'block';
                    document.getElementById('summaryDuration').innerText = summary.duration;
                    document.getElementById('summaryEmotion').innerText = summary.dominant_emotion;
                    document.getElementById('summaryBlinks').innerText = summary.total_blinks;
                });
        });
});
