import { IsInt, Max, Min } from 'class-validator';

export class CreateRoundSnapshotDto {
  @IsInt()
  @Min(1)
  @Max(9)
  stage: number;

  @IsInt()
  @Min(1)
  @Max(7)
  roundNumber: number;

  @IsInt()
  @Min(0)
  gold: number;

  @IsInt()
  @Min(0)
  @Max(100)
  hp: number;

  @IsInt()
  @Min(1)
  @Max(11)
  level: number;

  @IsInt()
  streak: number;
}
