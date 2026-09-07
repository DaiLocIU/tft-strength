<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted, nextTick } from 'vue';
import axios from 'axios';
import {
  UploadCloud,
  Image as ImageIcon,
  CheckSquare,
  Crosshair,
  Layers,
  ZoomIn,
  ZoomOut,
  Maximize2,
  Trash2,
  RefreshCw,
  Sparkles,
  CheckCircle2,
  Sliders,
  Check,
  Cpu,
  FileCode,
  Copy,
  X,
  Ban,
  ShieldAlert,
} from 'lucide-vue-next';
import { User } from '../types';

const props = defineProps<{
  user: User | null;
}>();

const VISION_API_BASE = typeof window !== 'undefined' && window.location.port === '8000' ? '' : '/vision-api';

interface ScreenshotItem {
  name: string;
  url: string;
  thumb_url?: string;
  size: number;
  has_annotation?: boolean;
}

interface ReferenceIconItem {
  filename: string;
  name: string;
  url: string;
  width: number;
  height: number;
}

interface ModelStatus {
  status: string;
  architecture: string;
  version: string;
  classes_count: number;
  total_embeddings: number;
  total_negatives?: number;
  last_trained_at: string;
}

interface CropBox {
  id: string;
  name: string;
  stars?: 1 | 2 | 3;
  x: number;
  y: number;
  width: number;
  height: number;
  confidence?: number;
  status: 'detected' | 'confirmed' | 'corrected' | 'manual' | 'rejected';
  previewUrl?: string;
}

// --- Reactive State ---
const activeTab = ref<'screenshots' | 'icons' | 'negatives'>('screenshots');
const screenshots = ref<ScreenshotItem[]>([]);
const icons = ref<ReferenceIconItem[]>([]);
const negatives = ref<ReferenceIconItem[]>([]);
const modelStatus = ref<ModelStatus | null>(null);

const currentFilename = ref('');
const currentImageUrl = ref('');
const imageDim = reactive({ width: 0, height: 0 });

const boxes = ref<CropBox[]>([]);
const selectedBoxId = ref<string | null>(null);

const zoom = ref(1.0);
const pan = reactive({ x: 0, y: 0 });

const threshold = ref(0.65);
const isDetecting = ref(false);
const isSavingDataset = ref(false);

const isDrawing = ref(false);
const drawStart = reactive({ x: 0, y: 0 });
const activeDrawBox = ref<{ x: number; y: number; width: number; height: number } | null>(null);

const isDragging = ref(false);
const dragMode = ref<'pan' | 'move_box' | 'resize_box'>('pan');
const dragStart = reactive({ mouseX: 0, mouseY: 0, boxX: 0, boxY: 0, boxW: 0, boxH: 0 });
const resizeHandle = ref('');

const jsonModalOpen = ref(false);
const jsonInputText = ref('');

const toast = reactive<{ message: string; type: 'success' | 'error' | 'info'; visible: boolean }>({
  message: '',
  type: 'info',
  visible: false,
});
let toastTimer: any = null;

const showToast = (message: string, type: 'success' | 'error' | 'info' = 'info') => {
  if (toastTimer) clearTimeout(toastTimer);
  toast.message = message;
  toast.type = type;
  toast.visible = true;
  toastTimer = setTimeout(() => {
    toast.visible = false;
  }, 3200);
};

// --- DOM References ---
const viewportRef = ref<HTMLDivElement | null>(null);
const imageElementRef = ref<HTMLImageElement | null>(null);
const fileInputRef = ref<HTMLInputElement | null>(null);

// --- Helpers ---
const getFullUrl = (url: string) => {
  if (!url) return '';
  if (url.startsWith('http')) return url;
  return `${VISION_API_BASE}${url}`;
};

const naturalSortScreenshots = (list: ScreenshotItem[]) => {
  return list.slice().sort((a, b) => {
    const aMatch = a.name.match(/image_(\d+)/i);
    const bMatch = b.name.match(/image_(\d+)/i);
    if (aMatch && bMatch) {
      return parseInt(aMatch[1], 10) - parseInt(bMatch[1], 10);
    }
    return a.name.localeCompare(b.name, undefined, { numeric: true, sensitivity: 'base' });
  });
};

