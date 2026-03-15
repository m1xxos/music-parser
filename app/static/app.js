/* Music Parser – Frontend Logic with Waveform Scrubber */

// ── Waveform state ───────────────────────────────────────────────────────────
let audioBuffer = null;
let audioContext = null;
let audioElement = null;
let startTime = 0;
let endTime = 0;
let duration = 0;
let waveformPeaks = [];
let startHandlePos = 0;
let endHandlePos = 0;
let isDragging = null;
let isPlaying = false;
let playStartTime = 0;
let playStartOffset = 0;

// ── UI Elements ──────────────────────────────────────────────────────────────
let canvas, ctx, waveformContainer;
let startTimeDisplay, endTimeDisplay;
let playBtn, playBtnText, playIcon, pauseIcon;
let audioLoader;

function initWaveformUI() {
  canvas = document.getElementById('waveformCanvas');
  ctx = canvas.getContext('2d');
  waveformContainer = document.getElementById('waveformContainer');
  startTimeDisplay = document.getElementById('startTimeDisplay');
  endTimeDisplay = document.getElementById('endTimeDisplay');
  playBtn = document.getElementById('playBtn');
  playBtnText = document.getElementById('playBtnText');
  playIcon = document.getElementById('playIcon');
  pauseIcon = document.getElementById('pauseIcon');
  audioLoader = document.getElementById('audioLoader');

  // Set canvas resolution
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  canvas.width = rect.width * dpr;
  canvas.height = rect.height * dpr;
  ctx.scale(dpr, dpr);

  // Event listeners
  canvas.addEventListener('mousedown', onCanvasMouseDown);
  canvas.addEventListener('mousemove', onCanvasMouseMove);
  canvas.addEventListener('mouseup', onCanvasMouseUp);
  canvas.addEventListener('mouseleave', onCanvasMouseUp);

  // Touch support
  canvas.addEventListener('touchstart', onCanvasTouchStart, { passive: false });
  canvas.addEventListener('touchmove', onCanvasTouchMove, { passive: false });
  canvas.addEventListener('touchend', onCanvasMouseUp);

  document.getElementById('startTime').addEventListener('input', onManualTimeChange);
  document.getElementById('endTime').addEventListener('input', onManualTimeChange);

  // Initial draw
  drawWaveform();
}

// ── Advanced panel toggle ────────────────────────────────────────────────────
function toggleAdvanced() {
  const panel = document.getElementById('advancedPanel');
  panel.classList.toggle('open');
  if (panel.classList.contains('open')) {
    setTimeout(() => {
      initWaveformUI();
      // Trigger a resize event to ensure canvas is properly sized
      window.dispatchEvent(new Event('resize'));
    }, 100);
  }
}

// ── Waveform data fetching ───────────────────────────────────────────────────
async function fetchWaveformData(url) {
  try {
    audioLoader.classList.add('show');
    waveformContainer.classList.remove('has-audio');
    playBtn.disabled = true;

    // Extract video ID from various URL formats
    const videoId = extractVideoId(url);
    if (!videoId) {
      throw new Error('Could not extract video ID from URL');
    }

    // Fetch waveform with the full URL
    const response = await fetch(`/api/waveform/${videoId}?url=${encodeURIComponent(url)}`);
    if (!response.ok) {
      throw new Error('Failed to fetch waveform data');
    }

    const data = await response.json();
    audioBuffer = data;
    duration = data.duration || 0;
    waveformPeaks = data.peaks || [];

    // Initialize handles - start at beginning, end at full duration
    startHandlePos = 0;
    endHandlePos = canvas.getBoundingClientRect().width;
    startTime = 0;
    endTime = duration;

    updateDisplays();
    drawWaveform();

    waveformContainer.classList.add('has-audio');
    playBtn.disabled = false;
    audioLoader.classList.remove('show');
  } catch (error) {
    console.error('Waveform fetch error:', error);
    audioLoader.classList.remove('show');
    // Still allow manual time entry
  }
}

