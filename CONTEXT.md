# TFT Team Strength

Domain language for TFT match tracking, round progression, economy monitoring, and team strength analytics.

## Language

**Match Timeline**:
The aggregate tracking a complete TFT match game from start to finish, including its placement, comp label, game version, and sequential round snapshots.
_Avoid_: MatchSession, GameRecord, MatchLog

**Round Snapshot**:
A point-in-time capture of a player's board state during a specific TFT stage-round (e.g. 2-1, 3-5), recording HP, gold, level, and streak.
_Avoid_: GameRound, Turn, RoundState

**Board State**:
The inferred set of occupied hexes and champion identities on a player's TFT board at one moment, including uncertain or missing detections that need user review.
_Avoid_: BoardResult, DetectionOutput, VisionPayload

**Board State Intake**:
The workflow that accepts a raw screenshot, creates a reviewable Board State draft, runs vision inference, records user corrections, and applies the reviewed result to a Round Snapshot.
_Avoid_: VisionUpload, ScreenshotService, DetectionController

**Board Geometry**:
The projected hex grid of a cropped TFT board, including each hex center, row/column identity, draw polygon, and crop area used for occupancy detection.
_Avoid_: HexHelpers, GridMath, BoardCoordinates

**Vision Model Adapter**:
The thin boundary that turns raw YOLO detection or classification results into project prediction records such as board boxes, champion boxes, hex occupancy, and champion identity candidates.
_Avoid_: YoloUtils, ModelHelpers, PredictionParsing

**Dataset Workflow**:
The complete, target-specific lifecycle that prepares annotated TFT screenshots for a vision model, from validation or labeling through splitting and review.
_Avoid_: DataScripts, TrainingPrep, DatasetHelpers

**Champion-to-Hex Evidence**:
The inferred relationship between a detected champion box and the single board hex it occupies, including the champion foot point, occupied hex candidates under large boxes, identity prediction, and suppressed extra occupancy signals.
_Avoid_: ChampionMapping, BoxToHexUtils, AssignmentHelpers

**Stage-Round Identifier**:
The standard TFT designation combining stage number and round number within that stage (e.g. '2-3') or its numeric internal ID.
_Avoid_: RoundName, TurnIndex

**Match Timeline Store**:
The persistence seam decoupling match and round state operations from the database engine, with production Postgres and test in-memory adapters.
_Avoid_: DatabaseService, MatchDao, PrismaWrapper

**Auth Configuration**:
The centralized configuration for authentication parameters (secrets, token expiration durations, OAuth client identifiers) with environment-aware fail-fast validation on startup.
_Avoid_: EnvService, ConfigMap, AuthOptions

**User Store**:
The persistence seam decoupling user identity and session token operations from the database engine, with production Postgres and test in-memory adapters.
_Avoid_: UserRepository, UserDao, PrismaUserWrapper

**Match Evaluator**:
The pure domain module that evaluates team strength across all round snapshots of a match, computing per-round breakdowns and aggregate match strength metrics.
_Avoid_: StrengthCalculatorService, StrengthHelper, MatchScorer