// --- Fetch Functions ---
const fetchScreenshots = async () => {
  try {
    const res = await axios.get(`${VISION_API_BASE}/api/screenshots`);
    const sorted = naturalSortScreenshots(res.data.screenshots || []);
    screenshots.value = sorted;
    if (sorted.length > 0 && !currentFilename.value) {
      selectScreenshot(sorted[0]);
    }
  } catch {
    // ignore
  }
};

const fetchIcons = async () => {
  try {
    const res = await axios.get(`${VISION_API_BASE}/api/icons`);
    icons.value = res.data.icons || [];
  } catch {
    // ignore
  }
};

const fetchNegatives = async () => {
  try {
    const res = await axios.get(`${VISION_API_BASE}/api/negatives`);
    negatives.value = res.data.negatives || [];
  } catch {
    // ignore
  }
};

const fetchModelStatus = async () => {
  try {
    const res = await axios.get(`${VISION_API_BASE}/api/model/status`);
    modelStatus.value = res.data;
  } catch {
    // ignore
  }
};

const selectScreenshot = async (item: ScreenshotItem) => {
  const fullUrl = getFullUrl(item.url);
  currentFilename.value = item.name;
  currentImageUrl.value = fullUrl;
  selectedBoxId.value = null;

  try {
    const res = await axios.get(`${VISION_API_BASE}/api/annotations/${encodeURIComponent(item.name)}`);
    if (res.data.has_annotation && Array.isArray(res.data.data?.annotations)) {
      const validBoxes: CropBox[] = res.data.data.annotations
        .filter((b: any) => b && typeof b === 'object' && b.id)
        .map((b: any) => ({
          ...b,
          stars: (b.stars as 1 | 2 | 3) || 1,
        }));
      boxes.value = validBoxes;
      showToast(`Loaded ${validBoxes.length} existing annotations`, 'info');
    } else {
      boxes.value = [];
    }
  } catch {
    boxes.value = [];
  }
};

const onImageLoaded = (e: Event) => {
  const img = e.currentTarget as HTMLImageElement;
  const w = img.naturalWidth || img.width;
  const h = img.naturalHeight || img.height;
  imageDim.width = w;
  imageDim.height = h;
  fitToScreen(w, h);
};

const fitToScreen = (overrideW?: number, overrideH?: number) => {
  if (!viewportRef.value) return;
  const vp = viewportRef.value.getBoundingClientRect();
  const w = overrideW || imageDim.width;
  const h = overrideH || imageDim.height;
  if (w <= 0 || h <= 0) return;

  const scaleX = (vp.width - 48) / w;
  const scaleY = (vp.height - 48) / h;
  const fitZoom = Math.min(scaleX, scaleY, 1.0);

  const fitPanX = (vp.width - w * fitZoom) / 2;
  const fitPanY = (vp.height - h * fitZoom) / 2;

  zoom.value = fitZoom;
  pan.x = fitPanX;
  pan.y = fitPanY;
};

// --- Detection ---
const handleRunDetection = async () => {
  if (!currentFilename.value) return;
  isDetecting.value = true;
  showToast(`Scanning for champions (Conf >= ${Math.round(threshold.value * 100)}%)...`, 'info');

  try {
    const res = await axios.post(`${VISION_API_BASE}/api/vision/detect`, {
      screenshot_name: currentFilename.value,
      threshold: threshold.value,
    });

    if (res.data.status === 'success') {
      const detectedBoxes: CropBox[] = (res.data.detections || []).map((d: any) => ({
        id: d.id,
        name: d.name,
        stars: (d.stars as 1 | 2 | 3) || 1,
        x: d.x,
        y: d.y,
        width: d.width,
        height: d.height,
        confidence: d.confidence,
        status: 'detected',
      }));

      boxes.value = detectedBoxes;
      showToast(`Found ${detectedBoxes.length} champions in ${res.data.elapsed_seconds}s!`, 'success');
    }
  } catch {
    showToast('Detection scan failed. Check server logs.', 'error');
  } finally {
    isDetecting.value = false;
  }
};

// --- Box Actions ---
const handleConfirmBox = (boxId: string) => {
  boxes.value = boxes.value.map((b) => (b.id === boxId ? { ...b, status: 'confirmed' } : b));
};

