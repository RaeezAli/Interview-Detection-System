/* ============================================================
   InterviewAI — Loading Page JS  (static/js/loading.js)
   Handles Socket.IO progress, step animation, and session check.
   ============================================================ */
(function () {
    const progressFill  = document.getElementById("progress-fill");
    const percentText   = document.getElementById("percent-text");
    const loadingView   = document.getElementById("loading-view");
    const successView   = document.getElementById("success-view");
    const stepsList     = document.getElementById("steps-list");
    const stepLabel     = document.getElementById("live-step-label");
    const errorBox      = document.getElementById("error-box");
    const stepIds       = ["step-1","step-2","step-3","step-4","step-5","step-6","step-7","step-8"];
    let cssStep         = 0;
    let socketConnected = false;

    /* ── Socket.IO ─────────────────────────────────────────── */
    const socket = io({ transports: ["websocket", "polling"] });

    socket.on("connect", () => { 
        socketConnected = true; 
        console.log("Loading page connected to socket");
        
        fetch("/check_session")
            .then(r => r.json())
            .then(data => {
                if (!data.active) {
                    setTimeout(() => { window.location.href = "/"; }, 2000);
                    return;
                }
                if (data.report_ready) {
                    setTimeout(() => { window.location.href = "/report"; }, 1000);
                }
                // Otherwise just wait for analysis_complete socket event
            });
    });

    socket.on("analysis_progress", (data) => {
        const pct = Math.min(Math.round(data.progress), 100);
        progressFill.style.width = pct + "%";
        percentText.textContent  = pct;
        if (stepLabel) stepLabel.textContent = data.current_step || "";
        activateCSSStep(Math.min(Math.floor(pct / 12.5), stepIds.length - 1));
    });

    socket.on("analysis_complete", (data) => {
        progressFill.style.width = "100%";
        percentText.textContent  = "100";
        markAllComplete();
        setTimeout(() => showSuccess(data.redirect || "/report"), 500);
    });

    socket.on("analysis_error", (data) => {
        console.error("Analysis error:", data);
        const errorDiv = document.getElementById("error-message");
        if (errorDiv) {
            errorDiv.style.display = "block";
            errorDiv.textContent = "Analysis failed: " + (data.message || data.error || "Unknown error");
        }
        const backBtn = document.getElementById("go-back-btn");
        if (backBtn) backBtn.style.display = "block";
    });

    /* ── Step helpers ──────────────────────────────────────── */
    function activateCSSStep(index) {
        if (index <= cssStep) return;
        for (let i = cssStep; i < index; i++) {
            const el = document.getElementById(stepIds[i]);
            if (el) { el.classList.remove("active"); el.classList.add("completed"); }
        }
        const current = document.getElementById(stepIds[index]);
        if (current) current.classList.add("active");
        cssStep = index;
    }

    function markAllComplete() {
        stepIds.forEach(id => {
            const el = document.getElementById(id);
            if (el) { el.classList.remove("active"); el.classList.add("completed"); }
        });
    }

    function showSuccess(redirectUrl) {
        loadingView.style.display = "none";
        stepsList.style.display   = "none";
        successView.style.display = "block";
        const chk = document.querySelector(".success-checkmark");
        if (chk) chk.style.display = "block";
        setTimeout(() => window.location.href = redirectUrl, 1500);
    }

    /* ── Polling fallback ──────────────────────────────────── */
    function pollForReport() {
        fetch("/get_report_data")
            .then(r => r.json())
            .then(d => { if (d.ready) showSuccess(d.redirect); else if (!socketConnected) setTimeout(pollForReport, 3000); })
            .catch(() => setTimeout(pollForReport, 5000));
    }

    /* ── Session check on load ─────────────────────────────── */
    window.addEventListener("load", () => {
        fetch("/check_session")
            .then(r => r.json())
            .then(d => { if (!d.active) window.location.href = "/"; });

        setTimeout(() => { if (!socketConnected) activateCSSStep(0); }, 1000);
        setTimeout(() => { if (!socketConnected) pollForReport(); }, 5000);
    });
})();
