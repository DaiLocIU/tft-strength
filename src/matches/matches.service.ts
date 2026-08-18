/* eslint-disable @typescript-eslint/no-unsafe-call */
/* eslint-disable @typescript-eslint/no-unsafe-member-access */
/* eslint-disable @typescript-eslint/no-unsafe-return */
/* eslint-disable @typescript-eslint/no-unsafe-assignment */
/* eslint-disable @typescript-eslint/no-redundant-type-constituents */

// The rules above are disabled because PrismaClient (from generated/prisma/client.ts)
// uses // @ts-nocheck internally (Prisma v7 generated code), causing ESLint's
// type checker to evaluate Prisma types as `any`. These operations are safe at runtime.

import { Injectable, NotFoundException } from '@nestjs/common';
import { MatchModel } from '../../generated/prisma/models/Match';
import { PrismaService } from '../prisma/prisma.service';
import { CreateMatchDto } from './dto/create-match.dto';
import { UpdateMatchDto } from './dto/update-match.dto';

@Injectable()
export class MatchesService {
  constructor(private readonly prisma: PrismaService) {}

  async create(
    createMatchDto: CreateMatchDto,
    userId: number,
  ): Promise<MatchModel> {
    return await this.prisma.match.create({
      data: {
        userId,
        placement: createMatchDto.placement,
        playedAt: createMatchDto.playedAt
          ? new Date(createMatchDto.playedAt)
          : undefined,
        comp: createMatchDto.comp,
        version: createMatchDto.version,
      },
    });
  }

  async findAll(userId: number): Promise<MatchModel[]> {
    return await this.prisma.match.findMany({
      where: { userId },
      orderBy: { playedAt: 'desc' },
    });
  }

  async findOne(id: number, userId?: number): Promise<MatchModel> {
    const match = await this.prisma.match.findFirst({
      where: { id, ...(userId ? { userId } : {}) },
    });

    if (!match) {
      throw new NotFoundException(`Match with ID #${id} not found`);
    }

    return match;
  }

  async update(
    id: number,
    updateMatchDto: UpdateMatchDto,
    userId?: number,
  ): Promise<MatchModel> {
    await this.findOne(id, userId);

    return await this.prisma.match.update({
      where: { id },
      data: {
        placement: updateMatchDto.placement,
        playedAt: updateMatchDto.playedAt
          ? new Date(updateMatchDto.playedAt)
          : undefined,
        comp: updateMatchDto.comp,
        version: updateMatchDto.version,
      },
    });
  }

  async remove(id: number, userId?: number): Promise<MatchModel> {
    await this.findOne(id, userId);

    return await this.prisma.match.delete({
      where: { id },
    });
  }
}