const handleSetStars = (boxId: string, stars: 1 | 2 | 3) => {
  boxes.value = boxes.value.map((b) =>
    b.id === boxId
      ? {
          ...b,
          stars,
          status: b.status === 'rejected' ? 'rejected' : 'corrected',
        }
      : b,
  );
};

const handleToggleRejectBox = (boxId: string) => {
  boxes.value = boxes.value.map((b) =>
    b.id === boxId
      ? {
          ...b,
          status: b.status === 'rejected' ? 'corrected' : 'rejected',
        }
      : b,
  );
};

const handleConfirmAll = () => {
  boxes.value = boxes.value.map((b) => (b.status === 'rejected' ? b : { ...b, status: 'confirmed' }));
  showToast('All active detections marked as confirmed!', 'success');
};

const handleSaveActiveLearning = async () => {
  if (!boxes.value || boxes.value.length === 0 || !currentFilename.value) return;

  isSavingDataset.value = true;
  try {
    const payload = {
      screenshot_name: currentFilename.value,
      items: boxes.value
        .filter((b) => b)
        .map((b) => ({
          id: b.id,
          name: (b.name || 'noise').trim().toLowerCase().replace(/\s+/g, '_'),
          stars: b.stars || 1,
          x: Math.round(b.x),
          y: Math.round(b.y),
          width: Math.round(b.width),
          height: Math.round(b.height),
          confidence: b.confidence,
          status: b.status,
        })),
    };

    const res = await axios.post(`${VISION_API_BASE}/api/annotations/save`, payload);
    if (res.data.status === 'success') {
      showToast(
        `Learned ${res.data.saved_templates_count} positive icons & ${res.data.saved_negatives_count} negative rejection prototypes!`,
        'success',
      );
      fetchIcons();
      fetchNegatives();
      fetchScreenshots();
      fetchModelStatus();
    }
  } catch {
    showToast('Failed to save dataset feedback', 'error');
  } finally {
    isSavingDataset.value = false;
  }
};

const handleUpload = async (e: Event) => {
  const target = e.target as HTMLInputElement;
  const files = target.files;
  if (!files || files.length === 0) return;

  showToast(`Uploading ${files.length} screenshot(s)...`, 'info');
  let lastUploaded = null;
  for (let i = 0; i < files.length; i++) {
    const file = files[i];
    const formData = new FormData();
    formData.append('file', file);
    try {
      const res = await axios.post(`${VISION_API_BASE}/api/screenshots/upload`, formData);
      if (res.data.status === 'success') {
        lastUploaded = { name: res.data.name, url: res.data.url, size: file.size };
      }
    } catch {
      showToast(`Upload failed for ${file.name}`, 'error');
    }
  }
  await fetchScreenshots();
  if (lastUploaded) {
    showToast(`Uploaded ${files.length} screenshot(s) successfully!`, 'success');
    selectScreenshot(lastUploaded);
  }
  if (target) target.value = '';
};

const handleDeleteIcon = async (filename: string) => {
  if (!confirm(`Delete ${filename}?`)) return;
  try {
    await axios.delete(`${VISION_API_BASE}/api/icons/${filename}`);
    showToast(`Deleted ${filename}`, 'success');
    fetchIcons();
    fetchModelStatus();
  } catch {
    showToast('Failed to delete icon', 'error');
  }
};

const handleDeleteNegative = async (filename: string) => {
  if (!confirm(`Delete negative noise prototype ${filename}?`)) return;
  try {
    await axios.delete(`${VISION_API_BASE}/api/negatives/${filename}`);
    showToast(`Deleted negative prototype ${filename}`, 'success');
    fetchNegatives();
    fetchModelStatus();
  } catch {
    showToast('Failed to delete negative sample', 'error');
  }
};

// --- Canvas Coordinate Conversion ---
const getCanvasCoords = (e: MouseEvent) => {
  if (!viewportRef.value) return { x: 0, y: 0 };
  const rect = viewportRef.value.getBoundingClientRect();
  const screenX = e.clientX - rect.left;
  const screenY = e.clientY - rect.top;
  const imageX = (screenX - pan.x) / zoom.value;
  const imageY = (screenY - pan.y) / zoom.value;
  return {
    x: Math.max(0, Math.min(imageDim.width, imageX)),
    y: Math.max(0, Math.min(imageDim.height, imageY)),
  };
};

