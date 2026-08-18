import { Module } from '@nestjs/common';
import { AppController } from './app.controller';
import { AppService } from './app.service';
import { AuthModule } from './auth/auth.module';
import { MatchesModule } from './matches/matches.module';
import { PrismaModule } from './prisma/prisma.module';
import { RoundsModule } from './rounds/rounds.module';

@Module({
  imports: [PrismaModule, AuthModule, MatchesModule, RoundsModule],
  controllers: [AppController],
  providers: [AppService],
})
export class AppModule {}
