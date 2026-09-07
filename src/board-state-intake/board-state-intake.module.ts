import { UploadsController } from './uploads.controller';
import { DirectUploadsService } from './uploads.service';
import { ScreenshotStorageService } from './screenshot-storage.service';
import { SaveBoardRoundService } from './save-board-round.service';
import { Module } from '@nestjs/common';
import { PrismaModule } from '../prisma/prisma.module';
import { BoardStateIntakeController } from './board-state-intake.controller';
import { BoardStateIntakeService } from './board-state-intake.service';
import { PythonBoardStateAdapter } from './python-board-state.adapter';
import { BOARD_STATE_DRAFT_STORE } from './stores/board-state-draft.store.interface';
import { PrismaBoardStateDraftStore } from './stores/prisma-board-state-draft.store';
import { VISION_MODEL_ADAPTER } from './vision-model-adapter.interface';

@Module({
  imports: [PrismaModule],
  controllers: [BoardStateIntakeController, UploadsController],
  providers: [
    ScreenshotStorageService,
    DirectUploadsService,
    SaveBoardRoundService,
    BoardStateIntakeService,
    {
      provide: BOARD_STATE_DRAFT_STORE,
      useClass: PrismaBoardStateDraftStore,
    },
    {
      provide: VISION_MODEL_ADAPTER,
      useClass: PythonBoardStateAdapter,
    },
  ],
  exports: [
    BoardStateIntakeService,
    BOARD_STATE_DRAFT_STORE,
    VISION_MODEL_ADAPTER,
  ],
})
export class BoardStateIntakeModule {}