// --- Mouse Canvas Handlers ---
const handleMouseDown = (e: MouseEvent) => {
  if (e.button !== 0) return;
  if ((e.target as HTMLElement).closest('.studio-drawn-box')) return;

  const coords = getCanvasCoords(e);
  if (e.shiftKey || e.altKey) {
    // Pan mode
    isDragging.value = true;
    dragMode.value = 'pan';
    dragStart.mouseX = e.clientX;
    dragStart.mouseY = e.clientY;
    dragStart.boxX = pan.x;
    dragStart.boxY = pan.y;
  } else {
    // Draw box mode
    isDrawing.value = true;
    drawStart.x = coords.x;
    drawStart.y = coords.y;
    activeDrawBox.value = { x: coords.x, y: coords.y, width: 0, height: 0 };
  }
};

const handleMouseMove = (e: MouseEvent) => {
  if (isDrawing.value && activeDrawBox.value) {
    const coords = getCanvasCoords(e);
    const x = Math.min(drawStart.x, coords.x);
    const y = Math.min(drawStart.y, coords.y);
    const w = Math.abs(coords.x - drawStart.x);
    const h = Math.abs(coords.y - drawStart.y);
    activeDrawBox.value = { x, y, width: w, height: h };
  } else if (isDragging.value) {
    if (dragMode.value === 'pan') {
      pan.x = dragStart.boxX + (e.clientX - dragStart.mouseX);
      pan.y = dragStart.boxY + (e.clientY - dragStart.mouseY);
    } else if (dragMode.value === 'move_box' && selectedBoxId.value) {
      const dx = (e.clientX - dragStart.mouseX) / zoom.value;
      const dy = (e.clientY - dragStart.mouseY) / zoom.value;
      boxes.value = boxes.value.map((b) =>
        b.id === selectedBoxId.value
          ? {
              ...b,
              x: Math.max(0, Math.min(imageDim.width - b.width, dragStart.boxX + dx)),
              y: Math.max(0, Math.min(imageDim.height - b.height, dragStart.boxY + dy)),
            }
          : b,
      );
    } else if (dragMode.value === 'resize_box' && selectedBoxId.value) {
      const dx = (e.clientX - dragStart.mouseX) / zoom.value;
      const dy = (e.clientY - dragStart.mouseY) / zoom.value;
      const hdl = resizeHandle.value;

      boxes.value = boxes.value.map((b) => {
        if (b.id !== selectedBoxId.value) return b;
        let { x, y, width, height } = {
          x: dragStart.boxX,
          y: dragStart.boxY,
          width: dragStart.boxW,
          height: dragStart.boxH,
        };

        if (hdl.includes('e')) width = Math.max(20, dragStart.boxW + dx);
        if (hdl.includes('s')) height = Math.max(20, dragStart.boxH + dy);
        if (hdl.includes('w')) {
          const newW = Math.max(20, dragStart.boxW - dx);
          x = dragStart.boxX + (dragStart.boxW - newW);
          width = newW;
        }
        if (hdl.includes('n')) {
          const newH = Math.max(20, dragStart.boxH - dy);
          y = dragStart.boxY + (dragStart.boxH - newH);
          height = newH;
        }

        return { ...b, x, y, width, height, status: b.status === 'rejected' ? 'rejected' : 'corrected' };
      });
    }
  }
};

const handleMouseUp = () => {
  if (isDrawing.value && activeDrawBox.value) {
    const { x, y, width, height } = activeDrawBox.value;
    if (width > 20 && height > 20) {
      const newBox: CropBox = {
        id: `box_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`,
        name: '',
        stars: 1,
        x: Math.round(x),
        y: Math.round(y),
        width: Math.round(width),
        height: Math.round(height),
        status: 'manual',
      };
      boxes.value.push(newBox);
      selectedBoxId.value = newBox.id;
    }
  }
  isDrawing.value = false;
  activeDrawBox.value = null;
  isDragging.value = false;
};

const handleStartMoveBox = (box: CropBox, e: MouseEvent) => {
  e.stopPropagation();
  selectedBoxId.value = box.id;
  isDragging.value = true;
  dragMode.value = 'move_box';
  dragStart.mouseX = e.clientX;
  dragStart.mouseY = e.clientY;
  dragStart.boxX = box.x;
  dragStart.boxY = box.y;
};

