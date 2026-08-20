import React, { useState } from 'react';
import { Swords, LogOut, ChevronDown, Shield } from 'lucide-react';
import { User } from '../types';

interface NavbarProps {
  user: User | null;
  onGoogleLogin: () => void;
  onLogout: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  user,
  onGoogleLogin,
  onLogout,
}) => {
  const [dropdownOpen, setDropdownOpen] = useState(false);

  return (
    <header className="navbar-container">
      <div className="navbar-left">
        <div className="logo-badge">
          <div className="logo-icon-wrap">
            <Swords size={22} className="logo-icon text-cyan" />
          </div>
          <div className="logo-text">
            <span className="brand-title">TFT TEAM STRENGTH</span>
            <span className="brand-subtitle">Enchanted Wilds • Set 18</span>
          </div>
        </div>

        <nav className="nav-links">
          <a href="#matches" className="nav-link active">Match History</a>
          <a href="#meta" className="nav-link">Meta Comps</a>
          <a href="#builder" className="nav-link">Team Builder</a>
          <a href="#tierlist" className="nav-link">Tier List</a>
        </nav>
      </div>

      <div className="navbar-right">
        {user ? (
          <div className="user-dropdown-container">
            <button
              className="user-profile-btn"
              onClick={() => setDropdownOpen(!dropdownOpen)}
            >
              <img
                src={
                  user.avatar ||
                  'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150&auto=format&fit=crop&q=80'
                }
                alt={user.name || 'User Avatar'}
                className="user-avatar"
              />
              <div className="user-text-info">
                <span className="user-display-name">{user.name || 'Summoner'}</span>
                <span className="user-email-text">{user.email}</span>
              </div>
              <ChevronDown size={14} className="dropdown-arrow" />
            </button>

            {dropdownOpen && (
              <div className="dropdown-menu" onClick={() => setDropdownOpen(false)}>
                <div className="dropdown-header">
                  <span className="user-full-name">{user.name || 'Summoner'}</span>
                  <span className="user-full-email">{user.email}</span>
                </div>
                <div className="dropdown-divider"></div>
                <div className="dropdown-item">
                  <Shield size={14} className="text-emerald" />
                  <span>Session Active (Protected)</span>
                </div>
                <div className="dropdown-divider"></div>
                <button onClick={onLogout} className="dropdown-item btn-logout-item">
                  <LogOut size={14} />
                  <span>Sign Out</span>
                </button>
              </div>
            )}
          </div>
        ) : (
          <button
            onClick={onGoogleLogin}
            className="google-sign-in-btn"
            id="btn-google-login"
          >
            <svg className="google-icon" viewBox="0 0 24 24">
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
        )}
      </div>
    </header>
  );
};
