import { Test, TestingModule } from '@nestjs/testing';
import { StatsController } from './stats.controller';
import { StatsService } from './stats.service';

describe('StatsController', () => {
  let controller: StatsController;
  let service: { getStats: jest.Mock };

  beforeEach(async () => {
    service = {
      getStats: jest.fn(),
    };

    const module: TestingModule = await Test.createTestingModule({
      controllers: [StatsController],
      providers: [
        {
          provide: StatsService,
          useValue: service,
        },
      ],
    }).compile();

    controller = module.get<StatsController>(StatsController);
  });

  it('should be defined', () => {
    expect(controller).toBeDefined();
  });

  it('should call statsService.getStats with userId', async () => {
    const expected = { compStats: [], strengthCurve: [] };
    service.getStats.mockResolvedValue(expected);

    const result = await controller.getStats(1);
    expect(result).toBe(expected);
    expect(service.getStats).toHaveBeenCalledWith(1);
  });
});