const handleStartResizeBox = (box: CropBox, handle: string, e: MouseEvent) => {
  e.stopPropagation();
  selectedBoxId.value = box.id;
  isDragging.value = true;
  dragMode.value = 'resize_box';
  resizeHandle.value = handle;
  dragStart.mouseX = e.clientX;
  dragStart.mouseY = e.clientY;
  dragStart.boxX = box.x;
  dragStart.boxY = box.y;
  dragStart.boxW = box.width;
  dragStart.boxH = box.height;
};

const handleWheel = (e: WheelEvent) => {
  e.preventDefault();
  const zoomFactor = 1.1;
  const newZoom = e.deltaY < 0 ? zoom.value * zoomFactor : zoom.value / zoomFactor;
  zoom.value = Math.max(0.1, Math.min(5.0, newZoom));
};

const generateBoxPreview = (box: CropBox) => {
  if (!imageElementRef.value || imageDim.width === 0) return '';
  const canvas = document.createElement('canvas');
  canvas.width = Math.max(1, box.width);
  canvas.height = Math.max(1, box.height);
  const ctx = canvas.getContext('2d');
  if (ctx && imageElementRef.value) {
    ctx.drawImage(
      imageElementRef.value,
      box.x,
      box.y,
      box.width,
      box.height,
      0,
      0,
      box.width,
      box.height,
    );
    return canvas.toDataURL('image/png');
  }
  return '';
};

onMounted(() => {
  fetchScreenshots();
  fetchIcons();
  fetchNegatives();
  fetchModelStatus();
  window.addEventListener('mouseup', handleMouseUp);
});

onUnmounted(() => {
  window.removeEventListener('mouseup', handleMouseUp);
  if (toastTimer) clearTimeout(toastTimer);
});
</script>

