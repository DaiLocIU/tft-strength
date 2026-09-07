import { Module } from '@nestjs/common';
import { AppController } from './app.controller';
import { AppService } from './app.service';
import { AuthModule } from './auth/auth.module';
import { BoardStateIntakeModule } from './board-state-intake/board-state-intake.module';
import { MatchTimelineModule } from './match-timeline/match-timeline.module';
import { PrismaModule } from './prisma/prisma.module';
import { StatsModule } from './stats/stats.module';
import { TftDataModule } from './tft-data/tft-data.module';

@Module({
  imports: [
    PrismaModule,
    AuthModule,
    MatchTimelineModule,
    StatsModule,
    BoardStateIntakeModule,
    TftDataModule,
  ],
  controllers: [AppController],
  providers: [AppService],
})
export class AppModule {}
