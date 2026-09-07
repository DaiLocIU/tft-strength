export interface User {
  id: number;
  email: string;
  name?: string;
  avatar?: string;
  googleId?: string;
  createdAt?: string;
  updatedAt?: string;
}

export interface TokensResponse {
  accessToken: string;
  refreshToken: string;
}

export interface Match {
  comp?: string;
  playedAt?: string;
  version?: string;
  id: number;
  userId: number;
  placement: number;
  gameMode?: string;
  augments?: string[];
  champions?: {
    name: string;
    cost: number;
    stars: number;
    items?: string[];
  }[];
  traits?: {
    name: string;
    tier: number;
    activeCount: number;
  }[];
  damageDealt?: number;
  goldLeft?: number;
  roundsSurvived?: number;
  createdAt: string;
}

export interface TftChampionAsset {
  id: string;
  apiName: string;
  name: string;
  cost: number | null;
  imageUrl: string | null;
  traits: string[];
}

export interface TftSetChampionsResponse {
  set: number;
  locale: string;
  source: 'communitydragon';
  champions: TftChampionAsset[];
}

export interface BoardStateUnit {
  row: number;
  column: number;
  champion: string;
  raw_champion?: string | null;
  source: string;
  occupancy_confidence?: number | null;
  champion_confidence?: number | null;
  identity_confidence?: number | null;
  star?: string | null;
  star_confidence?: number | null;
  needs_review: boolean;
  review_reason?: string | null;
}

export interface HudField {
  value: number | string | null;
  confidence: number | null;
  source: 'ocr';
  needs_review: boolean;
  reason: string;
}

export interface BoardState {
  hud?: Partial<Record<'round' | 'level' | 'gold' | 'hp' | 'streak', HudField>>;
  image_name: string;
  units: BoardStateUnit[];
  review?: {
    low_identity_confidence?: BoardStateUnit[];
    missing_hexes?: {
      row: number;
      column: number;
      reason: string;
      occupancy_confidence?: number | null;
    }[];
    [key: string]: unknown;
  };
  parameters?: Record<string, unknown>;
}

export interface BoardStateDraft {
  id: number;
  userId: number;
  matchId: number | null;
  roundId: number | null;
  screenshotFilename: string;
  originalFilename: string;
  storagePath: string;
  status: 'uploaded' | 'detected' | 'failed';
  boardState: BoardState | null;
  errorMessage: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface SaveBoardRound {
  matchId: number;
  stage: number;
  roundNumber: number;
  gold: number;
  hp: number;
  level: number;
  streak: number;
  units: { row: number; column: number; champion: string; stars: number }[];
}

export interface BoardGuide {
  round: string;
  tips: { title: string; detail: string }[];
  basis: string;
}

export interface RoundSnapshot {
  id: number;
  matchId: number;
  stage: number;
  roundNumber: number;
  level: number;
  gold: number;
  hp: number;
  streak: number;
  boardStateDrafts?: {
    id: number;
    originalFilename: string;
    boardState: BoardState | null;
  }[];
}
