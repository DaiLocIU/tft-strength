import { IsInt, IsOptional, Min } from 'class-validator';

export class UploadBoardStateImageDto {
  @IsOptional()
  @IsInt()
  @Min(1)
  matchId?: number;

  @IsOptional()
  @IsInt()
  @Min(1)
  roundId?: number;
}
