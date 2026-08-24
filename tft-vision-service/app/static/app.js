/**
 * TFT Icon Studio — Frontend Canvas & Cropping Engine
 */

class IconStudioApp {
  constructor() {
    this.currentImage = null;
    this.currentFilename = null;
    this.zoom = 1.0;
    this.pan = { x: 0, y: 0 };
    this.tool = 'draw'; // 'draw' | 'pan'
    this.boxes = []; // [{ id, name, x, y, width, height, previewUrl }]
    this.selectedBoxId = null;

    this.isDrawing = false;
    this.drawStart = { x: 0, y: 0 };
    this.activeBox = null;

    this.isPanning = false;
    this.panStart = { x: 0, y: 0 };

    this.initElements();
    this.initEventListeners();
    this.fetchScreenshots();
    this.fetchReferenceIcons();
  }

  initElements() {
    this.viewport = document.getElementById('viewport');
    this.canvasContainer = document.getElementById('canvas-container');
    this.canvas = document.getElementById('main-canvas');
    this.ctx = this.canvas.getContext('2d');
    this.boxOverlay = document.getElementById('box-overlay');
    this.emptyState = document.getElementById('empty-state');
    this.infobar = document.getElementById('infobar');

    // Toolbar
    this.toolDrawBtn = document.getElementById('tool-draw-btn');
    this.toolPanBtn = document.getElementById('tool-pan-btn');
    this.zoomOutBtn = document.getElementById('zoom-out-btn');
    this.zoomInBtn = document.getElementById('zoom-in-btn');
    this.zoomFitBtn = document.getElementById('zoom-fit-btn');
    this.zoomLevelDisplay = document.getElementById('zoom-level');
    this.saveBatchBtn = document.getElementById('save-batch-btn');
    this.saveCountBadge = document.getElementById('save-count-badge');
    this.quickSaveBtn = document.getElementById('quick-save-btn');
    this.btnBoxCount = document.getElementById('btn-box-count');

    // Sidebars & Lists
    this.screenshotList = document.getElementById('screenshot-list');
    this.iconsGallery = document.getElementById('icons-gallery');
    this.boxList = document.getElementById('box-list');
    this.boxCountDisplay = document.getElementById('box-count');
    this.libraryCount = document.getElementById('library-count');
    this.clearBoxesBtn = document.getElementById('clear-boxes-btn');
    this.dropzone = document.getElementById('dropzone');
    this.fileInput = document.getElementById('file-input');

    // Infobar
    this.currentFilenameDisplay = document.getElementById('current-filename');
    this.currentDimDisplay = document.getElementById('current-dim');
    this.cursorCoordsDisplay = document.getElementById('cursor-coords');
  }

