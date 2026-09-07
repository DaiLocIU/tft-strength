import {
  IsDateString,
  IsInt,
  IsOptional,
  IsString,
  Max,
  Min,
} from 'class-validator';

export class CreateMatchDto {
  @IsOptional()
  @IsInt()
  @Min(1)
  @Max(8)
  placement?: number;

  @IsOptional()
  @IsDateString()
  playedAt?: string;

  @IsOptional()
  @IsString()
  name?: string;

  @IsOptional()
  @IsString()
  comp?: string;

}
