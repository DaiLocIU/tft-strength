import { Test, TestingModule } from '@nestjs/testing';
import { RoundsService } from './rounds.service';
import { PrismaService } from '../prisma/prisma.service';

describe('RoundsService', () => {
  let service: RoundsService;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [
        RoundsService,
        {
          provide: PrismaService,
          useValue: {
            match: {
              findUnique: jest.fn(),
            },
            round: {
              create: jest.fn(),
              findMany: jest.fn(),
              findUnique: jest.fn(),
              update: jest.fn(),
              delete: jest.fn(),
            },
          },
        },
      ],
    }).compile();

    service = module.get<RoundsService>(RoundsService);
  });

  it('should be defined', () => {
    expect(service).toBeDefined();
  });
});
