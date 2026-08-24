import { scoreRound } from './strength.util';

describe('scoreRound', () => {
  it('gives max placement score for 1st place', () => {
    const result = scoreRound({
      placement: 1,
      level: 9,
      goldLeft: 10,
      champions: [],
    });
    expect(result.placementScore).toBe(100);
  });

  it('gives zero placement score for 8th place', () => {
    const result = scoreRound({
      placement: 8,
      level: 5,
      goldLeft: 0,
      champions: [],
    });
    expect(result.placementScore).toBe(0);
  });

  it('rewards higher star levels more than linearly', () => {
    const oneStar = scoreRound({
      placement: 4,
      level: 8,
      goldLeft: 5,
      champions: [{ cost: 5, starLevel: 1 }],
    });
    const threeStar = scoreRound({
      placement: 4,
      level: 8,
      goldLeft: 5,
      champions: [{ cost: 5, starLevel: 3 }],
    });
    // 3-star should be much more than 3x the 1-star board score
    expect(threeStar.boardScore).toBeGreaterThan(oneStar.boardScore * 3);
  });

  it('handles an empty board without crashing', () => {
    const result = scoreRound({
      placement: 5,
      level: 3,
      goldLeft: 0,
      champions: [],
    });
    expect(result.boardScore).toBe(0);
    expect(result.total).toBeGreaterThanOrEqual(0);
  });

  it('caps total score at 100', () => {
    const result = scoreRound({
      placement: 1,
      level: 9,
      goldLeft: 50,
      champions: Array.from({ length: 9 }, () => ({ cost: 5, starLevel: 3 })),
    });
    expect(result.total).toBeLessThanOrEqual(100);
  });
});
