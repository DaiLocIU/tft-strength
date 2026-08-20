import React, { useEffect, useState } from 'react';
import confetti from 'canvas-confetti';
import { Navbar } from './components/Navbar';
import { MatchesDashboard } from './components/MatchesDashboard';
import { CreateMatchModal } from './components/CreateMatchModal';
import { api, getUser, setAuthData } from './services/api';
import { Match, User } from './types';

export const App: React.FC = () => {
  const [user, setUser] = useState<User | null>(getUser());
  const [matches, setMatches] = useState<Match[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error401, setError401] = useState<string | null>(null);
  const [isCreateMatchOpen, setIsCreateMatchOpen] = useState(false);

  // 1. Handle OAuth redirect callback from NestJS (/auth/google/callback → FE redirect)
  useEffect(() => {
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
        // ignore parse error
      }

      // Save to localStorage + update in-memory tokens
      setAuthData({ accessToken, refreshToken }, parsedUser);

      // Directly update React state so Navbar re-renders immediately
      setUser(parsedUser);

      // Clean query params from URL bar
      window.history.replaceState({}, document.title, window.location.pathname);

      // Trigger celebration confetti
      confetti({ particleCount: 75, spread: 60, origin: { y: 0.6 }, colors: ['#00f2fe', '#4facfe', '#10b981', '#f59e0b'] });

      // Load matches right after login
      setTimeout(() => {
        handleLoadMatches();
      }, 100);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // 2. Auto-load matches if already logged in on page visit
  useEffect(() => {
    if (getUser()) {
      handleLoadMatches();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const triggerConfetti = () => {
    confetti({
      particleCount: 75,
      spread: 60,
      origin: { y: 0.6 },
      colors: ['#00f2fe', '#4facfe', '#10b981', '#f59e0b'],
    });
  };

  // 4. Fetch Matches from protected API (GET /matches)
  const handleLoadMatches = async () => {
    setLoading(true);
    setError401(null);
    try {
      const data = await api.getMatches();
      setMatches(data);
    } catch (err: any) {
      if (err.response?.status === 401) {
        setError401('401 Unauthorized - Please log in with Google to access your matches');
      } else {
        setError401(err.response?.data?.message || err.message || 'Error loading matches');
      }
      setMatches(null);
    } finally {
      setLoading(false);
    }
  };

  // 5. Direct Real Google Login (calls backend /auth/google)
  const handleGoogleLogin = () => {
    api.loginWithGoogle();
  };

  // 6. Create Match
  const handleCreateMatch = async (matchData: Partial<Match>) => {
    await api.createMatch(matchData);
    const updated = await api.getMatches();
    setMatches(updated);
    triggerConfetti();
  };

  // 7. Logout
  const handleLogout = async () => {
    await api.logout();
    setUser(null);
    setMatches(null);
    setError401(null);
  };

  return (
    <div className="app-layout">
      {/* App Header */}
      <Navbar
        user={user}
        onGoogleLogin={handleGoogleLogin}
        onLogout={handleLogout}
      />

      {/* Main Content */}
      <main className="main-content">
        <MatchesDashboard
          matches={matches}
          loading={loading}
          error401={error401}
          user={user}
          onLoadMatches={handleLoadMatches}
          onOpenCreateMatch={() => setIsCreateMatchOpen(true)}
          onGoogleLogin={handleGoogleLogin}
        />
      </main>

      {/* Create Match Modal */}
      <CreateMatchModal
        isOpen={isCreateMatchOpen}
        onClose={() => setIsCreateMatchOpen(false)}
        onSubmit={handleCreateMatch}
      />
    </div>
  );
};
