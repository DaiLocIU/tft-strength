import { Module } from '@nestjs/common';
import { PrismaModule } from '../prisma/prisma.module';
import { MatchesController } from './matches.controller';
import { MatchTimelineService } from './match-timeline.service';
import { RoundsController } from './rounds.controller';
import { MATCH_TIMELINE_STORE } from './stores/match-timeline.store.interface';
import { PrismaMatchTimelineStore } from './stores/prisma-match-timeline.store';

@Module({
  imports: [PrismaModule],
  controllers: [MatchesController, RoundsController],
  providers: [
    MatchTimelineService,
    {
      provide: MATCH_TIMELINE_STORE,
      useClass: PrismaMatchTimelineStore,
    },
  ],
  exports: [MatchTimelineService, MATCH_TIMELINE_STORE],
})
export class MatchTimelineModule {}
