import type { MatchModel } from '../../../generated/prisma/models/Match';
import type { RoundModel } from '../../../generated/prisma/models/Round';

export type MatchTimelineAggregate = MatchModel & {
  rounds: RoundModel[];
};

export interface CreateMatchData {
  userId: number;
  placement?: number | null;
  playedAt?: Date;
  name?: string;
  comp?: string;
}

export interface UpdateMatchData {
  placement?: number | null;
  playedAt?: Date;
  name?: string;
  comp?: string;
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

  // Aggregate operations
  findMatchWithRounds(
    id: number,
    userId?: number,
  ): Promise<MatchTimelineAggregate | null>;
  findAllMatchesWithRounds(userId: number): Promise<MatchTimelineAggregate[]>;

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
