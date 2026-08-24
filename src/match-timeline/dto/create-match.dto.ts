import {
  IsDateString,
  IsInt,
  IsOptional,
  IsString,
  Max,
  Min,
} from 'class-validator';

export class CreateMatchDto {
  @IsInt()
  @Min(1)
  @Max(8)
  placement: number;

  @IsOptional()
  @IsDateString()
  playedAt?: string;

  @IsOptional()
  @IsString()
  comp?: string;

  @IsOptional()
  @IsString()
  version?: string;
}
