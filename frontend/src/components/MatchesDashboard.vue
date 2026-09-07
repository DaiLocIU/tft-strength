<script setup lang="ts">
import { ref, computed } from 'vue';
import {
  Trophy,
  Swords,
  AlertTriangle,
  RefreshCw,
  PlusCircle,
  Star,
  Users,
  Flame,
  Award,
  Filter,
  Layers,
} from 'lucide-vue-next';
import { Match, User } from '../types';

const props = defineProps<{
  matches: Match[] | null;
  loading: boolean;
  error401: string | null;
  user: User | null;
}>();

const emit = defineEmits<{
  (e: 'openMatch', id: number): void;
  (e: 'loadMatches'): void;
  (e: 'openCreateMatch'): void;
  (e: 'googleLogin'): void;
}>();

const filter = ref<'all' | 'top4' | 'win'>('all');

const totalMatches = computed(() => (props.matches ? props.matches.length : 0));
const wins = computed(() =>
  props.matches ? props.matches.filter((m) => m.placement === 1).length : 0,
);
const top4s = computed(() =>
  props.matches ? props.matches.filter((m) => m.placement <= 4).length : 0,
);
const avgPlacement = computed(() => {
  if (props.matches && props.matches.length > 0) {
    return (
      props.matches.reduce((acc, m) => acc + m.placement, 0) /
      props.matches.length
    ).toFixed(1);
  }
  return '—';
});
const winRate = computed(() =>
  totalMatches.value > 0
    ? Math.round((wins.value / totalMatches.value) * 100)
    : 0,
);
const top4Rate = computed(() =>
  totalMatches.value > 0
    ? Math.round((top4s.value / totalMatches.value) * 100)
    : 0,
);

const filteredMatches = computed(() => {
  if (!props.matches) return [];
  return props.matches.filter((m) => {
    if (filter.value === 'win') return m.placement === 1;
    if (filter.value === 'top4') return m.placement <= 4;
    return true;
  });
});
function formatMatchDate(match: Match) {
  const value = match.playedAt || match.createdAt;
  return value && !Number.isNaN(Date.parse(value))
    ? new Date(value).toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
      })
    : 'Date unavailable';
}
</script>

