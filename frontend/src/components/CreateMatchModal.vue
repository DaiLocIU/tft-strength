<script setup lang="ts">
import { ref, watch } from 'vue';
import { X, Swords, Sparkles, Loader2 } from 'lucide-vue-next';
import { Match } from '../types';

const props = defineProps<{
  isOpen: boolean;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'submit', matchData: Partial<Match>): void;
}>();

const name = ref('');
const placement = ref<number | null>(null);
const loading = ref(false);

watch(
  () => props.isOpen,
  (isOpen) => {
    if (!isOpen) return;
    name.value = '';
    placement.value = null;
  },
);

const handleSubmit = async () => {
  loading.value = true;
  try {
    emit('submit', {
      placement: placement.value,
      name: name.value.trim() || undefined,
    });
    emit('close');
  } finally {
    loading.value = false;
  }
};
</script>

<template>
  <div v-if="isOpen" class="modal-overlay" @click="emit('close')">
    <div class="create-match-modal-card" @click.stop>
      <div class="modal-top-bar">
        <div class="modal-title-group">
          <Swords :size="20" class="text-amber" />
          <h2>Record TFT Match</h2>
        </div>
        <button class="modal-btn-close" aria-label="Close record match dialog" @click="emit('close')">
          <X :size="18" />
        </button>
      </div>

      <form @submit.prevent="handleSubmit" class="modal-form">
        <div class="form-group">
          <label>Final Placement <span class="form-optional">(optional)</span></label>
          <div class="placement-selector-grid">
            <button
              v-for="p in [1, 2, 3, 4, 5, 6, 7, 8]"
              :key="p"
              type="button"
              :class="[
                'placement-choice-btn',
                { active: placement === p },
                p === 1 ? 'choice-1' : p <= 4 ? 'choice-top4' : 'choice-bot4',
              ]"
              @click="placement = p"
            >
              #{{ p }}
            </button>
          </div>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label for="match-version">TFT Set</label>
            <input id="match-version" value="Set 18" class="form-input" disabled />
          </div>

          <div class="form-group">
            <label for="match-name">Name <span class="form-optional">(optional)</span></label>
            <input
              id="match-name"
              v-model="name"
              type="text"
              class="form-input"
              maxlength="255"
              placeholder="e.g. Climb to Diamond"
            />
          </div>
        </div>

        <div class="modal-actions-row">
          <button type="button" @click="emit('close')" class="btn-form-cancel">
            Cancel
          </button>
          <button type="submit" :disabled="loading" class="btn-form-submit">
            <Loader2 v-if="loading" :size="16" class="animate-spin" />
            <Sparkles v-else :size="16" />
            <span>Save Match Record</span>
          </button>
        </div>
      </form>
    </div>
  </div>
</template>
