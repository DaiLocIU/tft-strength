<script setup lang="ts">
import {
  computed,
  nextTick,
  onActivated,
  onBeforeUnmount,
  onMounted,
  reactive,
  ref,
  watch,
} from 'vue';
import {
  CheckCircle2,
  ImageUp,
  Loader2,
  ScanLine,
  Sparkles,
  Plus,
  Swords,
  Shield,
  ChevronRight,
  X,
} from 'lucide-vue-next';
import ScreenshotViewer from './ScreenshotViewer.vue';
import ChampionPicker from './ChampionPicker.vue';
import { api } from '../services/api';
import {
  BoardState,
  BoardStateDraft,
  BoardStateUnit,
  TftChampionAsset,
  User,
  Match,
  BoardGuide,
} from '../types';

const props = defineProps<{
  user: User | null;
}>();

const emit = defineEmits<{ (e: 'viewGames'): void }>();
const games = ref<Match[]>([]);
const gamesLoading = ref(false);
const saveError = ref('');
const saved = ref(false);
const saving = ref(false);
const selectedHex = ref<string | null>(null);
const confirmed = ref(false);
const round = reactive({
  matchId: 0,
  stage: '' as number | '',
  roundNumber: '' as number | '',
  gold: '' as number | '',
  hp: '' as number | '',
  level: '' as number | '',
  streak: '' as number | '',
});
const guide = ref<BoardGuide | null>(null);
const guidePanel = ref<HTMLElement | null>(null);
const analyzing = ref(false);
const guideError = ref('');
let reviewRevision = 0;
const validRound = computed(() =>
  [
    [round.stage, 1, 9],
    [round.roundNumber, 1, 7],
    [round.level, 1, 11],
    [round.hp, 0, 100],
    [round.gold, 0, 999],
    [round.streak, -99, 99],
  ].every(
    ([value, min, max]) =>
      typeof value === 'number' &&
      Number.isInteger(value) &&
      value >= Number(min) &&
      value <= Number(max),
  ),
);
function contextPayload() {
  return {
    stage: Number(round.stage),
    roundNumber: Number(round.roundNumber),
    level: Number(round.level),
    hp: Number(round.hp),
    gold: Number(round.gold),
    streak: Number(round.streak),
  };
}
async function analyzeBoard() {
  if (
    !draft.value ||
    !validRound.value ||
    !validUnits.value ||
    !confirmed.value ||
    analyzing.value ||
    detecting.value
  )
    return;
  analyzing.value = true;
  guideError.value = '';
  const revision = reviewRevision;
  try {
    const result = await api.analyzeBoard(draft.value.id, {
      ...contextPayload(),
      units: boardState.value!.units.map((u) => ({
        row: u.row,
        column: u.column,
        champion: u.champion,
        stars: starCount(u),
      })),
    });
    if (revision === reviewRevision) {
      guide.value = result;
      await nextTick();
      guidePanel.value?.focus();
    }
  } catch {
    guideError.value =
      'Could not generate the guide. Your review is preserved; please retry.';
  } finally {
    analyzing.value = false;
  }
}
function fieldStatus(field: 'round' | 'level' | 'gold' | 'hp' | 'streak') {
  const prediction = boardState.value?.hud?.[field];
  if (!prediction || prediction.value === null) {
    const hasValue =
      field === 'round'
        ? round.stage !== '' && round.roundNumber !== ''
        : round[field] !== '';
    return hasValue ? 'Entered by you' : 'Not detected · enter manually';
  }
  const current =
    field === 'round' ? `${round.stage}-${round.roundNumber}` : round[field];
  return String(current) === String(prediction.value)
    ? 'Detected · check value'
    : 'Edited by you';
}
const selectedUnit = computed(() =>
  boardState.value?.units.find(
    (u) => hexKey(u.row, u.column) === selectedHex.value,
  ),
);
const traits = computed(() => {
  const counts = new Map<string, number>();
  const seen = new Set<string>();
  for (const unit of boardState.value?.units ?? []) {
    const asset = championByName.value.get(normalizeName(unit.champion));
    if (!asset || seen.has(asset.apiName)) continue;
    seen.add(asset.apiName);
    for (const trait of asset.traits)
      counts.set(trait, (counts.get(trait) ?? 0) + 1);
  }
  return [...counts].sort((a, b) => b[1] - a[1]);
});
const teamCost = computed(() =>
  (boardState.value?.units ?? []).reduce(
    (sum, u) =>
      sum + (costForUnit(u) ?? 0) * 3 ** Math.max(0, starCount(u) - 1),
    0,
  ),
);
function unitIssue(unit: BoardStateUnit): string | null {
  if (!championByName.value.has(normalizeName(unit.champion)))
    return 'Choose a known champion';
  if (!starCount(unit)) return 'Choose a star level';
  return null;
}
const incompleteUnits = computed(() =>
  (boardState.value?.units ?? []).filter((unit) => unitIssue(unit)),
);
const validUnits = computed(
  () => !!boardState.value?.units.length && incompleteUnits.value.length === 0,
);
function unitNeedsReview(unit?: BoardStateUnit) {
  return !!unit && (!!unit.needs_review || !!unitIssue(unit));
}
async function loadGames() {
  if (!props.user) return;
  gamesLoading.value = true;
  saveError.value = '';
  try {
    games.value = await api.getMatches();
  } catch {
    saveError.value = 'Could not load games. Retry to choose a game.';
  } finally {
    gamesLoading.value = false;
  }
}
const championPicker = ref<InstanceType<typeof ChampionPicker> | null>(null);
function editChampion(champion: TftChampionAsset) {
  if (
    !boardState.value ||
    !selectedHex.value ||
    saving.value ||
    saved.value ||
    detecting.value
  )
    return;
  if (selectedUnit.value) {
    selectedUnit.value.champion = champion.name;
    selectedUnit.value.raw_champion = null;
    selectedUnit.value.needs_review = !starCount(selectedUnit.value);
    selectedUnit.value.review_reason = null;
  } else {
    const [row, column] = selectedHex.value.split(',').map(Number);
    boardState.value.units.push({
      row,
      column,
      champion: champion.name,
      star: '1_star',
      source: 'user_review',
      needs_review: false,
    });
  }
  confirmed.value = false;
}
function editStars(level: number) {
  if (
    !selectedUnit.value ||
    saving.value ||
    saved.value ||
    detecting.value ||
    ![1, 2, 3].includes(level)
  )
    return;
  selectedUnit.value.star = `${level}_star`;
  selectedUnit.value.star_confidence = null;
  confirmed.value = false;
}
function openPicker(event: Event) {
  championPicker.value?.open(event.currentTarget as HTMLElement);
}
function selectHex(row: number, column: number, event: Event) {
  if (!boardState.value || saved.value || saving.value || detecting.value)
    return;
  selectedHex.value = hexKey(row, column);
  openPicker(event);
}
function removeUnit() {
  if (!boardState.value) return;
  boardState.value.units = boardState.value.units.filter(
    (u) => hexKey(u.row, u.column) !== selectedHex.value,
  );
  selectedHex.value = null;
  confirmed.value = false;
}
async function saveRound() {
  if (
    !draft.value ||
    !validUnits.value ||
    !validRound.value ||
    !confirmed.value ||
    saving.value ||
    detecting.value ||
    uploading.value ||
    saved.value
  )
    return;
  saving.value = true;
  saveError.value = '';
  try {
    draft.value = await api.saveBoardRound(draft.value.id, {
      ...round,
      ...contextPayload(),
      units: boardState.value!.units.map((u) => ({
        row: u.row,
        column: u.column,
        champion: u.champion,
        stars: starCount(u),
      })),
    });
    saved.value = true;
    selectedHex.value = null;
  } catch (err: any) {
    saveError.value =
      err.response?.data?.message || 'Could not save this round. Please retry.';
  } finally {
    saving.value = false;
  }
}

