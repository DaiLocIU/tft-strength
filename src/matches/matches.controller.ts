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
import { MatchesService } from './matches.service';
import { CreateMatchDto } from './dto/create-match.dto';
import { UpdateMatchDto } from './dto/update-match.dto';

@UseGuards(JwtAuthGuard)
@Controller('matches')
export class MatchesController {
  constructor(private readonly matchesService: MatchesService) {}

  @Post()
  create(
    @CurrentUser('userId') userId: number,
    @Body() createMatchDto: CreateMatchDto,
  ) {
    return this.matchesService.create(createMatchDto, userId);
  }

  @Get()
  findAll(@CurrentUser('userId') userId: number) {
    return this.matchesService.findAll(userId);
  }

  @Get(':id')
  findOne(@CurrentUser('userId') userId: number, @Param('id') id: string) {
    return this.matchesService.findOne(+id, userId);
  }

  @Patch(':id')
  update(
    @CurrentUser('userId') userId: number,
    @Param('id') id: string,
    @Body() updateMatchDto: UpdateMatchDto,
  ) {
    return this.matchesService.update(+id, updateMatchDto, userId);
  }

  @Delete(':id')
  remove(@CurrentUser('userId') userId: number, @Param('id') id: string) {
    return this.matchesService.remove(+id, userId);
  }
}
