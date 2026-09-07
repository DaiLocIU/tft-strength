import {
  BoardStateDraft,
  BoardStateDraftStatus,
  CreateBoardStateDraftData,
  UpdateBoardStateDraftData,
} from '../board-state-intake.types';

export const BOARD_STATE_DRAFT_STORE = Symbol('BOARD_STATE_DRAFT_STORE');

export interface BoardStateDraftStore {
  transition(id: number, userId: number, from: BoardStateDraftStatus[], data: UpdateBoardStateDraftData, before?: Date): Promise<BoardStateDraft | null>;
  createDraft(data: CreateBoardStateDraftData): Promise<BoardStateDraft>;
  findDraftById(id: number, userId?: number): Promise<BoardStateDraft | null>;
  updateDraft(
    id: number,
    data: UpdateBoardStateDraftData,
  ): Promise<BoardStateDraft>;
}
