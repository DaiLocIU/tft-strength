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
import { CreateMatchDto } from './dto/create-match.dto';
import { UpdateMatchDto } from './dto/update-match.dto';
import { MatchTimelineService } from './match-timeline.service';

@UseGuards(JwtAuthGuard)
@Controller('matches')
export class MatchesController {
  constructor(private readonly matchTimelineService: MatchTimelineService) {}

  @Post()
  create(
    @CurrentUser('userId') userId: number,
    @Body() createMatchDto: CreateMatchDto,
  ) {
    return this.matchTimelineService.createMatch(createMatchDto, userId);
  }

  @Get()
  findAll(@CurrentUser('userId') userId: number) {
    return this.matchTimelineService.findAllMatches(userId);
  }

  @Get(':id')
  findOne(@CurrentUser('userId') userId: number, @Param('id') id: string) {
    return this.matchTimelineService.findOneMatch(+id, userId);
  }

  @Patch(':id')
  update(
    @CurrentUser('userId') userId: number,
    @Param('id') id: string,
    @Body() updateMatchDto: UpdateMatchDto,
  ) {
    return this.matchTimelineService.updateMatch(+id, updateMatchDto, userId);
  }

  @Delete(':id')
  remove(@CurrentUser('userId') userId: number, @Param('id') id: string) {
    return this.matchTimelineService.removeMatch(+id, userId);
  }
}
