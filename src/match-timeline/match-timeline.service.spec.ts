import {
  BadRequestException,
  ConflictException,
  NotFoundException,
} from '@nestjs/common';
import { MatchTimelineService } from './match-timeline.service';
import { MemoryMatchTimelineStore } from './stores/memory-match-timeline.store';

describe('MatchTimelineService (with MemoryStore Seam)', () => {
  let service: MatchTimelineService;
  let store: MemoryMatchTimelineStore;

  const USER_A = 1;
  const USER_B = 2;

  beforeEach(() => {
    store = new MemoryMatchTimelineStore();
    service = new MatchTimelineService(store);
  });

  describe('Match Lifecycle', () => {
    it('should create and retrieve a match for a user', async () => {
      const created = await service.createMatch(
        { placement: 1, comp: 'Rebel Sorcerer', version: '14.1' },
        USER_A,
      );

      expect(created.id).toBeDefined();
      expect(created.placement).toBe(1);
      expect(created.userId).toBe(USER_A);
      expect(created.comp).toBe('Rebel Sorcerer');

      const found = await service.findOneMatch(created.id, USER_A);
      expect(found).toEqual(created);
    });

    it('should isolate matches by user', async () => {
      const matchA = await service.createMatch({ placement: 2 }, USER_A);
      const matchB = await service.createMatch({ placement: 4 }, USER_B);

      const userAMatches = await service.findAllMatches(USER_A);
      expect(userAMatches).toHaveLength(1);
      expect(userAMatches[0].id).toBe(matchA.id);

      const userBMatches = await service.findAllMatches(USER_B);
      expect(userBMatches).toHaveLength(1);
      expect(userBMatches[0].id).toBe(matchB.id);

      // User A cannot access User B's match
      await expect(service.findOneMatch(matchB.id, USER_A)).rejects.toThrow(
        NotFoundException,
      );
    });

    it('should update match details', async () => {
      const match = await service.createMatch({ placement: 8 }, USER_A);
      const updated = await service.updateMatch(
        match.id,
        { placement: 1, comp: 'Pivot to Academy' },
        USER_A,
      );

      expect(updated.placement).toBe(1);
      expect(updated.comp).toBe('Pivot to Academy');
    });

    it('should remove a match and cascade its rounds', async () => {
      const match = await service.createMatch({ placement: 3 }, USER_A);
      await service.recordRoundSnapshot(
        match.id,
        { stage: 2, roundNumber: 1, gold: 10, hp: 100, level: 3, streak: 0 },
        USER_A,
      );

      await service.removeMatch(match.id, USER_A);

      await expect(service.findOneMatch(match.id, USER_A)).rejects.toThrow(
        NotFoundException,
      );
    });
  });

  describe('Round Snapshot Operations', () => {
    let matchId: number;

    beforeEach(async () => {
      const match = await service.createMatch({ placement: 1 }, USER_A);
      matchId = match.id;
    });

    it('should record sequential round snapshots', async () => {
      const round21 = await service.recordRoundSnapshot(
        matchId,
        { stage: 2, roundNumber: 1, gold: 10, hp: 100, level: 3, streak: 1 },
        USER_A,
      );
      const round22 = await service.recordRoundSnapshot(
        matchId,
        { stage: 2, roundNumber: 2, gold: 15, hp: 95, level: 4, streak: -1 },
        USER_A,
      );

      expect(round21.stage).toBe(2);
      expect(round21.roundNumber).toBe(1);
      expect(round22.stage).toBe(2);
      expect(round22.roundNumber).toBe(2);

      const all = await service.findAllRoundSnapshots(matchId, USER_A);
      expect(all).toHaveLength(2);
      expect(all[0].roundNumber).toBe(1);
      expect(all[1].roundNumber).toBe(2);
    });

    it('should prevent duplicate round snapshots in the same match', async () => {
      await service.recordRoundSnapshot(
        matchId,
        { stage: 2, roundNumber: 3, gold: 20, hp: 90, level: 4, streak: 2 },
        USER_A,
      );

      await expect(
        service.recordRoundSnapshot(
          matchId,
          { stage: 2, roundNumber: 3, gold: 25, hp: 85, level: 5, streak: 3 },
          USER_A,
        ),
      ).rejects.toThrow(ConflictException);
    });

    it('should retrieve round snapshots by string identifier like "2-3" or numeric ID', async () => {
      const round = await service.recordRoundSnapshot(
        matchId,
        { stage: 3, roundNumber: 5, gold: 50, hp: 70, level: 7, streak: 4 },
        USER_A,
      );

      // Lookup by '3-5'
      const byString = await service.findOneRoundSnapshot(
        matchId,
        '3-5',
        USER_A,
      );
      expect(byString.id).toBe(round.id);

      // Lookup by numeric ID
      const byId = await service.findOneRoundSnapshot(
        matchId,
        round.id,
        USER_A,
      );
      expect(byId.id).toBe(round.id);
    });

    it('should reject invalid string identifiers with BadRequestException', async () => {
      await expect(
        service.findOneRoundSnapshot(matchId, 'invalid-identifier', USER_A),
      ).rejects.toThrow(BadRequestException);
    });

    it('should update a round snapshot', async () => {
      await service.recordRoundSnapshot(
        matchId,
        { stage: 4, roundNumber: 1, gold: 30, hp: 50, level: 8, streak: -2 },
        USER_A,
      );

      const updated = await service.updateRoundSnapshot(
        matchId,
        '4-1',
        { gold: 45, hp: 55 },
        USER_A,
      );

      expect(updated.gold).toBe(45);
      expect(updated.hp).toBe(55);
    });

    it('should remove a round snapshot', async () => {
      await service.recordRoundSnapshot(
        matchId,
        { stage: 5, roundNumber: 1, gold: 10, hp: 20, level: 9, streak: 1 },
        USER_A,
      );

      await service.removeRoundSnapshot(matchId, '5-1', USER_A);

      await expect(
        service.findOneRoundSnapshot(matchId, '5-1', USER_A),
      ).rejects.toThrow(NotFoundException);
    });
  });

  describe('Match Strength Scoring', () => {
    it('should compute overall and per-round strength scores for a match', async () => {
      const match = await service.createMatch({ placement: 1 }, USER_A);
      await service.recordRoundSnapshot(
        match.id,
        { stage: 2, roundNumber: 1, gold: 10, hp: 100, level: 3, streak: 1 },
        USER_A,
      );
      await service.recordRoundSnapshot(
        match.id,
        { stage: 2, roundNumber: 2, gold: 20, hp: 95, level: 4, streak: 2 },
        USER_A,
      );

      const strength = await service.getMatchStrength(match.id, USER_A);
      expect(strength.matchId).toBe(match.id);
      expect(strength.rounds).toHaveLength(2);
      expect(strength.rounds[0].stage).toBe(2);
      expect(strength.rounds[0].roundNumber).toBe(1);
      expect(strength.rounds[0].placementScore).toBe(100);
      expect(strength.rounds[0].total).toBeGreaterThan(0);
      expect(strength.overallStrength).toBeGreaterThan(0);
    });

    it('should return 0 overallStrength when a match has no rounds', async () => {
      const match = await service.createMatch({ placement: 4 }, USER_A);
      const strength = await service.getMatchStrength(match.id, USER_A);
      expect(strength.matchId).toBe(match.id);
      expect(strength.overallStrength).toBe(0);
      expect(strength.rounds).toEqual([]);
    });
  });
});
