/* Music Parser – waveform scrubber */

// State
let duration = 0;
let waveformPeaks = [];
let startHandlePos = 0;
let endHandlePos = 0;
let isDragging = null;
let startTime = 0;
let endTime = 0;
let isWaveformInit = false;
let resizeTimeout = null;
let currentVideoId = null;

// Audio playback state
let audioElement = null;
let isPlaying = false;
let previewLoaded = false;

// UI elements
let canvas, ctx;
let playBtn, playIcon, pauseIcon;
let scrubPreview, scrubThumbnail, scrubTime;
let currentVideoId = null;
let scrubThumbnailUrl = null;

function initWaveform() {
  if (isWaveformInit) return;

  canvas = document.getElementById('waveformCanvas');
  if (!canvas) return;

  ctx = canvas.getContext('2d');
  
  // Get play button elements
  playBtn = document.getElementById('playBtn');
  playIcon = document.getElementById('playIcon');
  pauseIcon = document.getElementById('pauseIcon');
  
  // Get scrub preview elements
  scrubPreview = document.getElementById('scrubPreview');
  scrubThumbnail = document.getElementById('scrubThumbnail');
  scrubTime = document.getElementById('scrubTime');

  // Set canvas resolution
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  canvas.width = rect.width * dpr;
  canvas.height = rect.height * dpr;
  ctx.scale(dpr, dpr);

  // Events
  canvas.addEventListener('mousedown', onCanvasMouseDown);
  canvas.addEventListener('mousemove', onCanvasMouseMove);
  canvas.addEventListener('mouseup', onCanvasMouseUp);
  canvas.addEventListener('mouseleave', onCanvasMouseUp);
  canvas.addEventListener('touchstart', onCanvasTouchStart, { passive: false });
  canvas.addEventListener('touchmove', onCanvasTouchMove, { passive: false });
  canvas.addEventListener('touchend', onCanvasMouseUp);

  const startInput = document.getElementById('startTime');
  const endInput = document.getElementById('endTime');
  if (startInput) startInput.addEventListener('input', onManualTimeChange);
  if (endInput) endInput.addEventListener('input', onManualTimeChange);

  isWaveformInit = true;
  drawWaveform();
}

function toggleOptions() {
  const panel = document.getElementById('optionsPanel');
  const btn = document.getElementById('optionsToggleBtn');
  
  if (!panel) return;
  
  panel.classList.toggle('open');
  
  if (panel.classList.contains('open')) {
    btn.innerHTML = `
      <svg fill="currentColor" viewBox="0 0 24 24" style="width:18px;height:18px;">
        <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
      </svg>
      Hide Options
    `;
    // Initialize waveform after panel is visible
    setTimeout(() => {
      initWaveform();
      // Fetch waveform if URL exists
      const urlInput = document.getElementById('url');
      if (urlInput && urlInput.value.trim()) {
        fetchWaveform(urlInput.value.trim());
      }
    }, 100);
  } else {
    btn.innerHTML = `
      <svg fill="currentColor" viewBox="0 0 24 24" style="width:18px;height:18px;">
        <path d="M19.14 12.94c.04-.31.06-.63.06-.94 0-.31-.02-.63-.06-.94l2.03-1.58c.18-.14.23-.41.12-.61l-1.92-3.32c-.12-.22-.37-.29-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54c-.04-.24-.24-.41-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.04.31-.06.63-.06.94s.02.63.06.94l-2.03 1.58c-.18.14-.23.41-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z"/>
      </svg>
      Trim & Options
    `;
  }
}

async function fetchWaveform(url) {
  const videoId = extractVideoId(url);
  if (!videoId) return;

  try {
    const response = await fetch(`/api/waveform/${videoId}?url=${encodeURIComponent(url)}`);
    if (!response.ok) return;

    const data = await response.json();
    duration = data.duration || 0;
    waveformPeaks = data.peaks || [];
    currentVideoId = videoId;

    // Auto-populate metadata from video info
    if (data.title) {
      const titleInput = document.getElementById('metaTitle');
      if (titleInput) titleInput.value = data.title;
    }
    if (data.artist) {
      const artistInput = document.getElementById('metaArtist');
      if (artistInput) artistInput.value = data.artist;
    }

    // Initialize handles
    if (canvas) {
      const rect = canvas.getBoundingClientRect();
      startHandlePos = 0;
      endHandlePos = rect.width;
      startTime = 0;
      endTime = duration;

      updateDisplays();
      drawWaveform();
      
      // Enable play button
      if (playBtn) {
        playBtn.disabled = false;
        playBtn.title = "Play 30s preview";
      }
    }
  } catch (e) {
    console.error('Waveform error:', e);
  }
}

