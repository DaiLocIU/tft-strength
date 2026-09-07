<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref } from 'vue';
import { Check, Search, X } from 'lucide-vue-next';
import type { TftChampionAsset } from '../types';

const props = defineProps<{
  champions: TftChampionAsset[];
  selected?: string;
  loading: boolean;
  stars?: number;
  disabled?: boolean;
}>();
const emit = defineEmits<{
  (event: 'select', champion: TftChampionAsset): void;
  (event: 'retry'): void;
  (event: 'stars', stars: number): void;
}>();
const panel = ref<HTMLElement | null>(null);
const search = ref<HTMLInputElement | null>(null);
const query = ref('');
const isOpen = ref(false);
const failedImages = ref(new Set<string>());
let anchor: HTMLElement | null = null;
const groups = computed(() => {
  const term = query.value.trim().toLowerCase();
  const filtered = props.champions.filter(
    (c) =>
      c.traits.length > 0 &&
      (!term || `${c.name} ${c.traits.join(' ')}`.toLowerCase().includes(term)),
  );
  const costs = [...new Set(filtered.map((c) => c.cost))].sort(
    (a, b) => (a ?? 99) - (b ?? 99),
  );
  return costs.map((cost) => ({
    cost,
    champions: filtered.filter((c) => c.cost === cost),
  }));
});
function position() {
  if (!panel.value || !anchor) return;
  const rect = anchor.getBoundingClientRect();
  const width = Math.min(1000, window.innerWidth - 24);
  panel.value.style.width = `${width}px`;
  panel.value.style.maxHeight = `${Math.min(620, window.innerHeight - 24)}px`;
  const height = panel.value.getBoundingClientRect().height;
  const below = rect.bottom + 10;
  const top =
    below + height <= window.innerHeight - 12
      ? below
      : Math.max(12, rect.top - height - 10);
  panel.value.style.left = `${Math.max(12, Math.min(rect.left - width / 3, window.innerWidth - width - 12))}px`;
  panel.value.style.top = `${Math.min(top, Math.max(12, window.innerHeight - height - 12))}px`;
}
async function open(target: HTMLElement) {
  anchor = target;
  query.value = '';
  await nextTick();
  panel.value?.showPopover();
  isOpen.value = true;
  position();
  search.value?.focus({ preventScroll: true });
}
function close(restoreFocus = true) {
  panel.value?.hidePopover();
  if (restoreFocus) anchor?.focus({ preventScroll: true });
}
function choose(champion: TftChampionAsset) {
  emit('select', champion);
  close();
}
function toggle(event: Event) {
  isOpen.value = (event as Event & { newState: string }).newState === 'open';
  window.removeEventListener('resize', position);
  if (isOpen.value) window.addEventListener('resize', position);
}
onBeforeUnmount(() => window.removeEventListener('resize', position));
defineExpose({ open, close, isOpen });
</script>

