import { Type } from 'class-transformer';
import {
  ArrayMaxSize,
  ArrayMinSize,
  IsArray,
  IsInt,
  IsString,
  Max,
  MaxLength,
  Min,
  ValidateNested,
} from 'class-validator';
import { CreateRoundSnapshotDto } from '../../match-timeline/dto/create-round-snapshot.dto';

export class ReviewedUnitDto {
  @IsInt() @Min(0) @Max(3) row: number;
  @IsInt() @Min(0) @Max(6) column: number;
  @IsString() @MaxLength(100) champion: string;
  @IsInt() @Min(1) @Max(3) stars: number;
}

export class SaveBoardRoundDto extends CreateRoundSnapshotDto {
  @IsInt() @Min(1) matchId: number;
  @IsArray()
  @ArrayMinSize(1)
  @ArrayMaxSize(28)
  @ValidateNested({ each: true })
  @Type(() => ReviewedUnitDto)
  units: ReviewedUnitDto[];
}
