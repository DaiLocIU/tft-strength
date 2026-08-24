import {
  Body,
  Controller,
  Delete,
  Get,
  Param,
  Patch,
  Post,
  UseGuards,
} from '@nestjs/common';
import { CurrentUser } from '../auth/decorators/current-user.decorator';
import { JwtAuthGuard } from '../auth/guards/jwt-auth.guard';
import { CreateRoundSnapshotDto } from './dto/create-round-snapshot.dto';
import { UpdateRoundSnapshotDto } from './dto/update-round-snapshot.dto';
import { MatchTimelineService } from './match-timeline.service';

@UseGuards(JwtAuthGuard)
@Controller('matches/:id/rounds')
export class RoundsController {
  constructor(private readonly matchTimelineService: MatchTimelineService) {}

  @Post()
  create(
    @CurrentUser('userId') userId: number,
    @Param('id') matchId: string,
    @Body() createRoundDto: CreateRoundSnapshotDto,
  ) {
    return this.matchTimelineService.recordRoundSnapshot(
      +matchId,
      createRoundDto,
      userId,
    );
  }

  @Get()
  findAll(@CurrentUser('userId') userId: number, @Param('id') matchId: string) {
    return this.matchTimelineService.findAllRoundSnapshots(+matchId, userId);
  }

  @Get(':roundId')
  findOne(
    @CurrentUser('userId') userId: number,
    @Param('id') matchId: string,
    @Param('roundId') roundId: string,
  ) {
    return this.matchTimelineService.findOneRoundSnapshot(
      +matchId,
      roundId,
      userId,
    );
  }

  @Patch(':roundId')
  update(
    @CurrentUser('userId') userId: number,
    @Param('id') matchId: string,
    @Param('roundId') roundId: string,
    @Body() updateRoundDto: UpdateRoundSnapshotDto,
  ) {
    return this.matchTimelineService.updateRoundSnapshot(
      +matchId,
      roundId,
      updateRoundDto,
      userId,
    );
  }

  @Delete(':roundId')
  remove(
    @CurrentUser('userId') userId: number,
    @Param('id') matchId: string,
    @Param('roundId') roundId: string,
  ) {
    return this.matchTimelineService.removeRoundSnapshot(
      +matchId,
      roundId,
      userId,
    );
  }
}
