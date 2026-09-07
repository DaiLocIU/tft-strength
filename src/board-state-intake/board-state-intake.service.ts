import {
  ConflictException,
  Inject,
  Injectable,
  NotFoundException,
} from '@nestjs/common';
import {
  BoardStateDraft,
  UploadedImageFile,
} from './board-state-intake.types';
import {
  BOARD_STATE_DRAFT_STORE,
} from './stores/board-state-draft.store.interface';
import type { BoardStateDraftStore } from './stores/board-state-draft.store.interface';
import {
  VISION_MODEL_ADAPTER,
} from './vision-model-adapter.interface';
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
  ) {}

  async createUploadDraft(
    input: CreateUploadDraftInput,
  ): Promise<BoardStateDraft> {
    return await this.draftStore.createDraft({
      userId: input.userId,
      matchId: input.matchId,
      roundId: input.roundId,
      screenshotFilename: input.file.filename,
      originalFilename: input.file.originalname,
      storagePath: input.file.path,
    });
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

  async detectDraft(input: DetectDraftInput): Promise<BoardStateDraft> {
    const draft = await this.findDraft(input.draftId, input.userId);
    if (draft.roundId) throw new ConflictException('This board has already been saved. Upload a new screenshot to detect another round.');

    try {
      const boardState = await this.visionModelAdapter.detectBoardState({
        imageName: draft.screenshotFilename,
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
