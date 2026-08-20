# TFT Team Strength — Frontend Web Application

A modern, production-grade **React + TypeScript + Vite + Axios** web application for tracking TFT (Teamfight Tactics) match history, team compositions, synergies, and player statistics with secure Google Authentication and automatic silent token refresh.

---

## 🚀 Getting Started

### 1. Start the NestJS Backend
In the project root:
```bash
pnpm start:dev
```
Backend runs at `http://localhost:3000`.

### 2. Start the Frontend Application
In the project root:
```bash
pnpm frontend:dev
```
Frontend runs at `http://localhost:5173`.

---

## 🌟 Application Features

- **Google Authentication**: One-click Google sign-in integrating with NestJS Passport OAuth & PostgreSQL database user provisioning.
- **Protected Match History**: Securely fetch and display match results with traits, synergies, champion tiers, augment chips, and damage metrics.
- **Match Recording**: Log new TFT matches with custom placement (#1 - #8), damage, gold, and game mode.
- **Stats Dashboard**: Real-time calculation of Win Rate %, Top 4 Rate %, Total Matches, and Average Placement.
- **Silent JWT Token Rotation**: Built-in Axios interceptor that catches expired access tokens (401), silently refreshes them via `/auth/refresh` in the background, and seamlessly retries failed requests without interrupting the user experience.
