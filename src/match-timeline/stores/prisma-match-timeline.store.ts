import { Injectable } from '@nestjs/common';
import { MatchModel } from '../../../generated/prisma/models/Match';
import { RoundModel } from '../../../generated/prisma/models/Round';
import { PrismaService } from '../../prisma/prisma.service';
import {
  CreateMatchData,
  CreateRoundData,
  MatchTimelineAggregate,
  MatchTimelineStore,
  UpdateMatchData,
  UpdateRoundData,
} from './match-timeline.store.interface';

@Injectable()
export class PrismaMatchTimelineStore implements MatchTimelineStore {
  constructor(private readonly prisma: PrismaService) {}

  async createMatch(data: CreateMatchData): Promise<MatchModel> {
    return await this.prisma.match.create({
      data: {
        userId: data.userId,
        placement: data.placement,
        playedAt: data.playedAt,
        name: data.name,
        comp: data.comp,
      },
    });
  }

  async findAllMatches(userId: number): Promise<MatchModel[]> {
    return await this.prisma.match.findMany({
      where: { userId },
      orderBy: { playedAt: 'desc' },
    });
  }

  async findMatchById(id: number, userId?: number): Promise<MatchModel | null> {
    return await this.prisma.match.findFirst({
      where: { id, ...(userId ? { userId } : {}) },
    });
  }

  async findMatchWithRounds(
    id: number,
    userId?: number,
  ): Promise<MatchTimelineAggregate | null> {
    return await this.prisma.match.findFirst({
      where: { id, ...(userId ? { userId } : {}) },
      include: {
        rounds: {
          orderBy: [{ stage: 'asc' }, { roundNumber: 'asc' }],
        },
      },
    });
  }

  async findAllMatchesWithRounds(
    userId: number,
  ): Promise<MatchTimelineAggregate[]> {
    return await this.prisma.match.findMany({
      where: { userId },
      include: {
        rounds: {
          orderBy: [{ stage: 'asc' }, { roundNumber: 'asc' }],
        },
      },
      orderBy: { playedAt: 'asc' },
    });
  }

  async updateMatch(id: number, data: UpdateMatchData): Promise<MatchModel> {
    return await this.prisma.match.update({
      where: { id },
      data: {
        placement: data.placement,
        playedAt: data.playedAt,
        name: data.name,
        comp: data.comp,
      },
    });
  }

  async deleteMatch(id: number): Promise<MatchModel> {
    return await this.prisma.match.delete({
      where: { id },
    });
  }

  async createRound(data: CreateRoundData): Promise<RoundModel> {
    return await this.prisma.round.create({
      data: {
        matchId: data.matchId,
        stage: data.stage,
        roundNumber: data.roundNumber,
        gold: data.gold,
        hp: data.hp,
        level: data.level,
        streak: data.streak,
      },
    });
  }

  async findAllRounds(matchId: number): Promise<RoundModel[]> {
    return await this.prisma.round.findMany({
      where: { matchId },
      orderBy: [{ stage: 'asc' }, { roundNumber: 'asc' }],
    });
  }

  private async withSavedBoard(round: RoundModel | null) {
    if (!round) return null;
    const boardStateDrafts = await this.prisma.$queryRaw<
      {
        id: number;
        originalFilename: string;
        boardState: unknown;
      }[]
    >`SELECT "id", "originalFilename", "boardState" FROM "BoardStateDraft"
      WHERE "roundId" = ${round.id} AND "matchId" = ${round.matchId}
      AND "status" IN ('detected', 'completed') ORDER BY "updatedAt" DESC LIMIT 1`;
    return { ...round, boardStateDrafts };
  }

  async findRoundById(id: number, matchId: number): Promise<RoundModel | null> {
    return this.withSavedBoard(
      await this.prisma.round.findFirst({ where: { id, matchId } }),
    );
  }

  async findRoundByStageAndNumber(
    matchId: number,
    stage: number,
    roundNumber: number,
  ): Promise<RoundModel | null> {
    return this.withSavedBoard(
      await this.prisma.round.findFirst({
        where: { matchId, stage, roundNumber },
      }),
    );
  }

  async updateRound(id: number, data: UpdateRoundData): Promise<RoundModel> {
    return await this.prisma.round.update({
      where: { id },
      data: {
        stage: data.stage,
        roundNumber: data.roundNumber,
        gold: data.gold,
        hp: data.hp,
        level: data.level,
        streak: data.streak,
      },
    });
  }

  async deleteRound(id: number): Promise<RoundModel> {
    return await this.prisma.round.delete({
      where: { id },
    });
  }
}