<template>
  <div class="matches-dashboard-wrapper">
    <!-- 1. Header and Action Bar -->
    <div class="dashboard-header-card">
      <div class="dashboard-title-group">
        <div class="icon-badge">
          <Trophy :size="22" class="text-amber" />
        </div>
        <div>
          <h1 class="dashboard-main-title">Match History</h1>
          <p class="dashboard-subtext">
            Track your TFT team compositions, synergies, and placement rankings
          </p>
        </div>
      </div>

      <div class="dashboard-action-buttons">
        <button
          @click="emit('loadMatches')"
          :disabled="loading"
          class="btn-refresh-data"
          id="btn-load-matches"
        >
          <RefreshCw :size="16" :class="{ 'animate-spin': loading }" />
          <span>{{
            loading
              ? 'Fetching...'
              : matches
                ? 'Refresh Matches'
                : 'Load My Matches'
          }}</span>
        </button>

        <button
          v-if="user"
          @click="emit('openCreateMatch')"
          class="btn-create-match"
          id="btn-add-match"
        >
          <PlusCircle :size="16" />
          <span>Record Match</span>
        </button>
      </div>
    </div>

    <!-- 2. Stats Summary Row -->
    <div v-if="matches && matches.length > 0" class="stats-summary-grid">
      <div class="stat-card">
        <div class="stat-card-header">
          <span class="stat-label">Total Matches</span>
          <Layers :size="16" class="text-cyan" />
        </div>
        <span class="stat-value">{{ totalMatches }}</span>
      </div>

      <div class="stat-card">
        <div class="stat-card-header">
          <span class="stat-label">1st Place Wins</span>
          <Award :size="16" class="text-amber" />
        </div>
        <span class="stat-value text-amber">{{ wins }} ({{ winRate }}%)</span>
      </div>

      <div class="stat-card">
        <div class="stat-card-header">
          <span class="stat-label">Top 4 Rate</span>
          <Flame :size="16" class="text-emerald" />
        </div>
        <span class="stat-value text-emerald"
          >{{ top4s }} ({{ top4Rate }}%)</span
        >
      </div>

      <div class="stat-card">
        <div class="stat-card-header">
          <span class="stat-label">Avg Placement</span>
          <Trophy :size="16" class="text-indigo" />
        </div>
        <span class="stat-value">#{{ avgPlacement }}</span>
      </div>
    </div>

    <!-- 3. 401 UNAUTHORIZED ALERT -->
    <div v-if="error401" class="unauthorized-card" id="error-401-banner">
      <div class="alert-icon-circle">
        <AlertTriangle :size="24" class="text-red" />
      </div>
      <div class="alert-body">
        <div class="alert-heading-row">
          <span class="error-pill">401 Unauthorized</span>
          <h3>Authentication Required</h3>
        </div>
        <p class="alert-text">{{ error401 }}</p>
        <p class="alert-subtext">
          Please sign in with your Google account to securely access your
          personal match records.
        </p>
        <div class="alert-cta-row">
          <button @click="emit('googleLogin')" class="btn-alert-signin">
            <span>Sign In with Google</span>
          </button>
        </div>
      </div>
    </div>

    <!-- 4. LOADING STATE -->
    <div v-if="loading && !matches" class="loading-container">
      <div class="spinner-glow"></div>
      <p>Loading your TFT match history...</p>
    </div>

    <!-- 5. GUEST EMPTY STATE -->
    <div v-if="!matches && !error401 && !loading" class="guest-card">
      <div class="guest-hero-icon">
        <Swords :size="36" class="text-cyan" />
      </div>
      <h2>Welcome to TFT Team Strength</h2>
      <p>
        Analyze your team builds, champion star levels, augment choices, and
        synergy power across games.
      </p>
      <div class="guest-cta-group">
        <button @click="emit('loadMatches')" class="btn-guest-load">
          <span>View Match Records</span>
        </button>
        <button @click="emit('googleLogin')" class="btn-guest-login">
          <span>Sign In with Google</span>
        </button>
      </div>
    </div>

    <!-- 6. AUTHENTICATED MATCHES LIST -->
    <div v-if="matches && matches.length > 0" class="matches-section">
      <div class="filter-bar">
        <div class="filter-label-wrap">
          <Filter :size="15" class="text-muted" />
          <span>Filter:</span>
        </div>
        <div class="filter-chips">
          <button
            :class="['filter-chip', { active: filter === 'all' }]"
            @click="filter = 'all'"
          >
            All Matches ({{ matches.length }})
          </button>
          <button
            :class="['filter-chip', { active: filter === 'win' }]"
            @click="filter = 'win'"
          >
            Victories ({{ wins }})
          </button>
          <button
            :class="['filter-chip', { active: filter === 'top4' }]"
            @click="filter = 'top4'"
          >
            Top 4 ({{ top4s }})
          </button>
        </div>
      </div>

      <div class="matches-list">
        <div
          v-for="match in filteredMatches"
          :key="match.id"
          role="button"
          tabindex="0"
          :aria-label="`Review match ${match.id}, placement ${match.placement}`"
          @click="emit('openMatch', match.id)"
          @keydown.enter="emit('openMatch', match.id)"
          @keydown.space.prevent="emit('openMatch', match.id)"
          :class="[
            'match-item-card',
            match.placement === 1
              ? 'placement-1'
              : match.placement <= 4
                ? 'placement-top4'
                : 'placement-bot4',
          ]"
        >
          <div class="match-left-column">
            <div
              :class="[
                'placement-tag',
                match.placement === 1
                  ? 'tag-win'
                  : match.placement <= 4
                    ? 'tag-top4'
                    : 'tag-bot4',
              ]"
            >
              <span class="placement-number">#{{ match.placement }}</span>
              <span class="placement-text">{{
                match.placement === 1
                  ? 'Victory'
                  : match.placement <= 4
                    ? 'Top 4'
                    : 'Defeat'
              }}</span>
            </div>

            <div class="match-meta-details">
              <span class="game-mode-tag">{{
                match.gameMode || 'Ranked TFT'
              }}</span>
              <span class="rounds-survived-tag">{{
                match.comp || 'Open round timeline →'
              }}</span>
            </div>
          </div>

          <div class="match-center-column">
            <!-- Synergies -->
            <div
              v-if="match.traits && match.traits.length > 0"
              class="traits-badge-list"
            >
              <div
                v-for="(trait, idx) in match.traits"
                :key="idx"
                :class="['trait-badge', `tier-${trait.tier}`]"
              >
                <Users :size="11" />
                <span>{{ trait.name }} ({{ trait.activeCount }})</span>
              </div>
            </div>

            <!-- Champions -->
            <div
              v-if="match.champions && match.champions.length > 0"
              class="champions-tray"
            >
              <div
                v-for="(champ, idx) in match.champions"
                :key="idx"
                :class="['champ-card-item', `cost-${champ.cost}`]"
              >
                <div class="champ-star-rating">
                  <Star
                    v-for="sIdx in champ.stars"
                    :key="sIdx"
                    :size="9"
                    fill="#f59e0b"
                    color="#f59e0b"
                  />
                </div>
                <span class="champ-card-name">{{ champ.name }}</span>
                <div
                  v-if="champ.items && champ.items.length > 0"
                  class="champ-items-dots"
                >
                  <span
                    v-for="(item, iIdx) in champ.items"
                    :key="iIdx"
                    class="item-badge-dot"
                    :title="item"
                  ></span>
                </div>
              </div>
            </div>

            <!-- Augments -->
            <div
              v-if="match.augments && match.augments.length > 0"
              class="augments-tray"
            >
              <span
                v-for="(aug, idx) in match.augments"
                :key="idx"
                class="augment-badge"
              >
                ⚡ {{ aug }}
              </span>
            </div>
          </div>

          <div class="match-right-column">
            <div v-if="match.damageDealt != null" class="game-stat-pill">
              <span class="stat-title">Damage</span>
              <span class="stat-number">{{
                (match.damageDealt ?? 0).toLocaleString()
              }}</span>
            </div>
            <div v-if="match.goldLeft != null" class="game-stat-pill">
              <span class="stat-title">Gold Left</span>
              <span class="stat-number">💰 {{ match.goldLeft || 0 }}</span>
            </div>
            <span class="game-time">
              {{ formatMatchDate(match) }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- 7. EMPTY STATE -->
    <div v-if="matches && matches.length === 0" class="empty-matches-container">
      <Trophy :size="48" class="text-muted" />
      <h3>No Match Records Yet</h3>
      <p>You haven't logged any TFT matches yet. Record your first game now!</p>
      <button @click="emit('openCreateMatch')" class="btn-create-first">
        <PlusCircle :size="16" />
        <span>Record Your First Match</span>
      </button>
    </div>
  </div>
</template>

<style scoped>
.match-item-card[role='button'] {
  cursor: pointer;
}
.match-item-card[role='button']:hover {
  border-color: #bda7ff;
}
.match-item-card[role='button']:focus-visible {
  outline: 3px solid #bda7ff;
  outline-offset: 4px;
}
</style>
