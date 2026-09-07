import { Injectable } from '@nestjs/common';
import { TftChampionAsset, TftSetChampionsResponse } from './tft-data.types';

interface CommunityDragonChampion {
  apiName?: string;
  characterName?: string;
  name?: string;
  cost?: number | null;
  icon?: string;
  squareIcon?: string;
  traits?: string[];
}

interface CommunityDragonSetData {
  number?: number;
  champions?: CommunityDragonChampion[];
}

interface CommunityDragonTftData {
  setData?: CommunityDragonSetData[];
  sets?: Record<string, { champions?: CommunityDragonChampion[] }>;
}

const CDRAGON_TFT_URL = 'https://raw.communitydragon.org/latest/cdragon/tft/en_us.json';

@Injectable()
export class TftDataService {
  private cachedData: CommunityDragonTftData | null = null;

  async getSetChampions(setNumber: number): Promise<TftSetChampionsResponse> {
    const data = await this.getCommunityDragonData();
    const champions = this.findSetChampions(data, setNumber)
      .map((champion) => this.toChampionAsset(champion))
      .filter((champion) => champion.name.length > 0)
      .sort((a, b) => a.name.localeCompare(b.name));

    return {
      set: setNumber,
      locale: 'en_us',
      source: 'communitydragon',
      champions,
    };
  }

  private async getCommunityDragonData(): Promise<CommunityDragonTftData> {
    if (this.cachedData) {
      return this.cachedData;
    }

    const response = await fetch(CDRAGON_TFT_URL);

    if (!response.ok) {
      throw new Error(`CommunityDragon returned ${response.status}`);
    }

    this.cachedData = (await response.json()) as CommunityDragonTftData;
    return this.cachedData;
  }

  private findSetChampions(
    data: CommunityDragonTftData,
    setNumber: number,
  ): CommunityDragonChampion[] {
    const setDataMatch = data.setData?.find((setData) => setData.number === setNumber);

    if (setDataMatch?.champions) {
      return setDataMatch.champions;
    }

    return data.sets?.[String(setNumber)]?.champions ?? [];
  }

  private toChampionAsset(champion: CommunityDragonChampion): TftChampionAsset {
    const apiName = champion.apiName ?? champion.characterName ?? champion.name ?? '';
    const name = champion.name ?? apiName;

    return {
      id: this.normalizeId(apiName || name),
      apiName,
      name,
      cost: champion.cost ?? null,
      imageUrl: this.toImageUrl(champion.squareIcon ?? champion.icon),
      traits: champion.traits ?? [],
    };
  }

  private normalizeId(value: string): string {
    return value.trim().toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '');
  }

  private toImageUrl(assetPath?: string): string | null {
    if (!assetPath) {
      return null;
    }

    return `https://raw.communitydragon.org/latest/game/${assetPath
      .toLowerCase()
      .replace('.tex', '.png')}`;
  }
}
