import { Injectable } from '@nestjs/common';
import {
  DetectBoardStateInput,
  VisionModelAdapter,
} from './vision-model-adapter.interface';
import { BoardState } from './board-state-intake.types';

@Injectable()
export class PythonBoardStateAdapter implements VisionModelAdapter {
  private readonly baseUrl =
    process.env.VISION_BOARD_STATE_URL ?? 'http://127.0.0.1:8095';

  async detectBoardState(input: DetectBoardStateInput): Promise<BoardState> {
    const url = new URL(
      input.imageUrl ? '/board-state' : '/board-state-bytes',
      this.baseUrl,
    );

    if (input.championConfidence !== undefined) {
      url.searchParams.set('champion_conf', String(input.championConfidence));
    }

    if (input.identityPadding !== undefined) {
      url.searchParams.set('identity_padding', String(input.identityPadding));
    }

    if (input.identityConfidence !== undefined) {
      url.searchParams.set('identity_conf', String(input.identityConfidence));
    }

    const headers: Record<string, string> = {
      'Content-Type': input.imageUrl
        ? 'application/json'
        : 'application/octet-stream',
    };
    if (process.env.VISION_SERVICE_KEY)
      headers['X-Vision-Key'] = process.env.VISION_SERVICE_KEY;
    if (process.env.VISION_VERCEL_BYPASS_TOKEN)
      headers['x-vercel-protection-bypass'] =
        process.env.VISION_VERCEL_BYPASS_TOKEN;
    if (!input.imageUrl && !input.imageBytes)
      throw new Error('Missing image source');
    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: input.imageUrl
        ? JSON.stringify({ imageUrl: input.imageUrl })
        : new Uint8Array(input.imageBytes!),
      signal: AbortSignal.timeout(240000),
    });

    if (!response.ok) {
      throw new Error(
        `Python Board State API failed with ${response.status}; retry detection`,
      );
    }

    const result = (await response.json()) as BoardState;
    if (!Array.isArray(result.units))
      throw new Error('Vision returned an invalid board');
    return { ...result, image_name: input.imageName };
  }
}