function extractVideoId(url) {
  const patterns = [
    /(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)/,
    /youtube\.com\/shorts\/([^&\n?#]+)/,
  ];
  for (const pattern of patterns) {
    const match = url.match(pattern);
    if (match) return match[1];
  }
  return 'preview_' + btoa(url).slice(0, 12);
}

function drawWaveform() {
  if (!ctx || !canvas) return;

  const rect = canvas.getBoundingClientRect();
  const width = rect.width;
  const height = rect.height;

  ctx.clearRect(0, 0, width, height);

  // Background
  ctx.fillStyle = '#ffffff';
  ctx.fillRect(0, 0, width, height);

  // Draw waveform
  if (waveformPeaks.length > 0) {
    const gradient = ctx.createLinearGradient(0, 0, 0, height);
    gradient.addColorStop(0, '#4285f4');
    gradient.addColorStop(1, '#9c27b0');
    ctx.fillStyle = gradient;
    
    const barWidth = width / waveformPeaks.length;
    const centerY = height / 2;

    for (let i = 0; i < waveformPeaks.length; i++) {
      const peak = waveformPeaks[i];
      const barHeight = peak * (height * 0.8);
      const x = i * barWidth;
      const y = centerY - barHeight / 2;
      
      // Rounded bars
      ctx.beginPath();
      ctx.roundRect(x, y, barWidth - 2, barHeight, 2);
      ctx.fill();
    }
  } else {
    // Placeholder waveform
    ctx.fillStyle = '#e0e0e0';
    const barWidth = 6;
    const centerY = height / 2;
    for (let x = 0; x < width; x += barWidth + 4) {
      const barHeight = Math.random() * height * 0.5 + 15;
      ctx.beginPath();
      ctx.roundRect(x, centerY - barHeight / 2, barWidth, barHeight, 2);
      ctx.fill();
    }
  }

  // Draw selection overlay
  if (endHandlePos > startHandlePos) {
    // Left overlay
    ctx.fillStyle = 'rgba(0, 0, 0, 0.15)';
    ctx.fillRect(0, 0, startHandlePos, height);

    // Right overlay
    ctx.fillRect(endHandlePos, 0, width - endHandlePos, height);

    // Selection highlight
    ctx.fillStyle = 'rgba(66, 133, 244, 0.1)';
    ctx.fillRect(startHandlePos, 0, endHandlePos - startHandlePos, height);
  }

  // Draw handles
  drawHandle(startHandlePos, true);
  drawHandle(endHandlePos, false);
}

function drawHandle(x, isStart) {
  if (!canvas) return;
  const height = canvas.getBoundingClientRect().height;
  const centerY = height / 2;

  // Handle shadow
  ctx.fillStyle = 'rgba(0, 0, 0, 0.2)';
  ctx.beginPath();
  ctx.arc(x + 1, centerY, 10, 0, Math.PI * 2);
  ctx.fill();

  // Handle circle
  ctx.fillStyle = '#fff';
  ctx.strokeStyle = '#4285f4';
  ctx.lineWidth = 3;
  ctx.beginPath();
  ctx.arc(x, centerY, 10, 0, Math.PI * 2);
  ctx.fill();
  ctx.stroke();

  // Handle icon
  ctx.fillStyle = '#4285f4';
  ctx.font = 'bold 10px Arial';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(isStart ? '◀' : '▶', x, centerY);
}

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
  e.preventDefault();
  const x = getCanvasX(e);
  const handle = getHandleAt(x);

  if (handle) {
    isDragging = handle;
    showScrubPreview(x);
  } else {
    // Click to set start or end
    const midPoint = (startHandlePos + endHandlePos) / 2;
    if (x < midPoint) {
      startHandlePos = x;
    } else {
      endHandlePos = x;
    }
    updateTimeFromPositions();
    updateDisplays();
    drawWaveform();
    showScrubPreview(x);
  }
}

function onCanvasMouseMove(e) {
  if (!isDragging) return;
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
  updateScrubPreview(x);
}

function onCanvasMouseUp() {
  isDragging = null;
  hideScrubPreview();
}

function onCanvasTouchStart(e) {
  e.preventDefault();
  onCanvasMouseDown(e);
}

function onCanvasTouchMove(e) {
  e.preventDefault();
  onCanvasMouseMove(e);
}

function updateTimeFromPositions() {
  if (!canvas || duration <= 0) return;
  const rect = canvas.getBoundingClientRect();
  const startRatio = startHandlePos / rect.width;
  const endRatio = endHandlePos / rect.width;

  startTime = startRatio * duration;
  endTime = endRatio * duration;

  const startInput = document.getElementById('startTime');
  const endInput = document.getElementById('endTime');
  if (startInput) startInput.value = formatTime(startTime);
  if (endInput) endInput.value = formatTime(endTime);
}

function updateDisplays() {
  const startEl = document.getElementById('startTimeDisplay');
  const endEl = document.getElementById('endTimeDisplay');
  if (startEl) startEl.textContent = formatTime(startTime);
  if (endEl) endEl.textContent = formatTime(endTime);
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

  const parts = value.split(':').map(Number);
  if (parts.length === 2 && parts.every(n => !isNaN(n))) {
    return parts[0] * 60 + parts[1];
  }
  if (parts.length === 3 && parts.every(n => !isNaN(n))) {
    return parts[0] * 3600 + parts[1] * 60 + parts[2];
  }

  const seconds = parseFloat(value);
  return isNaN(seconds) ? 0 : seconds;
}

function onManualTimeChange() {
  if (duration <= 0 || !canvas) return;
  
  const startInput = document.getElementById('startTime');
  const endInput = document.getElementById('endTime');
  
  const startInputValue = startInput ? startInput.value.trim() : '';
  const endInputValue = endInput ? endInput.value.trim() : '';

  if (startInputValue) startTime = parseTimeToSeconds(startInputValue);
  if (endInputValue) endTime = parseTimeToSeconds(endInputValue);

  const rect = canvas.getBoundingClientRect();
  startHandlePos = (startTime / duration) * rect.width;
  endHandlePos = (endTime / duration) * rect.width;
  
  updateDisplays();
  drawWaveform();
}

function setStatus(state, message) {
  const el = document.getElementById('status');
  if (!el) return;
  
  el.className = `show ${state}`;
  
  if (state === 'pending' || state === 'downloading') {
    el.innerHTML = `<span class="spinner"></span>${message}`;
  } else {
    el.textContent = message;
  }
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
      setStatus('error', 'Connection lost');
      return;
    }

    if (data.status === 'done') {
      setStatus('done', '✓ ' + data.message);
      document.getElementById('downloadBtn').disabled = false;
      return;
    }

    if (data.status === 'error') {
      setStatus('error', data.message);
      document.getElementById('downloadBtn').disabled = false;
      return;
    }

    setStatus(data.status, data.message);
  }

  setStatus('error', 'Timed out');
  document.getElementById('downloadBtn').disabled = false;
}