  initEventListeners() {
    // Tool buttons
    this.toolDrawBtn.addEventListener('click', () => this.setTool('draw'));
    this.toolPanBtn.addEventListener('click', () => this.setTool('pan'));

    // Zoom
    this.zoomInBtn.addEventListener('click', () => this.setZoom(this.zoom * 1.25));
    this.zoomOutBtn.addEventListener('click', () => this.setZoom(this.zoom / 1.25));
    this.zoomFitBtn.addEventListener('click', () => this.fitToScreen());

    // Mouse wheel zoom & pan
    this.viewport.addEventListener('wheel', (e) => this.handleWheel(e), { passive: false });

    // Canvas Pointer events
    this.canvasContainer.addEventListener('mousedown', (e) => this.handleMouseDown(e));
    window.addEventListener('mousemove', (e) => this.handleMouseMove(e));
    window.addEventListener('mouseup', (e) => this.handleMouseUp(e));

    // Dropzone & File Upload
    this.dropzone.addEventListener('click', () => this.fileInput.click());
    this.fileInput.addEventListener('change', (e) => this.handleFileSelect(e));
    this.dropzone.addEventListener('dragover', (e) => { e.preventDefault(); this.dropzone.classList.add('dragover'); });
    this.dropzone.addEventListener('dragleave', () => this.dropzone.classList.remove('dragover'));
    this.dropzone.addEventListener('drop', (e) => this.handleFileDrop(e));

    // Tabs
    document.querySelectorAll('.tab-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
        btn.classList.add('active');
        document.getElementById(`pane-${btn.dataset.tab}`).classList.add('active');
      });
    });

    // Refresh buttons
    document.getElementById('refresh-screenshots-btn').addEventListener('click', () => this.fetchScreenshots());
    document.getElementById('refresh-icons-btn').addEventListener('click', () => this.fetchReferenceIcons());

    // Actions
    this.clearBoxesBtn.addEventListener('click', () => this.clearAllBoxes());
    this.saveBatchBtn.addEventListener('click', () => this.saveBatch());
    this.quickSaveBtn.addEventListener('click', () => this.saveBatch());

    // Keyboard shortcuts
    window.addEventListener('keydown', (e) => {
      if (['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) return;
      if (e.key === 'd' || e.key === 'D') this.setTool('draw');
      if (e.key === 'h' || e.key === 'H' || e.code === 'Space') this.setTool('pan');
      if (e.key === 'f' || e.key === 'F') this.fitToScreen();
      if (e.key === 'Escape') this.selectBox(null);
    });
  }

  // --- API Integrations ---

  async fetchScreenshots() {
    try {
      const res = await fetch('/api/screenshots');
      const data = await res.json();
      this.renderScreenshotList(data.screenshots || []);
      if (data.screenshots && data.screenshots.length > 0 && !this.currentImage) {
        this.loadImage(data.screenshots[0].url, data.screenshots[0].name);
      }
    } catch (err) {
      this.showToast('Failed to load screenshots', 'error');
    }
  }

  async fetchReferenceIcons() {
    try {
      const res = await fetch('/api/icons');
      const data = await res.json();
      this.renderIconsGallery(data.icons || []);
    } catch (err) {
      this.showToast('Failed to load icons library', 'error');
    }
  }

  async uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);

    try {
      this.showToast('Uploading screenshot...', 'info');
      const res = await fetch('/api/screenshots/upload', {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();
      if (data.status === 'success') {
        this.showToast(`Uploaded ${data.name}`, 'success');
        await this.fetchScreenshots();
        this.loadImage(data.url, data.name);
      }
    } catch (err) {
      this.showToast('Upload failed', 'error');
    }
  }

  async deleteIcon(filename) {
    if (!confirm(`Delete icon ${filename}?`)) return;
    try {
      await fetch(`/api/icons/${filename}`, { method: 'DELETE' });
      this.showToast(`Deleted ${filename}`, 'success');
      this.fetchReferenceIcons();
    } catch (err) {
      this.showToast('Failed to delete icon', 'error');
    }
  }

  async saveBatch() {
    if (this.boxes.length === 0 || !this.currentFilename) return;

    // Validate names
    const unamed = this.boxes.some(b => !b.name.trim());
    if (unamed) {
      this.showToast('Please provide a name for all crop boxes', 'error');
      return;
    }

    const payload = {
      screenshot_name: this.currentFilename,
      crops: this.boxes.map(b => ({
        name: b.name.trim().toLowerCase().replace(/\s+/g, '_'),
        x: Math.round(b.x),
        y: Math.round(b.y),
        width: Math.round(b.width),
        height: Math.round(b.height),
      })),
    };

    try {
      this.saveBatchBtn.disabled = true;
      this.quickSaveBtn.disabled = true;
      const res = await fetch('/api/icons/crop-batch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await res.json();

      if (data.status === 'success') {
        this.showToast(`Saved ${data.count} reference icons!`, 'success');
        this.fetchReferenceIcons();
        this.clearAllBoxes();
      } else {
        this.showToast(data.detail || 'Save failed', 'error');
      }
    } catch (err) {
      this.showToast('Error saving icons batch', 'error');
    } finally {
      this.updateActionButtons();
    }
  }

  // --- Rendering UI ---

  renderScreenshotList(screenshots) {
    if (screenshots.length === 0) {
      this.screenshotList.innerHTML = '<div class="loading-state">No screenshots found.</div>';
      return;
    }

    this.screenshotList.innerHTML = screenshots.map(s => `
      <div class="screenshot-item ${s.name === this.currentFilename ? 'active' : ''}" data-url="${s.url}" data-name="${s.name}">
        <img class="screenshot-thumb" src="${s.url}" alt="${s.name}" loading="lazy">
        <div class="screenshot-info">
          <div class="screenshot-name" title="${s.name}">${s.name}</div>
          <div class="screenshot-size">${(s.size / 1024 / 1024).toFixed(2)} MB</div>
        </div>
      </div>
    `).join('');

    this.screenshotList.querySelectorAll('.screenshot-item').forEach(item => {
      item.addEventListener('click', () => {
        this.screenshotList.querySelectorAll('.screenshot-item').forEach(i => i.classList.remove('active'));
        item.classList.add('active');
        this.loadImage(item.dataset.url, item.dataset.name);
      });
    });
  }

  renderIconsGallery(icons) {
    this.libraryCount.textContent = icons.length;
    if (icons.length === 0) {
      this.iconsGallery.innerHTML = '<div class="loading-state">No saved icons yet.</div>';
      return;
    }

    this.iconsGallery.innerHTML = icons.map(icon => `
      <div class="icon-card">
        <button class="icon-delete-btn" data-filename="${icon.filename}" title="Delete icon">&times;</button>
        <img class="icon-card-thumb" src="${icon.url}?t=${Date.now()}" alt="${icon.name}">
        <div class="icon-card-name" title="${icon.name}">${icon.name}</div>
        <div class="icon-card-dim font-mono">${icon.width}×${icon.height}</div>
      </div>
    `).join('');

    this.iconsGallery.querySelectorAll('.icon-delete-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        this.deleteIcon(btn.dataset.filename);
      });
    });
  }

  renderBoxList() {
    this.boxCountDisplay.textContent = this.boxes.length;
    this.btnBoxCount.textContent = this.boxes.length;
    this.saveCountBadge.textContent = this.boxes.length;
    this.updateActionButtons();

    if (this.boxes.length === 0) {
      this.boxList.innerHTML = `
        <div class="empty-box-placeholder">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M12 2v20M2 12h20"></path>
          </svg>
          <p>Click &amp; drag on the image to create champion bounding boxes.</p>
        </div>
      `;
      return;
    }

    this.boxList.innerHTML = this.boxes.map((box, idx) => `
      <div class="box-card ${box.id === this.selectedBoxId ? 'selected' : ''}" data-id="${box.id}">
        <img class="box-card-preview" src="${box.previewUrl}" alt="Crop Preview">
        <div class="box-card-body">
          <input type="text" class="box-name-input" placeholder="e.g. jinx, vi_shop" value="${box.name}" data-id="${box.id}">
          <div class="box-meta">
            <span class="font-mono">${Math.round(box.width)}×${Math.round(box.height)} px</span>
            <button class="box-del-btn" data-id="${box.id}" title="Remove box">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
            </button>
          </div>
        </div>
      </div>
    `).join('');

    // Events in box cards
    this.boxList.querySelectorAll('.box-card').forEach(card => {
      card.addEventListener('click', (e) => {
        if (e.target.tagName === 'INPUT' || e.target.closest('.box-del-btn')) return;
        this.selectBox(card.dataset.id);
      });
    });

    this.boxList.querySelectorAll('.box-name-input').forEach(input => {
      input.addEventListener('input', (e) => {
        const box = this.boxes.find(b => b.id === input.dataset.id);
        if (box) {
          box.name = e.target.value;
          this.updateOverlayBox(box);
        }
      });
    });

    this.boxList.querySelectorAll('.box-del-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        this.deleteBox(btn.dataset.id);
      });
    });
  }

  updateActionButtons() {
    const disabled = this.boxes.length === 0;
    this.saveBatchBtn.disabled = disabled;
    this.quickSaveBtn.disabled = disabled;
  }

  // --- Canvas & Image Management ---

  loadImage(url, filename) {
    const img = new Image();
    img.crossOrigin = 'anonymous';
    img.onload = () => {
      this.currentImage = img;
      this.currentFilename = filename;

      this.canvas.width = img.naturalWidth;
      this.canvas.height = img.naturalHeight;
      this.ctx.drawImage(img, 0, 0);

      this.emptyState.style.display = 'none';
      this.currentFilenameDisplay.textContent = filename;
      this.currentDimDisplay.textContent = `${img.naturalWidth} × ${img.naturalHeight}`;

      this.clearAllBoxes();
      this.fitToScreen();
    };
    img.src = url;
  }

  fitToScreen() {
    if (!this.currentImage) return;
    const vpRect = this.viewport.getBoundingClientRect();
    const padding = 60;
    const scaleX = (vpRect.width - padding) / this.currentImage.naturalWidth;
    const scaleY = (vpRect.height - padding) / this.currentImage.naturalHeight;
    const fitZoom = Math.min(scaleX, scaleY, 1.0);

    this.zoom = fitZoom;
    this.pan = {
      x: (vpRect.width - this.currentImage.naturalWidth * this.zoom) / 2,
      y: (vpRect.height - this.currentImage.naturalHeight * this.zoom) / 2,
    };
    this.updateTransform();
  }

  setZoom(newZoom) {
    if (!this.currentImage) return;
    const clamped = Math.max(0.1, Math.min(newZoom, 4.0));
    const vpRect = this.viewport.getBoundingClientRect();
    const cx = vpRect.width / 2;
    const cy = vpRect.height / 2;

    const imgX = (cx - this.pan.x) / this.zoom;
    const imgY = (cy - this.pan.y) / this.zoom;

    this.zoom = clamped;
    this.pan.x = cx - imgX * this.zoom;
    this.pan.y = cy - imgY * this.zoom;

    this.updateTransform();
  }

  setTool(tool) {
    this.tool = tool;
    this.toolDrawBtn.classList.toggle('active', tool === 'draw');
    this.toolPanBtn.classList.toggle('active', tool === 'pan');
    this.viewport.style.cursor = tool === 'pan' ? 'grab' : 'crosshair';
  }

  updateTransform() {
    this.canvasContainer.style.transform = `translate(${this.pan.x}px, ${this.pan.y}px) scale(${this.zoom})`;
    this.zoomLevelDisplay.textContent = `${Math.round(this.zoom * 100)}%`;
  }

  handleWheel(e) {
    if (!this.currentImage) return;
    e.preventDefault();

    const zoomFactor = e.deltaY < 0 ? 1.15 : 0.85;
    const newZoom = Math.max(0.1, Math.min(this.zoom * zoomFactor, 4.0));

    const vpRect = this.viewport.getBoundingClientRect();
    const mouseX = e.clientX - vpRect.left;
    const mouseY = e.clientY - vpRect.top;

    const imgX = (mouseX - this.pan.x) / this.zoom;
    const imgY = (mouseY - this.pan.y) / this.zoom;

    this.zoom = newZoom;
    this.pan.x = mouseX - imgX * this.zoom;
    this.pan.y = mouseY - imgY * this.zoom;

    this.updateTransform();
  }

  // --- Drawing & Pointer Operations ---

  getImageCoords(e) {
    const rect = this.canvasContainer.getBoundingClientRect();
    const x = (e.clientX - rect.left) / this.zoom;
    const y = (e.clientY - rect.top) / this.zoom;
    return {
      x: Math.max(0, Math.min(x, this.currentImage ? this.currentImage.naturalWidth : 0)),
      y: Math.max(0, Math.min(y, this.currentImage ? this.currentImage.naturalHeight : 0)),
    };
  }

  handleMouseDown(e) {
    if (!this.currentImage) return;

    if (this.tool === 'pan' || e.button === 1 || e.spaceKey) {
      this.isPanning = true;
      this.panStart = { x: e.clientX - this.pan.x, y: e.clientY - this.pan.y };
      this.viewport.style.cursor = 'grabbing';
      return;
    }

    if (this.tool === 'draw' && e.button === 0) {
      // Don't draw if clicked on an existing box element
      if (e.target.closest('.drawn-box')) return;

      this.isDrawing = true;
      this.drawStart = this.getImageCoords(e);
      const id = 'box_' + Date.now();

      this.activeBox = {
        id,
        name: `champion_${this.boxes.length + 1}`,
        x: this.drawStart.x,
        y: this.drawStart.y,
        width: 1,
        height: 1,
        previewUrl: '',
      };

      this.createOverlayBoxElement(this.activeBox);
    }
  }

  handleMouseMove(e) {
    if (!this.currentImage) return;

    const coords = this.getImageCoords(e);
    this.cursorCoordsDisplay.textContent = `${Math.round(coords.x)}, ${Math.round(coords.y)}`;

    if (this.isPanning) {
      this.pan.x = e.clientX - this.panStart.x;
      this.pan.y = e.clientY - this.panStart.y;
      this.updateTransform();
      return;
    }

    if (this.isDrawing && this.activeBox) {
      const current = coords;
      const x = Math.min(this.drawStart.x, current.x);
      const y = Math.min(this.drawStart.y, current.y);
      const width = Math.abs(current.x - this.drawStart.x);
      const height = Math.abs(current.y - this.drawStart.y);

      this.activeBox.x = x;
      this.activeBox.y = y;
      this.activeBox.width = width;
      this.activeBox.height = height;

      this.updateOverlayBox(this.activeBox);
    }
  }

  handleMouseUp() {
    if (this.isPanning) {
      this.isPanning = false;
      this.viewport.style.cursor = this.tool === 'pan' ? 'grab' : 'crosshair';
    }

    if (this.isDrawing && this.activeBox) {
      this.isDrawing = false;
      if (this.activeBox.width > 10 && this.activeBox.height > 10) {
        this.activeBox.previewUrl = this.generateBoxPreview(this.activeBox);
        this.boxes.push(this.activeBox);
        this.selectBox(this.activeBox.id);
        this.renderBoxList();
      } else {
        const el = document.getElementById(this.activeBox.id);
        if (el) el.remove();
      }
      this.activeBox = null;
    }
  }

  createOverlayBoxElement(box) {
    const el = document.createElement('div');
    el.id = box.id;
    el.className = 'drawn-box';
    el.innerHTML = `
      <div class="drawn-box-label font-mono">${box.name}</div>
      <div class="box-handle tl"></div>
      <div class="box-handle tr"></div>
      <div class="box-handle bl"></div>
      <div class="box-handle br"></div>
    `;

    el.addEventListener('click', (e) => {
      e.stopPropagation();
      this.selectBox(box.id);
    });

    this.boxOverlay.appendChild(el);
    this.updateOverlayBox(box);
  }

  updateOverlayBox(box) {
    const el = document.getElementById(box.id);
    if (!el) return;

    el.style.left = `${box.x}px`;
    el.style.top = `${box.y}px`;
    el.style.width = `${box.width}px`;
    el.style.height = `${box.height}px`;

    const label = el.querySelector('.drawn-box-label');
    if (label) label.textContent = box.name || 'unnamed';
  }

  selectBox(boxId) {
    this.selectedBoxId = boxId;
    document.querySelectorAll('.drawn-box').forEach(el => {
      el.classList.toggle('selected', el.id === boxId);
    });
    document.querySelectorAll('.box-card').forEach(el => {
      el.classList.toggle('selected', el.dataset.id === boxId);
    });

    // Auto focus name input
    if (boxId) {
      const input = document.querySelector(`.box-name-input[data-id="${boxId}"]`);
      if (input) input.focus();
    }
  }

  deleteBox(boxId) {
    this.boxes = this.boxes.filter(b => b.id !== boxId);
    const el = document.getElementById(boxId);
    if (el) el.remove();
    this.renderBoxList();
  }

  clearAllBoxes() {
    this.boxes = [];
    this.boxOverlay.innerHTML = '';
    this.selectedBoxId = null;
    this.renderBoxList();
  }

  generateBoxPreview(box) {
    if (!this.currentImage) return '';
    const cropCanvas = document.createElement('canvas');
    cropCanvas.width = box.width;
    cropCanvas.height = box.height;
    const cropCtx = cropCanvas.getContext('2d');

    cropCtx.drawImage(
      this.currentImage,
      box.x, box.y, box.width, box.height,
      0, 0, box.width, box.height
    );

    return cropCanvas.toDataURL('image/png');
  }

  handleFileSelect(e) {
    const file = e.target.files[0];
    if (file) this.uploadFile(file);
  }

  handleFileDrop(e) {
    e.preventDefault();
    this.dropzone.classList.remove('dragover');
    const file = e.dataTransfer.files[0];
    if (file) this.uploadFile(file);
  }

  showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
      toast.style.transition = 'all 0.2s';
      setTimeout(() => toast.remove(), 200);
    }, 3000);
  }
}

// Initialize on DOM Ready
document.addEventListener('DOMContentLoaded', () => {
  window.app = new IconStudioApp();
});
