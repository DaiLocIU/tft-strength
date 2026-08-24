import { Module } from '@nestjs/common';
import { MatchTimelineModule } from '../match-timeline/match-timeline.module';
import { StatsController } from './stats.controller';
import { StatsService } from './stats.service';

@Module({
  imports: [MatchTimelineModule],
  controllers: [StatsController],
  providers: [StatsService],
  exports: [StatsService],
})
export class StatsModule {}