async function startDownload() {
  const url = document.getElementById('url').value.trim();
  if (!url) {
    setStatus('error', 'Please enter a URL');
    return;
  }

  // Fetch waveform (fast - metadata only)
  await fetchWaveform(url);

  const payload = {
    url,
    start_time: document.getElementById('startTime').value.trim() || null,
    end_time: document.getElementById('endTime').value.trim() || null,
    title: document.getElementById('metaTitle').value.trim() || null,
    artist: document.getElementById('metaArtist').value.trim() || null,
    album: document.getElementById('metaAlbum').value.trim() || null,
  };

  const btn = document.getElementById('downloadBtn');
  btn.disabled = true;
  setStatus('pending', 'Queuing...');

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
    setStatus('error', 'Failed: ' + e.message);
    btn.disabled = false;
    return;
  }

  setStatus('downloading', 'Downloading audio...');
  pollJob(jobId);
}

// Enter key to download
document.getElementById('url').addEventListener('keydown', (e) => {
  if (e.key === 'Enter') startDownload();
});

// Handle window resize with debounce
window.addEventListener('resize', () => {
  if (!isWaveformInit || !canvas) return;
  
  clearTimeout(resizeTimeout);
  resizeTimeout = setTimeout(() => {
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);
    drawWaveform();
  }, 250);
});

