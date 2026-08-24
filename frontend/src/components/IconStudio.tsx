import React, { useEffect, useRef, useState } from 'react';
import axios from 'axios';
import {
  Crop,
  Hand,
  ZoomIn,
  ZoomOut,
  Maximize2,
  Save,
  Trash2,
  UploadCloud,
  RefreshCw,
  Image as ImageIcon,
  Layers,
  Sparkles,
  Lock,
  CheckCircle2,
  Sliders,
  Check,
  Cpu,
  FileCode,
  Copy,
  X,
} from 'lucide-react';
import { User } from '../types';

const VISION_API_BASE = 'http://localhost:8000';

interface ScreenshotItem {
  name: string;
  url: string;
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
  last_trained_at: string;
}

interface CropBox {
  id: string;
  name: string;
  x: number;
  y: number;
  width: number;
  height: number;
  confidence?: number;
  status: 'detected' | 'confirmed' | 'corrected' | 'manual';
  previewUrl?: string;
}

interface IconStudioProps {
  user: User | null;
}

export const IconStudio: React.FC<IconStudioProps> = ({ user }) => {
  const isAuthorized = user?.email === 'loc.ldl.itou@gmail.com';

  const [activeTab, setActiveTab] = useState<'screenshots' | 'library'>('screenshots');
  const [screenshots, setScreenshots] = useState<ScreenshotItem[]>([]);
  const [icons, setIcons] = useState<ReferenceIconItem[]>([]);
  const [modelStatus, setModelStatus] = useState<ModelStatus | null>(null);
  const [isRetraining, setIsRetraining] = useState<boolean>(false);

  const [currentImageUrl, setCurrentImageUrl] = useState<string | null>(null);
  const [currentFilename, setCurrentFilename] = useState<string | null>(null);
  const [imageDim, setImageDim] = useState<{ width: number; height: number }>({ width: 0, height: 0 });

  const [tool, setTool] = useState<'draw' | 'pan'>('draw');
  const [zoom, setZoom] = useState<number>(1.0);
  const [pan, setPan] = useState<{ x: number; y: number }>({ x: 0, y: 0 });

  // Detection & Learning
  const [threshold, setThreshold] = useState<number>(0.90);
  const [isDetecting, setIsDetecting] = useState<boolean>(false);
  const [isSavingDataset, setIsSavingDataset] = useState<boolean>(false);

  // JSON Import / Export Modal
  const [isJsonModalOpen, setIsJsonModalOpen] = useState<boolean>(false);
  const [jsonInputText, setJsonInputText] = useState<string>('');

  const [boxes, setBoxes] = useState<CropBox[]>([]);
  const [selectedBoxId, setSelectedBoxId] = useState<string | null>(null);
  const [cursorPos, setCursorPos] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [toast, setToast] = useState<{ msg: string; type: 'success' | 'error' | 'info' } | null>(null);

  const viewportRef = useRef<HTMLDivElement | null>(null);
  const canvasContainerRef = useRef<HTMLDivElement | null>(null);
  const mainImageRef = useRef<HTMLImageElement | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const isDrawingRef = useRef(false);
  const drawStartRef = useRef<{ x: number; y: number }>({ x: 0, y: 0 });
  const activeBoxRef = useRef<CropBox | null>(null);

  const resizeStateRef = useRef<{
    boxId: string;
    handle: string;
    startCoords: { x: number; y: number };
    origBox: { x: number; y: number; width: number; height: number };
  } | null>(null);

  const moveStateRef = useRef<{
    boxId: string;
    startCoords: { x: number; y: number };
    origBox: { x: number; y: number };
  } | null>(null);

  const isPanningRef = useRef(false);
  const panStartRef = useRef<{ x: number; y: number }>({ x: 0, y: 0 });

  const showToast = (msg: string, type: 'success' | 'error' | 'info' = 'info') => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 3500);
  };

  const getFullUrl = (relativeUrl: string) => {
    const parts = relativeUrl.split('/').map((p) => encodeURIComponent(p));
    return `${VISION_API_BASE}${parts.join('/')}`;
  };

  useEffect(() => {
    if (isAuthorized) {
      fetchScreenshots();
      fetchIcons();
      fetchModelStatus();
    }
  }, [isAuthorized]);

  const fetchModelStatus = async () => {
    try {
      const res = await axios.get(`${VISION_API_BASE}/api/model/status`);
      setModelStatus(res.data);
    } catch {
      // ignore
    }
  };

  const handleRetrainModel = async () => {
    setIsRetraining(true);
    showToast('Retraining CNN feature embedding index with augmentations...', 'info');
    try {
      const res = await axios.post(`${VISION_API_BASE}/api/model/retrain`);
      if (res.data.status === 'success') {
        showToast(res.data.message, 'success');
        fetchModelStatus();
      }
    } catch {
      showToast('Retraining failed', 'error');
    } finally {
      setIsRetraining(false);
    }
  };

  const fetchScreenshots = async () => {
    try {
      const res = await axios.get(`${VISION_API_BASE}/api/screenshots`);
      const list: ScreenshotItem[] = res.data.screenshots || [];
      setScreenshots(list);
      if (list.length > 0 && !currentFilename) {
        selectScreenshot(list[0]);
      }
    } catch {
      showToast('Vision Service API offline on port 8000', 'error');
    }
  };

  const fetchIcons = async () => {
    try {
      const res = await axios.get(`${VISION_API_BASE}/api/icons`);
      setIcons(res.data.icons || []);
    } catch {
      // ignore
    }
  };

  const selectScreenshot = async (item: ScreenshotItem) => {
    const fullUrl = getFullUrl(item.url);
    setCurrentFilename(item.name);
    setCurrentImageUrl(fullUrl);
    setSelectedBoxId(null);

    // Check if previous annotations exist
    try {
      const res = await axios.get(`${VISION_API_BASE}/api/annotations/${encodeURIComponent(item.name)}`);
      if (res.data.has_annotation && Array.isArray(res.data.data?.annotations)) {
        const validBoxes = res.data.data.annotations.filter((b: any) => b && typeof b === 'object' && b.id);
        setBoxes(validBoxes);
        showToast(`Loaded ${validBoxes.length} existing annotations`, 'info');
      } else {
        setBoxes([]);
      }
    } catch {
      setBoxes([]);
    }
  };

  const onImageLoaded = (e: React.SyntheticEvent<HTMLImageElement>) => {
    const img = e.currentTarget;
    const w = img.naturalWidth;
    const h = img.naturalHeight;
    setImageDim({ width: w, height: h });
    fitToScreen(w, h);
  };

  const fitToScreen = (w = imageDim.width, h = imageDim.height) => {
    if (!w || !h || !viewportRef.current) return;
    const vp = viewportRef.current.getBoundingClientRect();
    const padding = 60;
    const scaleX = (vp.width - padding) / w;
    const scaleY = (vp.height - padding) / h;
    const fitZoom = Math.max(0.05, Math.min(scaleX, scaleY, 1.0));

    setZoom(fitZoom);
    setPan({
      x: (vp.width - w * fitZoom) / 2,
      y: (vp.height - h * fitZoom) / 2,
    });
  };

  // --- AI Detection Scan ---

  const handleRunDetection = async () => {
    if (!currentFilename) return;
    setIsDetecting(true);
    showToast(`Scanning with AI detection (${Math.round(threshold * 100)}% threshold)...`, 'info');

    try {
      const res = await axios.post(`${VISION_API_BASE}/api/vision/detect`, {
        screenshot_name: currentFilename,
        threshold,
      });

      if (res.data.status === 'success' && Array.isArray(res.data.detections)) {
        const detectedList: CropBox[] = res.data.detections
          .filter((d: any) => d && typeof d === 'object')
          .map((d: any) => ({
            ...d,
            status: 'detected',
          }));

        setBoxes(detectedList);
        showToast(`Found ${detectedList.length} champion detections! Review them on right.`, 'success');
      }
    } catch {
      showToast('Detection scan failed', 'error');
    } finally {
      setIsDetecting(false);
    }
  };

  // --- Human in the loop Feedback Actions ---

  const handleConfirmBox = (boxId: string) => {
    setBoxes((prev) =>
      (prev || []).map((b) => (b && b.id === boxId ? { ...b, status: 'confirmed' } : b)),
    );
  };

  const handleConfirmAll = () => {
    setBoxes((prev) => (prev || []).map((b) => (b ? { ...b, status: 'confirmed' } : b)));
    showToast('All detections marked as confirmed!', 'success');
  };

  const handleSaveActiveLearning = async () => {
    if (!boxes || boxes.length === 0 || !currentFilename) return;

    setIsSavingDataset(true);
    try {
      const payload = {
        screenshot_name: currentFilename,
        items: boxes
          .filter((b) => b && b.name)
          .map((b) => ({
            id: b.id,
            name: b.name.trim().toLowerCase().replace(/\s+/g, '_'),
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
          `Dataset saved! Retrained CNN with ${res.data.saved_templates_count} new templates.`,
          'success',
        );
        fetchIcons();
        fetchScreenshots();
        fetchModelStatus();
      }
    } catch {
      showToast('Failed to save dataset feedback', 'error');
    } finally {
      setIsSavingDataset(false);
    }
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);
    try {
      showToast('Uploading screenshot...', 'info');
      const res = await axios.post(`${VISION_API_BASE}/api/screenshots/upload`, formData);
      if (res.data.status === 'success') {
        showToast(`Uploaded ${res.data.name}`, 'success');
        await fetchScreenshots();
        selectScreenshot({ name: res.data.name, url: res.data.url, size: file.size });
      }
    } catch {
      showToast('Upload failed', 'error');
    }
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

  // --- JSON / Python Coordinates Parser ---

  const handleParseAndApplyJson = () => {
    if (!jsonInputText.trim()) return;
    const w = imageDim.width || 3456;
    const h = imageDim.height || 2234;

    try {
      let cleaned = jsonInputText.trim();
      // Handle Python syntax e.g. crops = { "Elder_Dragon": (0.13, 0.41, 0.29, 0.53), ... }
      if (cleaned.includes('crops =') || cleaned.includes('crops=')) {
        cleaned = cleaned.substring(cleaned.indexOf('{'));
      }
      // Replace python tuples (a, b, c, d) with [a, b, c, d]
      cleaned = cleaned.replace(/\((\s*[\d\.]+\s*,\s*[\d\.]+\s*,\s*[\d\.]+\s*,\s*[\d\.]+\s*)\)/g, '[$1]');
      // Clean trailing commas before closing braces
      cleaned = cleaned.replace(/,\s*([\}\]])/g, '$1');

      const parsed = JSON.parse(cleaned);
      const parsedBoxes: CropBox[] = [];

      if (Array.isArray(parsed)) {
        // Array format [{ name, x, y, width, height } or { name, ymin, xmin, ymax, xmax }]
        parsed.forEach((item: any, idx: number) => {
          const name = item.name || `item_${idx + 1}`;
          let x = 0, y = 0, width = 0, height = 0;

          if (item.xmin !== undefined && item.ymin !== undefined) {
            x = item.xmin * w;
            y = item.ymin * h;
            width = (item.xmax - item.xmin) * w;
            height = (item.ymax - item.ymin) * h;
          } else {
            x = item.x || 0;
            y = item.y || 0;
            width = item.width || 100;
            height = item.height || 100;
          }

          parsedBoxes.push({
            id: item.id || `box_${Date.now()}_${idx}`,
            name,
            x: Math.round(x),
            y: Math.round(y),
            width: Math.round(width),
            height: Math.round(height),
            confidence: item.confidence,
            status: item.status || 'manual',
          });
        });
      } else if (typeof parsed === 'object' && parsed !== null) {
        if (parsed.annotations && Array.isArray(parsed.annotations)) {
          // File format { annotations: [...] }
          parsed.annotations.forEach((item: any, idx: number) => {
            parsedBoxes.push({
              id: item.id || `box_${Date.now()}_${idx}`,
              name: item.name || `item_${idx + 1}`,
              x: Math.round(item.x),
              y: Math.round(item.y),
              width: Math.round(item.width),
              height: Math.round(item.height),
              confidence: item.confidence,
              status: item.status || 'confirmed',
            });
          });
        } else {
          // Dictionary format { "name": (ymin, xmin, ymax, xmax) or [ymin, xmin, ymax, xmax] }
          Object.entries(parsed).forEach(([key, val], idx) => {
            if (Array.isArray(val) && val.length === 4) {
              const [ymin, xmin, ymax, xmax] = val as number[];
              const x = xmin * w;
              const y = ymin * h;
              const width = (xmax - xmin) * w;
              const height = (ymax - ymin) * h;

              parsedBoxes.push({
                id: `box_${Date.now()}_${idx}`,
                name: key.toLowerCase(),
                x: Math.round(x),
                y: Math.round(y),
                width: Math.round(width),
                height: Math.round(height),
                status: 'confirmed',
              });
            }
          });
        }
      }

      if (parsedBoxes.length > 0) {
        setBoxes(parsedBoxes);
        setIsJsonModalOpen(false);
        setJsonInputText('');
        showToast(`Imported & applied ${parsedBoxes.length} boxes to canvas!`, 'success');
      } else {
        showToast('No valid boxes found in JSON', 'error');
      }
    } catch (err: any) {
      showToast(`JSON Parse Error: ${err.message}`, 'error');
    }
  };

  const handleExportJson = () => {
    if (boxes.length === 0) return;
    const w = imageDim.width || 3456;
    const h = imageDim.height || 2234;

    const dictFormat: Record<string, number[]> = {};
    boxes.forEach((b) => {
      const ymin = Number((b.y / h).toFixed(2));
      const xmin = Number((b.x / w).toFixed(2));
      const ymax = Number(((b.y + b.height) / h).toFixed(2));
      const xmax = Number(((b.x + b.width) / w).toFixed(2));
      dictFormat[b.name] = [ymin, xmin, ymax, xmax];
    });

    const output = JSON.stringify(dictFormat, null, 2);
    navigator.clipboard.writeText(output);
    showToast('Copied JSON coordinates to clipboard!', 'success');
  };

  // --- Pointer & Box Interactions ---

  const getImageCoords = (clientX: number, clientY: number) => {
    if (!canvasContainerRef.current || !imageDim.width) return { x: 0, y: 0 };
    const rect = canvasContainerRef.current.getBoundingClientRect();
    const x = (clientX - rect.left) / zoom;
    const y = (clientY - rect.top) / zoom;
    return {
      x: Math.max(0, Math.min(x, imageDim.width)),
      y: Math.max(0, Math.min(y, imageDim.height)),
    };
  };

  const handleStartResizeBox = (box: CropBox, handle: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const coords = getImageCoords(e.clientX, e.clientY);
    resizeStateRef.current = {
      boxId: box.id,
      handle,
      startCoords: coords,
      origBox: { x: box.x, y: box.y, width: box.width, height: box.height },
    };
  };

  const handleStartMoveBox = (box: CropBox, e: React.MouseEvent) => {
    if ((e.target as HTMLElement).closest('.studio-resize-handle')) return;
    e.stopPropagation();
    setSelectedBoxId(box.id);
    const coords = getImageCoords(e.clientX, e.clientY);
    moveStateRef.current = {
      boxId: box.id,
      startCoords: coords,
      origBox: { x: box.x, y: box.y },
    };
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    if (!currentImageUrl) return;

    if (tool === 'pan' || e.button === 1 || e.altKey) {
      isPanningRef.current = true;
      panStartRef.current = { x: e.clientX - pan.x, y: e.clientY - pan.y };
      return;
    }

    if (tool === 'draw' && e.button === 0) {
      if ((e.target as HTMLElement).closest('.studio-drawn-box')) return;

      setSelectedBoxId(null);
      isDrawingRef.current = true;
      const coords = getImageCoords(e.clientX, e.clientY);
      drawStartRef.current = coords;

      const newId = `box_${Date.now()}`;
      const newBox: CropBox = {
        id: newId,
        name: `champion_${(boxes || []).length + 1}`,
        x: coords.x,
        y: coords.y,
        width: 1,
        height: 1,
        status: 'manual',
      };
      activeBoxRef.current = newBox;
    }
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!currentImageUrl) return;
    const coords = getImageCoords(e.clientX, e.clientY);
    setCursorPos({ x: Math.round(coords.x), y: Math.round(coords.y) });

    if (isPanningRef.current) {
      setPan({
        x: e.clientX - panStartRef.current.x,
        y: e.clientY - panStartRef.current.y,
      });
      return;
    }

    // 1. Resizing existing box
    if (resizeStateRef.current) {
      const { boxId, handle, startCoords, origBox } = resizeStateRef.current;
      const dx = coords.x - startCoords.x;
      const dy = coords.y - startCoords.y;

      let newX = origBox.x;
      let newY = origBox.y;
      let newW = origBox.width;
      let newH = origBox.height;

      if (handle.includes('e')) newW = Math.max(16, origBox.width + dx);
      if (handle.includes('s')) newH = Math.max(16, origBox.height + dy);
      if (handle.includes('w')) {
        const allowedDx = Math.min(dx, origBox.width - 16);
        newX = origBox.x + allowedDx;
        newW = origBox.width - allowedDx;
      }
      if (handle.includes('n')) {
        const allowedDy = Math.min(dy, origBox.height - 16);
        newY = origBox.y + allowedDy;
        newH = origBox.height - allowedDy;
      }

      setBoxes((prev) =>
        (prev || []).map((b) =>
          b && b.id === boxId
            ? { ...b, x: Math.round(newX), y: Math.round(newY), width: Math.round(newW), height: Math.round(newH) }
            : b,
        ),
      );
      return;
    }

    // 2. Moving existing box
    if (moveStateRef.current) {
      const { boxId, startCoords, origBox } = moveStateRef.current;
      const dx = coords.x - startCoords.x;
      const dy = coords.y - startCoords.y;
      const newX = Math.max(0, origBox.x + dx);
      const newY = Math.max(0, origBox.y + dy);

      setBoxes((prev) =>
        (prev || []).map((b) =>
          b && b.id === boxId
            ? { ...b, x: Math.round(newX), y: Math.round(newY) }
            : b,
        ),
      );
      return;
    }

    // 3. Drawing new box
    if (isDrawingRef.current && activeBoxRef.current) {
      const x = Math.min(drawStartRef.current.x, coords.x);
      const y = Math.min(drawStartRef.current.y, coords.y);
      const width = Math.abs(coords.x - drawStartRef.current.x);
      const height = Math.abs(coords.y - drawStartRef.current.y);

      activeBoxRef.current = {
        ...activeBoxRef.current,
        x,
        y,
        width,
        height,
      };

      setBoxes((prev) => {
        const filtered = (prev || []).filter(
          (b) => b && activeBoxRef.current && b.id !== activeBoxRef.current.id,
        );
        return activeBoxRef.current ? [...filtered, activeBoxRef.current] : filtered;
      });
    }
  };

  const generateBoxPreview = (box: CropBox): string => {
    if (!mainImageRef.current || !box || box.width <= 0 || box.height <= 0) return '';
    try {
      const offscreen = document.createElement('canvas');
      offscreen.width = Math.max(1, Math.round(box.width));
      offscreen.height = Math.max(1, Math.round(box.height));
      const ctx = offscreen.getContext('2d');
      ctx?.drawImage(
        mainImageRef.current,
        Math.round(box.x),
        Math.round(box.y),
        Math.round(box.width),
        Math.round(box.height),
        0,
        0,
        Math.round(box.width),
        Math.round(box.height),
      );
      return offscreen.toDataURL('image/png');
    } catch {
      return '';
    }
  };

  const handleMouseUp = () => {
    isPanningRef.current = false;

    // Finish resize / move: update preview
    if (resizeStateRef.current || moveStateRef.current) {
      const activeId = resizeStateRef.current?.boxId || moveStateRef.current?.boxId;
      resizeStateRef.current = null;
      moveStateRef.current = null;

      if (activeId) {
        setBoxes((prev) =>
          (prev || []).map((b) => {
            if (b && b.id === activeId) {
              const preview = generateBoxPreview(b);
              return { ...b, previewUrl: preview };
            }
            return b;
          }),
        );
      }
      return;
    }

    if (isDrawingRef.current && activeBoxRef.current) {
      isDrawingRef.current = false;
      const b = activeBoxRef.current;

      if (b && b.width > 12 && b.height > 12) {
        const preview = generateBoxPreview(b);
        const finalBox: CropBox = { ...b, previewUrl: preview };
        setBoxes((prev) => [
          ...(prev || []).filter((x) => x && x.id !== b.id),
          finalBox,
        ]);
        setSelectedBoxId(finalBox.id);
      } else if (b) {
        setBoxes((prev) => (prev || []).filter((x) => x && x.id !== b.id));
      }
      activeBoxRef.current = null;
    }
  };

  const handleWheel = (e: React.WheelEvent) => {
    if (!currentImageUrl || !viewportRef.current) return;
    e.preventDefault();

    const zoomFactor = e.deltaY < 0 ? 1.15 : 0.85;
    const newZoom = Math.max(0.05, Math.min(zoom * zoomFactor, 4.0));

    const vpRect = viewportRef.current.getBoundingClientRect();
    const mouseX = e.clientX - vpRect.left;
    const mouseY = e.clientY - vpRect.top;

    const imgX = (mouseX - pan.x) / zoom;
    const imgY = (mouseY - pan.y) / zoom;

    setZoom(newZoom);
    setPan({
      x: mouseX - imgX * newZoom,
      y: mouseY - imgY * newZoom,
    });
  };

  if (!isAuthorized) {
    return (
      <div className="unauthorized-card">
        <div className="lock-icon-wrap">
          <Lock size={36} className="text-amber" />
        </div>
        <h2>Access Restricted</h2>
        <p>TFT Icon Studio is available exclusively for admin user: <code>loc.ldl.itou@gmail.com</code></p>
        <span className="unauth-hint">Logged in as: {user?.email || 'Guest'}</span>
      </div>
    );
  }

  return (
    <div className="icon-studio-root">
      {/* Studio Header Toolbar */}
      <div className="studio-toolbar">
        <div className="studio-tool-group">
          <button
            className={`studio-tool-btn ${tool === 'draw' ? 'active' : ''}`}
            onClick={() => setTool('draw')}
            title="Draw Box Mode (D)"
          >
            <Crop size={16} />
            <span>Draw Box</span>
          </button>
          <button
            className={`studio-tool-btn ${tool === 'pan' ? 'active' : ''}`}
            onClick={() => setTool('pan')}
            title="Pan Mode (H)"
          >
            <Hand size={16} />
            <span>Pan</span>
          </button>
        </div>

        <div className="studio-divider"></div>

        {/* AI Detection Scanner */}
        <div className="studio-detect-group">
          <div className="threshold-pill">
            <Sliders size={13} className="text-cyan" />
            <span className="font-mono">Conf: &ge;{Math.round(threshold * 100)}%</span>
            <input
              type="range"
              min="0.50"
              max="0.99"
              step="0.01"
              value={threshold}
              onChange={(e) => setThreshold(parseFloat(e.target.value))}
              className="threshold-slider"
              title="Detection confidence threshold"
            />
            <button
              className={`preset-btn ${threshold >= 0.90 ? 'active' : ''}`}
              onClick={() => setThreshold(0.90)}
              title="Strict (>90% only, 0 false positives)"
            >
              &gt;90%
            </button>
            <button
              className={`preset-btn ${threshold === 0.80 ? 'active' : ''}`}
              onClick={() => setThreshold(0.80)}
              title="Balanced (>80%)"
            >
              &gt;80%
            </button>
          </div>

          <button
            className="btn btn-scan-glow"
            disabled={!currentFilename || isDetecting}
            onClick={handleRunDetection}
          >
            <Sparkles size={15} className={isDetecting ? 'animate-spin' : ''} />
            <span>{isDetecting ? 'Scanning...' : 'Run AI Detection'}</span>
          </button>
        </div>

        <div className="studio-divider"></div>

        {/* Deep Learning Model Status & Active Learning Trigger */}
        <div className="studio-model-badge-group">
          <div className="model-status-pill" title={`Architecture: ${modelStatus?.architecture || 'MobileNetV2'}`}>
            <Cpu size={14} className="text-cyan" />
            <div className="model-status-info">
              <span className="model-name">MobileNetV2 CNN</span>
              <span className="model-meta">
                {modelStatus ? `${modelStatus.classes_count} Classes • ${modelStatus.total_embeddings} Embeds` : 'Active'}
              </span>
            </div>
          </div>

          <button
            className="btn-model-retrain"
            onClick={handleRetrainModel}
            disabled={isRetraining}
            title="Retrain / Update CNN embedding index with current templates & augmentations"
          >
            <RefreshCw size={13} className={isRetraining ? 'animate-spin' : ''} />
            <span>{isRetraining ? 'Retraining...' : 'Retrain Model'}</span>
          </button>
        </div>

        <div className="studio-divider"></div>

        <div className="studio-zoom-controls">
          <button className="studio-icon-btn" onClick={() => setZoom((z) => Math.max(0.05, z / 1.25))}>
            <ZoomOut size={16} />
          </button>
          <span className="studio-zoom-text font-mono">{Math.round(zoom * 100)}%</span>
          <button className="studio-icon-btn" onClick={() => setZoom((z) => Math.min(4.0, z * 1.25))}>
            <ZoomIn size={16} />
          </button>
          <button className="studio-icon-btn" onClick={() => fitToScreen()} title="Fit to screen">
            <Maximize2 size={16} />
          </button>
        </div>

        <div className="studio-actions">
          <button
            className="btn-import-json"
            onClick={() => setIsJsonModalOpen(true)}
            title="Paste or import JSON bounding box coordinates"
          >
            <FileCode size={15} />
            <span>Import JSON</span>
          </button>

          <button
            className="btn-save-train-header"
            disabled={boxes.length === 0 || isSavingDataset}
            onClick={handleSaveActiveLearning}
          >
            <Save size={15} />
            <span>Approve &amp; Train ({boxes.length})</span>
          </button>
        </div>
      </div>

      {/* Main Studio Body */}
      <div className="studio-body">
        
        {/* Left Sidebar */}
        <aside className="studio-sidebar left-sidebar">
          <div className="studio-tabs">
            <button
              className={`studio-tab ${activeTab === 'screenshots' ? 'active' : ''}`}
              onClick={() => setActiveTab('screenshots')}
            >
              <ImageIcon size={14} />
              <span>Screenshots</span>
            </button>
            <button
              className={`studio-tab ${activeTab === 'library' ? 'active' : ''}`}
              onClick={() => setActiveTab('library')}
            >
              <Layers size={14} />
              <span>Icons ({icons.length})</span>
            </button>
          </div>

          {activeTab === 'screenshots' ? (
            <div className="studio-pane">
              <input
                type="file"
                ref={fileInputRef}
                accept="image/*"
                style={{ display: 'none' }}
                onChange={handleUpload}
              />
              <div className="studio-dropzone" onClick={() => fileInputRef.current?.click()}>
                <UploadCloud size={24} className="text-cyan" />
                <p><strong>Click to upload</strong> screenshot</p>
                <span>Supports 4K / Retina PNG</span>
              </div>

              <div className="studio-section-header">
                <span>Available Screenshots</span>
                <button className="studio-icon-btn-sm" onClick={fetchScreenshots}>
                  <RefreshCw size={12} />
                </button>
              </div>

              <div className="studio-item-list custom-scroll">
                {screenshots.map((s) => (
                  <div
                    key={s.name}
                    className={`studio-screenshot-card ${s.name === currentFilename ? 'active' : ''}`}
                    onClick={() => selectScreenshot(s)}
                  >
                    <img src={getFullUrl(s.url)} alt={s.name} />
                    <div className="studio-item-meta">
                      <span className="studio-item-title">{s.name}</span>
                      <div className="studio-item-sub font-mono">
                        <span>{(s.size / 1024 / 1024).toFixed(2)} MB</span>
                        {s.has_annotation && (
                          <span className="annotated-badge">Annotated</span>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="studio-pane">
              <div className="studio-section-header">
                <span>Saved Reference Icons</span>
                <button className="studio-icon-btn-sm" onClick={fetchIcons}>
                  <RefreshCw size={12} />
                </button>
              </div>
              <div className="studio-icons-grid custom-scroll">
                {icons.map((ic) => (
                  <div key={ic.filename} className="studio-icon-card">
                    <button
                      className="studio-icon-del"
                      onClick={() => handleDeleteIcon(ic.filename)}
                      title="Delete icon"
                    >
                      &times;
                    </button>
                    <img src={`${getFullUrl(ic.url)}?t=${Date.now()}`} alt={ic.name} />
                    <span className="studio-icon-name">{ic.name}</span>
                    <span className="studio-icon-dim font-mono">{ic.width}×{ic.height}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </aside>

        {/* Center Canvas Viewport */}
        <section
          className="studio-viewport"
          ref={viewportRef}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onWheel={handleWheel}
          style={{ cursor: tool === 'pan' ? 'grab' : 'crosshair' }}
        >
          {currentImageUrl ? (
            <div
              className="studio-canvas-container"
              ref={canvasContainerRef}
              style={{
                transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
                transformOrigin: '0 0',
                position: 'absolute',
                top: 0,
                left: 0,
              }}
            >
              {/* Native lossless image rendering */}
              <img
                ref={mainImageRef}
                src={currentImageUrl}
                alt="Selected screenshot"
                crossOrigin="anonymous"
                draggable={false}
                onLoad={onImageLoaded}
                style={{
                  display: 'block',
                  userSelect: 'none',
                  pointerEvents: 'none',
                  maxWidth: 'none',
                }}
              />

              {/* Render Drawn & Detected Bounding Boxes */}
              {boxes.map((box) => {
                const isConfirmed = box.status === 'confirmed';
                const isSelected = box.id === selectedBoxId;

                return (
                  <div
                    key={box.id}
                    className={`studio-drawn-box ${isSelected ? 'selected' : ''} ${box.status}`}
                    style={{
                      left: `${box.x}px`,
                      top: `${box.y}px`,
                      width: `${box.width}px`,
                      height: `${box.height}px`,
                    }}
                    onMouseDown={(e) => handleStartMoveBox(box, e)}
                    onClick={(e) => {
                      e.stopPropagation();
                      setSelectedBoxId(box.id);
                    }}
                  >
                    <span className={`studio-box-label font-mono ${box.status}`}>
                      {box.name || 'unnamed'}
                      {box.confidence ? ` (${box.confidence}%)` : ''}
                      {isConfirmed ? ' ✓' : ''}
                    </span>

                    {isSelected && (
                      <>
                        <div
                          className="studio-resize-handle nw"
                          onMouseDown={(e) => handleStartResizeBox(box, 'nw', e)}
                          title="Resize top-left"
                        />
                        <div
                          className="studio-resize-handle n"
                          onMouseDown={(e) => handleStartResizeBox(box, 'n', e)}
                          title="Resize top"
                        />
                        <div
                          className="studio-resize-handle ne"
                          onMouseDown={(e) => handleStartResizeBox(box, 'ne', e)}
                          title="Resize top-right"
                        />
                        <div
                          className="studio-resize-handle e"
                          onMouseDown={(e) => handleStartResizeBox(box, 'e', e)}
                          title="Resize right"
                        />
                        <div
                          className="studio-resize-handle se"
                          onMouseDown={(e) => handleStartResizeBox(box, 'se', e)}
                          title="Resize bottom-right"
                        />
                        <div
                          className="studio-resize-handle s"
                          onMouseDown={(e) => handleStartResizeBox(box, 's', e)}
                          title="Resize bottom"
                        />
                        <div
                          className="studio-resize-handle sw"
                          onMouseDown={(e) => handleStartResizeBox(box, 'sw', e)}
                          title="Resize bottom-left"
                        />
                        <div
                          className="studio-resize-handle w"
                          onMouseDown={(e) => handleStartResizeBox(box, 'w', e)}
                          title="Resize left"
                        />
                      </>
                    )}
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="studio-empty-boxes">
              <Sparkles size={36} className="text-cyan" />
              <p>Select a screenshot on the left to start drawing bounding boxes.</p>
            </div>
          )}

          {/* Infobar */}
          <div className="studio-infobar">
            <span><strong>File:</strong> {currentFilename || 'None'}</span>
            <span><strong>Res:</strong> {imageDim.width > 0 ? `${imageDim.width}×${imageDim.height}` : '0×0'}</span>
            <span><strong>Cursor:</strong> {cursorPos.x}, {cursorPos.y}</span>
            <span><strong>Items:</strong> {boxes.length} ({boxes.filter(b => b.status === 'confirmed').length} verified)</span>
          </div>
        </section>

        {/* Right Sidebar: Human-in-the-loop Box Manager */}
        <aside className="studio-sidebar right-sidebar">
          <div className="studio-section-header pad-header">
            <span>Detected &amp; Crops ({boxes.length})</span>
            <div className="header-actions-group">
              {boxes.length > 0 && (
                <>
                  <button
                    className="studio-action-pill text-cyan"
                    onClick={handleExportJson}
                    title="Copy bounding boxes JSON coordinates to clipboard"
                  >
                    <Copy size={11} />
                    <span>JSON</span>
                  </button>
                  <button
                    className="studio-action-pill text-emerald"
                    onClick={handleConfirmAll}
                    title="Mark all as confirmed"
                  >
                    <Check size={11} />
                    <span>All</span>
                  </button>
                  <button
                    className="studio-action-pill text-rose"
                    onClick={() => {
                      setBoxes([]);
                      setSelectedBoxId(null);
                    }}
                    title="Clear list"
                  >
                    <Trash2 size={11} />
                    <span>Clear</span>
                  </button>
                </>
              )}
            </div>
          </div>

          <div className="studio-box-list custom-scroll">
            {boxes.length === 0 ? (
              <div className="studio-empty-boxes">
                <Sparkles size={24} className="text-dim" />
                <p>Click "Run AI Detection", drag to crop units, or click "Import JSON".</p>
              </div>
            ) : (
              boxes.map((box) => (
                <div
                  key={box.id}
                  className={`studio-box-item ${box.id === selectedBoxId ? 'selected' : ''} ${box.status}`}
                  onClick={() => setSelectedBoxId(box.id)}
                >
                  <img
                    src={box.previewUrl || generateBoxPreview(box)}
                    alt="crop"
                    className="studio-box-thumb"
                  />
                  <div className="studio-box-item-body">
                    <div className="box-name-row">
                      <input
                        type="text"
                        className="studio-box-name-input"
                        value={box.name}
                        placeholder="champion_name"
                        onChange={(e) => {
                          const val = e.target.value;
                          setBoxes((prev) =>
                            prev.map((b) =>
                              b.id === box.id
                                ? { ...b, name: val, status: 'corrected' }
                                : b,
                            ),
                          );
                        }}
                      />
                      {box.status === 'confirmed' ? (
                        <span className="badge-confirmed" title="Verified Ground Truth">
                          <Check size={12} />
                        </span>
                      ) : (
                        <button
                          className="btn-confirm-single"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleConfirmBox(box.id);
                          }}
                          title="Confirm as correct"
                        >
                          <Check size={12} />
                        </button>
                      )}
                    </div>

                    <div className="studio-box-meta">
                      <span className={`status-pill ${box.status}`}>
                        {box.confidence ? `${box.confidence}% match` : box.status}
                      </span>
                      <span className="font-mono">
                        {Math.round(box.width)}×{Math.round(box.height)} px
                      </span>
                      <button
                        className="studio-icon-btn-sm text-rose"
                        onClick={(e) => {
                          e.stopPropagation();
                          setBoxes((prev) => prev.filter((b) => b.id !== box.id));
                        }}
                        title="Remove false positive"
                      >
                        <Trash2 size={13} />
                      </button>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>

          <div className="studio-footer-action">
            <button
              className="btn btn-primary btn-block glow-btn"
              disabled={boxes.length === 0 || isSavingDataset}
              onClick={handleSaveActiveLearning}
            >
              <CheckCircle2 size={16} />
              <span>
                {isSavingDataset
                  ? 'Training Templates...'
                  : `Save & Train Feedback (${boxes.length})`}
              </span>
            </button>
          </div>
        </aside>

      </div>

      {/* JSON Import Modal */}
      {isJsonModalOpen && (
        <div className="modal-overlay" onClick={() => setIsJsonModalOpen(false)}>
          <div className="json-modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="json-modal-header">
              <div className="json-modal-title">
                <FileCode size={18} className="text-cyan" />
                <h3>Import / Paste Coordinates</h3>
              </div>
              <button className="modal-btn-close" onClick={() => setIsJsonModalOpen(false)}>
                <X size={18} />
              </button>
            </div>

            <div className="json-modal-body">
              <p className="json-modal-desc">
                Paste Python dictionary coordinates (e.g. <code>crops = &#123; "draven": (0.13, 0.41, 0.29, 0.53) &#125;</code>) or JSON boxes array:
              </p>

              <textarea
                className="json-textarea font-mono"
                rows={12}
                placeholder={`{\n  "draven": [0.13, 0.41, 0.29, 0.53],\n  "kayle": [0.35, 0.31, 0.48, 0.38]\n}`}
                value={jsonInputText}
                onChange={(e) => setJsonInputText(e.target.value)}
              />
            </div>

            <div className="json-modal-footer">
              <button className="btn btn-ghost" onClick={() => setIsJsonModalOpen(false)}>
                Cancel
              </button>
              <button
                className="btn btn-primary glow-btn"
                disabled={!jsonInputText.trim()}
                onClick={handleParseAndApplyJson}
              >
                Apply to Canvas &amp; Update UI
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Toast */}
      {toast && (
        <div className={`studio-toast ${toast.type}`}>
          <span>{toast.msg}</span>
        </div>
      )}
    </div>
  );
};
