import { IsInt, IsOptional, Max, Min, ValidateIf } from 'class-validator';

export class CreateRoundDto {
  @IsOptional()
  @IsInt()
  matchId?: number;

  @IsInt()
  @Min(1)
  @Max(7)
  stage: number;

  @IsInt()
  @Min(1)
  @Max(7)
  @ValidateIf((o: CreateRoundDto) => o.stage === 1)
  @Max(4, { message: 'roundNumber cannot be greater than 4 for Stage 1' })
  roundNumber: number;

  @IsInt()
  @Min(0)
  gold: number;

  @IsInt()
  @Min(0)
  hp: number;

  @IsInt()
  @Min(0)
  level: number;

  @IsInt()
  streak: number;
}