<template>
  <div class="icon-studio-container">
    <!-- Toast Notification -->
    <div v-if="toast.visible" :class="['studio-toast', toast.type]">
      <span>{{ toast.message }}</span>
    </div>

    <!-- Main Workspace Area -->
    <div class="icon-studio-layout">
      <!-- 1. LEFT SIDEBAR (Tabs: Screenshots / Icons / Negatives) -->
      <aside class="studio-sidebar-left">
        <div class="studio-tabs-bar">
          <button
            :class="['studio-tab-btn', { active: activeTab === 'screenshots' }]"
            @click="activeTab = 'screenshots'"
          >
            <ImageIcon :size="14" />
            <span>Screenshots ({{ screenshots.length }})</span>
          </button>
          <button
            :class="['studio-tab-btn', { active: activeTab === 'icons' }]"
            @click="activeTab = 'icons'"
          >
            <Layers :size="14" />
            <span>Library ({{ icons.length }})</span>
          </button>
          <button
            :class="['studio-tab-btn', { active: activeTab === 'negatives' }]"
            @click="activeTab = 'negatives'"
            title="Learned background noise / false-positive suppression templates"
          >
            <ShieldAlert :size="14" class="text-rose" />
            <span>Negatives ({{ negatives.length }})</span>
          </button>
        </div>

        <!-- Screenshots Tab -->
        <div v-if="activeTab === 'screenshots'" class="studio-pane">
          <input
            type="file"
            ref="fileInputRef"
            accept="image/*"
            multiple
            style="display: none"
            @change="handleUpload"
          />
          <div class="studio-dropzone" @click="fileInputRef?.click()">
            <UploadCloud :size="24" class="text-cyan" />
            <p><strong>Click to upload</strong> screenshot</p>
            <span>Supports 4K / Retina PNG</span>
          </div>

          <div class="studio-section-header">
            <span>Available Screenshots</span>
            <button class="studio-icon-btn-sm" @click="fetchScreenshots">
              <RefreshCw :size="12" />
            </button>
          </div>

          <div class="studio-list-scroll">
            <div
              v-for="shot in screenshots"
              :key="shot.name"
              :class="['studio-screenshot-card', { active: currentFilename === shot.name }]"
              @click="selectScreenshot(shot)"
            >
              <img
                :src="getFullUrl(shot.thumb_url || shot.url)"
                alt="thumb"
                class="studio-thumb-img"
              />
              <div class="studio-card-info">
                <span class="studio-card-title">{{ shot.name }}</span>
                <span v-if="shot.has_annotation" class="studio-pill-green">Annotated</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Reference Icons Tab -->
        <div v-if="activeTab === 'icons'" class="studio-pane">
          <div class="studio-section-header">
            <span>Active Icon Library</span>
            <button class="studio-icon-btn-sm" @click="fetchIcons">
              <RefreshCw :size="12" />
            </button>
          </div>

          <div class="studio-icons-grid">
            <div
              v-for="icon in icons"
              :key="icon.filename"
              class="studio-icon-preview-card"
            >
              <img :src="getFullUrl(icon.url)" :alt="icon.name" />
              <span class="icon-label">{{ icon.name }}</span>
              <button
                class="btn-delete-icon"
                @click.stop="handleDeleteIcon(icon.filename)"
                title="Delete template"
              >
                <Trash2 :size="11" />
              </button>
            </div>
          </div>
        </div>

        <!-- Negatives Tab -->
        <div v-if="activeTab === 'negatives'" class="studio-pane">
          <div class="studio-section-header">
            <span>Noise Rejection Bank</span>
            <button class="studio-icon-btn-sm" @click="fetchNegatives">
              <RefreshCw :size="12" />
            </button>
          </div>

          <div class="negatives-alert-banner">
            <ShieldAlert :size="15" class="text-rose" />
            <p>Templates learned as False Positives. Matcher suppresses any window matching these noise patterns.</p>
          </div>

          <div class="studio-icons-grid">
            <div
              v-for="neg in negatives"
              :key="neg.filename"
              class="studio-icon-preview-card negative"
            >
              <img :src="getFullUrl(neg.url)" :alt="neg.name" />
              <span class="icon-label font-mono">{{ neg.name }}</span>
              <button
                class="btn-delete-icon text-rose"
                @click.stop="handleDeleteNegative(neg.filename)"
                title="Delete negative sample"
              >
                <Trash2 :size="11" />
              </button>
            </div>
          </div>
        </div>
      </aside>

      <!-- 2. CENTER CANVAS WORKSPACE -->
      <main class="studio-canvas-stage">
        <!-- Top Toolbar -->
        <header class="studio-toolbar">
          <div class="toolbar-group">
            <span class="current-shot-name font-mono">{{ currentFilename || 'No Image Selected' }}</span>
            <span class="dim-badge font-mono">{{ imageDim.width }} × {{ imageDim.height }} px</span>
          </div>

          <!-- Threshold Slider with Presets -->
          <div class="toolbar-group">
            <div class="threshold-control-wrap">
              <Sliders :size="13" class="text-cyan" />
              <label>Sensitivity:</label>
              <div class="threshold-presets">
                <button
                  :class="['preset-chip', { active: threshold === 0.60 }]"
                  @click="threshold = 0.60"
                  title="Permissive (60%)"
                >
                  60%
                </button>
                <button
                  :class="['preset-chip', { active: threshold === 0.65 }]"
                  @click="threshold = 0.65"
                  title="Default (65%)"
                >
                  65%
                </button>
                <button
                  :class="['preset-chip', { active: threshold === 0.75 }]"
                  @click="threshold = 0.75"
                  title="Balanced (75%)"
                >
                  75%
                </button>
                <button
                  :class="['preset-chip', { active: threshold === 0.90 }]"
                  @click="threshold = 0.90"
                  title="Strict (90%)"
                >
                  90%
                </button>
              </div>
              <input
                type="range"
                min="0.40"
                max="0.95"
                step="0.01"
                v-model.number="threshold"
                class="threshold-slider"
              />
              <span class="threshold-val-text font-mono">{{ Math.round(threshold * 100) }}%</span>
            </div>

            <button
              class="btn-detect-ai"
              @click="handleRunDetection"
              :disabled="isDetecting || !currentFilename"
            >
              <Sparkles :size="14" :class="{ 'animate-spin': isDetecting }" />
              <span>{{ isDetecting ? 'Scanning...' : 'Run AI Scan' }}</span>
            </button>
          </div>

          <!-- Canvas Zoom & Navigation Tools -->
          <div class="toolbar-group">
            <button class="studio-icon-btn" @click="zoom = Math.min(5.0, zoom * 1.2)" title="Zoom In">
              <ZoomIn :size="14" />
            </button>
            <button class="studio-icon-btn" @click="zoom = Math.max(0.1, zoom / 1.2)" title="Zoom Out">
              <ZoomOut :size="14" />
            </button>
            <button class="studio-icon-btn" @click="fitToScreen()" title="Fit to Screen">
              <Maximize2 :size="14" />
            </button>
            <span class="zoom-text font-mono">{{ Math.round(zoom * 100) }}%</span>
          </div>
        </header>

        <!-- Viewport -->
        <div
          ref="viewportRef"
          class="studio-viewport"
          @mousedown="handleMouseDown"
          @mousemove="handleMouseMove"
          @wheel="handleWheel"
        >
          <div
            v-if="currentImageUrl"
            class="studio-transform-layer"
            :style="{
              transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
              transformOrigin: '0 0',
              width: `${imageDim.width}px`,
              height: `${imageDim.height}px`,
            }"
          >
            <img
              ref="imageElementRef"
              :src="currentImageUrl"
              alt="screenshot"
              class="studio-base-image"
              @load="onImageLoaded"
              draggable="false"
            />

            <!-- Render Drawn & Detected Bounding Boxes -->
            <div
              v-for="box in boxes"
              :key="box.id"
              :class="[
                'studio-drawn-box',
                { selected: box.id === selectedBoxId },
                box.status,
              ]"
              :style="{
                left: `${box.x}px`,
                top: `${box.y}px`,
                width: `${box.width}px`,
                height: `${box.height}px`,
              }"
              @mousedown="handleStartMoveBox(box, $event)"
              @click.stop="selectedBoxId = box.id"
            >
              <span :class="['studio-box-label font-mono', box.status]">
                <template v-if="box.status === 'rejected'">
                  [False Positive 🚫] {{ box.name || 'noise' }}
                </template>
                <template v-else>
                  {{ box.name || 'unnamed' }}
                  <span :class="['studio-star-badge', `stars-${box.stars || 1}`]">
                    {{ ' ' }}{{ box.stars === 3 ? '★★★' : box.stars === 2 ? '★★' : '★' }}
                  </span>
                </template>
                <template v-if="box.confidence"> ({{ box.confidence }}%)</template>
                <template v-if="box.status === 'confirmed'"> ✓</template>
              </span>

              <!-- 8 Resize Handles when Selected -->
              <template v-if="box.id === selectedBoxId">
                <div class="studio-resize-handle nw" @mousedown="handleStartResizeBox(box, 'nw', $event)" />
                <div class="studio-resize-handle n" @mousedown="handleStartResizeBox(box, 'n', $event)" />
                <div class="studio-resize-handle ne" @mousedown="handleStartResizeBox(box, 'ne', $event)" />
                <div class="studio-resize-handle e" @mousedown="handleStartResizeBox(box, 'e', $event)" />
                <div class="studio-resize-handle se" @mousedown="handleStartResizeBox(box, 'se', $event)" />
                <div class="studio-resize-handle s" @mousedown="handleStartResizeBox(box, 's', $event)" />
                <div class="studio-resize-handle sw" @mousedown="handleStartResizeBox(box, 'sw', $event)" />
                <div class="studio-resize-handle w" @mousedown="handleStartResizeBox(box, 'w', $event)" />
              </template>
            </div>

            <!-- Active Drawing Rubber-Band -->
            <div
              v-if="isDrawing && activeDrawBox"
              class="studio-active-draw-box"
              :style="{
                left: `${activeDrawBox.x}px`,
                top: `${activeDrawBox.y}px`,
                width: `${activeDrawBox.width}px`,
                height: `${activeDrawBox.height}px`,
              }"
            />
          </div>
        </div>
      </main>

      <!-- 3. RIGHT SIDEBAR (Detections, Stars, Active Learning) -->
      <aside class="studio-sidebar-right">
        <div class="studio-sidebar-header">
          <div class="header-title-wrap">
            <Crosshair :size="15" class="text-cyan" />
            <span class="sidebar-title">Detected Units ({{ boxes.length }})</span>
          </div>

          <div class="header-actions-wrap">
            <button
              v-if="boxes.length > 0"
              class="studio-action-pill text-emerald"
              @click="handleConfirmAll"
              title="Confirm all detections as correct"
            >
              <CheckCircle2 :size="12" />
              <span>Confirm All</span>
            </button>
            <button
              v-if="boxes.length > 0"
              class="studio-action-pill text-rose"
              @click="boxes = []"
              title="Clear all bounding boxes"
            >
              <Trash2 :size="12" />
              <span>Clear</span>
            </button>
          </div>
        </div>

        <div class="studio-boxes-list-scroll">
          <div v-if="boxes.length === 0" class="empty-boxes-hint">
            <Crosshair :size="32" class="text-muted" />
            <p>No champions labeled yet.</p>
            <span>Click <strong>Run AI Scan</strong> or click & drag on canvas to draw a box.</span>
          </div>

          <div
            v-for="box in boxes"
            :key="box.id"
            :class="[
              'studio-box-item-card',
              { selected: box.id === selectedBoxId },
              box.status,
            ]"
            @click="selectedBoxId = box.id"
          >
            <img
              :src="box.previewUrl || generateBoxPreview(box)"
              alt="crop"
              class="studio-box-thumb"
            />
            <div class="studio-box-item-body">
              <div class="box-name-row">
                <input
                  type="text"
                  class="studio-box-name-input"
                  v-model="box.name"
                  placeholder="champion_name"
                  @input="box.status = box.status === 'rejected' ? 'rejected' : 'corrected'"
                />
                <span
                  v-if="box.status === 'confirmed'"
                  class="badge-confirmed"
                  title="Verified Ground Truth"
                >
                  <Check :size="12" />
                </span>
                <span
                  v-else-if="box.status === 'rejected'"
                  class="badge-rejected"
                  title="Marked as False Positive / Background Noise"
                >
                  <Ban :size="11" />
                </span>
                <button
                  v-else
                  class="btn-confirm-single"
                  @click.stop="handleConfirmBox(box.id)"
                  title="Confirm as correct"
                >
                  <Check :size="12" />
                </button>
              </div>

              <!-- Star Level Selector (1★ Bronze, 2★ Silver, 3★ Gold) -->
              <div
                v-if="box.status !== 'rejected'"
                class="box-stars-selector"
                @click.stop
              >
                <button
                  type="button"
                  :class="['star-pill star-1', { active: box.stars === 1 || !box.stars }]"
                  @click="handleSetStars(box.id, 1)"
                  title="1-Star (Bronze)"
                >
                  ★ 1
                </button>
                <button
                  type="button"
                  :class="['star-pill star-2', { active: box.stars === 2 }]"
                  @click="handleSetStars(box.id, 2)"
                  title="2-Star (Silver)"
                >
                  ★★ 2
                </button>
                <button
                  type="button"
                  :class="['star-pill star-3', { active: box.stars === 3 }]"
                  @click="handleSetStars(box.id, 3)"
                  title="3-Star (Gold)"
                >
                  ★★★ 3
                </button>
              </div>

              <div class="studio-box-meta">
                <span :class="['status-pill', box.status]">
                  {{
                    box.status === 'rejected'
                      ? 'False Positive 🚫'
                      : box.confidence
                      ? `${box.confidence}% match`
                      : box.status
                  }}
                </span>
                <button
                  :class="['btn-reject-single', { active: box.status === 'rejected' }]"
                  @click.stop="handleToggleRejectBox(box.id)"
                  :title="box.status === 'rejected' ? 'Restore box' : 'Mark as False Positive / Noise to teach AI'"
                >
                  <Ban :size="11" />
                  <span>{{ box.status === 'rejected' ? 'Wrong 🚫' : 'Reject' }}</span>
                </button>
                <button
                  class="studio-icon-btn-sm text-rose"
                  @click.stop="boxes = boxes.filter((b) => b.id !== box.id)"
                  title="Remove box"
                >
                  <Trash2 :size="13" />
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Footer Actions (Approve & Train) -->
        <div class="studio-footer-action">
          <button
            class="btn-save-train-footer"
            :disabled="boxes.length === 0 || isSavingDataset"
            @click="handleSaveActiveLearning"
          >
            <Sparkles :size="15" :class="{ 'animate-spin': isSavingDataset }" />
            <span>{{ isSavingDataset ? 'Training Model...' : 'Approve & Train Model' }}</span>
          </button>
        </div>
      </aside>
    </div>
  </div>
</template>
