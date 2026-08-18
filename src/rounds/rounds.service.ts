/* eslint-disable @typescript-eslint/no-unsafe-call */
/* eslint-disable @typescript-eslint/no-unsafe-member-access */
/* eslint-disable @typescript-eslint/no-unsafe-return */
/* eslint-disable @typescript-eslint/no-unsafe-assignment */
/* eslint-disable @typescript-eslint/no-redundant-type-constituents */

// The rules above are disabled because PrismaClient (from generated/prisma/client.ts)
// uses // @ts-nocheck internally (Prisma v7 generated code), causing ESLint's
// type checker to evaluate Prisma types as `any`. These operations are safe at runtime.

import {
  BadRequestException,
  ConflictException,
  Injectable,
  NotFoundException,
} from '@nestjs/common';
import { RoundModel } from '../../generated/prisma/models/Round';
import { PrismaService } from '../prisma/prisma.service';
import { CreateRoundDto } from './dto/create-round.dto';
import { UpdateRoundDto } from './dto/update-round.dto';

@Injectable()
export class RoundsService {
  constructor(private readonly prisma: PrismaService) {}

  private parseRoundIdentifier(roundId: string | number): {
    stage?: number;
    roundNumber?: number;
    id?: number;
  } {
    const str = String(roundId).trim();
    if (str.includes('-')) {
      const [stageStr, roundNumStr] = str.split('-');
      const stage = parseInt(stageStr, 10);
      const roundNumber = parseInt(roundNumStr, 10);
      if (!isNaN(stage) && !isNaN(roundNumber)) {
        return { stage, roundNumber };
      }
    }

    const num = parseInt(str, 10);
    if (!isNaN(num)) {
      return { id: num };
    }

    throw new BadRequestException(
      `Invalid round identifier: '${roundId}'. Use format like '2-3' or numeric ID.`,
    );
  }

  async create(
    matchId: number,
    createRoundDto: CreateRoundDto,
  ): Promise<RoundModel> {
    const match = await this.prisma.match.findUnique({
      where: { id: matchId },
    });

    if (!match) {
      throw new NotFoundException(`Match with ID #${matchId} not found`);
    }

    const existingRound = await this.prisma.round.findFirst({
      where: {
        matchId,
        stage: createRoundDto.stage,
        roundNumber: createRoundDto.roundNumber,
      },
    });

    if (existingRound) {
      throw new ConflictException(
        `Round ${createRoundDto.stage}-${createRoundDto.roundNumber} already exists for Match #${matchId}`,
      );
    }

    return await this.prisma.round.create({
      data: {
        matchId,
        stage: createRoundDto.stage,
        roundNumber: createRoundDto.roundNumber,
        gold: createRoundDto.gold,
        hp: createRoundDto.hp,
        level: createRoundDto.level,
        streak: createRoundDto.streak,
      },
    });
  }

  async findAll(matchId: number): Promise<RoundModel[]> {
    const match = await this.prisma.match.findUnique({
      where: { id: matchId },
    });

    if (!match) {
      throw new NotFoundException(`Match with ID #${matchId} not found`);
    }

    return await this.prisma.round.findMany({
      where: { matchId },
      orderBy: [{ stage: 'asc' }, { roundNumber: 'asc' }],
    });
  }

  async findOne(
    matchId: number,
    roundId: string | number,
  ): Promise<RoundModel> {
    const parsed = this.parseRoundIdentifier(roundId);

    const round = await this.prisma.round.findFirst({
      where: parsed.id
        ? { id: parsed.id, matchId }
        : { matchId, stage: parsed.stage, roundNumber: parsed.roundNumber },
    });

    if (!round) {
      throw new NotFoundException(
        `Round '${roundId}' not found in Match #${matchId}`,
      );
    }

    return round;
  }

  async update(
    matchId: number,
    roundId: string | number,
    updateRoundDto: UpdateRoundDto,
  ): Promise<RoundModel> {
    const existing = await this.findOne(matchId, roundId);

    if (
      (updateRoundDto.stage !== undefined &&
        updateRoundDto.stage !== existing.stage) ||
      (updateRoundDto.roundNumber !== undefined &&
        updateRoundDto.roundNumber !== existing.roundNumber)
    ) {
      const targetStage = updateRoundDto.stage ?? existing.stage;
      const targetRoundNumber =
        updateRoundDto.roundNumber ?? existing.roundNumber;

      const conflictingRound = await this.prisma.round.findFirst({
        where: {
          matchId,
          stage: targetStage,
          roundNumber: targetRoundNumber,
          NOT: { id: existing.id },
        },
      });

      if (conflictingRound) {
        throw new ConflictException(
          `Round ${targetStage}-${targetRoundNumber} already exists for Match #${matchId}`,
        );
      }
    }

    return await this.prisma.round.update({
      where: { id: existing.id },
      data: {
        stage: updateRoundDto.stage,
        roundNumber: updateRoundDto.roundNumber,
        gold: updateRoundDto.gold,
        hp: updateRoundDto.hp,
        level: updateRoundDto.level,
        streak: updateRoundDto.streak,
      },
    });
  }

  async remove(matchId: number, roundId: string | number): Promise<RoundModel> {
    const existing = await this.findOne(matchId, roundId);

    return await this.prisma.round.delete({
      where: { id: existing.id },
    });
  }
}
