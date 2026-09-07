<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue';
import {
  ArrowLeft,
  ChevronRight,
  Swords,
  ImageIcon,
  Layers,
} from 'lucide-vue-next';
import { api } from '../services/api';
import type { Match, RoundSnapshot, TftChampionAsset } from '../types';
import ScreenshotViewer from './ScreenshotViewer.vue';
const props = defineProps<{ matchId: number; roundId: number | null }>();
const emit = defineEmits<{
  (e: 'back'): void;
  (e: 'round', id: number | null): void;
  (e: 'addRound'): void;
}>();
const match = ref<Match | null>(null);
const rounds = ref<RoundSnapshot[]>([]);
const selected = ref<RoundSnapshot | null>(null);
const champions = ref<TftChampionAsset[]>([]);
const loading = ref(false);
const roundLoading = ref(false);
const error = ref('');
const roundError = ref('');
const imageError = ref('');
const imageUrl = ref<string | null>(null);
const viewer = ref<InstanceType<typeof ScreenshotViewer> | null>(null);
const heading = ref<HTMLElement | null>(null);
let loadVersion = 0;
let roundVersion = 0;
const board = computed(() => selected.value?.boardStateDrafts?.[0]);
const units = computed(() => board.value?.boardState?.units ?? []);
const groups = computed(() =>
  [...new Set(rounds.value.map((r) => r.stage))].map((stage) => ({
    stage,
    rounds: rounds.value.filter((r) => r.stage === stage),
  })),
);
const cells = computed(() =>
  Array.from({ length: 28 }, (_, i) => ({
    row: Math.floor(i / 7),
    column: i % 7,
    unit: units.value.find(
      (u) => u.row === Math.floor(i / 7) && u.column === i % 7,
    ),
  })),
);
const normalize = (value: string) =>
  value.toLowerCase().replace(/[^a-z0-9]/g, '');
function asset(name: string) {
  return champions.value.find((c) => normalize(c.name) === normalize(name));
}
function stars(value?: string | null) {
  return '★'.repeat(Number(value?.match(/[123]/)?.[0] ?? 0));
}
function date(value?: string) {
  return value && !Number.isNaN(Date.parse(value))
    ? new Date(value).toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
      })
    : 'Date unavailable';
}
function clearImage() {
  if (imageUrl.value) URL.revokeObjectURL(imageUrl.value);
  imageUrl.value = null;
}
async function load() {
  const version = ++loadVersion;
  ++roundVersion;
  loading.value = true;
  error.value = '';
  selected.value = null;
  clearImage();
  try {
    const [m, r] = await Promise.all([
      api.getMatch(props.matchId),
      api.getRounds(props.matchId),
    ]);
    if (version !== loadVersion) return;
    match.value = m;
    rounds.value = r.sort(
      (a, b) => a.stage - b.stage || a.roundNumber - b.roundNumber,
    );
    await loadRound();
  } catch {
    if (version === loadVersion)
      error.value =
        'This match could not be loaded. It may have been deleted, or your session may have expired.';
  } finally {
    if (version === loadVersion) loading.value = false;
  }
}
async function loadRound() {
  const version = ++roundVersion;
  selected.value = null;
  roundError.value = '';
  imageError.value = '';
  clearImage();
  roundLoading.value = false;
  if (!props.roundId) return;
  roundLoading.value = true;
  try {
    const result = await api.getRound(props.matchId, props.roundId);
    if (version !== roundVersion) return;
    selected.value = result;
    await nextTick();
    heading.value?.focus();
    const draft = result.boardStateDrafts?.[0];
    if (draft) {
      try {
        const blob = await api.getScreenshot(draft.id);
        if (version === roundVersion)
          imageUrl.value = URL.createObjectURL(blob);
      } catch {
        if (version === roundVersion)
          imageError.value =
            'Original screenshot unavailable. Your saved board is still shown.';
      }
    }
  } catch {
    if (version === roundVersion)
      roundError.value = 'Could not load this round. Please retry.';
  } finally {
    if (version === roundVersion) roundLoading.value = false;
  }
}
watch(() => props.matchId, load, { immediate: true });
watch(() => props.roundId, loadRound);
api
  .getSetChampions(18)
  .then((data) => (champions.value = data.champions))
  .catch(() => {});
onBeforeUnmount(() => {
  ++loadVersion;
  ++roundVersion;
  clearImage();
});
</script>

