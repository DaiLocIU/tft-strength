import {
  Controller,
  Get,
  Post,
  Body,
  Patch,
  Param,
  Delete,
  UseGuards,
} from '@nestjs/common';
import { CurrentUser } from '../auth/decorators/current-user.decorator';
import { JwtAuthGuard } from '../auth/guards/jwt-auth.guard';
import { RoundsService } from './rounds.service';
import { CreateRoundDto } from './dto/create-round.dto';
import { UpdateRoundDto } from './dto/update-round.dto';

@UseGuards(JwtAuthGuard)
@Controller('matches/:id/rounds')
export class RoundsController {
  constructor(private readonly roundsService: RoundsService) {}

  @Post()
  create(
    @CurrentUser('userId') userId: number,
    @Param('id') matchId: string,
    @Body() createRoundDto: CreateRoundDto,
  ) {
    return this.roundsService.create(+matchId, createRoundDto, userId);
  }

  @Get()
  findAll(@CurrentUser('userId') userId: number, @Param('id') matchId: string) {
    return this.roundsService.findAll(+matchId, userId);
  }

  @Get(':roundId')
  findOne(
    @CurrentUser('userId') userId: number,
    @Param('id') matchId: string,
    @Param('roundId') roundId: string,
  ) {
    return this.roundsService.findOne(+matchId, roundId, userId);
  }

  @Patch(':roundId')
  update(
    @CurrentUser('userId') userId: number,
    @Param('id') matchId: string,
    @Param('roundId') roundId: string,
    @Body() updateRoundDto: UpdateRoundDto,
  ) {
    return this.roundsService.update(+matchId, roundId, updateRoundDto, userId);
  }

  @Delete(':roundId')
  remove(
    @CurrentUser('userId') userId: number,
    @Param('id') matchId: string,
    @Param('roundId') roundId: string,
  ) {
    return this.roundsService.remove(+matchId, roundId, userId);
  }
}
