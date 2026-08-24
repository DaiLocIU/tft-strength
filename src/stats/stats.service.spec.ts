import { Test, TestingModule } from '@nestjs/testing';
import { MemoryMatchTimelineStore } from '../match-timeline/stores/memory-match-timeline.store';
import { MATCH_TIMELINE_STORE } from '../match-timeline/stores/match-timeline.store.interface';
import { StatsService } from './stats.service';

describe('StatsService (with MemoryMatchTimelineStore Seam)', () => {
  let service: StatsService;
  let store: MemoryMatchTimelineStore;

  const USER_ID = 1;

  beforeEach(async () => {
    store = new MemoryMatchTimelineStore();

    const module: TestingModule = await Test.createTestingModule({
      providers: [
        StatsService,
        {
          provide: MATCH_TIMELINE_STORE,
          useValue: store,
        },
      ],
    }).compile();

    service = module.get<StatsService>(StatsService);
  });

  it('should return empty arrays when user has no matches', async () => {
    const result = await service.getStats(USER_ID);

    expect(result).toEqual({
      compStats: [],
      strengthCurve: [],
    });
  });

  it('should calculate compStats (winRate & top4Rate) and strengthCurve properly', async () => {
    // Match 1: 1st place, Rebel Sorcerer, 2 rounds
    const m1 = await store.createMatch({
      userId: USER_ID,
      placement: 1,
      comp: 'Rebel Sorcerer',
      playedAt: new Date('2026-01-01T10:00:00Z'),
    });
    await store.createRound({
      matchId: m1.id,
      stage: 2,
      roundNumber: 1,
      gold: 20,
      level: 4,
      hp: 100,
      streak: 1,
    });
    await store.createRound({
      matchId: m1.id,
      stage: 3,
      roundNumber: 1,
      gold: 50,
      level: 6,
      hp: 90,
      streak: 2,
    });

    // Match 2: 3rd place, Rebel Sorcerer, 1 round
    const m2 = await store.createMatch({
      userId: USER_ID,
      placement: 3,
      comp: 'Rebel Sorcerer',
      playedAt: new Date('2026-01-02T10:00:00Z'),
    });
    await store.createRound({
      matchId: m2.id,
      stage: 2,
      roundNumber: 1,
      gold: 10,
      level: 3,
      hp: 80,
      streak: -1,
    });

    // Match 3: 6th place, Unknown comp, 0 rounds
    const m3 = await store.createMatch({
      userId: USER_ID,
      placement: 6,
      playedAt: new Date('2026-01-03T10:00:00Z'),
    });

    // Match for another user (should be isolated)
    await store.createMatch({
      userId: 999,
      placement: 1,
      comp: 'Rebel Sorcerer',
    });

    const result = await service.getStats(USER_ID);

    // compStats check
    expect(result.compStats).toHaveLength(2);
    const rebelStat = result.compStats.find(
      (c) => c.compName === 'Rebel Sorcerer',
    );
    expect(rebelStat).toBeDefined();
    expect(rebelStat?.games).toBe(2);
    expect(rebelStat?.winRate).toBe(50); // 1 win out of 2 games
    expect(rebelStat?.top4Rate).toBe(100); // 2 top4s (1st and 3rd)

    const unknownStat = result.compStats.find((c) => c.compName === 'Unknown');
    expect(unknownStat).toBeDefined();
    expect(unknownStat?.games).toBe(1);
    expect(unknownStat?.winRate).toBe(0);
    expect(unknownStat?.top4Rate).toBe(0);

    // strengthCurve check
    expect(result.strengthCurve).toHaveLength(3);
    expect(result.strengthCurve[0].matchId).toBe(m1.id);
    expect(result.strengthCurve[0].placement).toBe(1);
    expect(result.strengthCurve[0].strength).toBeGreaterThan(0);
    expect(result.strengthCurve[0].date).toEqual(
      new Date('2026-01-01T10:00:00Z'),
    );

    expect(result.strengthCurve[1].matchId).toBe(m2.id);
    expect(result.strengthCurve[1].placement).toBe(3);

    expect(result.strengthCurve[2].matchId).toBe(m3.id);
    expect(result.strengthCurve[2].placement).toBe(6);
    expect(result.strengthCurve[2].strength).toBe(0);
  });
});
