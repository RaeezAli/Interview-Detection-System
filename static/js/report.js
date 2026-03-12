/* ============================================================
   InterviewAI — Report Page JS  (static/js/report.js)
   Reads data from body data-attributes, builds all Chart.js charts.
   ============================================================ */
(function () {
    const body      = document.body;
    const chartData = JSON.parse(body.dataset.chartData  || "{}");
    const perfColor = body.dataset.perfColor || "green";
    const overallScore = parseFloat(body.dataset.overallScore || "0");

    const colorMap  = { green: "#10b981", yellow: "#f59e0b", red: "#ef4444" };
    const mainColor = colorMap[perfColor] || "#6366f1";

    const AXIS_STYLE = { ticks: { color: "#a1a1aa" }, grid: { color: "rgba(255,255,255,.05)" } };

    /* ── Doughnut — overall score ──────────────────────────── */
    const dCtx = document.getElementById("doughnutChart");
    if (dCtx) {
        new Chart(dCtx, {
            type: "doughnut",
            data: {
                datasets: [{
                    data: [overallScore, 100 - overallScore],
                    backgroundColor: [mainColor, "rgba(255,255,255,0.06)"],
                    borderWidth: 0,
                    borderRadius: 6
                }]
            },
            options: {
                cutout: "78%",
                plugins: { legend: { display: false }, tooltip: { enabled: false } },
                responsive: true,
                maintainAspectRatio: false
            }
        });
    }

    /* ── Radar ─────────────────────────────────────────────── */
    const rCtx = document.getElementById("radarChart");
    if (rCtx && chartData.radar_chart) {
        new Chart(rCtx, {
            type: "radar",
            data: {
                labels: chartData.radar_chart.labels,
                datasets: [{
                    data: chartData.radar_chart.data,
                    backgroundColor: "rgba(99,102,241,0.15)",
                    borderColor: "rgba(99,102,241,1)",
                    pointBackgroundColor: "rgba(99,102,241,1)",
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    r: {
                        min: 0, max: 100,
                        ticks: { stepSize: 20, color: "#a1a1aa", backdropColor: "transparent" },
                        grid: { color: "rgba(255,255,255,.08)" },
                        pointLabels: { color: "#a1a1aa", font: { size: 11 } }
                    }
                }
            }
        });
    }

    /* ── Line — timeline ───────────────────────────────────── */
    const lCtx = document.getElementById("lineChart");
    if (lCtx && chartData.line_chart) {
        new Chart(lCtx, {
            type: "line",
            data: {
                labels: chartData.line_chart.labels,
                datasets: (chartData.line_chart.datasets || []).map(d => ({
                    ...d, tension: 0.4, fill: false, pointRadius: 3, borderWidth: 2
                }))
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { labels: { color: "#a1a1aa", font: { size: 11 } } } },
                scales: { x: AXIS_STYLE, y: { ...AXIS_STYLE, min: 0, max: 100 } }
            }
        });
    }

    /* ── Emotion Pie ───────────────────────────────────────── */
    const eCtx = document.getElementById("emotionChart");
    if (eCtx && chartData.emotion_pie_chart) {
        new Chart(eCtx, {
            type: "pie",
            data: {
                labels: chartData.emotion_pie_chart.labels,
                datasets: [{
                    data: chartData.emotion_pie_chart.data,
                    backgroundColor: chartData.emotion_pie_chart.colors,
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: "right", labels: { color: "#a1a1aa", font: { size: 11 } } } }
            }
        });
    }

    /* ── Bar — score breakdown ─────────────────────────────── */
    const bCtx = document.getElementById("barChart");
    if (bCtx && chartData.doughnut_chart) {
        new Chart(bCtx, {
            type: "bar",
            data: {
                labels: chartData.doughnut_chart.labels,
                datasets: [{
                    data: chartData.doughnut_chart.data,
                    backgroundColor: chartData.doughnut_chart.colors,
                    borderRadius: 6,
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: "y",
                plugins: { legend: { display: false } },
                scales: {
                    x: { ...AXIS_STYLE, min: 0, max: 100 },
                    y: { ticks: { color: "#a1a1aa" }, grid: { display: false } }
                }
            }
        });
    }

    /* ── Transcription toggle ──────────────────────────────── */
    window.toggleTranscription = function () {
        const text = document.getElementById("transcriptText");
        const btn = document.getElementById("transcriptBtn");
        if (!text || !btn) return;
        if (text.style.display === "none" || text.style.display === "") {
            text.style.display = "block";
            btn.textContent = "Hide Transcription";
        } else {
            text.style.display = "none";
            btn.textContent = "Show Transcription";
        }
    };
})();
