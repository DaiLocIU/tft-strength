import { ScreenshotStorageService } from './screenshot-storage.service';

describe('Supabase screenshot storage', () => {
  it('uploads unchanged bytes, reads privately and deletes by object prefix', async () => {
    const originalEnv = { ...process.env };
    process.env.SUPABASE_URL = 'https://storage.example.test';
    process.env.SUPABASE_SERVICE_ROLE_KEY = 'test-key';
    process.env.SUPABASE_STORAGE_BUCKET = 'boards';
    const bytes = Buffer.from([0, 255, 1]);
    const mockedFetch = jest
      .spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce(new Response('{}'))
      .mockResolvedValueOnce(new Response(bytes))
      .mockResolvedValueOnce(new Response('{}'))
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            signedURL: '/object/sign/boards/7/image.png?token=temporary',
          }),
        ),
      );
    try {
      const storage = new ScreenshotStorageService();
      const path = await storage.put(7, 'image.png', bytes, 'image/png');
      expect(path).toBe('supabase://boards/7/image.png');
      expect(mockedFetch.mock.calls[0][0]).toBe(
        'https://storage.example.test/storage/v1/object/boards/7/image.png',
      );
      expect(
        Buffer.from(mockedFetch.mock.calls[0][1]?.body as Uint8Array),
      ).toEqual(bytes);
      expect(await storage.read(path)).toEqual(bytes);
      expect(mockedFetch.mock.calls[1][0]).toBe(
        'https://storage.example.test/storage/v1/object/authenticated/boards/7/image.png',
      );
      await storage.remove(path);
      expect(mockedFetch.mock.calls[2]).toEqual([
        'https://storage.example.test/storage/v1/object/boards',
        expect.objectContaining({
          method: 'DELETE',
          body: JSON.stringify({ prefixes: ['7/image.png'] }),
        }),
      ]);
      expect(await storage.signedDownloadUrl(path)).toBe(
        'https://storage.example.test/storage/v1/object/sign/boards/7/image.png?token=temporary',
      );
      expect(mockedFetch.mock.calls[3]).toEqual([
        'https://storage.example.test/storage/v1/object/sign/boards/7/image.png',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ expiresIn: 60 }),
        }),
      ]);
    } finally {
      mockedFetch.mockRestore();
      process.env = originalEnv;
    }
  });
});
