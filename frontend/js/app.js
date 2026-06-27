(function () {
  const dropZone = document.getElementById("drop-zone");
  const fileInput = document.getElementById("file-input");
  const fileName = document.getElementById("file-name");
  const passwordInput = document.getElementById("password-input");
  const unlockBtn = document.getElementById("unlock-btn");
  const errorMsg = document.getElementById("error-msg");
  const downloadLink = document.getElementById("download-link");
  const resetBtn = document.getElementById("reset-btn");

  const stateIdle = document.getElementById("state-idle");
  const stateWorking = document.getElementById("state-working");
  const stateResult = document.getElementById("state-result");

  let selectedFile = null;
  let blobUrl = null;

  function show(state) {
    stateIdle.hidden = state !== "idle";
    stateWorking.hidden = state !== "working";
    stateResult.hidden = state !== "result";
  }

  function setFile(file) {
    if (!file || !file.name.toLowerCase().endsWith(".pdf")) {
      showError("Please choose a PDF file.");
      return;
    }
    selectedFile = file;
    fileName.textContent = file.name;
    fileName.hidden = false;
    clearError();
  }

  function showError(msg) {
    errorMsg.textContent = msg;
    errorMsg.hidden = false;
  }

  function clearError() {
    errorMsg.hidden = true;
    errorMsg.textContent = "";
  }

  dropZone.addEventListener("click", () => fileInput.click());
  dropZone.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") fileInput.click();
  });

  dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("drag-over");
  });
  dropZone.addEventListener("dragleave", () => dropZone.classList.remove("drag-over"));
  dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("drag-over");
    const file = e.dataTransfer.files[0];
    if (file) setFile(file);
  });

  fileInput.addEventListener("change", () => {
    if (fileInput.files[0]) setFile(fileInput.files[0]);
  });

  unlockBtn.addEventListener("click", async () => {
    clearError();
    if (!selectedFile) { showError("Please choose a PDF file."); return; }

    const formData = new FormData();
    formData.append("file", selectedFile);
    formData.append("password", passwordInput.value);

    show("working");

    try {
      const resp = await fetch("/api/unlock", { method: "POST", body: formData });

      if (resp.ok) {
        const blob = await resp.blob();
        if (blobUrl) URL.revokeObjectURL(blobUrl);
        blobUrl = URL.createObjectURL(blob);

        const cd = resp.headers.get("Content-Disposition") || "";
        const match = cd.match(/filename="?([^"]+)"?/);
        const outName = match ? match[1] : "unlocked.pdf";

        downloadLink.href = blobUrl;
        downloadLink.download = outName;
        show("result");
      } else {
        const data = await resp.json().catch(() => ({}));
        show("idle");
        showError(data.error || "Something went wrong. Please try again.");
      }
    } catch {
      show("idle");
      showError("Network error — please try again.");
    }
  });

  resetBtn.addEventListener("click", () => {
    selectedFile = null;
    fileInput.value = "";
    fileName.hidden = true;
    passwordInput.value = "";
    clearError();
    if (blobUrl) { URL.revokeObjectURL(blobUrl); blobUrl = null; }
    show("idle");
  });
})();
