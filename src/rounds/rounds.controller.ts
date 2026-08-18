import {
  Controller,
  Get,
  Post,
  Body,
  Patch,
  Param,
  Delete,
} from '@nestjs/common';
import { RoundsService } from './rounds.service';
import { CreateRoundDto } from './dto/create-round.dto';
import { UpdateRoundDto } from './dto/update-round.dto';

@Controller('matches/:id/rounds')
export class RoundsController {
  constructor(private readonly roundsService: RoundsService) {}

  @Post()
  create(@Param('id') matchId: string, @Body() createRoundDto: CreateRoundDto) {
    return this.roundsService.create(+matchId, createRoundDto);
  }

  @Get()
  findAll(@Param('id') matchId: string) {
    return this.roundsService.findAll(+matchId);
  }

  @Get(':roundId')
  findOne(@Param('id') matchId: string, @Param('roundId') roundId: string) {
    return this.roundsService.findOne(+matchId, roundId);
  }

  @Patch(':roundId')
  update(
    @Param('id') matchId: string,
    @Param('roundId') roundId: string,
    @Body() updateRoundDto: UpdateRoundDto,
  ) {
    return this.roundsService.update(+matchId, roundId, updateRoundDto);
  }

  @Delete(':roundId')
  remove(@Param('id') matchId: string, @Param('roundId') roundId: string) {
    return this.roundsService.remove(+matchId, roundId);
  }
}
