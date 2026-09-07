import {
  BadRequestException,
  ConflictException,
  NotFoundException,
} from '@nestjs/common';
import { SaveBoardRoundService } from './save-board-round.service';
import { SaveBoardRoundDto } from './dto/save-board-round.dto';

const dto: SaveBoardRoundDto = {
  matchId: 2,
  stage: 3,
  roundNumber: 2,
  gold: 30,
  hp: 80,
  level: 6,
  streak: -2,
  units: [{ row: 3, column: 1, champion: 'Ashe', stars: 2 }],
};
describe('SaveBoardRoundService', () => {
  let tx: any;
  let service: SaveBoardRoundService;
  beforeEach(() => {
    tx = {
      $queryRaw: jest
        .fn()
        .mockResolvedValueOnce([
          {
            id: 1,
            roundId: null,
            status: 'detected',
            boardState: { image_name: 'board.png', units: [] },
          },
        ])
        .mockResolvedValueOnce([{ id: 2 }]),
      $executeRaw: jest.fn(),
      round: {
        findFirst: jest.fn().mockResolvedValue(null),
        create: jest.fn().mockResolvedValue({ id: 4 }),
      },
    };
    service = new SaveBoardRoundService({
      $transaction: (fn: any) => fn(tx),
    } as any);
  });
  it('saves reviewed positions and stars with the round', async () => {
    const result = await service.save(1, 7, dto);
    expect(result.roundId).toBe(4);
    expect(result.matchId).toBe(2);
    expect(result.boardState.units[0]).toMatchObject({
      champion: 'Ashe',
      row: 3,
      column: 1,
      star: '2_star',
      needs_review: false,
    });
    expect(tx.round.create).toHaveBeenCalledWith({
      data: {
        matchId: 2,
        stage: 3,
        roundNumber: 2,
        gold: 30,
        hp: 80,
        level: 6,
        streak: -2,
      },
    });
    expect(tx.$executeRaw).toHaveBeenCalledTimes(1);
  });
  it('rejects another user’s draft before creating a round', async () => {
    tx.$queryRaw.mockReset().mockResolvedValueOnce([]);
    await expect(service.save(1, 7, dto)).rejects.toThrow(NotFoundException);
    expect(tx.round.create).not.toHaveBeenCalled();
  });
  it('rejects a game the user does not own', async () => {
    tx.$queryRaw
      .mockReset()
      .mockResolvedValueOnce([{ id: 1, status: 'detected', boardState: {} }])
      .mockResolvedValueOnce([]);
    await expect(service.save(1, 7, dto)).rejects.toThrow(NotFoundException);
    expect(tx.round.create).not.toHaveBeenCalled();
  });
  it('does not overwrite an existing round', async () => {
    tx.round.findFirst.mockResolvedValue({ id: 3 });
    await expect(service.save(1, 7, dto)).rejects.toThrow(ConflictException);
    expect(tx.round.create).not.toHaveBeenCalled();
  });
  it('prevents repeated saves of the same board', async () => {
    tx.$queryRaw.mockReset().mockResolvedValueOnce([{ id: 1, roundId: 4 }]);
    await expect(service.save(1, 7, dto)).rejects.toThrow(ConflictException);
    expect(tx.round.create).not.toHaveBeenCalled();
  });
  it('rejects duplicate positions', async () => {
    await expect(
      service.save(1, 7, { ...dto, units: [...dto.units, ...dto.units] }),
    ).rejects.toThrow(BadRequestException);
    expect(tx.round.create).not.toHaveBeenCalled();
  });
  it('reports persistence failures instead of reporting success', async () => {
    tx.$executeRaw.mockRejectedValue(new Error('Database unavailable'));
    await expect(service.save(1, 7, dto)).rejects.toThrow(
      'Database unavailable',
    );
  });
});