const screenshotViewer = ref<InstanceType<typeof ScreenshotViewer> | null>(
  null,
);
const fileInput = ref<HTMLInputElement | null>(null);
const draft = ref<BoardStateDraft | null>(null);
const boardState = ref<BoardState | null>(null);
const uploadedPreviewUrl = ref<string | null>(null);
const uploadedPreviewName = ref<string | null>(null);
const champions = ref<TftChampionAsset[]>([]);
const loadingChampions = ref(false);
const uploading = ref(false);
const detecting = ref(false);
const error = ref<string | null>(null);
watch(
  [round, boardState],
  () => {
    confirmed.value = false;
    guide.value = null;
    reviewRevision += 1;
  },
  { deep: true },
);

const championByName = computed(() => {
  const map = new Map<string, TftChampionAsset>();
  for (const champion of champions.value) {
    map.set(normalizeName(champion.name), champion);
    map.set(normalizeName(champion.apiName), champion);
  }
  return map;
});

const unitsByHex = computed(() => {
  const map = new Map<string, BoardStateUnit>();
  for (const unit of boardState.value?.units ?? []) {
    map.set(hexKey(unit.row, unit.column), unit);
  }
  return map;
});

const hexes = computed(() => {
  const cells: { row: number; column: number; unit?: BoardStateUnit }[] = [];
  for (let row = 0; row < 4; row += 1) {
    for (let column = 0; column < 7; column += 1) {
      cells.push({
        row,
        column,
        unit: unitsByHex.value.get(hexKey(row, column)),
      });
    }
  }
  return cells;
});

const needsReviewCount = computed(
  () => boardState.value?.units.filter(unitNeedsReview).length ?? 0,
);

const missingHexCount = computed(
  () => boardState.value?.review?.missing_hexes?.length ?? 0,
);

const uploadStatus = computed(() => {
  if (uploading.value) return 'Uploading';
  if (draft.value) return 'Uploaded';
  return 'Waiting';
});

const detectionStatus = computed(() => {
  if (detecting.value) return 'Detecting';
  if (boardState.value) return 'Ready';
  return 'Not run';
});

function hexKey(row: number, column: number) {
  return `${row},${column}`;
}

function normalizeName(value: string) {
  return value
    .trim()
    .toLowerCase()
    .replace(/^tft\d+_/, '')
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '');
}

function imageForUnit(unit?: BoardStateUnit) {
  if (!unit || unit.champion === 'unknown') {
    return null;
  }

  return (
    championByName.value.get(normalizeName(unit.raw_champion || unit.champion))
      ?.imageUrl ?? null
  );
}

function costForUnit(unit?: BoardStateUnit) {
  if (!unit || unit.champion === 'unknown') {
    return null;
  }

  return (
    championByName.value.get(normalizeName(unit.raw_champion || unit.champion))
      ?.cost ?? null
  );
}

function starCount(unit?: BoardStateUnit) {
  const match = unit?.star?.match(/[123]/);
  return match ? Number(match[0]) : 0;
}

async function loadChampions() {
  loadingChampions.value = true;
  error.value = null;
  try {
    champions.value = (await api.getSetChampions(18)).champions;
  } catch (err: any) {
    error.value =
      'Champion data could not be loaded. Check the API connection and retry.';
  } finally {
    loadingChampions.value = false;
  }
}

async function handleUpload(event: Event) {
  const target = event.target as HTMLInputElement;
  const file = target.files?.[0];
  if (!file) return;
  if (!file.type.startsWith('image/') || file.size > 25 * 1024 * 1024) {
    error.value = 'Choose an image smaller than 25 MB.';
    target.value = '';
    return;
  }
  draft.value = null;
  saved.value = false;
  confirmed.value = false;
  selectedHex.value = null;
  saveError.value = '';

  if (uploadedPreviewUrl.value) {
    URL.revokeObjectURL(uploadedPreviewUrl.value);
  }
  uploadedPreviewUrl.value = URL.createObjectURL(file);
  uploadedPreviewName.value = file.name;
  uploading.value = true;
  detecting.value = false;
  error.value = null;
  boardState.value = null;
  round.stage = '';
  round.roundNumber = '';
  round.level = '';
  round.gold = '';
  round.hp = '';
  round.streak = '';
  guide.value = null;
  guideError.value = '';

  try {
    draft.value = await api.uploadBoardStateImage(file);
  } catch (err: any) {
    error.value = err.response?.data?.message || err.message || 'Upload failed';
  } finally {
    uploading.value = false;
    target.value = '';
  }
}

