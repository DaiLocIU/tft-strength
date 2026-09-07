import {
  BoardStateDraft,
  CreateBoardStateDraftData,
  UpdateBoardStateDraftData,
} from '../board-state-intake.types';

export const BOARD_STATE_DRAFT_STORE = Symbol('BOARD_STATE_DRAFT_STORE');

export interface BoardStateDraftStore {
  createDraft(data: CreateBoardStateDraftData): Promise<BoardStateDraft>;
  findDraftById(id: number, userId?: number): Promise<BoardStateDraft | null>;
  updateDraft(
    id: number,
    data: UpdateBoardStateDraftData,
  ): Promise<BoardStateDraft>;
}