function extractVideoId(url) {
  // YouTube patterns
  const patterns = [
    /(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)/,
    /youtube\.com\/shorts\/([^&\n?#]+)/,
  ];
  for (const pattern of patterns) {
    const match = url.match(pattern);
    if (match) return match[1];
  }
  // For other sites, use a hash of the URL
  return 'preview_' + btoa(url).slice(0, 12);
}

// ── Waveform drawing ─────────────────────────────────────────────────────────
function drawWaveform() {
  if (!ctx) return;

  const rect = canvas.getBoundingClientRect();
  const width = rect.width;
  const height = rect.height;

  ctx.clearRect(0, 0, width, height);

  // Background gradient
  const bgGradient = ctx.createLinearGradient(0, 0, 0, height);
  bgGradient.addColorStop(0, '#1a1229');
  bgGradient.addColorStop(1, '#251a3a');
  ctx.fillStyle = bgGradient;
  ctx.fillRect(0, 0, width, height);

  // Draw waveform peaks
  if (waveformPeaks.length > 0) {
    const gradient = ctx.createLinearGradient(0, 0, 0, height);
    gradient.addColorStop(0, '#a855f7');
    gradient.addColorStop(0.5, '#c026d3');
    gradient.addColorStop(1, '#7c3aed');
    ctx.fillStyle = gradient;

    const barWidth = width / waveformPeaks.length;
    const centerY = height / 2;

    // Draw bars with rounded tops
    for (let i = 0; i < waveformPeaks.length; i++) {
      const peak = waveformPeaks[i];
      const barHeight = peak * (height * 0.7);
      const x = i * barWidth;
      const y = centerY - barHeight / 2;
      
      // Draw mirrored bars
      roundRect(ctx, x, y, barWidth - 1, barHeight, 2);
      ctx.fill();
    }
  } else {
    // Placeholder waveform
    ctx.fillStyle = '#3d2a4f';
    const barWidth = 4;
    const centerY = height / 2;
    for (let x = 0; x < width; x += barWidth + 2) {
      const barHeight = Math.random() * height * 0.4 + 15;
      roundRect(ctx, x, centerY - barHeight / 2, barWidth, barHeight, 2);
      ctx.fill();
    }
  }

  // Draw selection overlay
  if (endHandlePos > startHandlePos) {
    // Left overlay
    const leftGradient = ctx.createLinearGradient(0, 0, startHandlePos, 0);
    leftGradient.addColorStop(0, 'rgba(15, 10, 26, 0.8)');
    leftGradient.addColorStop(1, 'rgba(15, 10, 26, 0.4)');
    ctx.fillStyle = leftGradient;
    ctx.fillRect(0, 0, startHandlePos, height);

    // Right overlay
    const rightGradient = ctx.createLinearGradient(endHandlePos, 0, width, 0);
    rightGradient.addColorStop(0, 'rgba(15, 10, 26, 0.4)');
    rightGradient.addColorStop(1, 'rgba(15, 10, 26, 0.8)');
    ctx.fillStyle = rightGradient;
    ctx.fillRect(endHandlePos, 0, width - endHandlePos, height);

    // Selection highlight
    ctx.fillStyle = 'rgba(168, 85, 247, 0.15)';
    ctx.fillRect(startHandlePos, 0, endHandlePos - startHandlePos, height);
  }

  // Draw handles
  drawHandle(startHandlePos, true);
  drawHandle(endHandlePos, false);

  // Draw playhead if playing
  if (isPlaying && audioElement) {
    const currentTime = audioElement.currentTime;
    if (currentTime >= startTime && currentTime <= endTime) {
      const progress = (currentTime - startTime) / (endTime - startTime);
      const playheadX = startHandlePos + progress * (endHandlePos - startHandlePos);
      
      // Playhead line
      ctx.strokeStyle = '#f5f3ff';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(playheadX, 0);
      ctx.lineTo(playheadX, height);
      ctx.stroke();
      
      // Playhead dot
      ctx.fillStyle = '#f5f3ff';
      ctx.beginPath();
      ctx.arc(playheadX, 8, 4, 0, Math.PI * 2);
      ctx.fill();
    }
  }
}

function roundRect(ctx, x, y, width, height, radius) {
  ctx.beginPath();
  ctx.moveTo(x + radius, y);
  ctx.lineTo(x + width - radius, y);
  ctx.quadraticCurveTo(x + width, y, x + width, y + radius);
  ctx.lineTo(x + width, y + height - radius);
  ctx.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
  ctx.lineTo(x + radius, y + height);
  ctx.quadraticCurveTo(x, y + height, x, y + height - radius);
  ctx.lineTo(x, y + radius);
  ctx.quadraticCurveTo(x, y, x + radius, y);
  ctx.closePath();
}

function drawHandle(x, isStart) {
  const height = canvas.getBoundingClientRect().height;
  
  // Handle glow
  const glowGradient = ctx.createRadialGradient(x, height / 2, 0, x, height / 2, 20);
  glowGradient.addColorStop(0, 'rgba(168, 85, 247, 0.4)');
  glowGradient.addColorStop(1, 'rgba(168, 85, 247, 0)');
  ctx.fillStyle = glowGradient;
  ctx.fillRect(x - 20, 0, 40, height);
  
  // Handle bar
  const barGradient = ctx.createLinearGradient(x - 2, 0, x + 2, 0);
  barGradient.addColorStop(0, '#a855f7');
  barGradient.addColorStop(1, '#c026d3');
  ctx.fillStyle = barGradient;
  ctx.fillRect(x - 2, 0, 4, height);

  // Handle circle
  const circleGradient = ctx.createRadialGradient(x, height / 2, 0, x, height / 2, 10);
  circleGradient.addColorStop(0, '#a855f7');
  circleGradient.addColorStop(1, '#7c3aed');
  ctx.fillStyle = circleGradient;
  ctx.beginPath();
  ctx.arc(x, height / 2, 10, 0, Math.PI * 2);
  ctx.fill();
  
  // Circle border
  ctx.strokeStyle = '#f5f3ff';
  ctx.lineWidth = 2;
  ctx.stroke();

  // Handle icon
  ctx.fillStyle = '#f5f3ff';
  ctx.font = 'bold 10px Arial';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(isStart ? '◀' : '▶', x, height / 2);
}

// ── Mouse/Touch interaction ──────────────────────────────────────────────────
function getCanvasX(e) {
  const rect = canvas.getBoundingClientRect();
  const clientX = e.touches ? e.touches[0].clientX : e.clientX;
  return Math.max(0, Math.min(rect.width, clientX - rect.left));
}

function getHandleAt(x) {
  const threshold = 20;
  if (Math.abs(x - startHandlePos) < threshold) return 'start';
  if (Math.abs(x - endHandlePos) < threshold) return 'end';
  return null;
}

function onCanvasMouseDown(e) {
  if (!audioBuffer) return;
  e.preventDefault();

  const x = getCanvasX(e);
  const handle = getHandleAt(x);

  if (handle) {
    isDragging = handle;
  } else {
    // Click on waveform - set start or end based on position
    const midPoint = (startHandlePos + endHandlePos) / 2;
    if (x < midPoint) {
      startHandlePos = x;
    } else {
      endHandlePos = x;
    }
    updateTimeFromPositions();
    updateDisplays();
    drawWaveform();
  }
}

function onCanvasMouseMove(e) {
  if (!isDragging || !audioBuffer) return;
  e.preventDefault();

  const x = getCanvasX(e);
  const rect = canvas.getBoundingClientRect();

  if (isDragging === 'start') {
    startHandlePos = Math.max(0, Math.min(x, endHandlePos - 10));
  } else if (isDragging === 'end') {
    endHandlePos = Math.max(startHandlePos + 10, Math.min(x, rect.width));
  }

  updateTimeFromPositions();
  updateDisplays();
  drawWaveform();
}

function onCanvasMouseUp() {
  isDragging = null;
}

function onCanvasTouchStart(e) {
  e.preventDefault();
  onCanvasMouseDown(e);
}

function onCanvasTouchMove(e) {
  e.preventDefault();
  onCanvasMouseMove(e);
}

// ── Time conversion ──────────────────────────────────────────────────────────
function updateTimeFromPositions() {
  const rect = canvas.getBoundingClientRect();
  const startRatio = startHandlePos / rect.width;
  const endRatio = endHandlePos / rect.width;

  startTime = startRatio * duration;
  endTime = endRatio * duration;

  // Update hidden inputs
  document.getElementById('startTime').value = formatTime(startTime);
  document.getElementById('endTime').value = formatTime(endTime);
}

function updatePositionsFromTime() {
  if (!audioBuffer) return;

  const rect = canvas.getBoundingClientRect();
  startHandlePos = (startTime / duration) * rect.width;
  endHandlePos = (endTime / duration) * rect.width;

  document.getElementById('startTime').value = formatTime(startTime);
  document.getElementById('endTime').value = formatTime(endTime);

  updateDisplays();
  drawWaveform();
}

function onManualTimeChange() {
  const startInput = document.getElementById('startTime').value.trim();
  const endInput = document.getElementById('endTime').value.trim();

  if (startInput) startTime = parseTimeToSeconds(startInput);
  if (endInput) endTime = parseTimeToSeconds(endInput);

  if (audioBuffer) {
    updatePositionsFromTime();
  }
}

// ── Display helpers ──────────────────────────────────────────────────────────
function updateDisplays() {
  startTimeDisplay.textContent = formatTime(startTime);
  endTimeDisplay.textContent = formatTime(endTime);
}

function formatTime(seconds) {
  if (!seconds || seconds < 0) return '0:00';
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

function parseTimeToSeconds(value) {
  if (!value) return 0;
  value = value.trim();

  // HH:MM:SS or MM:SS
  const parts = value.split(':').map(Number);
  if (parts.length === 2 && parts.every(n => !isNaN(n))) {
    return parts[0] * 60 + parts[1];
  }
  if (parts.length === 3 && parts.every(n => !isNaN(n))) {
    return parts[0] * 3600 + parts[1] * 60 + parts[2];
  }

  // Pure seconds
  const seconds = parseFloat(value);
  return isNaN(seconds) ? 0 : seconds;
}

// ── Audio playback ───────────────────────────────────────────────────────────
async function togglePlay() {
  if (!audioBuffer) return;

  if (isPlaying) {
    stopPlayback();
  } else {
    await startPlayback();
  }
}

async function startPlayback() {
  // Create audio element if not exists
  if (!audioElement) {
    audioElement = new Audio();
    audioElement.addEventListener('ended', () => stopPlayback());
    audioElement.addEventListener('timeupdate', onAudioTimeUpdate);
  }

  // Load audio if not loaded
  if (!audioElement.src || audioElement.src === '') {
    const videoId = extractVideoId(document.getElementById('url').value.trim());
    const previewUrl = `/api/audio-preview/${videoId}`;
    audioElement.src = previewUrl;
  }

  try {
    await audioElement.load();

    // Calculate the offset within the selected range
    const rangeDuration = endTime - startTime;
    const offset = startTime;

    audioElement.currentTime = offset;
    playStartOffset = offset;

    await audioElement.play();

    isPlaying = true;
    playBtnText.textContent = 'Pause';
    playIcon.style.display = 'none';
    pauseIcon.style.display = 'inline';
    playBtn.classList.add('active');

    animatePlayhead();
  } catch (e) {
    console.error('Playback error:', e);
    stopPlayback();
  }
}

function stopPlayback() {
  if (audioElement) {
    audioElement.pause();
  }
  isPlaying = false;
  playBtnText.textContent = 'Play';
  playIcon.style.display = 'inline';
  pauseIcon.style.display = 'none';
  playBtn.classList.remove('active');
}

function onAudioTimeUpdate() {
  if (!audioElement || !isPlaying) return;

  const currentTime = audioElement.currentTime;

  // Check if we've reached the end time
  if (currentTime >= endTime) {
    stopPlayback();
    audioElement.currentTime = endTime;
  }

  drawWaveform();
}

function animatePlayhead() {
  if (!isPlaying) return;
  drawWaveform();
  if (isPlaying) {
    requestAnimationFrame(animatePlayhead);
  }
}

// ── Status display ───────────────────────────────────────────────────────────
function setStatus(state, message) {
  const el = document.getElementById('status');
  el.className = `show ${state}`;

  const spinner = (state === 'pending' || state === 'downloading')
    ? '<div class="spinner"></div>'
    : '';

  const icons = { done: '✓', error: '✕' };
  const icon = icons[state] ? `<span style="font-size:1.2em;font-weight:bold;">${icons[state]}</span>` : '';

  el.innerHTML = `${spinner}${icon}<span>${message}</span>`;
}

function hideStatus() {
  document.getElementById('status').className = '';
  document.getElementById('status').innerHTML = '';
}

async function pollJob(jobId) {
  const interval = 2000;
  const maxAttempts = 300;

  for (let i = 0; i < maxAttempts; i++) {
    await new Promise(r => setTimeout(r, interval));

    let data;
    try {
      const resp = await fetch(`/api/jobs/${jobId}`);
      data = await resp.json();
    } catch {
      setStatus('error', 'Lost connection to server.');
      return;
    }

    if (data.status === 'done') {
      setStatus('done', `✓ ${data.message}`);
      document.getElementById('downloadBtn').disabled = false;
      return;
    }

    if (data.status === 'error') {
      setStatus('error', `✕ ${data.message}`);
      document.getElementById('downloadBtn').disabled = false;
      return;
    }

    setStatus(data.status, data.message);
  }

  setStatus('error', 'Timed out waiting for job to finish.');
  document.getElementById('downloadBtn').disabled = false;
}

async function startDownload() {
  const url = document.getElementById('url').value.trim();
  if (!url) {
    setStatus('error', 'Please enter a URL.');
    return;
  }

  // Fetch waveform data when URL is entered
  await fetchWaveformData(url);

  const payload = {
    url,
    start_time: document.getElementById('startTime').value.trim() || null,
    end_time: document.getElementById('endTime').value.trim() || null,
    title: document.getElementById('metaTitle').value.trim() || null,
    artist: document.getElementById('metaArtist').value.trim() || null,
    album: document.getElementById('metaAlbum').value.trim() || null,
  };

  document.getElementById('downloadBtn').disabled = true;
  setStatus('pending', 'Queuing job…');

  let jobId;
  try {
    const resp = await fetch('/api/download', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ detail: resp.statusText }));
      throw new Error(err.detail || 'Server error');
    }

    const data = await resp.json();
    jobId = data.job_id;
  } catch (e) {
    setStatus('error', `Failed to start: ${e.message}`);
    document.getElementById('downloadBtn').disabled = false;
    return;
  }

  setStatus('downloading', 'Downloading audio…');
  pollJob(jobId);
}

// Allow pressing Enter in the URL field
document.getElementById('url').addEventListener('keydown', (e) => {
  if (e.key === 'Enter') startDownload();
});

// Initialize on load
document.addEventListener('DOMContentLoaded', () => {
  // Waveform UI will be initialized when advanced panel opens
});

// Handle window resize for responsive canvas
window.addEventListener('resize', () => {
  if (canvas && ctx) {
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);
    drawWaveform();
  }
});
