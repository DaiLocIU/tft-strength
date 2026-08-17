import { Module } from '@nestjs/common';
import { AppController } from './app.controller';
import { AppService } from './app.service';
import { MatchesModule } from './matches/matches.module';
import { PrismaModule } from './prisma/prisma.module';

@Module({
  imports: [PrismaModule, MatchesModule],
  controllers: [AppController],
  providers: [AppService],
})
export class AppModule {}