<template>
  <section class="match-detail">
    <nav class="detail-breadcrumb" aria-label="Breadcrumb">
      <button @click="emit('back')">
        <ArrowLeft :size="16" aria-hidden="true" /> Match history
      </button>
      <ChevronRight :size="14" aria-hidden="true" /><button
        @click="emit('round', null)"
      >
        Match #{{ matchId }}
      </button>
      <template v-if="selected"
        ><ChevronRight :size="14" aria-hidden="true" /><span
          >Round {{ selected.stage }}-{{ selected.roundNumber }}</span
        ></template
      >
    </nav>
    <div v-if="error" class="detail-empty" role="alert">
      <p>{{ error }}</p>
      <button @click="load">Retry</button>
    </div>
    <div v-else-if="loading" class="detail-empty" role="status">
      Loading match timeline…
    </div>
    <template v-else-if="match">
      <header class="detail-hero">
        <div class="detail-placement">#{{ match.placement }}</div>
        <div>
          <p class="detail-eyebrow">
            {{
              match.placement === 1
                ? 'VICTORY'
                : match.placement <= 4
                  ? 'TOP FOUR'
                  : 'MATCH REVIEW'
            }}
          </p>
          <h1>{{ match.comp || `Match #${match.id}` }}</h1>
          <p>
            {{ date(match.playedAt || match.createdAt) }}
            <span v-if="match.version"> · Patch {{ match.version }}</span>
          </p>
        </div>
        <div class="detail-total">
          <strong>{{ rounds.length }}</strong
          ><span>saved rounds</span>
        </div>
      </header>
      <div v-if="!rounds.length" class="detail-empty">
        <Layers :size="32" aria-hidden="true" />
        <h2>Your timeline starts with one round</h2>
        <p>
          Upload a screenshot in Board Review, confirm its values, then save it
          to this match.
        </p>
        <button @click="emit('addRound')">Open Board Review</button>
      </div>
      <div v-else class="detail-layout">
        <aside class="round-timeline" aria-label="Saved rounds">
          <header>
            <h2>Round timeline</h2>
            <span>{{ rounds.length }} saved</span>
          </header>
          <div
            v-for="group in groups"
            :key="group.stage"
            class="timeline-stage"
          >
            <h3>STAGE {{ group.stage }}</h3>
            <button
              v-for="round in group.rounds"
              :key="round.id"
              :class="{ selected: roundId === round.id }"
              :aria-current="roundId === round.id ? 'step' : undefined"
              @click="emit('round', round.id)"
            >
              <span class="round-number"
                >{{ round.stage }}-{{ round.roundNumber }}</span
              ><span class="round-mini"
                >Lv. {{ round.level
                }}<small>{{ round.hp }} HP · {{ round.gold }} gold</small></span
              ><ChevronRight :size="16" aria-hidden="true" />
            </button>
          </div>
        </aside>
        <div class="round-content">
          <div v-if="roundError" class="detail-empty" role="alert">
            <p>{{ roundError }}</p>
            <button @click="loadRound">Retry round</button>
          </div>
          <div v-else-if="!selected" class="detail-empty" role="status">
            <Swords :size="32" aria-hidden="true" />
            <h2>
              {{
                roundLoading
                  ? 'Loading round…'
                  : 'Review your game, round by round'
              }}
            </h2>
            <p>
              Select a saved round to see its champions, positions, stars, and
              player state.
            </p>
            <button v-if="!roundId" @click="emit('round', rounds[0].id)">
              Review first round <ChevronRight :size="16" aria-hidden="true" />
            </button>
          </div>
          <template v-else>
            <header class="round-heading">
              <div>
                <p class="detail-eyebrow">SAVED SNAPSHOT</p>
                <h2 ref="heading" tabindex="-1">
                  Round {{ selected.stage }}-{{ selected.roundNumber }}
                </h2>
              </div>
              <span>Read-only review</span>
            </header>
            <dl class="round-stats">
              <div>
                <dt>Level</dt>
                <dd>{{ selected.level }}</dd>
              </div>
              <div>
                <dt>Health</dt>
                <dd>{{ selected.hp }} <small>HP</small></dd>
              </div>
              <div>
                <dt>Gold</dt>
                <dd>{{ selected.gold }}</dd>
              </div>
              <div>
                <dt>Streak</dt>
                <dd>
                  {{ Math.abs(selected.streak) }}
                  <small>{{
                    selected.streak > 0
                      ? 'wins'
                      : selected.streak < 0
                        ? 'losses'
                        : 'streak'
                  }}</small>
                </dd>
              </div>
            </dl>
            <section class="saved-board">
              <header>
                <h3>
                  <Swords :size="18" aria-hidden="true" /> Team positioning
                </h3>
                <span>{{ units.length }} champions</span>
              </header>
              <template v-if="units.length"
                ><p class="board-direction">FRONTLINE</p>
                <div class="saved-hex-board">
                  <div
                    v-for="cell in cells"
                    :key="`${cell.row}-${cell.column}`"
                    class="saved-hex"
                    :class="{ offset: cell.row % 2, occupied: cell.unit }"
                    :title="`Row ${cell.row + 1}, hex ${cell.column + 1}`"
                  >
                    <template v-if="cell.unit"
                      ><img
                        v-if="asset(cell.unit.champion)?.imageUrl"
                        :src="asset(cell.unit.champion)!.imageUrl!"
                        alt=""
                        loading="lazy"
                      /><span class="saved-stars">{{
                        stars(cell.unit.star)
                      }}</span
                      ><span class="saved-name">{{
                        cell.unit.champion
                      }}</span></template
                    ><span v-else class="empty-hex">·</span>
                  </div>
                </div>
                <p class="board-direction">BACKLINE</p></template
              >
              <div v-else class="detail-empty">
                <p>
                  No champion board was saved for this round. Player stats are
                  available above.
                </p>
              </div>
            </section>
            <div v-if="units.length" class="saved-lineup">
              <div v-for="unit in units" :key="`${unit.row}-${unit.column}`">
                <span>{{ stars(unit.star) }}</span
                ><strong>{{ unit.champion }}</strong
                ><small
                  >Row {{ unit.row + 1 }} · Hex {{ unit.column + 1 }}</small
                >
              </div>
            </div>
            <section v-if="board" class="saved-screenshot">
              <header>
                <h3>
                  <ImageIcon :size="18" aria-hidden="true" /> Original
                  screenshot
                </h3>
                <span>Click to enlarge</span>
              </header>
              <button
                v-if="imageUrl"
                @click="viewer?.open()"
                aria-label="Enlarge original screenshot"
              >
                <img
                  :src="imageUrl"
                  alt="Original TFT screenshot for this saved round"
                />
              </button>
              <p v-else role="status">
                {{ imageError || 'Loading screenshot…' }}
              </p>
            </section>
          </template>
        </div>
      </div>
    </template>
    <ScreenshotViewer
      ref="viewer"
      :src="imageUrl"
      :filename="board?.originalFilename ?? null"
    />
  </section>
