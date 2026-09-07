import { Injectable } from '@nestjs/common';
import { mkdir, readFile, unlink, writeFile } from 'node:fs/promises';
import { join } from 'node:path';

/** Only NestJS knows where original screenshots are persisted. */
@Injectable()
export class ScreenshotStorageService {
  private readonly url = process.env.SUPABASE_URL;
  private readonly key = process.env.SUPABASE_SERVICE_ROLE_KEY;
  private readonly bucket =
    process.env.SUPABASE_STORAGE_BUCKET ?? 'board-screenshots';

  private async request(path: string, init: RequestInit = {}) {
    if (!this.url || !this.key)
      throw new Error('Supabase Storage is not configured');
    const response = await fetch(
      `${this.url.replace(/\/$/, '')}/storage/v1/object/${path}`,
      {
        ...init,
        headers: {
          apikey: this.key,
          ...init.headers,
        },
        signal: AbortSignal.timeout(30000),
      },
    );
    if (!response.ok)
      throw new Error(`Screenshot storage request failed (${response.status})`);
    return response;
  }

  async put(
    userId: number,
    filename: string,
    bytes: Buffer,
    contentType: string,
  ): Promise<string> {
    if (this.url) {
      const objectPath = `${this.bucket}/${userId}/${filename}`;
      await this.request(objectPath, {
        method: 'POST',
        headers: { 'Content-Type': contentType, 'x-upsert': 'false' },
        body: new Uint8Array(bytes),
      });
      return `supabase://${objectPath}`;
    }
    if (process.env.VERCEL)
      throw new Error('Configure Supabase Storage before uploading on Vercel');
    const directory =
      process.env.BOARD_STATE_UPLOAD_DIR ?? 'vision-board-detector/data/raw';
    await mkdir(directory, { recursive: true });
    const path = join(directory, filename);
    await writeFile(path, bytes);
    return path;
  }

  objectPath(userId: number, draftId: number, extension: string): string {
    if (!this.url || !this.key)
      throw new Error('Supabase Storage is not configured');
    return `supabase://${this.bucket}/${userId}/${draftId}/original${extension}`;
  }

  async signedUpload(path: string) {
    const objectPath = path.slice('supabase://'.length);
    const response = await this.request(`upload/sign/${objectPath}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'x-upsert': 'false' },
      body: '{}',
    });
    const data = (await response.json()) as { url?: string };
    if (!data.url)
      throw new Error('Storage did not return a signed upload URL');

    const signedUrl = new URL(
      data.url.startsWith('http')
        ? data.url
        : `${this.url!.replace(/\/$/, '')}/storage/v1${data.url}`,
    ).href;
    const token = new URL(data.url, this.url).searchParams.get('token');

    if (!token) throw new Error('Storage did not return an upload token');

    return {
      signedUrl,
      token,
      bucketName: this.bucket,
      objectName: objectPath.slice(this.bucket.length + 1),
    };
  }

  async verifyImage(path: string): Promise<void> {
    const response = await this.request(
      `info/${path.slice('supabase://'.length)}`,
    );

    const data = (await response.json()) as {
      size?: number;
      content_type?: string;
      contentType?: string;
      metadata?: {
        size?: number;
        mimetype?: string;
        contentType?: string;
      };
    };

    const size = data.size ?? data.metadata?.size;

    const mimetype =
      data.content_type ??
      data.contentType ??
      data.metadata?.mimetype ??
      data.metadata?.contentType;

    if (
      !Number.isInteger(size) ||
      size! <= 0 ||
      size! > 10_000_000 ||
      !['image/png', 'image/jpeg', 'image/webp'].includes(mimetype ?? '')
    ) {
      throw new Error(
        'Stored screenshot must be PNG, JPEG, or WebP up to 10 MB',
      );
    }
  }

  async signedDownloadUrl(path: string): Promise<string> {
    if (!path.startsWith('supabase://'))
      throw new Error('Image is not in Supabase');
    const response = await this.request(
      `sign/${path.slice('supabase://'.length)}`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ expiresIn: 60 }),
      },
    );
    const result = (await response.json()) as { signedURL?: string };
    if (!result.signedURL)
      throw new Error('Storage did not return a signed URL');
    return new URL(
      `${this.url!.replace(/\/$/, '')}/storage/v1${result.signedURL}`,
    ).href;
  }

  async read(path: string): Promise<Buffer> {
    if (!path.startsWith('supabase://')) return readFile(path);
    const response = await this.request(
      `authenticated/${path.slice('supabase://'.length)}`,
    );
    return Buffer.from(await response.arrayBuffer());
  }

  async remove(path: string): Promise<void> {
    if (!path.startsWith('supabase://')) return unlink(path);
    const [bucket, ...segments] = path.slice('supabase://'.length).split('/');
    await this.request(bucket, {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prefixes: [segments.join('/')] }),
    });
  }
}
