import { OmitType } from '@nestjs/mapped-types';
import { SaveBoardRoundDto } from './dto/save-board-round.dto';

export class AnalyzeBoardDto extends OmitType(SaveBoardRoundDto, [
  'matchId',
] as const) {}

export function buildBoardGuide(dto: AnalyzeBoardDto) {
  const tips: { title: string; detail: string }[] = [];
  const oneStar = dto.units.filter((unit) => unit.stars === 1).length;
  if (dto.units.length < dto.level)
    tips.push({
      title: 'Check your board capacity',
      detail: `You reviewed ${dto.units.length} units at level ${dto.level}. Check for missed detections, then fill any available slots unless you are deliberately playing fewer units.`,
    });
  if (dto.hp <= 30)
    tips.push({
      title: 'Review your next fight before saving gold',
      detail: `At ${dto.hp} HP, inspect your frontline, items, and available upgrades. Consider spending if you are losing fights; this screenshot cannot establish your combat strength.`,
    });
  if (dto.stage <= 2)
    tips.push({
      title: 'Early board: 1-star units can be normal',
      detail: `At round ${dto.stage}-${dto.roundNumber}, ${oneStar} one-star units alone do not make this a weak composition. Look for natural upgrades and check that your usable items are equipped.`,
    });
  else if (oneStar)
    tips.push({
      title: 'Review upgrades in context',
      detail: `At round ${dto.stage}-${dto.roundNumber}, review your ${oneStar} one-star units, especially your main frontline and carry. A newly acquired high-cost unit may still be useful at one star; avoid rerolling only to remove this warning.`,
    });
  if (tips.length < 3)
    tips.push({
      title: 'Inspect positioning and items',
      detail:
        'Keep your intended damage dealers protected and check your main tank’s items. Champion roles, equipped items, augments, and opponents are not evaluated in this version.',
    });
  return {
    round: `${dto.stage}-${dto.roundNumber}`,
    tips: tips.slice(0, 3),
    basis:
      'V1 review prompts based on the fields you confirmed. These are heuristics, not a comp tier or win prediction.',
  };
}
