import {
  BoardStateDraft,
  CreateBoardStateDraftData,
  UpdateBoardStateDraftData,
} from '../board-state-intake.types';
import { BoardStateDraftStore } from './board-state-draft.store.interface';

export class MemoryBoardStateDraftStore implements BoardStateDraftStore {
  private drafts: BoardStateDraft[] = [];
  private nextDraftId = 1;

  async createDraft(data: CreateBoardStateDraftData): Promise<BoardStateDraft> {
    const now = new Date();
    const draft: BoardStateDraft = {
      id: this.nextDraftId++,
      userId: data.userId,
      matchId: data.matchId ?? null,
      roundId: data.roundId ?? null,
      screenshotFilename: data.screenshotFilename,
      originalFilename: data.originalFilename,
      storagePath: data.storagePath,
      status: 'uploaded',
      boardState: null,
      errorMessage: null,
      createdAt: now,
      updatedAt: now,
    };

    this.drafts.push(draft);
    return { ...draft };
  }

  async findDraftById(
    id: number,
    userId?: number,
  ): Promise<BoardStateDraft | null> {
    const draft = this.drafts.find(
      (item) => item.id === id && (userId === undefined || item.userId === userId),
    );

    return draft ? { ...draft } : null;
  }

  async updateDraft(
    id: number,
    data: UpdateBoardStateDraftData,
  ): Promise<BoardStateDraft> {
    const index = this.drafts.findIndex((draft) => draft.id === id);

    if (index === -1) {
      throw new Error(`Board State draft #${id} not found in memory store`);
    }

    const current = this.drafts[index];
    const updated: BoardStateDraft = {
      ...current,
      status: data.status ?? current.status,
      boardState:
        data.boardState !== undefined ? data.boardState : current.boardState,
      errorMessage:
        data.errorMessage !== undefined
          ? data.errorMessage
          : current.errorMessage,
      updatedAt: new Date(),
    };

    this.drafts[index] = updated;
    return { ...updated };
  }

  reset() {
    this.drafts = [];
    this.nextDraftId = 1;
  }
}
