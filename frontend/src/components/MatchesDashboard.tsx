import React, { useState } from 'react';
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
} from 'lucide-react';
import { Match, User } from '../types';

interface MatchesDashboardProps {
  matches: Match[] | null;
  loading: boolean;
  error401: string | null;
  user: User | null;
  onLoadMatches: () => void;
  onOpenCreateMatch: () => void;
  onGoogleLogin: () => void;
}

export const MatchesDashboard: React.FC<MatchesDashboardProps> = ({
  matches,
  loading,
  error401,
  user,
  onLoadMatches,
  onOpenCreateMatch,
  onGoogleLogin,
}) => {
  const [filter, setFilter] = useState<'all' | 'top4' | 'win'>('all');

  // Stats calculation
  const totalMatches = matches ? matches.length : 0;
  const wins = matches ? matches.filter((m) => m.placement === 1).length : 0;
  const top4s = matches ? matches.filter((m) => m.placement <= 4).length : 0;
  const avgPlacement =
    matches && matches.length > 0
      ? (
          matches.reduce((acc, m) => acc + m.placement, 0) / matches.length
        ).toFixed(1)
      : '—';
  const winRate =
    totalMatches > 0 ? Math.round((wins / totalMatches) * 100) : 0;
  const top4Rate =
    totalMatches > 0 ? Math.round((top4s / totalMatches) * 100) : 0;

  const filteredMatches = matches
    ? matches.filter((m) => {
        if (filter === 'win') return m.placement === 1;
        if (filter === 'top4') return m.placement <= 4;
        return true;
      })
    : [];

  return (
    <div className="matches-dashboard-wrapper">
      {/* 1. Header and Action Bar */}
      <div className="dashboard-header-card">
        <div className="dashboard-title-group">
          <div className="icon-badge">
            <Trophy size={22} className="text-amber" />
          </div>
          <div>
            <h1 className="dashboard-main-title">Match History</h1>
            <p className="dashboard-subtext">
              Track your TFT team compositions, synergies, and placement rankings
            </p>
          </div>
        </div>

        <div className="dashboard-action-buttons">
          <button
            onClick={onLoadMatches}
            disabled={loading}
            className="btn-refresh-data"
            id="btn-load-matches"
          >
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
            <span>{loading ? 'Fetching...' : matches ? 'Refresh Matches' : 'Load My Matches'}</span>
          </button>

          {user && (
            <button
              onClick={onOpenCreateMatch}
              className="btn-create-match"
              id="btn-add-match"
            >
              <PlusCircle size={16} />
              <span>Record Match</span>
            </button>
          )}
        </div>
      </div>

      {/* 2. Stats Summary Row (When matches exist) */}
      {matches && matches.length > 0 && (
        <div className="stats-summary-grid">
          <div className="stat-card">
            <div className="stat-card-header">
              <span className="stat-label">Total Matches</span>
              <Layers size={16} className="text-cyan" />
            </div>
            <span className="stat-value">{totalMatches}</span>
          </div>

          <div className="stat-card">
            <div className="stat-card-header">
              <span className="stat-label">1st Place Wins</span>
              <Award size={16} className="text-amber" />
            </div>
            <span className="stat-value text-amber">{wins} ({winRate}%)</span>
          </div>

          <div className="stat-card">
            <div className="stat-card-header">
              <span className="stat-label">Top 4 Rate</span>
              <Flame size={16} className="text-emerald" />
            </div>
            <span className="stat-value text-emerald">{top4s} ({top4Rate}%)</span>
          </div>

          <div className="stat-card">
            <div className="stat-card-header">
              <span className="stat-label">Avg Placement</span>
              <Trophy size={16} className="text-indigo" />
            </div>
            <span className="stat-value">#{avgPlacement}</span>
          </div>
        </div>
      )}

      {/* 3. 401 UNAUTHORIZED ALERT (When unauthenticated) */}
      {error401 && (
        <div className="unauthorized-card" id="error-401-banner">
          <div className="alert-icon-circle">
            <AlertTriangle size={24} className="text-red" />
          </div>
          <div className="alert-body">
            <div className="alert-heading-row">
              <span className="error-pill">401 Unauthorized</span>
              <h3>Authentication Required</h3>
            </div>
            <p className="alert-text">
              {error401}
            </p>
            <p className="alert-subtext">
              Please sign in with your Google account to securely access your personal match records.
            </p>
            <div className="alert-cta-row">
              <button onClick={onGoogleLogin} className="btn-alert-signin">
                <span>Sign In with Google</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 4. LOADING STATE */}
      {loading && !matches && (
        <div className="loading-container">
          <div className="spinner-glow"></div>
          <p>Loading your TFT match history...</p>
        </div>
      )}

      {/* 5. GUEST EMPTY STATE */}
      {!matches && !error401 && !loading && (
        <div className="guest-card">
          <div className="guest-hero-icon">
            <Swords size={36} className="text-cyan" />
          </div>
          <h2>Welcome to TFT Team Strength</h2>
          <p>
            Analyze your team builds, champion star levels, augment choices, and synergy power across games.
          </p>
          <div className="guest-cta-group">
            <button onClick={onLoadMatches} className="btn-guest-load">
              <span>View Match Records</span>
            </button>
            <button onClick={onGoogleLogin} className="btn-guest-login">
              <span>Sign In with Google</span>
            </button>
          </div>
        </div>
      )}

      {/* 6. AUTHENTICATED MATCHES LIST */}
      {matches && matches.length > 0 && (
        <div className="matches-section">
          <div className="filter-bar">
            <div className="filter-label-wrap">
              <Filter size={15} className="text-muted" />
              <span>Filter:</span>
            </div>
            <div className="filter-chips">
              <button
                className={`filter-chip ${filter === 'all' ? 'active' : ''}`}
                onClick={() => setFilter('all')}
              >
                All Matches ({matches.length})
              </button>
              <button
                className={`filter-chip ${filter === 'win' ? 'active' : ''}`}
                onClick={() => setFilter('win')}
              >
                Victories ({wins})
              </button>
              <button
                className={`filter-chip ${filter === 'top4' ? 'active' : ''}`}
                onClick={() => setFilter('top4')}
              >
                Top 4 ({top4s})
              </button>
            </div>
          </div>

          <div className="matches-list">
            {filteredMatches.map((match) => {
              const isVictory = match.placement === 1;
              const isTop4 = match.placement <= 4;

              return (
                <div
                  key={match.id}
                  className={`match-item-card ${
                    isVictory ? 'placement-1' : isTop4 ? 'placement-top4' : 'placement-bot4'
                  }`}
                >
                  <div className="match-left-column">
                    <div className={`placement-tag ${isVictory ? 'tag-win' : isTop4 ? 'tag-top4' : 'tag-bot4'}`}>
                      <span className="placement-number">#{match.placement}</span>
                      <span className="placement-text">{isVictory ? 'Victory' : isTop4 ? 'Top 4' : 'Defeat'}</span>
                    </div>

                    <div className="match-meta-details">
                      <span className="game-mode-tag">{match.gameMode || 'Ranked TFT'}</span>
                      <span className="rounds-survived-tag">Stage {match.roundsSurvived || 35}</span>
                    </div>
                  </div>

                  <div className="match-center-column">
                    {/* Synergies */}
                    {match.traits && match.traits.length > 0 && (
                      <div className="traits-badge-list">
                        {match.traits.map((trait, idx) => (
                          <div key={idx} className={`trait-badge tier-${trait.tier}`}>
                            <Users size={11} />
                            <span>{trait.name} ({trait.activeCount})</span>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Champions */}
                    {match.champions && match.champions.length > 0 && (
                      <div className="champions-tray">
                        {match.champions.map((champ, idx) => (
                          <div key={idx} className={`champ-card-item cost-${champ.cost}`}>
                            <div className="champ-star-rating">
                              {Array.from({ length: champ.stars }).map((_, sIdx) => (
                                <Star key={sIdx} size={9} fill="#f59e0b" color="#f59e0b" />
                              ))}
                            </div>
                            <span className="champ-card-name">{champ.name}</span>
                            {champ.items && champ.items.length > 0 && (
                              <div className="champ-items-dots">
                                {champ.items.map((item, iIdx) => (
                                  <span key={iIdx} className="item-badge-dot" title={item}></span>
                                ))}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Augments */}
                    {match.augments && match.augments.length > 0 && (
                      <div className="augments-tray">
                        {match.augments.map((aug, idx) => (
                          <span key={idx} className="augment-badge">
                            ⚡ {aug}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>

                  <div className="match-right-column">
                    <div className="game-stat-pill">
                      <span className="stat-title">Damage</span>
                      <span className="stat-number">{(match.damageDealt || 135000).toLocaleString()}</span>
                    </div>
                    <div className="game-stat-pill">
                      <span className="stat-title">Gold Left</span>
                      <span className="stat-number">💰 {match.goldLeft || 0}</span>
                    </div>
                    <span className="game-time">
                      {new Date(match.createdAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* 7. AUTHENTICATED BUT EMPTY DATABASE */}
      {matches && matches.length === 0 && (
        <div className="empty-matches-container">
          <Trophy size={48} className="text-muted" />
          <h3>No Match Records Yet</h3>
          <p>You haven't logged any TFT matches yet. Record your first game now!</p>
          <button onClick={onOpenCreateMatch} className="btn-create-first">
            <PlusCircle size={16} />
            <span>Record Your First Match</span>
          </button>
        </div>
      )}
    </div>
  );
};
