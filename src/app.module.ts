import { Module } from '@nestjs/common';
import { AppController } from './app.controller';
import { AppService } from './app.service';
import { AuthModule } from './auth/auth.module';
import { MatchTimelineModule } from './match-timeline/match-timeline.module';
import { PrismaModule } from './prisma/prisma.module';

@Module({
  imports: [PrismaModule, AuthModule, MatchTimelineModule],
  controllers: [AppController],
  providers: [AppService],
})
export class AppModule {}
