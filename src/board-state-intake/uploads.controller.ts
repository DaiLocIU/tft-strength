import { Body, Controller, Param, ParseIntPipe, Post, UseGuards } from '@nestjs/common';
import { IsIn, IsInt, IsString, Max, MaxLength, Min } from 'class-validator';
import { CurrentUser } from '../auth/decorators/current-user.decorator';
import { JwtAuthGuard } from '../auth/guards/jwt-auth.guard';
import { DirectUploadsService } from './uploads.service';

export class InitUploadDto {
  @IsString() @MaxLength(255) filename: string;
  @IsIn(['image/png', 'image/jpeg', 'image/webp']) contentType: string;
  @IsInt() @Min(1) @Max(10_000_000) size: number;
}

@Controller('uploads')
@UseGuards(JwtAuthGuard)
export class UploadsController {
  constructor(private readonly uploads: DirectUploadsService) {}
  @Post('init')
  init(@CurrentUser('userId') userId: number, @Body() body: InitUploadDto) {
    return this.uploads.init(userId, body);
  }
  @Post(':id/complete')
  complete(@CurrentUser('userId') userId: number, @Param('id', ParseIntPipe) id: number) {
    return this.uploads.complete(userId, id);
  }
  @Post(':id/analyze')
  analyze(@CurrentUser('userId') userId: number, @Param('id', ParseIntPipe) id: number) {
    return this.uploads.analyze(userId, id);
  }
}
