import { randomUUID } from 'node:crypto';
import { ScreenshotStorageService } from './screenshot-storage.service';
import {
  ConflictException,
  BadRequestException,
  Inject,
  Injectable,
  NotFoundException,
} from '@nestjs/common';
import { BoardStateDraft, UploadedImageFile } from './board-state-intake.types';
import { BOARD_STATE_DRAFT_STORE } from './stores/board-state-draft.store.interface';
import type { BoardStateDraftStore } from './stores/board-state-draft.store.interface';
import { VISION_MODEL_ADAPTER } from './vision-model-adapter.interface';
import type { VisionModelAdapter } from './vision-model-adapter.interface';

export interface CreateUploadDraftInput {
  userId: number;
  matchId?: number;
  roundId?: number;
  file: UploadedImageFile;
}

export interface DetectDraftInput {
  userId: number;
  draftId: number;
  championConfidence?: number;
  identityPadding?: number;
  identityConfidence?: number;
}

@Injectable()
export class BoardStateIntakeService {
  constructor(
    @Inject(BOARD_STATE_DRAFT_STORE)
    private readonly draftStore: BoardStateDraftStore,
    @Inject(VISION_MODEL_ADAPTER)
    private readonly visionModelAdapter: VisionModelAdapter,
    private readonly screenshotStorage: ScreenshotStorageService,
  ) {}

  async createUploadDraft(
    input: CreateUploadDraftInput,
  ): Promise<BoardStateDraft> {
    const formats: Record<string, string> = {
      'image/png': '.png',
      'image/jpeg': '.jpg',
      'image/webp': '.webp',
    };
    const extension = formats[input.file.mimetype];
    if (!extension)
      throw new BadRequestException('Use a PNG, JPEG, or WebP screenshot');
    const filename = input.file.buffer
      ? `upload_${randomUUID()}${extension}`
      : input.file.filename;
    if (!filename) throw new BadRequestException('Missing screenshot');
    const storagePath = input.file.buffer
      ? await this.screenshotStorage.put(
          input.userId,
          filename,
          input.file.buffer,
          input.file.mimetype,
        )
      : input.file.path;
    if (!storagePath) throw new BadRequestException('Missing screenshot bytes');
    try {
      return await this.draftStore.createDraft({
        userId: input.userId,
        matchId: input.matchId,
        roundId: input.roundId,
        screenshotFilename: filename,
        originalFilename: input.file.originalname,
        storagePath,
      });
    } catch (error) {
      if (input.file.buffer)
        await this.screenshotStorage.remove(storagePath).catch(() => undefined);
      throw error;
    }
  }

  async uploadAndDetect(
    input: CreateUploadDraftInput,
  ): Promise<BoardStateDraft> {
    const draft = await this.createUploadDraft(input);
    try {
      return await this.detectDraft(
        { userId: input.userId, draftId: draft.id },
        input.file.buffer,
      );
    } catch {
      // Return the persisted draft so the user can retry without another upload.
      return this.findDraft(draft.id, input.userId);
    }
  }

  async imageUrl(draftId: number, userId: number) {
    const draft = await this.findDraft(draftId, userId);
    return { url: draft.storagePath.startsWith('supabase://') ? await this.screenshotStorage.signedDownloadUrl(draft.storagePath) : null };
  }

  async readImage(draftId: number, userId: number): Promise<Buffer> {
    const draft = await this.findDraft(draftId, userId);
    return this.screenshotStorage.read(draft.storagePath);
  }

  async findDraft(draftId: number, userId: number): Promise<BoardStateDraft> {
    const draft = await this.draftStore.findDraftById(draftId, userId);

    if (!draft) {
      throw new NotFoundException(
        `Board State draft #${draftId} not found or access denied`,
      );
    }

    return draft;
  }

  async detectDraft(
    input: DetectDraftInput,
    imageBytes?: Buffer,
  ): Promise<BoardStateDraft> {
    const draft = await this.findDraft(input.draftId, input.userId);
    if (draft.roundId)
      throw new ConflictException(
        'This board has already been saved. Upload a new screenshot to detect another round.',
      );

    try {
      const boardState = await this.visionModelAdapter.detectBoardState({
        imageName: draft.screenshotFilename,
        ...(draft.storagePath.startsWith('supabase://')
          ? {
              imageUrl: await this.screenshotStorage.signedDownloadUrl(
                draft.storagePath,
              ),
            }
          : {
              imageBytes:
                imageBytes ??
                (await this.screenshotStorage.read(draft.storagePath)),
            }),
        championConfidence: input.championConfidence,
        identityPadding: input.identityPadding,
        identityConfidence: input.identityConfidence,
      });

      return await this.draftStore.updateDraft(draft.id, {
        status: 'detected',
        boardState,
        errorMessage: null,
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      await this.draftStore.updateDraft(draft.id, {
        status: 'failed',
        errorMessage: message,
      });
      throw error;
    }
  }
}
