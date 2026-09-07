import { BoardStateIntakeService } from './board-state-intake.service';
import { ScreenshotStorageService } from './screenshot-storage.service';
import { MemoryBoardStateDraftStore } from './stores/memory-board-state-draft.store';
import { PythonBoardStateAdapter } from './python-board-state.adapter';

const bytes = Buffer.from([0, 255, 137, 80, 78, 71]);
const input = {
  userId: 7,
  file: {
    originalname: 'board.png',
    buffer: bytes,
    size: bytes.length,
    mimetype: 'image/png',
  },
};

function setup() {
  const storage = {
    put: jest.fn().mockResolvedValue('local/7/image.png'),
    read: jest.fn().mockResolvedValue(bytes),
    remove: jest.fn().mockResolvedValue(undefined),
  };
  const store = new MemoryBoardStateDraftStore();
  const vision = {
    detectBoardState: jest
      .fn()
      .mockResolvedValue({ image_name: 'upload', units: [] }),
  };
  const service = new BoardStateIntakeService(
    store,
    vision,
    storage as unknown as ScreenshotStorageService,
  );
  return { storage, store, vision, service };
}

describe('original screenshot flow', () => {
  it('stores the image and metadata before sending identical bytes to vision without downloading', async () => {
    const { storage, store, vision, service } = setup();
    vision.detectBoardState.mockImplementation(async (request) => {
      expect(storage.put).toHaveBeenCalledWith(
        7,
        expect.any(String),
        bytes,
        'image/png',
      );
      expect(await store.findDraftById(1, 7)).toMatchObject({
        status: 'uploaded',
      });
      expect(request.imageBytes).toBe(bytes);
      return { image_name: 'upload', units: [] };
    });
    const result = await service.uploadAndDetect(input);
    expect(result.status).toBe('detected');
    expect(storage.read).not.toHaveBeenCalled();
  });

  it('retains a failed draft and retries using stored bytes through NestJS', async () => {
    const { storage, vision, service } = setup();
    vision.detectBoardState.mockRejectedValueOnce(new Error('Unavailable'));
    const draft = await service.uploadAndDetect(input);
    expect(draft.status).toBe('failed');
    expect(storage.remove).not.toHaveBeenCalled();
    const retried = await service.detectDraft({ draftId: draft.id, userId: 7 });
    expect(retried.status).toBe('detected');
    expect(storage.read).toHaveBeenCalledWith(draft.storagePath);
    expect(vision.detectBoardState.mock.calls[1][0].imageBytes).toEqual(bytes);
    await expect(service.readImage(draft.id, 8)).rejects.toThrow(
      'access denied',
    );
    expect(storage.read).toHaveBeenCalledTimes(1);
  });

  it('does not run vision when storage fails', async () => {
    const { storage, vision, service } = setup();
    storage.put.mockRejectedValue(new Error('Storage unavailable'));
    await expect(service.uploadAndDetect(input)).rejects.toThrow(
      'Storage unavailable',
    );
    expect(vision.detectBoardState).not.toHaveBeenCalled();
  });

  it('cleans up the object when saving metadata fails', async () => {
    const { storage, store, vision, service } = setup();
    jest
      .spyOn(store, 'createDraft')
      .mockRejectedValue(new Error('Database unavailable'));
    await expect(service.uploadAndDetect(input)).rejects.toThrow(
      'Database unavailable',
    );
    expect(storage.remove).toHaveBeenCalledWith('local/7/image.png');
    expect(vision.detectBoardState).not.toHaveBeenCalled();
  });

  it('posts raw bytes and a service key, with no storage URL', async () => {
    const previous = process.env.VISION_SERVICE_KEY;
    process.env.VISION_SERVICE_KEY = 'test-service-key';
    const fetchMock = jest
      .spyOn(globalThis, 'fetch')
      .mockResolvedValue(
        new Response(JSON.stringify({ image_name: 'upload', units: [] })),
      );
    try {
      const result = await new PythonBoardStateAdapter().detectBoardState({
        imageName: 'stored.png',
        imageBytes: bytes,
      });
      const [url, request] = fetchMock.mock.calls[0];
      expect(String(url)).toMatch(/\/board-state-bytes$/);
      expect(request?.method).toBe('POST');
      expect(request?.headers).toMatchObject({
        'X-Vision-Key': 'test-service-key',
      });
      expect(Buffer.from(request?.body as Uint8Array)).toEqual(bytes);
      expect(result.image_name).toBe('stored.png');
    } finally {
      fetchMock.mockRestore();
      if (previous === undefined) delete process.env.VISION_SERVICE_KEY;
      else process.env.VISION_SERVICE_KEY = previous;
    }
  });
});

describe('signed URL inference', () => {
  it('signs the owned stored image on each attempt without reading its bytes', async () => {
    const store = new MemoryBoardStateDraftStore();
    const draft = await store.createDraft({
      userId: 7,
      screenshotFilename: 'image.png',
      originalFilename: 'image.png',
      storagePath: 'supabase://boards/7/image.png',
    });
    const storage = {
      signedDownloadUrl: jest
        .fn()
        .mockResolvedValueOnce('https://storage.test/image?token=one')
        .mockResolvedValueOnce('https://storage.test/image?token=two'),
      read: jest.fn(),
    };
    const vision = {
      detectBoardState: jest.fn(async (_input: { imageUrl?: string }) => ({
        units: [],
      })),
    };
    const service = new BoardStateIntakeService(
      store,
      vision,
      storage as unknown as ScreenshotStorageService,
    );
    await expect(
      service.detectDraft({ userId: 8, draftId: draft.id }),
    ).rejects.toThrow('access denied');
    expect(storage.signedDownloadUrl).not.toHaveBeenCalled();
    await service.detectDraft({ userId: 7, draftId: draft.id }, bytes);
    await service.detectDraft({ userId: 7, draftId: draft.id });
    expect(
      vision.detectBoardState.mock.calls.map((call) => call[0].imageUrl),
    ).toEqual([
      'https://storage.test/image?token=one',
      'https://storage.test/image?token=two',
    ]);
    expect(vision.detectBoardState.mock.calls[0][0]).not.toHaveProperty(
      'imageBytes',
    );
    expect(storage.read).not.toHaveBeenCalled();
  });

  it('posts a small JSON imageUrl request', async () => {
    const imageUrl = 'https://storage.test/image?token=temporary';
    const fetchMock = jest
      .spyOn(globalThis, 'fetch')
      .mockResolvedValue(new Response(JSON.stringify({ units: [] })));
    try {
      await new PythonBoardStateAdapter().detectBoardState({
        imageName: 'image.png',
        imageUrl,
      });
      expect(String(fetchMock.mock.calls[0][0])).toMatch(/\/board-state$/);
      expect(fetchMock.mock.calls[0][1]).toMatchObject({
        body: JSON.stringify({ imageUrl }),
        headers: { 'Content-Type': 'application/json' },
      });
    } finally {
      fetchMock.mockRestore();
    }
  });
});
