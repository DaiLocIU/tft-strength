import { MatchModel } from '../../../generated/prisma/models/Match';
import { RoundModel } from '../../../generated/prisma/models/Round';

export interface CreateMatchData {
  userId: number;
  placement: number;
  playedAt?: Date;
  comp?: string;
  version?: string;
}

export interface UpdateMatchData {
  placement?: number;
  playedAt?: Date;
  comp?: string;
  version?: string;
}

export interface CreateRoundData {
  matchId: number;
  stage: number;
  roundNumber: number;
  gold: number;
  hp: number;
  level: number;
  streak: number;
}

export interface UpdateRoundData {
  stage?: number;
  roundNumber?: number;
  gold?: number;
  hp?: number;
  level?: number;
  streak?: number;
}

export const MATCH_TIMELINE_STORE = Symbol('MATCH_TIMELINE_STORE');

export interface MatchTimelineStore {
  // Match operations
  createMatch(data: CreateMatchData): Promise<MatchModel>;
  findAllMatches(userId: number): Promise<MatchModel[]>;
  findMatchById(id: number, userId?: number): Promise<MatchModel | null>;
  updateMatch(id: number, data: UpdateMatchData): Promise<MatchModel>;
  deleteMatch(id: number): Promise<MatchModel>;

  // Round snapshot operations
  createRound(data: CreateRoundData): Promise<RoundModel>;
  findAllRounds(matchId: number): Promise<RoundModel[]>;
  findRoundById(id: number, matchId: number): Promise<RoundModel | null>;
  findRoundByStageAndNumber(
    matchId: number,
    stage: number,
    roundNumber: number,
  ): Promise<RoundModel | null>;
  updateRound(id: number, data: UpdateRoundData): Promise<RoundModel>;
  deleteRound(id: number): Promise<RoundModel>;
}