<template>
  <div
    ref="panel"
    id="board-champion-picker"
    popover="auto"
    role="dialog"
    aria-label="Choose champion"
    class="champion-picker"
    @toggle="toggle"
  >
    <header class="picker-header">
      <div>
        <h3>
          {{
            selected && selected !== 'unknown'
              ? 'Edit champion'
              : 'Choose champion'
          }}
        </h3>
        <p>Select a portrait to place it on this hex.</p>
      </div>
      <button
        class="picker-close"
        aria-label="Close champion picker"
        @click="close()"
      >
        <X :size="18" aria-hidden="true" />
      </button>
    </header>
    <section
      v-if="selected"
      class="picker-star-editor"
      aria-label="Champion star level"
    >
      <div class="star-champion">
        <strong>{{
          selected === 'unknown' ? 'Unknown champion' : selected
        }}</strong
        ><span role="status">{{
          stars ? `${stars}-star champion` : 'Star level needs review'
        }}</span>
      </div>
      <div class="star-options" role="group" aria-label="Set star level">
        <button
          v-for="level in [1, 2, 3]"
          :key="level"
          type="button"
          :aria-pressed="stars === level"
          :aria-label="`Set ${selected} to ${level} ${level === 1 ? 'star' : 'stars'}`"
          :disabled="disabled"
          @click="emit('stars', level)"
        >
          <span aria-hidden="true">{{ '★'.repeat(level) }}</span
          ><small>{{ level }} {{ level === 1 ? 'star' : 'stars' }}</small>
        </button>
      </div>
    </section>
    <label class="picker-search"
      ><Search :size="18" aria-hidden="true" /><span class="sr-label"
        >Search champions or traits</span
      ><input
        ref="search"
        v-model="query"
        type="search"
        placeholder="Search champions or traits…"
        autocomplete="off"
    /></label>
    <div class="picker-results">
      <p v-if="loading" class="picker-empty" role="status">
        Loading champions…
      </p>
      <template v-else>
        <section
          v-for="group in groups"
          :key="group.cost ?? 'other'"
          class="cost-group"
          :class="`cost-tier-${group.cost}`"
          :aria-label="
            group.cost == null
              ? 'Other champions'
              : `${group.cost} gold champions`
          "
        >
          <h4>{{ group.cost == null ? 'Other' : `${group.cost}-cost` }}</h4>
          <div class="portrait-grid">
            <button
              v-for="champion in group.champions"
              :key="champion.apiName"
              class="champion-choice"
              :aria-label="`${champion.name}, ${champion.cost ?? 'unknown'} gold`"
              :aria-pressed="selected === champion.name"
              :title="`${champion.name} · ${champion.traits.join(', ')}`"
              @click="choose(champion)"
            >
              <span class="portrait"
                ><img
                  v-if="
                    champion.imageUrl && !failedImages.has(champion.apiName)
                  "
                  :src="champion.imageUrl"
                  alt=""
                  loading="lazy"
                  @error="failedImages.add(champion.apiName)" /><span
                  v-else
                  class="portrait-fallback"
                  >{{ champion.name.slice(0, 2) }}</span
                ><Check
                  v-if="selected === champion.name"
                  class="selected-check"
                  :size="18"
                  aria-hidden="true" /></span
              ><span class="champion-label">{{ champion.name }}</span>
            </button>
          </div>
        </section>
        <div v-if="!groups.length" class="picker-empty" role="status">
          <p>
            {{
              champions.length
                ? `No champions match “${query}”.`
                : 'Champion data is unavailable.'
            }}
          </p>
          <button
            v-if="champions.length"
            class="picker-text-button"
            @click="
              query = '';
              search?.focus();
            "
          >
            Clear search</button
          ><button v-else class="picker-text-button" @click="emit('retry')">
            Retry loading champions
          </button>
        </div>
      </template>
    </div>
    <footer>Changes apply to your board · Esc to close</footer>
  </div>
</template>

<style scoped>
.picker-star-editor {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin: 0 18px 16px;
  padding: 14px;
  background: #1b1c24;
  border: 1px solid #555665;
  border-radius: 8px;
}
.star-champion strong {
  display: block;
  font-size: 14px;
}
.star-champion > span {
  display: block;
  color: #b9bacb;
  font-size: 12px;
  margin-top: 4px;
}
.star-options {
  display: flex;
  gap: 8px;
}
.star-options button {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 3px;
  min-width: 66px;
  min-height: 52px;
  border: 1px solid #656675;
  border-radius: 6px;
  background: #30313d;
  color: #f5c568;
  cursor: pointer;
  font: inherit;
  transition: background 0.15s;
}
.star-options small {
  color: #dddfea;
  font-size: 11px;
}
.star-options button[aria-pressed='true'] {
  border-color: #f5c568;
  background: #514329;
  box-shadow: inset 0 0 0 1px #f5c568;
}
.star-options button:hover:not(:disabled) {
  background: #544831;
}
.star-options button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
@media (max-width: 600px) {
  .picker-star-editor {
    margin: 0 12px 12px;
    padding: 12px;
  }
  .star-options {
    width: 100%;
  }
  .star-options button {
    flex: 1;
  }
}

