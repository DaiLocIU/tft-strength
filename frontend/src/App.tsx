import React, { useEffect, useState } from 'react';
import confetti from 'canvas-confetti';
import { Navbar } from './components/Navbar';
import { MatchesDashboard } from './components/MatchesDashboard';
import { CreateMatchModal } from './components/CreateMatchModal';
import { IconStudio } from './components/IconStudio';
import { api, getUser, setAuthData } from './services/api';
import { Match, User } from './types';

export const App: React.FC = () => {
  const [user, setUser] = useState<User | null>(getUser());
  const [activeTab, setActiveTab] = useState<'matches' | 'studio'>('matches');
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

      setAuthData({ accessToken, refreshToken }, parsedUser);
      setUser(parsedUser);
      window.history.replaceState({}, document.title, window.location.pathname);

      confetti({
        particleCount: 75,
        spread: 60,
        origin: { y: 0.6 },
        colors: ['#00f2fe', '#4facfe', '#10b981', '#f59e0b'],
      });

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

  const handleGoogleLogin = () => {
    api.loginWithGoogle();
  };

  const handleCreateMatch = async (matchData: Partial<Match>) => {
    await api.createMatch(matchData);
    const updated = await api.getMatches();
    setMatches(updated);
    triggerConfetti();
  };

  const handleLogout = async () => {
    await api.logout();
    setUser(null);
    setMatches(null);
    setError401(null);
    setActiveTab('matches');
  };

  return (
    <div className="app-layout">
      {/* App Header */}
      <Navbar
        user={user}
        activeTab={activeTab}
        onSelectTab={(t) => setActiveTab(t as 'matches' | 'studio')}
        onGoogleLogin={handleGoogleLogin}
        onLogout={handleLogout}
      />

      {/* Main Content */}
      <main className="main-content">
        {activeTab === 'studio' ? (
          <IconStudio user={user} />
        ) : (
          <MatchesDashboard
            matches={matches}
            loading={loading}
            error401={error401}
            user={user}
            onLoadMatches={handleLoadMatches}
            onOpenCreateMatch={() => setIsCreateMatchOpen(true)}
            onGoogleLogin={handleGoogleLogin}
          />
        )}
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
