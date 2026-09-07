import { Injectable } from '@nestjs/common';
import { PrismaService } from '../../prisma/prisma.service';
import {
  BoardState,
  BoardStateDraft,
  BoardStateDraftStatus,
  CreateBoardStateDraftData,
  UpdateBoardStateDraftData,
} from '../board-state-intake.types';
import { BoardStateDraftStore } from './board-state-draft.store.interface';

@Injectable()
export class PrismaBoardStateDraftStore implements BoardStateDraftStore {
  constructor(private readonly prisma: PrismaService) {}

  async createDraft(
    data: CreateBoardStateDraftData,
  ): Promise<BoardStateDraft> {
    const rows = await this.prisma.$queryRawUnsafe<any[]>(
      `
      INSERT INTO "BoardStateDraft" (
        "userId",
        "matchId",
        "roundId",
        "screenshotFilename",
        "originalFilename",
        "storagePath",
        "status",
        "updatedAt"
      )
      VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())
      RETURNING *
      `,
      data.userId,
      data.matchId ?? null,
      data.roundId ?? null,
      data.screenshotFilename,
      data.originalFilename,
      data.storagePath,
      data.status ?? 'uploaded',
    );

    return this.toDraft(rows[0]);
  }

  async findDraftById(
    id: number,
    userId?: number,
  ): Promise<BoardStateDraft | null> {
    const rows =
      userId === undefined
        ? await this.prisma.$queryRawUnsafe<any[]>(
            `SELECT * FROM "BoardStateDraft" WHERE "id" = $1 LIMIT 1`,
            id,
          )
        : await this.prisma.$queryRawUnsafe<any[]>(
            `SELECT * FROM "BoardStateDraft" WHERE "id" = $1 AND "userId" = $2 LIMIT 1`,
            id,
            userId,
          );

    return rows[0] ? this.toDraft(rows[0]) : null;
  }

  async updateDraft(
    id: number,
    data: UpdateBoardStateDraftData,
  ): Promise<BoardStateDraft> {
    const current = await this.findDraftById(id);
    if (!current) {
      throw new Error(`Board State draft #${id} not found`);
    }

    const rows = await this.prisma.$queryRawUnsafe<any[]>(
      `
      UPDATE "BoardStateDraft"
      SET
        "storagePath" = $5,
        "status" = $2,
        "boardState" = $3::jsonb,
        "errorMessage" = $4,
        "updatedAt" = NOW()
      WHERE "id" = $1
      RETURNING *
      `,
      id,
      data.status ?? current.status,
      this.toJsonParam(
        data.boardState === undefined ? current.boardState : data.boardState,
      ),
      data.errorMessage === undefined
        ? current.errorMessage
        : data.errorMessage,
      data.storagePath ?? current.storagePath,
    );

    return this.toDraft(rows[0]);
  }

  async transition(id: number, userId: number, from: BoardStateDraftStatus[], data: UpdateBoardStateDraftData, before?: Date): Promise<BoardStateDraft | null> {
    const rows = await this.prisma.$queryRawUnsafe<any[]>(`
      UPDATE "BoardStateDraft" SET "status" = $4,
        "boardState" = CASE WHEN $5::boolean THEN $6::jsonb ELSE "boardState" END,
        "errorMessage" = $7, "updatedAt" = NOW()
      WHERE "id" = $1 AND "userId" = $2 AND "status" = ANY($3::text[])
        AND "roundId" IS NULL AND ($8::timestamp IS NULL OR "updatedAt" <= $8::timestamp)
      RETURNING *`, id, userId, from, data.status, data.boardState !== undefined,
      this.toJsonParam(data.boardState ?? null), data.errorMessage ?? null, before ?? null);
    return rows[0] ? this.toDraft(rows[0]) : null;
  }

  private toDraft(record: any): BoardStateDraft {
    return {
      id: record.id,
      userId: record.userId,
      matchId: record.matchId,
      roundId: record.roundId,
      screenshotFilename: record.screenshotFilename,
      originalFilename: record.originalFilename,
      storagePath: record.storagePath,
      status: record.status,
      boardState: (record.boardState as BoardState | null) ?? null,
      errorMessage: record.errorMessage,
      createdAt: record.createdAt,
      updatedAt: record.updatedAt,
    };
  }

  private toJsonParam(value: BoardState | null): string | null {
    return value === null ? null : JSON.stringify(value);
  }
}
