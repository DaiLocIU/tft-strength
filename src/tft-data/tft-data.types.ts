export interface TftChampionAsset {
  id: string;
  apiName: string;
  name: string;
  cost: number | null;
  imageUrl: string | null;
  traits: string[];
}

export interface TftSetChampionsResponse {
  set: number;
  locale: string;
  source: 'communitydragon';
  champions: TftChampionAsset[];
}
