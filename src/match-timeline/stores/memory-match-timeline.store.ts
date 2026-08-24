import { MatchModel } from '../../../generated/prisma/models/Match';
import { RoundModel } from '../../../generated/prisma/models/Round';
import {
  CreateMatchData,
  CreateRoundData,
  MatchTimelineStore,
  UpdateMatchData,
  UpdateRoundData,
} from './match-timeline.store.interface';

export class MemoryMatchTimelineStore implements MatchTimelineStore {
  private matches: MatchModel[] = [];
  private rounds: RoundModel[] = [];
  private nextMatchId = 1;
  private nextRoundId = 1;

  async createMatch(data: CreateMatchData): Promise<MatchModel> {
    const match: MatchModel = {
      id: this.nextMatchId++,
      userId: data.userId,
      placement: data.placement,
      playedAt: data.playedAt ?? new Date(),
      comp: data.comp ?? null,
      version: data.version ?? null,
    };
    this.matches.push(match);
    return { ...match };
  }

  async findAllMatches(userId: number): Promise<MatchModel[]> {
    return this.matches
      .filter((m) => m.userId === userId)
      .sort((a, b) => b.playedAt.getTime() - a.playedAt.getTime())
      .map((m) => ({ ...m }));
  }

  async findMatchById(id: number, userId?: number): Promise<MatchModel | null> {
    const match = this.matches.find(
      (m) => m.id === id && (userId === undefined || m.userId === userId),
    );
    return match ? { ...match } : null;
  }

  async updateMatch(id: number, data: UpdateMatchData): Promise<MatchModel> {
    const index = this.matches.findIndex((m) => m.id === id);
    if (index === -1) {
      throw new Error(`Match #${id} not found in memory store`);
    }

    const current = this.matches[index];
    const updated: MatchModel = {
      ...current,
      placement: data.placement ?? current.placement,
      playedAt: data.playedAt ?? current.playedAt,
      comp: data.comp !== undefined ? (data.comp ?? null) : current.comp,
      version:
        data.version !== undefined ? (data.version ?? null) : current.version,
    };
    this.matches[index] = updated;
    return { ...updated };
  }

  async deleteMatch(id: number): Promise<MatchModel> {
    const index = this.matches.findIndex((m) => m.id === id);
    if (index === -1) {
      throw new Error(`Match #${id} not found in memory store`);
    }

    const [deleted] = this.matches.splice(index, 1);
    // Cascade delete rounds
    this.rounds = this.rounds.filter((r) => r.matchId !== id);
    return { ...deleted };
  }

  async createRound(data: CreateRoundData): Promise<RoundModel> {
    const round: RoundModel = {
      id: this.nextRoundId++,
      matchId: data.matchId,
      stage: data.stage,
      roundNumber: data.roundNumber,
      gold: data.gold,
      hp: data.hp,
      level: data.level,
      streak: data.streak,
    };
    this.rounds.push(round);
    return { ...round };
  }

  async findAllRounds(matchId: number): Promise<RoundModel[]> {
    return this.rounds
      .filter((r) => r.matchId === matchId)
      .sort((a, b) => {
        if (a.stage !== b.stage) return a.stage - b.stage;
        return a.roundNumber - b.roundNumber;
      })
      .map((r) => ({ ...r }));
  }

  async findRoundById(id: number, matchId: number): Promise<RoundModel | null> {
    const round = this.rounds.find((r) => r.id === id && r.matchId === matchId);
    return round ? { ...round } : null;
  }

  async findRoundByStageAndNumber(
    matchId: number,
    stage: number,
    roundNumber: number,
  ): Promise<RoundModel | null> {
    const round = this.rounds.find(
      (r) =>
        r.matchId === matchId &&
        r.stage === stage &&
        r.roundNumber === roundNumber,
    );
    return round ? { ...round } : null;
  }

  async updateRound(id: number, data: UpdateRoundData): Promise<RoundModel> {
    const index = this.rounds.findIndex((r) => r.id === id);
    if (index === -1) {
      throw new Error(`Round #${id} not found in memory store`);
    }

    const current = this.rounds[index];
    const updated: RoundModel = {
      ...current,
      stage: data.stage ?? current.stage,
      roundNumber: data.roundNumber ?? current.roundNumber,
      gold: data.gold ?? current.gold,
      hp: data.hp ?? current.hp,
      level: data.level ?? current.level,
      streak: data.streak ?? current.streak,
    };
    this.rounds[index] = updated;
    return { ...updated };
  }

  async deleteRound(id: number): Promise<RoundModel> {
    const index = this.rounds.findIndex((r) => r.id === id);
    if (index === -1) {
      throw new Error(`Round #${id} not found in memory store`);
    }

    const [deleted] = this.rounds.splice(index, 1);
    return { ...deleted };
  }

  reset() {
    this.matches = [];
    this.rounds = [];
    this.nextMatchId = 1;
    this.nextRoundId = 1;
  }
}
