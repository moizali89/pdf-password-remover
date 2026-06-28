(function () {
  const dropZone = document.getElementById("drop-zone");
  const fileInput = document.getElementById("file-input");
  const fileName = document.getElementById("file-name");
  const passwordInput = document.getElementById("password-input");
  const unlockBtn = document.getElementById("unlock-btn");
  const errorMsg = document.getElementById("error-msg");
  const downloadLink = document.getElementById("download-link");
  const resetBtn = document.getElementById("reset-btn");
  const modalOverlay = document.getElementById("modal-overlay");
  const modalClose = document.getElementById("modal-close");
  const loaderOverlay = document.getElementById("loader-overlay");

  const stateIdle = document.getElementById("state-idle");
  const stateResult = document.getElementById("state-result");

  // Keep the loader popup on screen for at least this long, even if the
  // conversion finishes sooner, so the user always sees it.
  // Default is overridden by the server's config.yaml (ui.min_loader_seconds).
  let MIN_LOADER_MS = 2000;

  fetch("/api/config")
    .then((r) => (r.ok ? r.json() : null))
    .then((cfg) => {
      if (cfg && typeof cfg.min_loader_seconds === "number") {
        MIN_LOADER_MS = cfg.min_loader_seconds * 1000;
      }
    })
    .catch(() => { /* keep the default if config can't be fetched */ });

  let selectedFile = null;
  let blobUrl = null;

  function show(state) {
    stateIdle.hidden = state !== "idle";
    stateResult.hidden = state !== "result";
  }

  function openLoader() { loaderOverlay.hidden = false; }
  function closeLoader() { loaderOverlay.hidden = true; }
  function sleep(ms) { return new Promise((resolve) => setTimeout(resolve, ms)); }

  async function setFile(file) {
    if (!file || !file.name.toLowerCase().endsWith(".pdf")) {
      showError("Please choose a PDF file.");
      return;
    }
    selectedFile = file;
    fileName.textContent = file.name;
    fileName.hidden = false;
    clearError();

    try {
      if (!(await isPdfEncrypted(file))) openModal();
    } catch {
      /* detection is best-effort; the unlock flow still works if it fails */
    }
  }

  function showError(msg) {
    errorMsg.textContent = msg;
    errorMsg.hidden = false;
  }

  function clearError() {
    errorMsg.hidden = true;
    errorMsg.textContent = "";
  }

  function openModal() { modalOverlay.hidden = false; }
  function closeModal() { modalOverlay.hidden = true; }

  // Encrypted PDFs always carry an /Encrypt entry in the trailer.
  // Scan the raw bytes for that token — fully local, no server call.
  async function isPdfEncrypted(file) {
    const bytes = new Uint8Array(await file.arrayBuffer());
    const needle = [0x2f, 0x45, 0x6e, 0x63, 0x72, 0x79, 0x70, 0x74]; // "/Encrypt"
    const last = bytes.length - needle.length;
    for (let i = 0; i <= last; i++) {
      let match = true;
      for (let j = 0; j < needle.length; j++) {
        if (bytes[i + j] !== needle[j]) { match = false; break; }
      }
      if (match) return true;
    }
    return false;
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

  // Dismissing the "no password" popup clears the unusable file and resets the form.
  modalClose.addEventListener("click", resetForm);
  modalOverlay.addEventListener("click", (e) => { if (e.target === modalOverlay) resetForm(); });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape" && !modalOverlay.hidden) resetForm(); });

  // Ensure the loader popup has been visible for at least MIN_LOADER_MS.
  async function holdLoader(startedAt) {
    const elapsed = Date.now() - startedAt;
    if (elapsed < MIN_LOADER_MS) await sleep(MIN_LOADER_MS - elapsed);
  }

  unlockBtn.addEventListener("click", async () => {
    clearError();
    if (!selectedFile) { showError("Please choose a PDF file."); return; }

    const formData = new FormData();
    formData.append("file", selectedFile);
    formData.append("password", passwordInput.value);

    openLoader();
    const startedAt = Date.now();

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

        await holdLoader(startedAt);
        closeLoader();
        show("result");
      } else {
        const data = await resp.json().catch(() => ({}));
        closeLoader();
        show("idle");
        showError(data.error || "Something went wrong. Please try again.");
      }
    } catch {
      closeLoader();
      show("idle");
      showError("Network error — please try again.");
    }
  });

  function resetForm() {
    selectedFile = null;
    fileInput.value = "";
    fileName.hidden = true;
    passwordInput.value = "";
    clearError();
    closeModal();
    if (blobUrl) { URL.revokeObjectURL(blobUrl); blobUrl = null; }
    show("idle");
  }

  resetBtn.addEventListener("click", resetForm);
})();
