export type BoardStateDraftStatus = 'draft' | 'uploading' | 'uploaded' | 'processing' | 'completed' | 'detected' | 'failed';

export interface UploadedImageFile {
  originalname: string;
  filename?: string;
  path?: string;
  buffer?: Buffer;
  size: number;
  mimetype: string;
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
  review?: Record<string, unknown>;
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
  status: BoardStateDraftStatus;
  boardState: BoardState | null;
  errorMessage: string | null;
  createdAt: Date;
  updatedAt: Date;
}

export interface CreateBoardStateDraftData {
  status?: BoardStateDraftStatus;
  userId: number;
  matchId?: number;
  roundId?: number;
  screenshotFilename: string;
  originalFilename: string;
  storagePath: string;
}

export interface UpdateBoardStateDraftData {
  storagePath?: string;
  status?: BoardStateDraftStatus;
  boardState?: BoardState | null;
  errorMessage?: string | null;
}
