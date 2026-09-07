import {
  BadRequestException,
  ConflictException,
  Injectable,
  NotFoundException,
} from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';
import { BoardStateDraft } from './board-state-intake.types';
import { SaveBoardRoundDto } from './dto/save-board-round.dto';

@Injectable()
export class SaveBoardRoundService {
  constructor(private readonly prisma: PrismaService) {}

  async save(draftId: number, userId: number, dto: SaveBoardRoundDto) {
    const cells = new Set(
      dto.units.map((unit) => `${unit.row},${unit.column}`),
    );
    if (
      cells.size !== dto.units.length ||
      dto.units.some(
        (unit) => !unit.champion.trim() || unit.champion === 'unknown',
      )
    ) {
      throw new BadRequestException(
        'Choose a champion for every occupied hex and remove duplicate positions.',
      );
    }
    return this.prisma.$transaction(async (tx) => {
      const [draft] = await tx.$queryRaw<BoardStateDraft[]>`
        SELECT * FROM "BoardStateDraft" WHERE "id" = ${draftId} AND "userId" = ${userId} FOR UPDATE`;
      if (!draft)
        throw new NotFoundException('Board not found or access denied');
      if (draft.roundId)
        throw new ConflictException(
          'This board has already been added to a game.',
        );
      if (!['detected', 'completed'].includes(draft.status) || !draft.boardState)
        throw new BadRequestException(
          'Detect the board before saving a round.',
        );
      const matches = await tx.$queryRaw<{ id: number }[]>`
        SELECT "id" FROM "Match" WHERE "id" = ${dto.matchId} AND "userId" = ${userId} FOR UPDATE`;
      if (!matches.length)
        throw new NotFoundException('Game not found or access denied');
      const existing = await tx.round.findFirst({
        where: {
          matchId: dto.matchId,
          stage: dto.stage,
          roundNumber: dto.roundNumber,
        },
      });
      if (existing)
        throw new ConflictException(
          `Round ${dto.stage}-${dto.roundNumber} already exists. Choose another round.`,
        );
      const round = await tx.round.create({
        data: {
          matchId: dto.matchId,
          stage: dto.stage,
          roundNumber: dto.roundNumber,
          gold: dto.gold,
          hp: dto.hp,
          level: dto.level,
          streak: dto.streak,
        },
      });
      const boardState = {
        ...draft.boardState,
        original_detection: draft.boardState,
        reviewed_hud: {
          stage: dto.stage,
          roundNumber: dto.roundNumber,
          level: dto.level,
          gold: dto.gold,
          hp: dto.hp,
          streak: dto.streak,
        },
        units: dto.units.map((unit) => ({
          row: unit.row,
          column: unit.column,
          champion: unit.champion,
          star: `${unit.stars}_star`,
          source: 'user_review',
          needs_review: false,
        })),
        review: { confirmed_by_user: true },
      };
      await tx.$executeRaw`
        UPDATE "BoardStateDraft" SET "matchId" = ${dto.matchId}, "roundId" = ${round.id},
        "boardState" = ${JSON.stringify(boardState)}::jsonb, "updatedAt" = NOW() WHERE "id" = ${draftId}`;
      return { ...draft, matchId: dto.matchId, roundId: round.id, boardState };
    });
  }
}
