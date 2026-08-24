import { Inject, Injectable } from '@nestjs/common';
import {
  MATCH_TIMELINE_STORE,
  type MatchTimelineStore,
} from '../match-timeline/stores/match-timeline.store.interface';
import { evaluateMatch } from '../strength/match-evaluator';

export interface CompStat {
  compName: string;
  games: number;
  winRate: number;
  top4Rate: number;
}

export interface StrengthCurvePoint {
  matchId: number;
  date: Date;
  strength: number;
  placement: number;
}

export interface UserStatsResponse {
  compStats: CompStat[];
  strengthCurve: StrengthCurvePoint[];
}

@Injectable()
export class StatsService {
  constructor(
    @Inject(MATCH_TIMELINE_STORE)
    private readonly store: MatchTimelineStore,
  ) {}

  async getStats(userId: number): Promise<UserStatsResponse> {
    const matches = await this.store.findAllMatchesWithRounds(userId);

    if (matches.length === 0) {
      return { compStats: [], strengthCurve: [] };
    }

    // --- Win rate by comp ---
    const compMap = new Map<
      string,
      { games: number; wins: number; top4s: number }
    >();

    for (const m of matches) {
      const key = m.comp ?? 'Unknown';
      const entry = compMap.get(key) ?? { games: 0, wins: 0, top4s: 0 };
      entry.games += 1;
      if (m.placement === 1) entry.wins += 1;
      if (m.placement <= 4) entry.top4s += 1;
      compMap.set(key, entry);
    }

    const compStats: CompStat[] = Array.from(compMap.entries()).map(
      ([compName, s]) => ({
        compName,
        games: s.games,
        winRate: this.round1((s.wins / s.games) * 100),
        top4Rate: this.round1((s.top4s / s.games) * 100),
      }),
    );

    // --- Strength curve ---
    const strengthCurve: StrengthCurvePoint[] = matches.map((m) => {
      const evaluated = evaluateMatch(m);

      return {
        matchId: m.id,
        date: m.playedAt,
        strength: evaluated.overallStrength,
        placement: m.placement,
      };
    });

    return { compStats, strengthCurve };
  }

  private round1(n: number): number {
    return Math.round(n * 10) / 10;
  }
}
