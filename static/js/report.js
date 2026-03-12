/**
 * static/js/report.js
 * ==================
 * Handles Chart.js initialization and UI interactions for the report page.
 */

function initCharts() {
    if (typeof chartData === 'undefined' || !chartData) {
        console.error("No chart data available at all.");
        return;
    }
    console.log("InterviewAI: Initializing charts with data:", chartData);
    
    // ── OVERALL SCORE DOUGHNUT ──────────────
    let doughnutEl = document.getElementById("doughnutChart");
    if (doughnutEl) {
        if (doughnutEl._chartInstance) doughnutEl._chartInstance.destroy();
        let score = parseInt(document.body.getAttribute("data-overall-score")) || 0;
        let perfColor = document.body.getAttribute("data-perf-color") || "blue";
        
        // Map perf-color name to actual hex
        let colorMap = { "green": "#10b981", "yellow": "#f59e0b", "red": "#ef4444", "blue": "#3b82f6" };
        let themeColor = colorMap[perfColor] || "#3b82f6";

        let doughnutChart = new Chart(doughnutEl, {
            type: "doughnut",
            data: {
                datasets: [{
                    data: [score, 100 - score],
                    backgroundColor: [themeColor, "rgba(255,255,255,0.05)"],
                    borderWidth: 0,
                    circumference: 360,
                    rotation: 0
                }]
            },
            options: {
                cutout: "85%",
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: { enabled: false }
                }
            }
        });
        doughnutEl._chartInstance = doughnutChart;
        console.log("Overall score doughnut created");
    }

    // Helper to safely get radar/bar values
    function safeGetValues(key) {
        if (chartData[key] && Array.isArray(chartData[key].data)) {
            console.log(`Extracting ${key} data:`, chartData[key].data);
            return chartData[key].data;
        }
        console.warn(`Chart data for ${key} is missing or invalid. Using zeros.`);
        return [0, 0, 0, 0, 0];
    }
    
    // ── RADAR CHART ──────────────────────────
    let radarEl = document.getElementById("radarChart");
    if (radarEl) {
        if (radarEl._chartInstance) radarEl._chartInstance.destroy();
        let radarValues = safeGetValues("radar_chart");
        let radarChart = new Chart(radarEl, {
            type: "radar",
            data: {
                labels: [
                    "Eye Contact",
                    "Expression",
                    "Posture",
                    "Speech Pace",
                    "Filler Words"
                ],
                datasets: [{
                    label: "Your Score",
                    data: chartData.radar_chart.data || [0, 0, 0, 0, 0],
                    backgroundColor: "rgba(99,102,241,0.25)",
                    borderColor: "#6366f1",
                    borderWidth: 2,
                    pointBackgroundColor: "#6366f1",
                    pointBorderColor: "#fff",
                    pointRadius: 5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    r: {
                        min: 0,
                        max: 100,
                        ticks: {
                            stepSize: 20,
                            color: "#888",
                            backdropColor: "transparent",
                            font: { size: 10 }
                        },
                        grid: { color: "rgba(255,255,255,0.08)" },
                        angleLines: { color: "rgba(255,255,255,0.08)" },
                        pointLabels: {
                            color: "#ccc",
                            font: { size: 11 }
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        labels: { color: "#ccc" }
                    }
                }
            }
        });
        radarEl._chartInstance = radarChart;
        console.log("Radar chart created");
    }

    // ── TIMELINE CHART ───────────────────────
    let timelineEl = document.getElementById("timelineChart");
    if (timelineEl) {
        if (timelineEl._chartInstance) timelineEl._chartInstance.destroy();
        
        let tc = chartData.line_chart || {};
        let timelineLabels = tc.labels || [];
        let datasets = tc.datasets || [];
        
        // Generate fallback data if empty
        if (timelineLabels.length === 0) {
            timelineLabels = ["0:00", "0:15", "0:30", "0:45", "1:00"];
        }
        
        let timelineChart = new Chart(timelineEl, {
            type: "line",
            data: {
                labels: timelineLabels,
                datasets: datasets.length > 0 ? datasets : [
                    {
                        label: "Eye Contact",
                        data: [70, 75, 80, 75, 70],
                        borderColor: "#6366f1",
                        backgroundColor: "transparent",
                        borderWidth: 2,
                        tension: 0.4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        min: 0,
                        max: 100,
                        ticks: { color: "#888", stepSize: 20 },
                        grid: { color: "rgba(255,255,255,0.08)" }
                    },
                    x: {
                        ticks: { color: "#888" },
                        grid: { display: false }
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        labels: { 
                            color: "#ccc",
                            boxWidth: 12,
                            font: { size: 11 }
                        }
                    }
                }
            }
        });
        timelineEl._chartInstance = timelineChart;
        console.log("Timeline chart created");
    }

    // ── EMOTION DONUT CHART ──────────────────
    let emotionEl = document.getElementById("emotionChart");
    if (emotionEl) {
        if (emotionEl._chartInstance) emotionEl._chartInstance.destroy();
        
        let emotionPie = chartData.emotion_pie_chart || {};
        let emotionLabels = emotionPie.labels || ["No Data"];
        let emotionValues = emotionPie.data || [100];
        let emotionColors = emotionPie.colors || ["#6366f1"];
        
        let emotionChart = new Chart(emotionEl, {
            type: "doughnut",
            data: {
                labels: emotionLabels,
                datasets: [{
                    data: emotionValues,
                    backgroundColor: emotionColors,
                    borderColor: "#1a1a2e",
                    borderWidth: 3,
                    hoverOffset: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: "65%",
                plugins: {
                    legend: {
                        display: true,
                        position: "bottom",
                        labels: {
                            color: "#ccc",
                            boxWidth: 12,
                            padding: 10,
                            font: { size: 11 }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(ctx) {
                                return ctx.label + ": " + ctx.parsed + "%";
                            }
                        }
                    }
                }
            }
        });
        emotionEl._chartInstance = emotionChart;
        console.log("Emotion donut chart created");
    }

    // ── BAR CHART ────────────────────────────
    let barEl = document.getElementById("barChart");
    if (barEl) {
        if (barEl._chartInstance) barEl._chartInstance.destroy();
        let barData = chartData.doughnut_chart ? chartData.doughnut_chart.data : [0,0,0,0,0];
        let barColors = chartData.doughnut_chart ? chartData.doughnut_chart.colors : ["#6366f1","#22c55e","#f59e0b","#ec4899","#ef4444"];
        
        let barChart = new Chart(barEl, {
            type: "bar",
            data: {
                labels: [
                    "Eye Contact",
                    "Expression",
                    "Posture",
                    "Speech Pace",
                    "Filler Words"
                ],
                datasets: [{
                    label: "Your Score",
                    data: barData,
                    backgroundColor: barColors,
                    borderRadius: 8,
                    borderSkipped: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        min: 0,
                        max: 100,
                        ticks: {
                            color: "#888",
                            stepSize: 20
                        },
                        grid: { color: "rgba(255,255,255,0.08)" }
                    },
                    x: {
                        ticks: { color: "#ccc" },
                        grid: { display: false }
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        labels: { color: "#ccc" }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(ctx) {
                                return ctx.parsed.y + "/100";
                            }
                        }
                    }
                }
            }
        });
        barEl._chartInstance = barChart;
        console.log("Bar chart created");
    }
}

// Toggle transcription function
function toggleTranscription() {
    let text = document.getElementById("transcriptText");
    let btn = document.getElementById("transcriptBtn");
    if (text.style.display === "none" || text.style.display === "") {
        text.style.display = "block";
        btn.textContent = "Hide Transcription";
    } else {
        text.style.display = "none";
        btn.textContent = "Show Transcription";
    }
}

// Initialize after page loads
document.addEventListener("DOMContentLoaded", function() {
    initCharts();

    // Mobile menu toggle
    let menuToggle = document.getElementById("menuToggle");
    let navActions = document.getElementById("navActions");
    if (menuToggle && navActions) {
        menuToggle.addEventListener("click", function() {
            navActions.classList.toggle("active");
            let icon = menuToggle.querySelector("i");
            if (navActions.classList.contains("active")) {
                icon.classList.replace("fa-bars", "fa-times");
            } else {
                icon.classList.replace("fa-times", "fa-bars");
            }
        });
    }
});
