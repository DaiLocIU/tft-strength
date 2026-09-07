# Board Review V1

## User workflow

1. Upload an unobstructed desktop TFT screenshot containing the board and HUD.
2. Detect champions, star levels, positions, round, player level, gold, HP and streak.
3. Enlarge the screenshot and correct hexes and HUD fields. Empty HUD fields mean not detected, not zero.
4. Confirm the review and request a board guide. Selecting a game is optional for analysis.
5. Select a game to save. The saved draft retains original detections alongside corrected units and reviewed HUD values.

## Local services and deployment requirements

- Existing NestJS API, PostgreSQL database, Vite frontend and Python vision service.
- Existing four YOLO classifiers/detectors and board detector remain required.
- Install **Tesseract 5 and English language data** in the Python service's host/container; the executable must be on PATH. No Python OCR package is needed.
- Start the vision service from `vision-board-detector`: `.venv/bin/python scripts/board_state_api.py` (port 8095). Restart it after Python source changes.
- `pnpm start:dev` starts NestJS; `pnpm --prefix frontend dev` starts Vite.
- Existing BoardStateDraft JSON stores HUD predictions; no schema migration is added by this feature.
- The original screenshot must be available under the vision service's `data/raw` directory, as in the existing upload flow. Uploads and the vision service must share that storage in deployment.

## HUD extraction

`src/board_detector/hud_ocr.py` uses bounded full-screenshot regions and Tesseract TSV text/confidence. There are initial profiles for a desktop game image (aspect ratio >= 1.7) and a taller browser/video capture. Regions were checked against local screenshots, not a held-out benchmark. Other resolutions, UI scaling, cropped videos, overlays and alternate layouts may need manual entry.

Level extraction checks the digit-first HUD region and an English “Lvl.” fallback. Streak reads the counter beside gold and uses the adjacent orange/blue icon to infer wins/losses; an unclear icon leaves the field blank. Positive values mean wins, negative values mean losses. The reroll counter is not a streak. This color heuristic still needs validation across HUD skins and layouts.

Round syntax and numeric ranges are checked. Ambiguous or low-confidence OCR results are blank. HP recognition uses the expanded local-player badge region; scouting and other HUD layouts require special care. Every prediction requires human confirmation, including high-confidence results. OCR confidence is not a calibrated probability of correctness. An unavailable OCR executable or a field failure does not discard champion detection.

Tesseract documentation: https://tesseract-ocr.github.io/tessdoc/Command-Line-Usage.html

## Guide scope

`POST /board-state-intake/drafts/:id/analyze` is authenticated, ownership-checked and accepts validated reviewed units and player state. It does not require a match ID. The rules prompt users to check unused board capacity, review upgrades in stage context and inspect survival at <=30 HP. These are transparent initial heuristics, not measured power scores, meta rankings or win predictions. Items, augments, champion roles and opponents are not inferred by the guide.

## Verification

- `python -m unittest discover -s tests -p 'test_hud_ocr.py'`
- `pnpm test -- --runInBand src/board-state-intake/board-guide.spec.ts src/board-state-intake/save-board-round.service.spec.ts`
- `pnpm --prefix frontend build` and `pnpm build`

Next evaluation: label an independent set of full screenshots with round, level, gold, local-player HP and signed streak. Report per-field exact-match accuracy, abstention/coverage, correction rate and latency. Keep those images out of ROI tuning. Do not quote the development smoke checks as model accuracy on a CV.
