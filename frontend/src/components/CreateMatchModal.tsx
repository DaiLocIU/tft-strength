import React, { useState } from 'react';
import { X, Swords, Sparkles, Loader2 } from 'lucide-react';
import { Match } from '../types';

interface CreateMatchModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (matchData: Partial<Match>) => Promise<void>;
}

export const CreateMatchModal: React.FC<CreateMatchModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
}) => {
  const [placement, setPlacement] = useState<number>(1);
  const [gameMode, setGameMode] = useState('Ranked (Set 13)');
  const [damageDealt, setDamageDealt] = useState(145000);
  const [goldLeft, setGoldLeft] = useState(42);
  const [roundsSurvived, setRoundsSurvived] = useState(36);
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await onSubmit({
        placement,
        gameMode,
        damageDealt,
        goldLeft,
        roundsSurvived,
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
      onClose();
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="create-match-modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-top-bar">
          <div className="modal-title-group">
            <Swords size={20} className="text-amber" />
            <h2>Record TFT Match</h2>
          </div>
          <button className="modal-btn-close" onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="modal-form">
          <div className="form-group">
            <label>Final Placement</label>
            <div className="placement-selector-grid">
              {[1, 2, 3, 4, 5, 6, 7, 8].map((p) => (
                <button
                  type="button"
                  key={p}
                  className={`placement-choice-btn ${placement === p ? 'active' : ''} ${
                    p === 1 ? 'choice-1' : p <= 4 ? 'choice-top4' : 'choice-bot4'
                  }`}
                  onClick={() => setPlacement(p)}
                >
                  #{p}
                </button>
              ))}
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Game Mode</label>
              <select
                value={gameMode}
                onChange={(e) => setGameMode(e.target.value)}
                className="form-input"
              >
                <option value="Ranked (Set 13)">Ranked (Set 13)</option>
                <option value="Normal">Normal</option>
                <option value="Hyper Roll">Hyper Roll</option>
                <option value="Double Up">Double Up</option>
              </select>
            </div>

            <div className="form-group">
              <label>Rounds Survived</label>
              <input
                type="number"
                value={roundsSurvived}
                onChange={(e) => setRoundsSurvived(Number(e.target.value))}
                className="form-input"
                min={1}
                max={50}
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Total Damage Dealt</label>
              <input
                type="number"
                value={damageDealt}
                onChange={(e) => setDamageDealt(Number(e.target.value))}
                className="form-input"
                step={1000}
              />
            </div>

            <div className="form-group">
              <label>Gold Left</label>
              <input
                type="number"
                value={goldLeft}
                onChange={(e) => setGoldLeft(Number(e.target.value))}
                className="form-input"
                min={0}
              />
            </div>
          </div>

          <div className="modal-actions-row">
            <button type="button" onClick={onClose} className="btn-form-cancel">
              Cancel
            </button>
            <button type="submit" disabled={loading} className="btn-form-submit">
              {loading ? <Loader2 size={16} className="animate-spin" /> : <Sparkles size={16} />}
              <span>Save Match Record</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
