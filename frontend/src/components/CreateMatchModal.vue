<script setup lang="ts">
import { ref } from 'vue';
import { X, Swords, Sparkles, Loader2 } from 'lucide-vue-next';
import { Match } from '../types';

const props = defineProps<{
  isOpen: boolean;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'submit', matchData: Partial<Match>): void;
}>();

const placement = ref<number>(1);
const gameMode = ref('Ranked (Set 13)');
const damageDealt = ref(145000);
const goldLeft = ref(42);
const roundsSurvived = ref(36);
const loading = ref(false);

const handleSubmit = async () => {
  loading.value = true;
  try {
    emit('submit', {
      placement: placement.value,
      gameMode: gameMode.value,
      damageDealt: damageDealt.value,
      goldLeft: goldLeft.value,
      roundsSurvived: roundsSurvived.value,
      augments: ['Prismatic Ticket', 'Cybernetic Uplink III', 'Binary Airdrop'],
      traits: [
        { name: 'Rebel', tier: 3, activeCount: 7 },
        { name: 'Sorcerer', tier: 2, activeCount: 4 },
        { name: 'Bruiser', tier: 1, activeCount: 2 },
      ],
      champions: [
        { name: 'Jinx', cost: 4, stars: 3, items: ['Infinity Edge', 'Guinsoo Rageblade', 'Giant Slayer'] },
        { name: 'Vi', cost: 4, stars: 2, items: ['Warmog Armor', 'Sunfire Cape', 'Dragon Claw'] },
        { name: 'Ekko', cost: 3, stars: 3, items: ['Hand of Justice', 'Ionic Spark'] },
        { name: 'Sevika', cost: 5, stars: 2, items: ['Bloodthirster', 'Titan Resolve'] },
      ],
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
        <button class="modal-btn-close" @click="emit('close')">
          <X :size="18" />
        </button>
      </div>

      <form @submit.prevent="handleSubmit" class="modal-form">
        <div class="form-group">
          <label>Final Placement</label>
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
            <label>Game Mode</label>
            <select v-model="gameMode" class="form-input">
              <option value="Ranked (Set 13)">Ranked (Set 13)</option>
              <option value="Normal">Normal</option>
              <option value="Hyper Roll">Hyper Roll</option>
              <option value="Double Up">Double Up</option>
            </select>
          </div>

          <div class="form-group">
            <label>Rounds Survived</label>
            <input
              type="number"
              v-model.number="roundsSurvived"
              class="form-input"
              :min="1"
              :max="50"
            />
          </div>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label>Total Damage Dealt</label>
            <input
              type="number"
              v-model.number="damageDealt"
              class="form-input"
              :step="1000"
            />
          </div>

          <div class="form-group">
            <label>Gold Left</label>
            <input
              type="number"
              v-model.number="goldLeft"
              class="form-input"
              :min="0"
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
