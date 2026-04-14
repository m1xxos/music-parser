const progressSegments = document.getElementById("progressSegments");
const progressValue = document.getElementById("progressValue");
const statusText = document.getElementById("statusText");
const resultText = document.getElementById("resultText");
const resultLink = document.getElementById("resultLink");

const form = document.getElementById("downloadForm");
const metadataButton = document.getElementById("metadataButton");
const downloadButton = document.getElementById("downloadButton");
const formatSelect = document.getElementById("formatSelect");
const qualitySelect = document.getElementById("qualitySelect");
const themeToggle = document.getElementById("themeToggle");

const urlInput = document.getElementById("urlInput");
const titleInput = document.getElementById("titleInput");
const artistInput = document.getElementById("artistInput");
const albumInput = document.getElementById("albumInput");
const yearInput = document.getElementById("yearInput");
const trackInput = document.getElementById("trackInput");
const genreInput = document.getElementById("genreInput");
const commentInput = document.getElementById("commentInput");
const scanToggle = document.getElementById("scanToggle");

let activeJobId = null;
let pollTimer = null;
const MAX_COMMENT_LENGTH = 10000;

function trimToLimit(value, limit) {
  if (typeof value !== "string") {
    return "";
  }
  return value.length > limit ? value.slice(0, limit) : value;
}

function initializeSegments() {
  for (let i = 0; i < 24; i += 1) {
    const segment = document.createElement("span");
    progressSegments.appendChild(segment);
  }
}

function setStatus(message, isError = false) {
  statusText.textContent = message;
  statusText.classList.toggle("error", isError);
}

function setProgress(percent, failed = false) {
  const value = Math.max(0, Math.min(100, Number(percent) || 0));
  progressValue.textContent = `${value}%`;

  const segments = progressSegments.querySelectorAll("span");
  const filledCount = Math.round((value / 100) * segments.length);

  segments.forEach((segment, index) => {
    segment.classList.toggle("filled", index < filledCount && !failed);
    segment.classList.toggle("failed", index < filledCount && failed);
  });
}

function setResultWaiting() {
  resultText.textContent = "[WAITING]";
  resultLink.hidden = true;
  resultLink.href = "#";
}

function setResultError(message) {
  resultText.textContent = `[ERROR] ${message}`;
  resultLink.hidden = true;
  resultLink.href = "#";
}

function setResultSuccess(job) {
  const filePath = job?.result?.file_path || "unknown";
  const scanMark = job?.result?.navidrome_scan_triggered ? " / SCAN TRIGGERED" : "";
  resultText.textContent = `[READY] ${filePath}${scanMark}`;

  if (job?.result?.download_url) {
    resultLink.hidden = false;
    resultLink.href = job.result.download_url;
  } else {
    resultLink.hidden = true;
  }
}

function setBusy(isBusy) {
  metadataButton.disabled = isBusy;
  downloadButton.disabled = isBusy;
}

async function apiFetch(path, options = {}) {
  const response = await fetch(path, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    let detail = `HTTP ${response.status}`;
    try {
      const payload = await response.json();
      if (payload?.detail) {
        detail = payload.detail;
      }
    } catch (_error) {
      // Keep fallback detail.
    }
    throw new Error(detail);
  }

  return response.json();
}

function applyMetadata(metadata) {
  titleInput.value = metadata?.title || "";
  artistInput.value = metadata?.artist || "";
  albumInput.value = metadata?.album || "";
  yearInput.value = metadata?.year || "";
  trackInput.value = metadata?.track || "";
  genreInput.value = metadata?.genre || "";
  commentInput.value = trimToLimit(metadata?.comment || metadata?.description || "", MAX_COMMENT_LENGTH);
}

async function fetchMetadata() {
  const url = urlInput.value.trim();
  if (!url) {
    setStatus("[ERROR: URL REQUIRED]", true);
    setResultError("URL is required");
    return;
  }

  setBusy(true);
  setStatus("[FETCHING METADATA]");

  try {
    const metadata = await apiFetch("/api/metadata", {
      method: "POST",
      body: JSON.stringify({ url }),
    });

    applyMetadata(metadata);
    setStatus(`[METADATA OK] ${metadata.source?.toUpperCase() || "UNKNOWN"}`);
    setResultWaiting();
  } catch (error) {
    setStatus("[FAILED TO FETCH METADATA]", true);
    setResultError(error.message);
  } finally {
    setBusy(false);
  }
}

function buildRequestPayload() {
  const payload = {
    url: urlInput.value.trim(),
    output_format: formatSelect.value,
    quality: qualitySelect.value,
    auto_scan_navidrome: Boolean(scanToggle.checked),
    metadata: {
      title: titleInput.value.trim() || null,
      artist: artistInput.value.trim() || null,
      album: albumInput.value.trim() || null,
      year: yearInput.value ? Number(yearInput.value) : null,
      track: trackInput.value ? Number(trackInput.value) : null,
      genre: genreInput.value.trim() || null,
      comment: trimToLimit(commentInput.value.trim(), MAX_COMMENT_LENGTH) || null,
    },
  };

  return payload;
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer);
    pollTimer = null;
  }
}

async function pollJob() {
  if (!activeJobId) {
    return;
  }

  try {
    const job = await apiFetch(`/api/jobs/${activeJobId}`);
    setStatus(job.message, job.state === "failed");
    setProgress(job.progress, job.state === "failed");

    if (job.state === "completed") {
      setResultSuccess(job);
      stopPolling();
      setBusy(false);
      activeJobId = null;
      return;
    }

    if (job.state === "failed") {
      setResultError(job.error || "job failed");
      stopPolling();
      setBusy(false);
      activeJobId = null;
    }
  } catch (error) {
    setStatus("[POLL ERROR]", true);
    setResultError(error.message);
    stopPolling();
    setBusy(false);
    activeJobId = null;
  }
}

async function startDownload(event) {
  event.preventDefault();

  const url = urlInput.value.trim();
  if (!url) {
    setStatus("[ERROR: URL REQUIRED]", true);
    setResultError("URL is required");
    return;
  }

  setBusy(true);
  setResultWaiting();
  setProgress(0);
  setStatus("[QUEUING]");

  try {
    const payload = buildRequestPayload();
    const created = await apiFetch("/api/jobs", {
      method: "POST",
      body: JSON.stringify(payload),
    });

    activeJobId = created.job_id;
    setStatus("[QUEUED]");
    setProgress(3);

    stopPolling();
    pollTimer = setInterval(pollJob, 1500);
    pollJob();
  } catch (error) {
    setStatus("[QUEUE FAILED]", true);
    setResultError(error.message);
    setBusy(false);
  }
}

function updateQualityAvailability() {
  const isFlac = formatSelect.value === "flac";
  qualitySelect.disabled = isFlac;
}

function toggleTheme() {
  const body = document.body;
  const current = body.getAttribute("data-theme");
  const nextTheme = current === "dark" ? "light" : "dark";
  body.setAttribute("data-theme", nextTheme);
  themeToggle.textContent = nextTheme === "dark" ? "[LIGHT MODE]" : "[DARK MODE]";
}

initializeSegments();
setProgress(0);
setResultWaiting();
updateQualityAvailability();

metadataButton.addEventListener("click", fetchMetadata);
form.addEventListener("submit", startDownload);
formatSelect.addEventListener("change", updateQualityAvailability);
themeToggle.addEventListener("click", toggleTheme);