.champion-picker {
  position: fixed;
  inset: auto;
  margin: 0;
  padding: 0;
  border: 1px solid #555665;
  border-radius: 10px;
  background: #262730;
  color: #f5f5fa;
  box-shadow: 0 20px 70px #0009;
  font: 14px/1.5 var(--font-sans, system-ui);
  overflow: auto;
  overscroll-behavior: contain;
  max-width: calc(100vw - 24px);
}
.picker-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding: 16px 18px 10px;
}
.picker-header h3 {
  font-size: 16px;
}
.picker-header p {
  font-size: 12px;
  color: #b9bacb;
  margin-top: 2px;
}
.picker-close {
  height: 36px;
  width: 36px;
  display: grid;
  place-items: center;
  flex-shrink: 0;
  background: #343540;
  color: #dddfea;
  border: 1px solid #555665;
  border-radius: 6px;
  cursor: pointer;
}
.picker-search {
  display: flex;
  align-items: center;
  gap: 10px;
  background: #1b1c24;
  border: 1px solid #555665;
  border-radius: 6px;
  margin: 0 18px 14px;
  padding: 0 12px;
  color: #b9bacb;
}
.picker-search input {
  min-width: 0;
  width: 100%;
  height: 42px;
  background: none;
  border: 0;
  color: #f5f5fa;
  font: inherit;
  outline: none;
}
.picker-search:focus-within {
  outline: 2px solid #b9a4ff;
  outline-offset: 2px;
}
.picker-search input::placeholder {
  color: #b9bacb;
}
.sr-label {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  overflow: hidden;
  clip-path: inset(50%);
  white-space: nowrap;
}
.cost-group {
  --tier: #a5acb7;
  display: grid;
  grid-template-columns: 64px minmax(0, 1fr);
  gap: 12px;
  padding: 14px 18px;
  background: #ffffff03;
}
.cost-group:nth-child(even) {
  background: #ffffff06;
}
.cost-group h4 {
  font-size: 13px;
  color: var(--tier);
  align-self: center;
  white-space: nowrap;
}
.cost-tier-2 {
  --tier: #63dc8b;
  background: #56b5720d !important;
}
.cost-tier-3 {
  --tier: #58b5ff;
  background: #479ce712 !important;
}
.cost-tier-4 {
  --tier: #ef82d4;
  background: #dd60c412 !important;
}
.cost-tier-5 {
  --tier: #ffc55b;
  background: #caa05112 !important;
}
.portrait-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  overflow-x: auto;
  padding: 2px 4px 8px;
  scrollbar-width: thin;
}
.champion-choice {
  flex: 0 0 62px;
  width: 62px;
  padding: 0;
  border: 0;
  background: none;
  color: #f5f5fa;
  font: inherit;
  cursor: pointer;
  border-radius: 7px;
  transition: background 0.15s;
}
.portrait {
  position: relative;
  display: block;
  width: 62px;
  height: 62px;
  border: 2px solid var(--tier);
  border-radius: 8px;
  overflow: hidden;
  background: #1b1c24;
}
.portrait img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.portrait-fallback {
  display: grid;
  place-items: center;
  height: 100%;
  font-size: 20px;
  color: var(--tier);
}
.champion-label {
  display: block;
  font-size: 11px;
  font-weight: 600;
  line-height: 1.3;
  margin-top: 5px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.champion-choice:hover .portrait {
  box-shadow: inset 0 0 0 2px #fff;
  filter: brightness(1.2);
}
.champion-choice[aria-pressed='true'] {
  background: #ffffff19;
  outline: 2px solid #fff;
  outline-offset: 4px;
}
.selected-check {
  position: absolute;
  right: 2px;
  top: 2px;
  background: #16151e;
  border-radius: 50%;
  color: white;
  padding: 2px;
}
.champion-picker button:focus-visible {
  outline: 3px solid #b9a4ff;
  outline-offset: 3px;
}
.picker-empty {
  padding: 28px 18px;
  text-align: center;
  color: #c7c8d8;
}
.picker-text-button {
  min-height: 40px;
  background: none;
  border: 0;
  color: #c5b2ff;
  font: inherit;
  cursor: pointer;
}
footer {
  padding: 10px 18px;
  font-size: 11px;
  color: #b9bacb;
  border-top: 1px solid #444550;
}
@media (max-width: 600px) {
  .cost-group {
    grid-template-columns: 1fr;
    gap: 10px;
    padding: 12px;
  }
  .portrait-grid {
    gap: 12px;
  }
  .champion-choice,
  .portrait {
    width: 58px;
  }
  .champion-choice {
    flex-basis: 58px;
  }
  .portrait {
    height: 58px;
  }
  .picker-search input {
    font-size: 16px;
  }
  .picker-header {
    padding: 12px;
  }
  .picker-search {
    margin: 0 12px 12px;
  }
  .picker-close {
    width: 44px;
    height: 44px;
  }
}
@media (prefers-reduced-motion: reduce) {
  .champion-choice {
    transition: none;
  }
}
</style>
