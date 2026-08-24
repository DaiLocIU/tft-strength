import { Test, TestingModule } from '@nestjs/testing';
import { MatchesController } from './matches.controller';
import { MatchTimelineService } from './match-timeline.service';
import { MemoryMatchTimelineStore } from './stores/memory-match-timeline.store';
import { MATCH_TIMELINE_STORE } from './stores/match-timeline.store.interface';

describe('MatchesController', () => {
  let controller: MatchesController;
  let service: MatchTimelineService;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      controllers: [MatchesController],
      providers: [
        MatchTimelineService,
        {
          provide: MATCH_TIMELINE_STORE,
          useClass: MemoryMatchTimelineStore,
        },
      ],
    }).compile();

    controller = module.get<MatchesController>(MatchesController);
    service = module.get<MatchTimelineService>(MatchTimelineService);
  });

  it('should be defined', () => {
    expect(controller).toBeDefined();
  });

  it('should create and retrieve matches via controller', async () => {
    const match = await controller.create(1, { placement: 1, comp: 'Rebel' });
    expect(match.id).toBeDefined();
    expect(match.placement).toBe(1);

    const matches = await controller.findAll(1);
    expect(matches).toHaveLength(1);

    const found = await controller.findOne(1, String(match.id));
    expect(found.id).toBe(match.id);
  });
});
