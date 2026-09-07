import { Controller, Get, Param } from '@nestjs/common';
import { TftDataService } from './tft-data.service';

@Controller('tft-data')
export class TftDataController {
  constructor(private readonly tftDataService: TftDataService) {}

  @Get('sets/:set/champions')
  getSetChampions(@Param('set') setNumber: string) {
    return this.tftDataService.getSetChampions(Number(setNumber));
  }
}
