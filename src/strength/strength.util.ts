export interface RoundChampionInput {
  cost: number; // 1-5
  starLevel: number; // 1-3
}

export interface RoundInput {
  placement: number; // 1-8
  level: number; // player level, e.g. 1-9
  goldLeft: number;
  champions: RoundChampionInput[];
}

export interface RoundStrength {
  placementScore: number;
  boardScore: number;
  economyScore: number;
  total: number; // 0-100
}

export function scoreRound(round: RoundInput): RoundStrength {
  // 1. Placement: 1st = 100, 8th = 0
  const placementScore = ((8 - round.placement) / 7) * 100;

  // 2. Board strength: sum of (cost * starLevel^1.5), normalized
  //    star^1.5 rewards 2/3-stars more than linear, matching TFT power curve
  const rawBoard = round.champions.reduce(
    (sum, c) => sum + c.cost * Math.pow(c.starLevel, 1.5),
    0,
  );
  // rough cap for normalization: 9 champs at cost 5, 3-star (~ a very strong board)
  const maxBoard = 9 * 5 * Math.pow(3, 1.5);
  const boardScore = Math.min((rawBoard / maxBoard) * 100, 100);

  // 3. Economy: level + leftover gold, capped
  const economyScore = Math.min(round.level * 8 + round.goldLeft * 1.5, 100);

  // Weighted total: placement matters most, board second, economy least
  const total = placementScore * 0.5 + boardScore * 0.35 + economyScore * 0.15;

  return {
    placementScore: round1(placementScore),
    boardScore: round1(boardScore),
    economyScore: round1(economyScore),
    total: round1(total),
  };
}

function round1(n: number): number {
  return Math.round(n * 10) / 10;
}
