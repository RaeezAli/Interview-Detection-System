/* ============================================================
   InterviewAI — Upload Page JS  (static/js/upload.js)
   Handles drag-and-drop file selection and preview.
   ============================================================ */
(function () {
    const dropZone   = document.getElementById("drop-zone");
    const fileInput  = document.getElementById("video-input");
    const fileInfo   = document.getElementById("file-info");
    const fileName   = document.getElementById("file-name");
    const fileSize   = document.getElementById("file-size");
    const analyzeBtn = document.getElementById("analyze-btn");

    if (!dropZone) return;

    dropZone.addEventListener("click", () => fileInput.click());

    dropZone.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropZone.classList.add("dragover");
    });
    dropZone.addEventListener("dragleave", () => dropZone.classList.remove("dragover"));
    dropZone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropZone.classList.remove("dragover");
        const file = e.dataTransfer.files[0];
        if (file) selectFile(file);
    });

    fileInput.addEventListener("change", () => {
        if (fileInput.files[0]) selectFile(fileInput.files[0]);
    });

    function selectFile(file) {
        const allowed = ["video/mp4","video/avi","video/quicktime","video/x-matroska","video/webm"];
        if (!allowed.includes(file.type) && !file.name.match(/\.(mp4|avi|mov|mkv|webm)$/i)) {
            alert("Invalid file type. Please upload MP4, AVI, MOV, MKV, or WEBM.");
            return;
        }
        const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
        if (sizeMB > 500) { alert("File too large. Max 500MB."); return; }

        if (fileName)  fileName.textContent  = file.name;
        if (fileSize)  fileSize.textContent  = sizeMB + " MB";
        if (fileInfo)  fileInfo.style.display = "block";
        if (analyzeBtn) analyzeBtn.style.display = "block";
        // Put into the hidden file input so the form submits correctly
        const dt = new DataTransfer();
        dt.items.add(file);
        fileInput.files = dt.files;
    }
})();