async function detectDraft() {
  if (!draft.value || saved.value) return;
  guide.value = null;
  confirmed.value = false;
  selectedHex.value = null;

  detecting.value = true;
  error.value = null;

  try {
    draft.value = await api.detectBoardStateDraft(draft.value.id);
    boardState.value = draft.value.boardState;
    const hud = boardState.value?.hud;
    const roundMatch = String(hud?.round?.value ?? '').match(
      /^([1-9])-([1-7])$/,
    );
    round.stage = roundMatch ? Number(roundMatch[1]) : '';
    round.roundNumber = roundMatch ? Number(roundMatch[2]) : '';
    for (const field of ['level', 'gold', 'hp', 'streak'] as const) {
      const value = hud?.[field]?.value;
      round[field] = typeof value === 'number' ? value : '';
    }
    for (const unit of boardState.value?.units ?? []) {
      const asset = championByName.value.get(
        normalizeName(unit.raw_champion || unit.champion),
      );
      if (asset && unit.champion !== 'unknown') {
        unit.champion = asset.name;
        unit.raw_champion = null;
      }
      const stars = starCount(unit);
      unit.star = stars ? `${stars}_star` : null;
    }
  } catch (err: any) {
    error.value =
      err.response?.data?.message || err.message || 'Board detection failed';
  } finally {
    detecting.value = false;
  }
}

onBeforeUnmount(() => {
  if (uploadedPreviewUrl.value) {
    URL.revokeObjectURL(uploadedPreviewUrl.value);
  }
});

onMounted(loadChampions);
onActivated(loadGames);
</script>