</template>

<style scoped>
.match-detail {
  --panel: #24252f;
  --deep: #1c1d25;
  --line: #424451;
  --ink: #f0f0f6;
  --muted: #b4b5c4;
  --accent: #bda7ff;
  color: var(--ink);
}
.match-detail button {
  font: inherit;
  color: inherit;
  cursor: pointer;
}
.match-detail button:focus-visible {
  outline: 3px solid var(--accent);
  outline-offset: 3px;
}
.detail-breadcrumb {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 20px;
  color: var(--muted);
  font-size: 14px;
}
.detail-breadcrumb button {
  display: flex;
  align-items: center;
  gap: 8px;
  background: none;
  border: 0;
  min-height: 44px;
}
.detail-hero {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 28px;
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 12px;
  margin-bottom: 24px;
}
.detail-placement {
  color: #ffd16a;
  font-size: 48px;
  font-weight: 800;
}
.detail-eyebrow {
  color: var(--accent);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 1.5px;
  margin: 0 0 6px;
}
h1 {
  font-size: 26px;
  margin: 0 0 6px;
  overflow-wrap: anywhere;
}
h2 {
  font-size: 20px;
  margin: 0;
}
h3 {
  margin: 0;
  font-size: 15px;
}
.detail-hero p:not(.detail-eyebrow) {
  color: var(--muted);
  margin: 0;
  font-size: 14px;
}
.detail-total {
  margin-left: auto;
  display: grid;
  text-align: right;
  gap: 4px;
  flex-shrink: 0;
}
.detail-total strong {
  font-size: 28px;
}
.detail-total span {
  color: var(--muted);
  font-size: 13px;
}
.detail-layout {
  display: grid;
  grid-template-columns: 250px minmax(0, 1fr);
  gap: 24px;
  align-items: start;
}
.round-timeline {
  border: 1px solid var(--line);
  border-radius: 10px;
  background: var(--deep);
  overflow: hidden;
}
.round-timeline header,
.saved-board header,
.saved-screenshot header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 18px;
  border-bottom: 1px solid var(--line);
}
.round-timeline h2 {
  font-size: 15px;
}
header > span {
  color: var(--muted);
  font-size: 12px;
}
.timeline-stage {
  padding: 16px 12px;
}
.timeline-stage h3 {
  color: var(--muted);
  font-size: 10px;
  letter-spacing: 2px;
  margin: 0 6px 10px;
}
.timeline-stage button {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 12px;
  text-align: left;
  border: 1px solid transparent;
  border-radius: 6px;
  padding: 14px 10px;
  background: transparent;
  margin-top: 6px;
}
.timeline-stage button:hover {
  background: var(--panel);
}
.timeline-stage button.selected {
  border-color: var(--accent);
  background: #352e48;
}
.round-number {
  font-size: 20px;
  font-weight: 700;
}
.round-mini {
  display: grid;
  gap: 4px;
  flex: 1;
  font-size: 13px;
}
.round-mini small {
  color: var(--muted);
  font-size: 11px;
}
.round-content {
  min-width: 0;
  display: grid;
  gap: 18px;
}
.round-heading {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}
.round-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  margin: 0;
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 8px;
}
.round-stats div {
  padding: 18px;
}
dt {
  color: var(--muted);
  font-size: 12px;
  margin-bottom: 8px;
}
dd {
  margin: 0;
  font-size: 24px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}
