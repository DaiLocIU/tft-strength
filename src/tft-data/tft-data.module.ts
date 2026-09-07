import { Module } from '@nestjs/common';
import { TftDataController } from './tft-data.controller';
import { TftDataService } from './tft-data.service';

@Module({
  controllers: [TftDataController],
  providers: [TftDataService],
  exports: [TftDataService],
})
export class TftDataModule {}
