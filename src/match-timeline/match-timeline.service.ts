import {
  BadRequestException,
  ConflictException,
  Inject,
  Injectable,
  NotFoundException,
} from '@nestjs/common';
import { MatchModel } from '../../generated/prisma/models/Match';
import { RoundModel } from '../../generated/prisma/models/Round';
import { CreateMatchDto } from './dto/create-match.dto';
import { CreateRoundSnapshotDto } from './dto/create-round-snapshot.dto';
import { UpdateMatchDto } from './dto/update-match.dto';
import { UpdateRoundSnapshotDto } from './dto/update-round-snapshot.dto';
import {
  MATCH_TIMELINE_STORE,
  type MatchTimelineStore,
} from './stores/match-timeline.store.interface';
import { evaluateMatch } from '../strength/match-evaluator';

@Injectable()
export class MatchTimelineService {
  constructor(
    @Inject(MATCH_TIMELINE_STORE)
    private readonly store: MatchTimelineStore,
  ) {}

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

  // --- Match Lifecycle Operations ---

  async createMatch(dto: CreateMatchDto, userId: number): Promise<MatchModel> {
    return await this.store.createMatch({
      userId,
      placement: dto.placement,
      playedAt: dto.playedAt ? new Date(dto.playedAt) : undefined,
      comp: dto.comp,
      version: dto.version,
    });
  }

  async findAllMatches(userId: number): Promise<MatchModel[]> {
    return await this.store.findAllMatches(userId);
  }

  async findOneMatch(id: number, userId: number): Promise<MatchModel> {
    const match = await this.store.findMatchById(id, userId);
    if (!match) {
      throw new NotFoundException(
        `Match with ID #${id} not found or access denied`,
      );
    }
    return match;
  }

  async updateMatch(
    id: number,
    dto: UpdateMatchDto,
    userId: number,
  ): Promise<MatchModel> {
    await this.findOneMatch(id, userId);

    return await this.store.updateMatch(id, {
      placement: dto.placement,
      playedAt: dto.playedAt ? new Date(dto.playedAt) : undefined,
      comp: dto.comp,
      version: dto.version,
    });
  }

  async removeMatch(id: number, userId: number): Promise<MatchModel> {
    await this.findOneMatch(id, userId);
    return await this.store.deleteMatch(id);
  }

  // --- Round Snapshot Operations ---

  async recordRoundSnapshot(
    matchId: number,
    dto: CreateRoundSnapshotDto,
    userId: number,
  ): Promise<RoundModel> {
    // 1. Verify match ownership
    await this.findOneMatch(matchId, userId);

    // 2. Prevent duplicate stage-round in same match
    const existing = await this.store.findRoundByStageAndNumber(
      matchId,
      dto.stage,
      dto.roundNumber,
    );

    if (existing) {
      throw new ConflictException(
        `Round ${dto.stage}-${dto.roundNumber} already exists for Match #${matchId}`,
      );
    }

    return await this.store.createRound({
      matchId,
      stage: dto.stage,
      roundNumber: dto.roundNumber,
      gold: dto.gold,
      hp: dto.hp,
      level: dto.level,
      streak: dto.streak,
    });
  }

  async findAllRoundSnapshots(
    matchId: number,
    userId: number,
  ): Promise<RoundModel[]> {
    await this.findOneMatch(matchId, userId);
    return await this.store.findAllRounds(matchId);
  }

  async findOneRoundSnapshot(
    matchId: number,
    roundId: string | number,
    userId: number,
  ): Promise<RoundModel> {
    await this.findOneMatch(matchId, userId);

    const parsed = this.parseRoundIdentifier(roundId);

    const round = parsed.id
      ? await this.store.findRoundById(parsed.id, matchId)
      : await this.store.findRoundByStageAndNumber(
          matchId,
          parsed.stage!,
          parsed.roundNumber!,
        );

    if (!round) {
      throw new NotFoundException(
        `Round '${roundId}' not found in Match #${matchId}`,
      );
    }

    return round;
  }

  async updateRoundSnapshot(
    matchId: number,
    roundId: string | number,
    dto: UpdateRoundSnapshotDto,
    userId: number,
  ): Promise<RoundModel> {
    const existing = await this.findOneRoundSnapshot(matchId, roundId, userId);

    if (
      (dto.stage !== undefined && dto.stage !== existing.stage) ||
      (dto.roundNumber !== undefined &&
        dto.roundNumber !== existing.roundNumber)
    ) {
      const targetStage = dto.stage ?? existing.stage;
      const targetRoundNumber = dto.roundNumber ?? existing.roundNumber;

      const conflicting = await this.store.findRoundByStageAndNumber(
        matchId,
        targetStage,
        targetRoundNumber,
      );

      if (conflicting && conflicting.id !== existing.id) {
        throw new ConflictException(
          `Round ${targetStage}-${targetRoundNumber} already exists for Match #${matchId}`,
        );
      }
    }

    return await this.store.updateRound(existing.id, {
      stage: dto.stage,
      roundNumber: dto.roundNumber,
      gold: dto.gold,
      hp: dto.hp,
      level: dto.level,
      streak: dto.streak,
    });
  }

  async removeRoundSnapshot(
    matchId: number,
    roundId: string | number,
    userId: number,
  ): Promise<RoundModel> {
    const existing = await this.findOneRoundSnapshot(matchId, roundId, userId);
    return await this.store.deleteRound(existing.id);
  }

  // --- Match Strength Scoring ---

  async getMatchStrength(matchId: number, userId: number) {
    const match = await this.store.findMatchWithRounds(matchId, userId);
    if (!match) {
      throw new NotFoundException(
        `Match with ID #${matchId} not found or access denied`,
      );
    }

    return evaluateMatch(match);
  }
}
