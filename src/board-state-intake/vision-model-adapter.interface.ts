import { BoardState } from './board-state-intake.types';

export const VISION_MODEL_ADAPTER = Symbol('VISION_MODEL_ADAPTER');

export interface DetectBoardStateInput {
  imageName: string;
  championConfidence?: number;
  identityPadding?: number;
  identityConfidence?: number;
}

export interface VisionModelAdapter {
  detectBoardState(input: DetectBoardStateInput): Promise<BoardState>;
}
