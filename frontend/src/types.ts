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
