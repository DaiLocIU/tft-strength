import { IsNumber, IsOptional, Max, Min } from 'class-validator';

export class DetectBoardStateDraftDto {
  @IsOptional()
  @IsNumber()
  @Min(0)
  @Max(1)
  championConfidence?: number;

  @IsOptional()
  @IsNumber()
  @Min(0)
  @Max(1)
  identityPadding?: number;

  @IsOptional()
  @IsNumber()
  @Min(0)
  @Max(1)
  identityConfidence?: number;
}
