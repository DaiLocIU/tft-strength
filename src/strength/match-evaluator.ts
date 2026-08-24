import { RoundChampionInput, RoundStrength, scoreRound } from './strength.util';

export interface EvaluatedRoundSnapshot {
  stage: number;
  roundNumber: number;
  gold: number;
  level: number;
  hp?: number;
  streak?: number;
  champions?: (
    | RoundChampionInput
    | { champion?: { cost: number }; cost?: number; starLevel?: number }
  )[];
}

export interface MatchEvaluationInput {
  id?: number;
  placement: number;
  rounds: EvaluatedRoundSnapshot[];
}

export interface EvaluatedRoundScore extends RoundStrength {
  stage: number;
  roundNumber: number;
}

export interface MatchEvaluationResult {
  matchId?: number;
  overallStrength: number;
  rounds: EvaluatedRoundScore[];
}

export function evaluateMatch(
  match: MatchEvaluationInput,
): MatchEvaluationResult {
  const roundScores: EvaluatedRoundScore[] = match.rounds.map((r) => {
    const rawChamps = r.champions ?? [];
    const champions: RoundChampionInput[] = rawChamps.map((rc) => {
      const championObj = (rc as { champion?: { cost: number } }).champion;
      const cost = championObj?.cost ?? (rc as { cost?: number }).cost ?? 1;
      const starLevel = (rc as { starLevel?: number }).starLevel ?? 1;
      return { cost, starLevel };
    });

    const score = scoreRound({
      placement: match.placement,
      level: r.level,
      goldLeft: r.gold,
      champions,
    });

    return {
      stage: r.stage,
      roundNumber: r.roundNumber,
      ...score,
    };
  });

  const overall =
    roundScores.length > 0
      ? roundScores.reduce((sum, r) => sum + r.total, 0) / roundScores.length
      : 0;

  return {
    matchId: match.id,
    overallStrength: Math.round(overall * 10) / 10,
    rounds: roundScores,
  };
}
