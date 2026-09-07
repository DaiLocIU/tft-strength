import { NotFoundException } from '@nestjs/common';
import { BoardStateIntakeService } from './board-state-intake.service';
import { BoardState } from './board-state-intake.types';
import { MemoryBoardStateDraftStore } from './stores/memory-board-state-draft.store';
import { VisionModelAdapter } from './vision-model-adapter.interface';

class FakeVisionModelAdapter implements VisionModelAdapter {
  calls: string[] = [];
  result: BoardState = {
    image_name: 'upload.png',
    units: [
      {
        row: 3,
        column: 2,
        champion: 'alune',
        source: 'both',
        star: '2star',
        needs_review: false,
      },
    ],
  };

  async detectBoardState(input: { imageName: string }): Promise<BoardState> {
    this.calls.push(input.imageName);
    return this.result;
  }
}

describe('BoardStateIntakeService', () => {
  let store: MemoryBoardStateDraftStore;
  let visionModelAdapter: FakeVisionModelAdapter;
  let service: BoardStateIntakeService;

  beforeEach(() => {
    store = new MemoryBoardStateDraftStore();
    visionModelAdapter = new FakeVisionModelAdapter();
    service = new BoardStateIntakeService(store, visionModelAdapter);
  });

  it('creates an uploaded Board State draft before detection runs', async () => {
    const draft = await service.createUploadDraft({
      userId: 7,
      matchId: 3,
      file: {
        originalname: 'raw-board.png',
        filename: 'stored-board.png',
        path: 'uploads/board-state/stored-board.png',
        size: 1234,
        mimetype: 'image/png',
      },
    });

    expect(draft.userId).toBe(7);
    expect(draft.matchId).toBe(3);
    expect(draft.status).toBe('uploaded');
    expect(draft.boardState).toBeNull();
  });

  it('runs vision detection and stores a reviewable Board State', async () => {
    const draft = await service.createUploadDraft({
      userId: 7,
      file: {
        originalname: 'raw-board.png',
        filename: 'stored-board.png',
        path: 'uploads/board-state/stored-board.png',
        size: 1234,
        mimetype: 'image/png',
      },
    });

    const detected = await service.detectDraft({
      userId: 7,
      draftId: draft.id,
      championConfidence: 0.65,
    });

    expect(visionModelAdapter.calls).toEqual(['stored-board.png']);
    expect(detected.status).toBe('detected');
    expect(detected.boardState?.units[0].champion).toBe('alune');
    expect(detected.boardState?.units[0].star).toBe('2star');
  });

  it('does not allow another user to read a draft', async () => {
    const draft = await service.createUploadDraft({
      userId: 7,
      file: {
        originalname: 'raw-board.png',
        filename: 'stored-board.png',
        path: 'uploads/board-state/stored-board.png',
        size: 1234,
        mimetype: 'image/png',
      },
    });

    await expect(service.findDraft(draft.id, 8)).rejects.toThrow(
      NotFoundException,
    );
  });
});
