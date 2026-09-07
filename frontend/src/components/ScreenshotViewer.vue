<script setup lang="ts">
import { onDeactivated, ref } from 'vue';
import { Maximize2, Minimize2, X } from 'lucide-vue-next';

defineProps<{ src: string | null; filename: string | null }>();
const dialog = ref<HTMLDialogElement | null>(null);
const actualSize = ref(false);
function open() {
  actualSize.value = false;
  dialog.value?.showModal();
}
function close() {
  dialog.value?.close();
}
function dismissBackdrop(event: MouseEvent) {
  if (!dialog.value || event.target !== dialog.value) return;
  const rect = dialog.value.getBoundingClientRect();
  if (
    event.clientX < rect.left ||
    event.clientX > rect.right ||
    event.clientY < rect.top ||
    event.clientY > rect.bottom
  )
    close();
}
onDeactivated(close);
defineExpose({ open });
</script>

<template>
  <dialog
    ref="dialog"
    class="screenshot-viewer"
    aria-labelledby="screenshot-viewer-title"
    @click="dismissBackdrop"
  >
    <header class="viewer-toolbar">
      <div>
        <h2 id="screenshot-viewer-title">Screenshot review</h2>
        <p>{{ filename || 'Uploaded screenshot' }}</p>
      </div>
      <div class="viewer-actions">
        <button
          type="button"
          :aria-pressed="actualSize"
          @click="actualSize = !actualSize"
        >
          <Minimize2
            v-if="actualSize"
            :size="17"
            aria-hidden="true"
          /><Maximize2 v-else :size="17" aria-hidden="true" />{{
            actualSize ? 'Fit to screen' : 'Actual size'
          }}
        </button>
        <button
          type="button"
          class="viewer-close"
          aria-label="Close screenshot preview"
          autofocus
          @click="close"
        >
          <X :size="20" aria-hidden="true" />
        </button>
      </div>
    </header>
    <div
      class="viewer-image-area"
      :class="{ 'actual-size': actualSize }"
      tabindex="0"
      aria-label="Screenshot image; scroll to review when viewing at actual size"
    >
      <img
        v-if="src"
        :src="src"
        :alt="
          filename
            ? `Board screenshot: ${filename}`
            : 'Uploaded TFT board screenshot'
        "
      />
    </div>
  </dialog>
</template>

<style scoped>
.screenshot-viewer {
  width: calc(100vw - 40px);
  max-width: 1600px;
  max-height: calc(100dvh - 40px);
  margin: auto;
  padding: 0;
  border: 1px solid #555665;
  border-radius: 12px;
  background: #20212a;
  color: #f5f5fa;
  box-shadow: 0 24px 90px #0008;
  overflow: hidden;
}
.screenshot-viewer::backdrop {
  background: #080910dd;
}
.viewer-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 18px;
  border-bottom: 1px solid #41424f;
  background: #30313d;
}
.viewer-toolbar > div:first-child {
  min-width: 0;
}
.viewer-toolbar h2 {
  font-size: 16px;
  line-height: 1.5;
}
.viewer-toolbar p {
  font-size: 12px;
  color: #c0c1d0;
  overflow-wrap: anywhere;
  max-height: 48px;
  overflow: auto;
}
.viewer-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}
.viewer-actions button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 44px;
  border: 1px solid #616273;
  border-radius: 6px;
  padding: 8px 12px;
  color: #f5f5fa;
  background: #262730;
  font: inherit;
  font-size: 13px;
  cursor: pointer;
}
.viewer-actions button:hover {
  background: #494052;
}
.viewer-actions .viewer-close {
  width: 44px;
  padding: 8px;
}
.viewer-image-area {
  overflow: auto;
  max-height: calc(100dvh - 134px);
  background: #111218;
  overscroll-behavior: contain;
}
.viewer-image-area img {
  display: block;
  width: 100%;
  max-height: calc(100dvh - 134px);
  object-fit: contain;
}
.viewer-image-area.actual-size img {
  width: auto;
  max-width: none;
  max-height: none;
  margin: auto;
}
.screenshot-viewer :focus-visible {
  outline: 3px solid #b9a4ff;
  outline-offset: -3px;
}
:global(body:has(.screenshot-viewer[open])) {
  overflow: hidden;
}
@media (max-width: 600px) {
  .screenshot-viewer {
    width: calc(100vw - 16px);
    max-height: calc(100dvh - 16px);
  }
  .viewer-toolbar {
    padding: 10px;
    gap: 8px;
  }
  .viewer-toolbar h2 {
    font-size: 14px;
  }
  .viewer-actions button {
    font-size: 11px;
    padding: 8px;
  }
  .viewer-actions button svg {
    flex-shrink: 0;
  }
  .viewer-image-area,
  .viewer-image-area img {
    max-height: calc(100dvh - 130px);
  }
}
</style>
