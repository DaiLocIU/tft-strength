<script setup lang="ts">
import { ref } from 'vue';
import { Swords, LogOut, ChevronDown, Shield, Grid3X3 } from 'lucide-vue-next';
import { User } from '../types';

const props = defineProps<{
  user: User | null;
  activeTab: string;
}>();

const emit = defineEmits<{
  (e: 'selectTab', tab: string): void;
  (e: 'googleLogin'): void;
  (e: 'logout'): void;
}>();

const dropdownOpen = ref(false);

const toggleDropdown = () => {
  dropdownOpen.value = !dropdownOpen.value;
};

const closeDropdown = () => {
  dropdownOpen.value = false;
};
</script>

<template>
  <header class="navbar-container">
    <div class="navbar-left">
      <div class="logo-badge" @click="emit('selectTab', 'matches')" style="cursor: pointer">
        <div class="logo-icon-wrap">
          <Swords :size="22" class="logo-icon text-cyan" />
        </div>
        <div class="logo-text">
          <span class="brand-title">TFT TEAM STRENGTH</span>
          <span class="brand-subtitle">Enchanted Wilds • Set 18</span>
        </div>
      </div>

      <nav class="nav-links">
        <button
          @click="emit('selectTab', 'matches')"
          :class="['nav-link', { active: activeTab === 'matches' }]"
        >
          Match History
        </button>

        <button
          @click="emit('selectTab', 'board')"
          :class="['nav-link studio-nav-link', { active: activeTab === 'board' }]"
        >
          <Grid3X3 :size="14" class="text-emerald" />
          <span>Board Review</span>
        </button>
      </nav>
    </div>

    <div class="navbar-right">
      <div v-if="user" class="user-dropdown-container">
        <button class="user-profile-btn" @click="toggleDropdown">
          <img
            :src="
              user.avatar ||
              'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150&auto=format&fit=crop&q=80'
            "
            :alt="user.name || 'User Avatar'"
            class="user-avatar"
          />
          <div class="user-text-info">
            <span class="user-display-name">{{ user.name || 'Summoner' }}</span>
            <span class="user-email-text">{{ user.email }}</span>
          </div>
          <ChevronDown :size="14" class="dropdown-arrow" />
        </button>

        <div v-if="dropdownOpen" class="dropdown-menu" @click="closeDropdown">
          <div class="dropdown-header">
            <span class="user-full-name">{{ user.name || 'Summoner' }}</span>
            <span class="user-full-email">{{ user.email }}</span>
          </div>
          <div class="dropdown-divider"></div>
          <div class="dropdown-item">
            <Shield :size="14" class="text-emerald" />
            <span>Session Active (Protected)</span>
          </div>
          <div class="dropdown-divider"></div>
          <button @click="emit('logout')" class="dropdown-item btn-logout-item">
            <LogOut :size="14" />
            <span>Sign Out</span>
          </button>
        </div>
      </div>

      <button
        v-else
        @click="emit('googleLogin')"
        class="google-sign-in-btn"
        id="btn-google-login"
      >
        <svg class="google-icon" viewBox="0 0 24 24">
          <path
            fill="#4285F4"
            d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.82-2.4 3.68v3.05h3.88c2.27-2.09 3.665-5.17 3.665-9.17z"
          />
          <path
            fill="#34A853"
            d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.05c-1.08.72-2.45 1.16-4.05 1.16-3.12 0-5.77-2.1-6.72-4.93H1.25v3.15C3.26 21.36 7.34 24 12 24z"
          />
          <path
            fill="#FBBC05"
            d="M5.28 14.27c-.25-.72-.38-1.49-.38-2.27s.13-1.55.38-2.27V6.58H1.25C.45 8.18 0 9.99 0 12s.45 3.82 1.25 5.42l4.03-3.15z"
          />
          <path
            fill="#EA4335"
            d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.34 0 3.26 2.64 1.25 6.58l4.03 3.15c.95-2.83 3.6-4.98 6.72-4.98z"
          />
        </svg>
        <span>Sign In with Google</span>
      </button>
    </div>
  </header>
</template>
