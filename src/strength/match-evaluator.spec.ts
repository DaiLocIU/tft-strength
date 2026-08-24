import { evaluateMatch } from './match-evaluator';

describe('evaluateMatch', () => {
  it('evaluates match with multiple rounds accurately', () => {
    const result = evaluateMatch({
      id: 42,
      placement: 1,
      rounds: [
        {
          stage: 2,
          roundNumber: 1,
          gold: 10,
          level: 3,
          champions: [{ cost: 1, starLevel: 2 }],
        },
        {
          stage: 3,
          roundNumber: 1,
          gold: 50,
          level: 6,
          champions: [{ cost: 3, starLevel: 2 }],
        },
      ],
    });

    expect(result.matchId).toBe(42);
    expect(result.rounds).toHaveLength(2);
    expect(result.rounds[0].stage).toBe(2);
    expect(result.rounds[0].roundNumber).toBe(1);
    expect(result.rounds[0].placementScore).toBe(100);
    expect(result.rounds[0].total).toBeGreaterThan(0);
    expect(result.overallStrength).toBeGreaterThan(0);
  });

  it('returns 0 overallStrength for a match with no rounds', () => {
    const result = evaluateMatch({
      id: 10,
      placement: 8,
      rounds: [],
    });

    expect(result.matchId).toBe(10);
    expect(result.overallStrength).toBe(0);
    expect(result.rounds).toEqual([]);
  });

  it('handles nested champion object structure from join tables', () => {
    const result = evaluateMatch({
      id: 99,
      placement: 2,
      rounds: [
        {
          stage: 4,
          roundNumber: 2,
          gold: 30,
          level: 7,
          champions: [
            {
              starLevel: 3,
              champion: { cost: 4 },
            },
          ],
        },
      ],
    });

    expect(result.rounds[0].boardScore).toBeGreaterThan(0);
    expect(result.overallStrength).toBeGreaterThan(0);
  });
});
