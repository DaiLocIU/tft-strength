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
    const url = new URL('/board-state', this.baseUrl);
    url.searchParams.set('image', input.imageName);

    if (input.championConfidence !== undefined) {
      url.searchParams.set('champion_conf', String(input.championConfidence));
    }

    if (input.identityPadding !== undefined) {
      url.searchParams.set('identity_padding', String(input.identityPadding));
    }

    if (input.identityConfidence !== undefined) {
      url.searchParams.set('identity_conf', String(input.identityConfidence));
    }

    const response = await fetch(url);

    if (!response.ok) {
      const body = await response.text();
      throw new Error(
        `Python Board State API failed with ${response.status}: ${body}`,
      );
    }

    return (await response.json()) as BoardState;
  }
}
