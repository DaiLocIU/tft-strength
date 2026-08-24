import { Test, TestingModule } from '@nestjs/testing';
import { MatchTimelineService } from './match-timeline.service';
import { RoundsController } from './rounds.controller';
import { MemoryMatchTimelineStore } from './stores/memory-match-timeline.store';
import { MATCH_TIMELINE_STORE } from './stores/match-timeline.store.interface';

describe('RoundsController', () => {
  let controller: RoundsController;
  let service: MatchTimelineService;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      controllers: [RoundsController],
      providers: [
        MatchTimelineService,
        {
          provide: MATCH_TIMELINE_STORE,
          useClass: MemoryMatchTimelineStore,
        },
      ],
    }).compile();

    controller = module.get<RoundsController>(RoundsController);
    service = module.get<MatchTimelineService>(MatchTimelineService);
  });

  it('should be defined', () => {
    expect(controller).toBeDefined();
  });

  it('should record and find round snapshots via controller', async () => {
    const match = await service.createMatch({ placement: 1 }, 1);

    const round = await controller.create(1, String(match.id), {
      stage: 2,
      roundNumber: 1,
      gold: 10,
      hp: 100,
      level: 3,
      streak: 1,
    });

    expect(round.id).toBeDefined();
    expect(round.stage).toBe(2);
    expect(round.roundNumber).toBe(1);

    const rounds = await controller.findAll(1, String(match.id));
    expect(rounds).toHaveLength(1);

    const found = await controller.findOne(1, String(match.id), '2-1');
    expect(found.id).toBe(round.id);
  });
});
