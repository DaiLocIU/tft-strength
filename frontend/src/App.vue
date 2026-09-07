<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue';
import confetti from 'canvas-confetti';
import MatchDetail from './components/MatchDetail.vue';
import Navbar from './components/Navbar.vue';
import MatchesDashboard from './components/MatchesDashboard.vue';
import CreateMatchModal from './components/CreateMatchModal.vue';
import IconStudio from './components/IconStudio.vue';
import BoardStateReview from './components/BoardStateReview.vue';
import { api, getUser, setAuthData } from './services/api';
import { Match, User } from './types';

const user = ref<User | null>(getUser());
const activeTab = ref<'matches' | 'board' | 'studio'>('matches');
const matches = ref<Match[] | null>(null);
const loading = ref(false);
const error401 = ref<string | null>(null);
const isCreateMatchOpen = ref(false);

const detailMatchId = ref<number | null>(null);
const detailRoundId = ref<number | null>(null);
function readRoute() {
  const route = window.location.hash.match(
    /^#\/matches\/(\d+)(?:\/rounds\/(\d+))?$/,
  );
  detailMatchId.value = route ? Number(route[1]) : null;
  detailRoundId.value = route?.[2] ? Number(route[2]) : null;
  if (route) activeTab.value = 'matches';
}
function openMatch(id: number, roundId: number | null = null) {
  window.location.hash = `/matches/${id}${roundId ? `/rounds/${roundId}` : ''}`;
}
function backToMatches() {
  window.location.hash = '/matches';
}
window.addEventListener('hashchange', readRoute);
readRoute();
onBeforeUnmount(() => window.removeEventListener('hashchange', readRoute));

const triggerConfetti = () => {
  confetti({
    particleCount: 75,
    spread: 60,
    origin: { y: 0.6 },
    colors: ['#00f2fe', '#4facfe', '#10b981', '#f59e0b'],
  });
};

const handleLoadMatches = async () => {
  loading.value = true;
  error401.value = null;
  try {
    const data = await api.getMatches();
    matches.value = data;
  } catch (err: any) {
    if (err.response?.status === 401) {
      error401.value =
        '401 Unauthorized - Please log in with Google to access your matches';
    } else {
      error401.value =
        err.response?.data?.message || err.message || 'Error loading matches';
    }
    matches.value = null;
  } finally {
    loading.value = false;
  }
};

const handleGoogleLogin = () => {
  api.loginWithGoogle();
};

const handleCreateMatch = async (matchData: Partial<Match>) => {
  await api.createMatch(matchData);
  const updated = await api.getMatches();
  matches.value = updated;
  triggerConfetti();
};

const handleLogout = async () => {
  await api.logout();
  user.value = null;
  backToMatches();
  matches.value = null;
  error401.value = null;
  activeTab.value = 'matches';
};

onMounted(() => {
  // 1. Handle OAuth redirect callback from NestJS (/auth/google/callback → FE redirect)
  const params = new URLSearchParams(window.location.search);
  const accessToken = params.get('accessToken');
  const refreshToken = params.get('refreshToken');
  const userStr = params.get('user');

  if (accessToken && refreshToken) {
    let parsedUser: User | null = null;
    try {
      if (userStr) {
        parsedUser = JSON.parse(decodeURIComponent(userStr));
      }
    } catch {
      // ignore
    }

    setAuthData({ accessToken, refreshToken }, parsedUser);
    user.value = parsedUser;
    window.history.replaceState({}, document.title, window.location.pathname);

    triggerConfetti();

    setTimeout(() => {
      handleLoadMatches();
    }, 100);
  } else if (getUser()) {
    handleLoadMatches();
  }
});
</script>

<template>
  <div class="app-layout">
    <!-- App Header -->
    <Navbar
      :user="user"
      :active-tab="activeTab"
      @select-tab="(t) => (activeTab = t as 'matches' | 'board' | 'studio')"
      @google-login="handleGoogleLogin"
      @logout="handleLogout"
    />

    <!-- Main Content -->
    <main class="main-content" :class="{ 'board-main': activeTab === 'board' }">
      <KeepAlive :key="user?.id ?? 'guest'" exclude="MatchDetail">
        <IconStudio v-if="activeTab === 'studio'" :user="user" />
        <BoardStateReview
          v-else-if="activeTab === 'board'"
          :user="user"
          @view-games="
            activeTab = 'matches';
            backToMatches();
            handleLoadMatches();
          "
        />
        <MatchDetail
          v-else-if="detailMatchId && user"
          :key="`match-${detailMatchId}`"
          :match-id="detailMatchId"
          :round-id="detailRoundId"
          @back="backToMatches"
          @round="openMatch(detailMatchId!, $event)"
          @add-round="activeTab = 'board'"
        />
        <MatchesDashboard
          v-else
          :matches="matches"
          :loading="loading"
          :error401="error401"
          :user="user"
          @open-match="openMatch"
          @load-matches="handleLoadMatches"
          @open-create-match="isCreateMatchOpen = true"
          @google-login="handleGoogleLogin"
        />
      </KeepAlive>
    </main>

    <!-- Create Match Modal -->
    <CreateMatchModal
      :is-open="isCreateMatchOpen"
      @close="isCreateMatchOpen = false"
      @submit="handleCreateMatch"
    />
  </div>
</template>