<template>
  <section class="review-page">
    <ScreenshotViewer
      ref="screenshotViewer"
      :src="uploadedPreviewUrl"
      :filename="uploadedPreviewName"
    />
    <ChampionPicker
      ref="championPicker"
      :champions="champions"
      :selected="selectedUnit?.champion"
      :stars="starCount(selectedUnit)"
      :disabled="saving || saved || detecting"
      @stars="editStars"
      :loading="loadingChampions"
      @select="editChampion"
      @retry="loadChampions"
    />
    <header class="review-heading">
      <div>
        <div class="eyebrow">YOUR GAME, HEX BY HEX <span>SET 18</span></div>
        <h1>Board Review</h1>
        <p>
          Detect your board and player stats. Review the results. Get a
          round-aware guide.
        </p>
      </div>
      <button class="review-btn quiet" @click="emit('viewGames')">
        Match history <ChevronRight :size="16" aria-hidden="true" />
      </button>
    </header>
    <div class="review-steps" aria-label="Review progress">
      <span :class="{ done: !!draft }"><b>01</b> Upload screenshot</span
      ><ChevronRight :size="14" aria-hidden="true" />
      <span :class="{ done: !!boardState }"><b>02</b> Review board</span
      ><ChevronRight :size="14" aria-hidden="true" />
      <span :class="{ done: saved }"><b>03</b> Get your guide</span>
    </div>
    <p v-if="!user" class="review-notice">
      Sign in using the header to upload and save your rounds.
    </p>
    <p v-if="error" class="review-notice danger" role="alert">
      {{ error }}
      <button
        v-if="!champions.length"
        class="text-button"
        @click="loadChampions"
      >
        Retry champion data
      </button>
    </p>
    <details class="review-help">
      <summary>How to get a useful board review</summary>
      <ol>
        <li>
          Upload a clear desktop screenshot with the full HUD visible: round at
          the top, level and gold above the shop, and your HP badge on the
          right.
        </li>
        <li>
          Detect the board. Click hexes to correct champions and stars; add
          missing units or remove false detections.
        </li>
        <li>
          Check round, level, gold, HP, and streak against the enlarged
          screenshot. Enter unreadable fields manually, then confirm your
          review.
        </li>
        <li>
          Generate your guide. You can review without choosing a game; select a
          game only when you want to save the round.
        </li>
      </ol>
      <p>
        V1 HUD detection supports standard desktop layouts and some video
        screenshots. Crops, overlays, UI scaling, and scouting another player
        may require manual correction. Guidance is a review aid, not a win
        prediction.
      </p>
    </details>
    <div
      v-if="guide"
      ref="guidePanel"
      tabindex="-1"
      class="review-guide"
      aria-label="Your board review results"
    >
      <h2>Your round {{ guide.round }} review</h2>
      <div class="guide-tips">
        <article v-for="tip in guide.tips" :key="tip.title">
          <h3>{{ tip.title }}</h3>
          <p>{{ tip.detail }}</p>
        </article>
      </div>
      <p class="field-hint">{{ guide.basis }}</p>
    </div>
    <div class="review-summary">
      <div class="summary-title">
        <div class="summary-emblem">
          <Swords :size="26" aria-hidden="true" />
        </div>
        <div>
          <h2>
            {{
              saved
                ? 'Round saved'
                : boardState
                  ? 'Your composition'
                  : 'Build your round'
            }}
          </h2>
          <p>
            {{
              boardState
                ? 'Review champions and star levels before saving.'
                : 'Start with a screenshot of your TFT board.'
            }}
          </p>
        </div>
      </div>
      <div class="summary-stats">
        <div>
          <span>Champions</span
          ><strong
            >{{ boardState ? boardState.units.length : '—'
            }}<small> / 28 hexes</small></strong
          >
        </div>
        <div>
          <span>Team value</span
          ><strong class="gold"
            >{{ boardState ? teamCost : '—' }}<small> gold</small></strong
          >
        </div>
        <div>
          <span>To review</span
          ><strong>{{
            boardState ? needsReviewCount + missingHexCount : '—'
          }}</strong>
        </div>
      </div>
    </div>
    <div class="review-grid">
      <aside class="review-sidebar">
        <section class="review-card screenshot-card">
          <div class="card-heading">
            <h2><ImageUp :size="16" aria-hidden="true" /> Screenshot</h2>
            <span>{{ uploadStatus }}</span>
          </div>
          <input
            ref="fileInput"
            type="file"
            accept="image/*"
            class="hidden-file-input"
            @change="handleUpload"
          />
          <button
            class="screenshot-input"
            :disabled="
              !uploadedPreviewUrl && (!user || uploading || detecting || saving)
            "
            :aria-label="
              uploadedPreviewUrl
                ? 'View screenshot in large preview'
                : 'Upload a screenshot'
            "
            :aria-haspopup="uploadedPreviewUrl ? 'dialog' : undefined"
            :title="
              uploadedPreviewUrl ? 'Click to enlarge screenshot' : undefined
            "
            @click="
              uploadedPreviewUrl ? screenshotViewer?.open() : fileInput?.click()
            "
          >
            <img
              v-if="uploadedPreviewUrl"
              :src="uploadedPreviewUrl"
              alt="Uploaded TFT board screenshot"
            />
            <template v-else
              ><ImageUp :size="30" aria-hidden="true" /><strong
                >Upload a screenshot</strong
              ><span>Image files · up to 25 MB</span></template
            >
          </button>
          <div class="screenshot-actions">
            <p v-if="uploadedPreviewName" class="filename">
              {{ uploadedPreviewName }}
            </p>
            <button
              class="review-btn quiet full"
              :disabled="!user || uploading || detecting || saving"
              @click="fileInput?.click()"
            >
              <ImageUp :size="16" aria-hidden="true" />{{
                uploading
                  ? 'Uploading…'
                  : uploadedPreviewUrl
                    ? 'Replace screenshot'
                    : 'Choose image'
              }}
            </button>
            <button
              class="review-btn accent full"
              :disabled="!draft || uploading || detecting || saving || saved"
              @click="detectDraft"
            >
              <Loader2
                v-if="detecting"
                :size="16"
                class="animate-spin"
                aria-hidden="true"
              /><Sparkles v-else :size="16" aria-hidden="true" />{{
                detecting
                  ? 'Detecting board…'
                  : boardState
                    ? 'Detect again'
                    : 'Detect board'
              }}
            </button>
          </div>
        </section>
        <section class="review-card traits-card">
          <div class="card-heading">
            <h2><Shield :size="16" aria-hidden="true" /> Traits</h2>
            <span>{{ traits.length }}</span>
          </div>
          <div class="trait-list">
            <div v-for="[name, count] in traits" :key="name" class="trait-row">
              <span class="trait-symbol"
                ><Shield :size="15" aria-hidden="true" /></span
              ><strong>{{ name }}</strong
              ><b>{{ count }}</b>
            </div>
            <p v-if="!traits.length" class="subtle-empty">
              Your team's traits appear here after detection.
            </p>
          </div>
          <p v-if="traits.length" class="card-footnote">
            Unique champions per trait.
          </p>
        </section>
      </aside>
      <section class="review-card composition-card">
        <div class="card-heading">
          <h2><Swords :size="17" aria-hidden="true" /> Team positioning</h2>
          <span class="detection-label" role="status">{{
            detectionStatus
          }}</span>
        </div>
        <div class="composition-board" :aria-busy="detecting">
          <div class="board-direction">FRONTLINE</div>
          <div class="tactical-grid">
            <button
              v-for="hex in hexes"
              :key="`${hex.row}-${hex.column}`"
              class="tactical-hex"
              aria-haspopup="dialog"
              aria-controls="board-champion-picker"
              :class="[
                `rarity-${costForUnit(hex.unit) || 0}`,
                {
                  occupied: hex.unit,
                  selected: selectedHex === hexKey(hex.row, hex.column),
                  uncertain: unitNeedsReview(hex.unit),
                },
              ]"
              :style="{
                gridColumn: hex.column + 1,
                gridRow: hex.row + 1,
                transform: hex.row % 2 ? 'translateX(50%)' : undefined,
              }"
              :disabled="!boardState || detecting || saving || saved"
              :aria-label="`Row ${hex.row + 1}, hex ${hex.column + 1}: ${hex.unit ? hex.unit.champion + ', ' + starCount(hex.unit) + ' stars' : 'empty, add champion'}`"
              @click="selectHex(hex.row, hex.column, $event)"
            >
              <span class="hex-fill"
                ><img
                  v-if="imageForUnit(hex.unit)"
                  :src="imageForUnit(hex.unit)!"
                  alt="" /><Plus
                  v-else-if="!hex.unit && boardState"
                  :size="16"
                  aria-hidden="true"
              /></span>
              <span v-if="hex.unit" class="unit-stars">{{
                '★'.repeat(starCount(hex.unit)) || '?'
              }}</span
              ><span v-if="hex.unit" class="unit-name">{{
                hex.unit.champion
              }}</span
              ><span v-if="unitNeedsReview(hex.unit)" class="unit-warning"
                >!</span
              >
            </button>
          </div>
          <div class="board-direction">BACKLINE</div>
          <div v-if="!boardState || detecting" class="board-overlay">
            <div>
              <Loader2
                v-if="detecting"
                class="animate-spin"
                :size="26"
                aria-hidden="true"
              /><ScanLine v-else :size="26" aria-hidden="true" />
              <h3>
                {{
                  detecting
                    ? 'Reading your board…'
                    : 'Your next move starts here'
                }}
              </h3>
              <p>
                {{
                  detecting
                    ? 'Finding champions, positions, and star levels.'
                    : 'Upload a screenshot, then detect your team.'
                }}
              </p>
            </div>
          </div>
        </div>
        <div class="board-caption">
          <span
            ><span class="legend-dot"></span>
            {{
              boardState
                ? 'Select any hex to edit its champion and stars'
                : '4 rows · 7 hexes · Your full board'
            }}</span
          ><span v-if="boardState">{{ needsReviewCount }} flagged</span>
        </div>
        <div v-if="selectedHex && !saved" class="unit-editor" :inert="saving">
          <template v-if="selectedUnit"
            ><label
              >Champion<button
                type="button"
                class="review-btn quiet"
                aria-haspopup="dialog"
                aria-controls="board-champion-picker"
                :aria-expanded="championPicker?.isOpen ?? false"
                @click="openPicker"
              >
                {{
                  selectedUnit.champion === 'unknown'
                    ? 'Choose champion'
                    : selectedUnit.champion
                }}<ChevronRight :size="16" aria-hidden="true" /></button></label
            ><label
              >Star level<select
                :value="selectedUnit.star"
                @change="
                  editStars(
                    Number(
                      ($event.target as HTMLSelectElement).value.charAt(0),
                    ),
                  )
                "
              >
                <option :value="null" disabled>Choose stars</option>
                <option value="1_star">1 star</option>
                <option value="2_star">2 stars</option>
                <option value="3_star">3 stars</option>
              </select></label
            ><button
              class="review-btn quiet"
              aria-label="Remove champion from selected hex"
              @click="removeUnit"
            >
              <X :size="16" aria-hidden="true" /> Remove
            </button></template
          >
          <template v-else
            ><p>Empty hex selected</p>
            <button class="review-btn quiet" @click="openPicker">
              <Plus :size="16" aria-hidden="true" /> Add champion
            </button></template
          >
        </div>
        <div class="roster-section">
          <div class="roster-heading">
            <h3>Champion lineup</h3>
            <span>{{
              loadingChampions ? 'Loading assets…' : 'Set 18 · Enchanted Wilds'
            }}</span>
          </div>
          <div v-if="boardState" class="champion-lineup">
            <button
              v-for="unit in boardState.units"
              :key="hexKey(unit.row, unit.column)"
              class="roster-unit"
              :disabled="saved || saving"
              @click="selectHex(unit.row, unit.column, $event)"
            >
              <img
                v-if="imageForUnit(unit)"
                :src="imageForUnit(unit)!"
                alt=""
              /><span v-else class="unknown-portrait">?</span
              ><strong>{{ unit.champion }}</strong
              ><small>{{ starCount(unit) }} ★</small>
            </button>
          </div>
          <p v-else class="subtle-empty">
            Detected champions will appear here. You can correct any champion or
            star level.
          </p>
        </div>
      </section>
      <aside class="review-card save-card">
        <div class="card-heading">
          <h2><ScanLine :size="17" aria-hidden="true" /> Round context</h2>
        </div>
        <div v-if="saved" class="save-success" role="status">
          <CheckCircle2 :size="36" aria-hidden="true" />
          <h3>Round {{ round.stage }}-{{ round.roundNumber }} saved</h3>
          <p>Your reviewed board is linked to game #{{ round.matchId }}.</p>
          <button class="review-btn quiet full" @click="emit('viewGames')">
            View match history <ChevronRight :size="16" aria-hidden="true" />
          </button>
          <p>Upload another screenshot to add your next round.</p>
        </div>
        <form v-else class="round-form" @submit.prevent="saveRound">
          <p>
            Review the detected values to get useful guidance. Choose a game
            only if you want to save this round.
          </p>
          <fieldset :disabled="saving">
            <label
              >Game<select
                v-model.number="round.matchId"
                required
                :disabled="gamesLoading || !user"
              >
                <option :value="0" disabled>
                  {{ gamesLoading ? 'Loading games…' : 'Select a game' }}
                </option>
                <option v-for="game in games" :key="game.id" :value="game.id">
                  #{{ game.id }} · {{ game.comp || 'Game' }} ·
                  {{
                    new Date(
                      game.playedAt || game.createdAt,
                    ).toLocaleDateString()
                  }}
                </option>
              </select></label
            >
            <button
              v-if="!games.length && !gamesLoading"
              type="button"
              class="text-button"
              @click="emit('viewGames')"
            >
              Create a game in match history
              <ChevronRight :size="14" aria-hidden="true" />
            </button>
            <div class="form-pair">
              <label
                >Stage
                <small class="field-hint">{{ fieldStatus('round') }}</small
                ><input
                  v-model.number="round.stage"
                  placeholder="Not detected"
                  type="number"
                  min="1"
                  max="9"
                  required /></label
              ><label
                >Round<input
                  v-model.number="round.roundNumber"
                  placeholder="Not detected"
                  type="number"
                  min="1"
                  max="7"
                  required
              /></label>
            </div>
            <div class="round-divider">PLAYER STATE</div>
            <div class="form-pair">
              <label
                >Level
                <small class="field-hint">{{ fieldStatus('level') }}</small
                ><input
                  v-model.number="round.level"
                  placeholder="Not detected"
                  type="number"
                  min="1"
                  max="11"
                  required /></label
              ><label
                >HP <small class="field-hint">{{ fieldStatus('hp') }}</small
                ><input
                  v-model.number="round.hp"
                  placeholder="Not detected"
                  type="number"
                  min="0"
                  max="100"
                  required /></label
              ><label
                >Gold <small class="field-hint">{{ fieldStatus('gold') }}</small
                ><input
                  v-model.number="round.gold"
                  placeholder="Not detected"
                  type="number"
                  min="0"
                  required /></label
              ><label
                >Streak
                <small class="field-hint">{{ fieldStatus('streak') }}</small
                ><input
                  v-model.number="round.streak"
                  placeholder="Not detected"
                  min="-99"
                  max="99"
                  type="number"
                  required
              /></label>
            </div>
            <span class="field-hint"
              >Positive = win streak · negative = loss streak. Enter 0 only when
              there is no streak.</span
            >
            <div
              v-if="incompleteUnits.length"
              id="board-review-issues"
              class="review-issues"
              role="status"
            >
              <strong>Complete these before confirming</strong>
              <button
                v-for="unit in incompleteUnits"
                :key="hexKey(unit.row, unit.column)"
                type="button"
                class="review-btn quiet full"
                @click="selectHex(unit.row, unit.column, $event)"
              >
                {{ unit.champion }} · row {{ unit.row + 1 }}, hex
                {{ unit.column + 1 }}:
                {{ unitIssue(unit) }}
              </button>
            </div>
            <label class="review-confirm"
              ><input
                v-model="confirmed"
                :aria-describedby="
                  incompleteUnits.length ? 'board-review-issues' : undefined
                "
                type="checkbox"
                :disabled="!validUnits || !validRound"
              /><span
                >I've checked champions, positions, stars, round, level, gold,
                HP, and streak.</span
              ></label
            >
            <p v-if="!validRound" class="field-hint">
              Enter all six context fields to enable your guide and saving.
            </p>
            <button
              type="button"
              class="review-btn accent full"
              :disabled="
                !validUnits ||
                !validRound ||
                !confirmed ||
                analyzing ||
                detecting ||
                saving
              "
              @click="analyzeBoard"
            >
              {{ analyzing ? 'Analyzing…' : 'Get my board guide' }}
            </button>
            <p v-if="guideError" class="save-error" role="alert">
              {{ guideError }}
            </p>
            <p v-if="!validUnits" class="field-hint">
              {{
                boardState
                  ? 'Choose a known champion and star level for each occupied hex.'
                  : 'Detect a board to enable saving.'
              }}
            </p>
            <button
              class="review-btn accent full"
              type="submit"
              :disabled="
                !validUnits ||
                !validRound ||
                !confirmed ||
                !round.matchId ||
                saving ||
                detecting ||
                uploading ||
                !user
              "
            >
              <Loader2
                v-if="saving"
                :size="16"
                class="animate-spin"
                aria-hidden="true"
              /><Plus v-else :size="16" aria-hidden="true" />{{
                saving ? 'Saving round…' : 'Add round to game'
              }}
            </button>
          </fieldset>
          <div v-if="saveError" class="save-error" role="alert">
            {{ saveError
            }}<button
              v-if="!games.length"
              type="button"
              class="text-button"
              @click="loadGames"
            >
              Retry loading games
            </button>
          </div>
        </form>
      </aside>
    </div>
  </section>
