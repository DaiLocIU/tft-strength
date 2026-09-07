import { BadRequestException, ConflictException, Inject, Injectable, NotFoundException } from '@nestjs/common';
import { BOARD_STATE_DRAFT_STORE } from './stores/board-state-draft.store.interface';
import type { BoardStateDraftStore } from './stores/board-state-draft.store.interface';
import { VISION_MODEL_ADAPTER } from './vision-model-adapter.interface';
import type { VisionModelAdapter } from './vision-model-adapter.interface';
import { ScreenshotStorageService } from './screenshot-storage.service';

@Injectable()
export class DirectUploadsService {
  constructor(
    @Inject(BOARD_STATE_DRAFT_STORE) private readonly store: BoardStateDraftStore,
    private readonly storage: ScreenshotStorageService,
    @Inject(VISION_MODEL_ADAPTER) private readonly vision: VisionModelAdapter,
  ) {}

  async init(userId: number, input: { filename: string; contentType: string; size: number }) {
    const extension = { 'image/png': '.png', 'image/jpeg': '.jpg', 'image/webp': '.webp' }[input.contentType];
    if (!extension || !Number.isInteger(input.size) || input.size <= 0 || input.size > 10_000_000)
      throw new BadRequestException('Choose a PNG, JPEG, or WebP screenshot up to 10 MB');
    const draft = await this.store.createDraft({ userId, originalFilename: input.filename,
      screenshotFilename: `original${extension}`, storagePath: '', status: 'draft' });
    const storagePath = this.storage.objectPath(userId, draft.id, extension);
    await this.store.updateDraft(draft.id, { storagePath });
    const upload = await this.storage.signedUpload(storagePath);
    const uploading = await this.store.transition(draft.id, userId, ['draft'], { status: 'uploading' });
    return { draft: uploading!, upload };
  }

  private async owned(userId: number, id: number) {
    const draft = await this.store.findDraftById(id, userId);
    if (!draft) throw new NotFoundException('Upload not found');
    return draft;
  }

  async complete(userId: number, id: number) {
    const draft = await this.owned(userId, id);
    if (['uploaded', 'processing', 'completed'].includes(draft.status)) return draft;
    if (draft.status !== 'uploading') throw new ConflictException('Upload is not awaiting completion');
    try { await this.storage.verifyImage(draft.storagePath); }
    catch { throw new BadRequestException('Upload is missing, incomplete, or invalid. Finish uploading before continuing.'); }
    const completed = await this.store.transition(id, userId, ['uploading'], { status: 'uploaded' });
    return completed ?? this.owned(userId, id);
  }

  async analyze(userId: number, id: number) {
    const draft = await this.owned(userId, id);
    if (draft.status === 'completed') return draft;
    if (draft.roundId) throw new ConflictException('This round has already been saved');
    const stale = draft.status === 'processing' ? new Date(Date.now() - 10 * 60_000) : undefined;
    const claimed = await this.store.transition(id, userId, stale ? ['processing'] : ['uploaded', 'failed'],
      { status: 'processing', errorMessage: null }, stale);
    if (!claimed) throw new ConflictException('Finish uploading first, or wait for the current analysis');
    try {
      // Resolve only the owned database path. URLs and paths from the browser are never used.
      const imageUrl = await this.storage.signedDownloadUrl(claimed.storagePath);
      const boardState = await this.vision.detectBoardState({ imageName: claimed.screenshotFilename, imageUrl });
      return (await this.store.transition(id, userId, ['processing'], { status: 'completed', boardState }, new Date(claimed.updatedAt.getTime() + 1))) ?? this.owned(userId, id);
    } catch {
      return (await this.store.transition(id, userId, ['processing'], {
        status: 'failed', errorMessage: 'Detection failed. Retry to request a fresh image URL.',
      }, new Date(claimed.updatedAt.getTime() + 1))) ?? this.owned(userId, id);
    }
  }
}