// Audio playback functions
async function togglePlay() {
  if (!currentVideoId || !playBtn) return;
  
  if (isPlaying) {
    stopPreview();
  } else {
    await loadAndPlayPreview();
  }
}

async function loadAndPlayPreview() {
  if (!currentVideoId || !playBtn) return;
  
  // Show loading state
  playBtn.disabled = true;
  playBtn.style.opacity = '0.7';
  
  try {
    // Create audio element if needed
    if (!audioElement) {
      audioElement = new Audio();
      audioElement.addEventListener('ended', () => stopPreview());
      audioElement.addEventListener('timeupdate', onAudioTimeUpdate);
    }
    
    // Load preview if not already loaded
    if (!previewLoaded) {
      const urlInput = document.getElementById('url');
      const url = urlInput ? urlInput.value.trim() : '';
      if (!url) throw new Error('No URL');
      
      const previewUrl = `/api/audio-preview/${currentVideoId}?url=${encodeURIComponent(url)}`;
      audioElement.src = previewUrl;
      await audioElement.load();
      previewLoaded = true;
    }
    
    // Play
    await audioElement.play();
    isPlaying = true;
    updatePlayButton();
  } catch (e) {
    console.error('Preview error:', e);
    playBtn.disabled = false;
    playBtn.style.opacity = '';
  }
}

function stopPreview() {
  if (audioElement) {
    audioElement.pause();
    audioElement.currentTime = 0;
  }
  isPlaying = false;
  previewLoaded = false;
  updatePlayButton();
}

function updatePlayButton() {
  if (!playBtn || !playIcon || !pauseIcon) return;
  
  if (isPlaying) {
    playIcon.style.display = 'none';
    pauseIcon.style.display = 'block';
    playBtn.title = 'Pause';
  } else {
    playIcon.style.display = 'block';
    pauseIcon.style.display = 'none';
    playBtn.title = 'Play 30s preview';
    playBtn.disabled = false;
    playBtn.style.opacity = '';
  }
}

function onAudioTimeUpdate() {
  if (!audioElement || !isPlaying) return;
  
  // Stop at end of preview
  if (audioElement.ended) {
    stopPreview();
  }
  
  // Redraw waveform with playhead
  drawWaveform();
}

// Scrub preview functions
function showScrubPreview(x) {
  if (!scrubPreview || !scrubThumbnail || !scrubTime) return;
  if (!currentVideoId || duration <= 0) return;
  
  const rect = canvas.getBoundingClientRect();
  const time = (x / rect.width) * duration;
  
  // Position preview at cursor
  scrubPreview.style.left = `${x}px`;
  scrubPreview.classList.add('show');
  
  // Update time display
  scrubTime.textContent = formatTime(time);
  
  // Get thumbnail URL from YouTube
  if (currentVideoId && !scrubThumbnailUrl) {
    scrubThumbnailUrl = `https://img.youtube.com/vi/${currentVideoId}/mqdefault.jpg`;
    scrubThumbnail.src = scrubThumbnailUrl;
  }
}

function updateScrubPreview(x) {
  if (!scrubPreview || !scrubTime) return;
  if (!currentVideoId || duration <= 0) return;
  
  const rect = canvas.getBoundingClientRect();
  const time = (x / rect.width) * duration;
  
  // Update position and time
  scrubPreview.style.left = `${x}px`;
  scrubTime.textContent = formatTime(time);
}

function hideScrubPreview() {
  if (scrubPreview) {
    scrubPreview.classList.remove('show');
  }
}
