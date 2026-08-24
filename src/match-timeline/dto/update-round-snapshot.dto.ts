import { PartialType } from '@nestjs/mapped-types';
import { CreateRoundSnapshotDto } from './create-round-snapshot.dto';

export class UpdateRoundSnapshotDto extends PartialType(
  CreateRoundSnapshotDto,
) {}
