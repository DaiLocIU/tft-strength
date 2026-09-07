import { readFile } from 'node:fs/promises';
import { AnalyzeBoardDto, buildBoardGuide } from './board-guide';
import {
  BadRequestException,
  Body,
  Controller,
  Get,
  StreamableFile,
  NotFoundException,
  Param,
  Post,
  UploadedFile,
  UseGuards,
  UseInterceptors,
} from '@nestjs/common';
import { FileInterceptor } from '@nestjs/platform-express';
import { SaveBoardRoundDto } from './dto/save-board-round.dto';
import { SaveBoardRoundService } from './save-board-round.service';
import { extname } from 'path';
import { CurrentUser } from '../auth/decorators/current-user.decorator';
import { JwtAuthGuard } from '../auth/guards/jwt-auth.guard';
import { BoardStateIntakeService } from './board-state-intake.service';
import { UploadedImageFile } from './board-state-intake.types';
import { DetectBoardStateDraftDto } from './dto/detect-board-state-draft.dto';

const { diskStorage } = require('multer');

const UPLOAD_DIR =
  process.env.BOARD_STATE_UPLOAD_DIR ?? 'vision-board-detector/data/raw';

function safeImageFilename(originalName: string): string {
  const extension = extname(originalName).toLowerCase() || '.png';
  const timestamp = Date.now();
  const suffix = Math.random().toString(36).slice(2, 8);
  return `upload_${timestamp}_${suffix}${extension}`;
}

@UseGuards(JwtAuthGuard)
@Controller('board-state-intake')
export class BoardStateIntakeController {
  constructor(
    private readonly boardStateIntakeService: BoardStateIntakeService,
    private readonly saveBoardRoundService: SaveBoardRoundService,
  ) {}

  @Post('drafts/upload')
  @UseInterceptors(
    FileInterceptor('file', {
      storage: diskStorage({
        destination: UPLOAD_DIR,
        filename: (
          _request: unknown,
          file: { originalname: string },
          callback: (error: Error | null, filename: string) => void,
        ) => {
          callback(null, safeImageFilename(file.originalname));
        },
      }),
      limits: {
        fileSize: 25 * 1024 * 1024,
      },
    }),
  )
  uploadDraft(
    @CurrentUser('userId') userId: number,
    @UploadedFile() file: UploadedImageFile | undefined,
    @Body() body: Record<string, unknown>,
  ) {
    if (!file) {
      throw new BadRequestException('Missing image file field: file');
    }

    return this.boardStateIntakeService.createUploadDraft({
      userId,
      matchId: this.optionalInteger(body.matchId),
      roundId: this.optionalInteger(body.roundId),
      file,
    });
  }

  @Get('drafts/:id')
  findDraft(
    @CurrentUser('userId') userId: number,
    @Param('id') draftId: string,
  ) {
    return this.boardStateIntakeService.findDraft(+draftId, userId);
  }

  @Get('drafts/:id/image')
  async image(@CurrentUser('userId') userId: number, @Param('id') id: string) {
    const draft = await this.boardStateIntakeService.findDraft(+id, userId);
    try {
      return new StreamableFile(await readFile(draft.storagePath), {
        type: 'application/octet-stream',
      });
    } catch {
      throw new NotFoundException('Screenshot is no longer available');
    }
  }

  @Post('drafts/:id/detect')
  detectDraft(
    @CurrentUser('userId') userId: number,
    @Param('id') draftId: string,
    @Body() dto: DetectBoardStateDraftDto,
  ) {
    return this.boardStateIntakeService.detectDraft({
      userId,
      draftId: +draftId,
      championConfidence: dto.championConfidence,
      identityPadding: dto.identityPadding,
      identityConfidence: dto.identityConfidence,
    });
  }

  @Post('drafts/:id/analyze')
  async analyze(
    @CurrentUser('userId') userId: number,
    @Param('id') id: string,
    @Body() dto: AnalyzeBoardDto,
  ) {
    const draft = await this.boardStateIntakeService.findDraft(+id, userId);
    if (!draft.boardState)
      throw new BadRequestException(
        'Detect a board before requesting a guide.',
      );
    return buildBoardGuide(dto);
  }

  @Post('drafts/:id/save-round')
  saveRound(
    @CurrentUser('userId') userId: number,
    @Param('id') id: string,
    @Body() dto: SaveBoardRoundDto,
  ) {
    return this.saveBoardRoundService.save(+id, userId, dto);
  }

  private optionalInteger(value: unknown): number | undefined {
    if (value === undefined || value === null || value === '') {
      return undefined;
    }

    const parsed = Number(value);

    if (!Number.isInteger(parsed) || parsed <= 0) {
      throw new BadRequestException(`Expected positive integer, got ${value}`);
    }

    return parsed;
  }
}