dd small {
  color: var(--muted);
  font-size: 12px;
  font-weight: 400;
}
.saved-board,
.saved-screenshot {
  background: var(--deep);
  border: 1px solid var(--line);
  border-radius: 10px;
  overflow: hidden;
}
.saved-board h3,
.saved-screenshot h3 {
  display: flex;
  align-items: center;
  gap: 8px;
}
.board-direction {
  text-align: center;
  letter-spacing: 3px;
  font-size: 10px;
  color: var(--muted);
  padding: 14px;
}
.saved-hex-board {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 8px 5px;
  padding: 0 7% 0 3%;
}
.saved-hex {
  aspect-ratio: 0.9;
  clip-path: polygon(50% 0, 100% 25%, 100% 75%, 50% 100%, 0 75%, 0 25%);
  background: #30323f;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}
.saved-hex.offset {
  transform: translateX(50%);
}
.saved-hex img {
  position: absolute;
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.saved-stars {
  position: absolute;
  top: 12%;
  color: #ffd16a;
  text-shadow: 0 1px 4px #000;
  font-size: clamp(10px, 1.5vw, 20px);
}
.saved-name {
  position: absolute;
  bottom: 21%;
  width: 100%;
  background: #000b;
  text-align: center;
  color: white;
  font-size: clamp(7px, 1vw, 12px);
  line-height: 1.4;
}
.empty-hex {
  color: #727483;
}
.saved-lineup {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.saved-lineup div {
  display: grid;
  gap: 4px;
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 6px;
  padding: 10px 14px;
}
.saved-lineup span {
  color: #ffd16a;
  font-size: 12px;
}
.saved-lineup strong {
  font-size: 13px;
}
.saved-lineup small {
  color: var(--muted);
  font-size: 11px;
}
.saved-screenshot button {
  display: block;
  border: 0;
  padding: 0;
  width: 100%;
  background: transparent;
}
.saved-screenshot img {
  display: block;
  width: 100%;
  max-height: 300px;
  object-fit: contain;
}
.saved-screenshot p {
  padding: 16px;
  color: var(--muted);
}
.detail-empty {
  display: flex;
  align-items: center;
  flex-direction: column;
  justify-content: center;
  text-align: center;
  min-height: 260px;
  padding: 32px;
  gap: 16px;
  background: var(--deep);
  border: 1px solid var(--line);
  border-radius: 10px;
}
.detail-empty p {
  max-width: 480px;
  color: var(--muted);
  line-height: 1.6;
  margin: 0;
}
.detail-empty button {
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 44px;
  padding: 10px 18px;
  background: #7750d7;
  border: 1px solid var(--accent);
  border-radius: 6px;
}
@media (max-width: 760px) {
  .detail-layout {
    grid-template-columns: 1fr;
  }
  .detail-hero {
    padding: 18px;
    gap: 14px;
  }
  .detail-placement {
    font-size: 32px;
  }
  h1 {
    font-size: 20px;
  }
  .detail-total {
    font-size: 12px;
  }
  .timeline-stage {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }
  .timeline-stage h3 {
    width: 100%;
  }
  .timeline-stage button {
    width: auto;
    flex: 1 1 130px;
    margin: 0;
  }
  .round-stats div {
    padding: 12px;
  }
  dd {
    font-size: 20px;
  }
  .detail-empty {
    padding: 24px 16px;
  }
}
</style>