</template>
<style scoped>
.review-help,
.review-guide {
  border: 1px solid #41424f;
  border-radius: 8px;
  padding: 16px;
  margin: 16px 0;
  background: #272832;
}
.review-help summary {
  cursor: pointer;
  min-height: 32px;
  font-weight: 650;
}
.review-help ol {
  padding: 12px 0 12px 22px;
  color: #c0c1d0;
}
.review-help li {
  padding: 5px 0;
}
.review-help p {
  color: #b1b2c3;
  font-size: 12px;
}
.review-guide h2 {
  font-size: 19px;
  margin-bottom: 14px;
}
.guide-tips {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 240px), 1fr));
  gap: 16px;
  margin-bottom: 12px;
}
.guide-tips article {
  padding: 14px;
  background: #20212a;
  border-radius: 6px;
}
.guide-tips h3 {
  font-size: 14px;
  color: #c5b2ff;
  margin-bottom: 8px;
}
.guide-tips p {
  font-size: 13px;
  color: #c0c1d0;
}

.review-page {
  --surface: #272832;
  --surface-raised: #30313d;
  --surface-deep: #20212a;
  --line: #41424f;
  --muted: #b1b2c3;
  --ink: #f5f5fa;
  --accent: #7952e8;
  --accent-light: #b9a4ff;
  --gold: #f5c568;
  color: var(--ink);
  font-size: 14px;
  line-height: 1.5;
}
.review-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  margin: 0 0 24px;
}
.eyebrow {
  color: var(--muted);
  font-size: 11px;
  letter-spacing: 1.6px;
  font-weight: 700;
}
.eyebrow span {
  color: var(--accent-light);
  margin-left: 12px;
  letter-spacing: 0.5px;
}
.review-heading h1 {
  font-size: 32px;
  letter-spacing: -0.8px;
  margin: 5px 0;
  font-weight: 750;
}
.review-heading p,
.summary-title p {
  color: var(--muted);
}
.review-btn {
  min-height: 44px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 14px;
  border: 1px solid var(--line);
  border-radius: 6px;
  font: inherit;
  font-weight: 650;
  cursor: pointer;
  transition:
    background 0.16s,
    border-color 0.16s;
  color: var(--ink);
}
.review-btn.quiet {
  background: var(--surface-raised);
}
.review-btn.accent {
  background: var(--accent);
  border-color: var(--accent);
}
.review-btn:hover:not(:disabled) {
  background: #6542cc;
  border-color: var(--accent-light);
}
.review-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
.full {
  width: 100%;
}
.review-page :is(button, input, select):focus-visible {
  outline: 3px solid var(--accent-light);
  outline-offset: 3px;
}
.review-steps {
  display: flex;
  gap: 24px;
  align-items: center;
  padding: 14px 20px;
  background: var(--surface-deep);
  border: 1px solid var(--line);
  border-radius: 8px 8px 0 0;
  color: var(--muted);
  font-size: 13px;
}
.review-steps span {
  display: flex;
  gap: 10px;
  align-items: center;
}
.review-steps b {
  font-size: 11px;
  background: var(--surface-raised);
  padding: 3px 7px;
  border-radius: 4px;
}
.review-steps .done {
  color: var(--accent-light);
}
.review-summary {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 24px;
  padding: 24px;
  background: var(--surface-raised);
  border: 1px solid var(--line);
  border-top: 0;
  border-left: 4px solid var(--accent);
  border-radius: 0 0 8px 8px;
  margin-bottom: 20px;
}
.summary-title {
  display: flex;
  align-items: center;
  gap: 16px;
}
.summary-title h2 {
  font-size: 20px;
}
.summary-title p {
  font-size: 12px;
  margin-top: 4px;
}
.summary-emblem {
  display: grid;
  place-items: center;
  width: 52px;
  height: 52px;
  background: #41365f;
  border: 1px solid #65518c;
  border-radius: 10px;
  color: var(--accent-light);
  flex-shrink: 0;
}
.summary-stats {
  display: flex;
  gap: 24px;
}
.summary-stats > div {
  padding-left: 24px;
  border-left: 1px solid var(--line);
}
.summary-stats span {
  display: block;
  font-size: 12px;
  color: var(--muted);
  white-space: nowrap;
}
.summary-stats strong {
  display: block;
  font-size: 24px;
  font-variant-numeric: tabular-nums;
}
.summary-stats small {
  font-size: 11px;
  font-weight: 400;
  color: var(--muted);
}
.gold {
  color: var(--gold);
}
.review-grid {
  display: grid;
  grid-template-columns: 220px minmax(0, 1fr) 270px;
  gap: 16px;
  align-items: start;
}
.review-sidebar {
  display: grid;
  gap: 16px;
}
.review-card {
  min-width: 0;
  border: 1px solid var(--line);
  background: var(--surface);
  border-radius: 8px;
  overflow: hidden;
}
.card-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 15px 16px;
  border-bottom: 1px solid var(--line);
  background: var(--surface-raised);
}
.card-heading h2 {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 700;
}
.card-heading > span {
  font-size: 11px;
  color: var(--muted);
}
.screenshot-input {
  width: 100%;
  aspect-ratio: 1.5;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 8px;
  background: var(--surface-deep);
  border: 0;
  color: var(--muted);
  cursor: pointer;
  font: inherit;
}
.screenshot-input strong {
  font-size: 12px;
  color: var(--ink);
}
.screenshot-input span {
  font-size: 11px;
}
.screenshot-input img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}
.screenshot-input:disabled {
  cursor: not-allowed;
}
.screenshot-actions {
  padding: 12px;
  display: grid;
  gap: 8px;
}
.filename {
  overflow-wrap: anywhere;
  color: var(--muted);
  font-size: 11px;
}
.trait-list {
  padding: 10px;
}
.trait-row {
  display: flex;
  gap: 10px;
  align-items: center;
  padding: 10px 4px;
  border-bottom: 1px solid var(--line);
}
.trait-row:last-child {
  border: 0;
}
.trait-row strong {
  font-size: 12px;
  flex: 1;
}
.trait-row b {
  background: var(--surface-deep);
  border-radius: 4px;
  padding: 2px 8px;
  color: var(--gold);
}
.trait-symbol {
  display: grid;
  place-items: center;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: var(--surface-deep);
  color: var(--gold);
}
.card-footnote {
  color: var(--muted);
  font-size: 11px;
  padding: 0 14px 12px;
}
.subtle-empty {
  font-size: 13px;
  color: var(--muted);
  padding: 12px 4px;
  line-height: 1.7;
}
.composition-board {
  position: relative;
  padding: 22px 18px 14px;
  background: var(--surface-deep);
}
.board-direction {
  font-size: 9px;
  letter-spacing: 2px;
  color: var(--muted);
  text-align: center;
}
.tactical-grid {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 7px 4px;
  padding: 20px 6.5% 20px 0;
}
.tactical-hex {
  --rarity: #3b3c49;
  position: relative;
  aspect-ratio: 0.9;
  width: 100%;
  background: transparent;
  border: 0;
  padding: 0;
  color: var(--ink);
  cursor: pointer;
  isolation: isolate;
}
.tactical-hex:before,
.hex-fill {
  position: absolute;
  inset: 0;
  clip-path: polygon(50% 0, 100% 25%, 100% 75%, 50% 100%, 0 75%, 0 25%);
  background: var(--rarity);
}
.tactical-hex:before {
  content: '';
  z-index: -1;
}
.hex-fill {
  inset: 2px;
  background: #17181f;
  display: grid;
  place-items: center;
  color: #686a7d;
  overflow: hidden;
}
.hex-fill img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.rarity-1 {
  --rarity: #a0a3b3;
}
.rarity-2 {
  --rarity: #54b883;
}
.rarity-3 {
  --rarity: #5598f3;
}
.rarity-4 {
  --rarity: #d76ae7;
}
.rarity-5 {
  --rarity: #f5ba47;
}
.tactical-hex.selected {
  filter: drop-shadow(0 0 5px var(--accent-light));
}
.tactical-hex.uncertain:before {
  background: #f5ba47;
}
.tactical-hex:not(:disabled):hover .hex-fill {
  background: #393144;
}
.tactical-hex:disabled {
  cursor: default;
}
.unit-stars {
  position: absolute;
  top: -7px;
  left: 0;
  right: 0;
  color: var(--gold);
  font-size: clamp(10px, 1.15vw, 18px);
  text-shadow: 0 1px 3px #000;
  letter-spacing: -2px;
  pointer-events: none;
}
.unit-name {
  position: absolute;
  bottom: 13%;
  left: 1px;
  right: 1px;
  font-size: clamp(8px, 0.72vw, 12px);
  font-weight: 700;
  text-shadow: 0 1px 3px #000;
  background: #1119;
  overflow-wrap: anywhere;
  pointer-events: none;
}
.unit-warning {
  position: absolute;
  right: -1px;
  top: 14%;
  font-size: 11px;
  width: 15px;
  height: 15px;
  line-height: 15px;
  border-radius: 50%;
  background: var(--gold);
  color: #17181f;
  font-weight: 800;
}
.board-overlay {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  background: #20212a70;
  pointer-events: none;
  text-align: center;
  padding: 24px;
}
.board-overlay > div {
  border: 1px solid var(--line);
  border-radius: 8px;
  background: #272832ed;
  padding: 24px;
  max-width: 330px;
}
.board-overlay svg {
  color: var(--accent-light);
  margin-bottom: 10px;
}
.board-overlay h3 {
  font-size: 17px;
  margin-bottom: 6px;
}
.board-overlay p {
  font-size: 12px;
  color: var(--muted);
}
.board-caption {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  padding: 12px 16px;
  border-top: 1px solid var(--line);
  font-size: 11px;
  color: var(--muted);
}
.legend-dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  background: var(--accent-light);
  border-radius: 50%;
  margin-right: 5px;
}
.roster-section {
  padding: 16px;
  border-top: 1px solid var(--line);
}
.roster-heading {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
}
.roster-heading h3 {
  font-size: 13px;
}
.roster-heading > span {
  font-size: 10px;
  color: var(--muted);
}
.champion-lineup {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 16px;
}
.roster-unit {
  border: 0;
  background: none;
  color: var(--ink);
  width: 52px;
  cursor: pointer;
  font: inherit;
}
.roster-unit img,
.unknown-portrait {
  width: 48px;
  height: 48px;
  object-fit: cover;
  border: 2px solid var(--line);
  border-radius: 6px;
  display: block;
}
.roster-unit strong {
  display: block;
  font-size: 10px;
  overflow-wrap: anywhere;
  margin-top: 5px;
}
.roster-unit small {
  font-size: 11px;
  color: var(--gold);
}
.unknown-portrait {
  display: grid;
  place-items: center;
  background: var(--surface-deep);
}
.unit-editor {
  display: flex;
  gap: 12px;
  padding: 16px;
  border-top: 1px solid var(--line);
  align-items: end;
  flex-wrap: wrap;
}
.unit-editor label {
  flex: 1;
  min-width: 100px;
}
.round-form,
.save-success {
  padding: 16px;
}
.round-form > p {
  color: var(--muted);
  font-size: 12px;
  margin-bottom: 20px;
}
.round-form fieldset {
  border: 0;
  min-width: 0;
  display: grid;
  gap: 14px;
}
.review-page label {
  display: flex;
  flex-direction: column;
  gap: 7px;
  font-size: 12px;
  font-weight: 600;
}
.review-page :is(input[type='number'], select) {
  width: 100%;
  min-width: 0;
  height: 42px;
  border: 1px solid #595a6b;
  background: var(--surface-deep);
  color: var(--ink);
  border-radius: 5px;
  padding: 0 10px;
  font: inherit;
  font-size: 13px;
  color-scheme: dark;
}
.form-pair {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
/* Keep paired inputs aligned regardless of helper text wrapping. */
.form-pair label > input {
  order: 1;
}
.form-pair label > .field-hint {
  order: 2;
}
.review-issues {
  display: grid;
  gap: 8px;
  color: var(--ink);
  font-size: 12px;
}
.review-issues .review-btn {
  white-space: normal;
  text-align: left;
  min-height: 44px;
}
.round-divider {
  font-size: 10px;
  letter-spacing: 1.5px;
  color: var(--muted);
  padding-top: 16px;
  border-top: 1px solid var(--line);
  margin-top: 4px;
}
.field-hint {
  font-size: 11px;
  color: var(--muted);
  font-weight: 400;
}
.review-page .review-confirm {
  flex-direction: row;
  align-items: flex-start;
  gap: 10px;
  padding-top: 14px;
  border-top: 1px solid var(--line);
  font-size: 12px;
  font-weight: 400;
  color: var(--muted);
}
.review-confirm input {
  width: 17px;
  height: 17px;
  margin-top: 2px;
  accent-color: var(--accent);
  flex-shrink: 0;
}
.text-button {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  min-height: 32px;
  text-align: left;
  background: transparent;
  border: 0;
  color: var(--accent-light);
  font: inherit;
  font-size: 12px;
  cursor: pointer;
}
.save-error,
.review-notice {
  color: #ffcea1;
  background: #513c2d;
  border: 1px solid #846349;
  padding: 12px;
  border-radius: 6px;
  font-size: 12px;
  margin-top: 12px;
}
.review-notice {
  margin: 12px 0;
}
.danger {
  color: #ffc3c3;
  background: #4c3037;
}
.save-success {
  display: grid;
  gap: 16px;
  color: var(--muted);
  font-size: 13px;
}
.save-success svg {
  color: var(--accent-light);
}
.save-success h3 {
  color: var(--ink);
}
@media (min-width: 1450px) {
  .composition-board {
    padding: 28px 24px;
  }
  .tactical-grid {
    gap: 12px 6px;
    padding-top: 28px;
    padding-bottom: 28px;
  }
}
@media (max-width: 1150px) {
  .review-grid {
    grid-template-columns: 190px minmax(0, 1fr);
  }
  .save-card {
    grid-column: 1/-1;
  }
  .round-form fieldset {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    align-items: start;
  }
  .review-issues {
    display: grid;
    gap: 8px;
    color: var(--ink);
    font-size: 12px;
  }
  .review-issues .review-btn {
    white-space: normal;
    text-align: left;
    min-height: 44px;
  }
  .round-divider {
    grid-column: 1/-1;
  }
  .summary-stats {
    gap: 12px;
  }
  .summary-stats > div {
    padding-left: 12px;
  }
  .summary-stats small {
    display: none;
  }
}
@media (max-width: 700px) {
  .review-heading {
    align-items: start;
    gap: 12px;
  }
  .review-heading h1 {
    font-size: 27px;
  }
  .review-heading p {
    font-size: 12px;
  }
  .review-heading > .review-btn {
    font-size: 11px;
    padding: 8px;
  }
  .eyebrow {
    font-size: 9px;
    letter-spacing: 0.8px;
  }
  .eyebrow span {
    display: none;
  }
  .review-steps {
    gap: 8px;
    padding: 12px;
    font-size: 10px;
    justify-content: space-between;
  }
  .review-steps span {
    gap: 5px;
  }
  .review-steps > svg {
    display: none;
  }
  .review-summary {
    display: block;
    padding: 16px;
  }
  .summary-title h2 {
    font-size: 18px;
  }
  .summary-stats {
    margin-top: 20px;
    justify-content: space-between;
  }
  .summary-stats > div {
    padding-left: 0;
    border: 0;
  }
  .review-grid {
    grid-template-columns: 1fr;
  }
  .review-sidebar {
    grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
    gap: 12px;
  }
  .review-card .card-heading {
    padding: 12px;
  }
  .card-heading h2 {
    font-size: 12px;
  }
  .card-heading > span {
    font-size: 10px;
  }
  .screenshot-input {
    aspect-ratio: 1.6;
  }
  .screenshot-input strong {
    font-size: 11px;
  }
  .screenshot-input span {
    font-size: 9px;
  }
  .screenshot-actions .review-btn {
    font-size: 11px;
    padding: 8px;
  }
  .trait-row {
    gap: 5px;
  }
  .trait-symbol {
    width: 24px;
    height: 24px;
  }
  .trait-row strong {
    font-size: 11px;
  }
  .composition-board {
    padding: 18px 12px;
  }
  .unit-name {
    font-size: 8px;
  }
  .unit-stars {
    font-size: 12px;
  }
  .roster-heading > span {
    font-size: 9px;
  }
  .round-form fieldset {
    grid-template-columns: 1fr;
  }
  .review-page :is(input[type='number'], select) {
    font-size: 16px;
  }
  .review-heading > .review-btn svg {
    display: none;
  }
}
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation: none !important;
    transition: none !important;
  }
}
</style>
