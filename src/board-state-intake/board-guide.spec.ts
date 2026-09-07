import { buildBoardGuide, AnalyzeBoardDto } from './board-guide';
const base: AnalyzeBoardDto = {
  stage: 2,
  roundNumber: 1,
  level: 1,
  hp: 100,
  gold: 10,
  streak: 0,
  units: [{ row: 3, column: 1, champion: 'Shen', stars: 1 }],
};
describe('round-aware board guide', () => {
  it('does not treat early one-star units as inherently weak', () => {
    const result = buildBoardGuide(base);
    expect(
      result.tips.some((t) => t.title.includes('1-star units can be normal')),
    ).toBe(true);
    expect(
      result.tips.some((t) => t.title === 'Review upgrades in context'),
    ).toBe(false);
  });
  it('makes later upgrade advice conditional rather than rating a comp', () => {
    expect(
      buildBoardGuide({ ...base, stage: 4 }).tips.find(
        (t) => t.title === 'Review upgrades in context',
      )?.detail,
    ).toContain('high-cost unit may still be useful');
  });
  it('flags potential missed detections before suggesting filling slots', () => {
    expect(buildBoardGuide({ ...base, level: 5 }).tips[0].detail).toContain(
      'missed detections',
    );
  });
  it('uses reviewed HP and limits output to three prompts', () => {
    const guide = buildBoardGuide({ ...base, hp: 20, level: 5 });
    expect(guide.tips).toHaveLength(3);
    expect(guide.tips.some((t) => t.detail.includes('20 HP'))).toBe(true);
  });
});
