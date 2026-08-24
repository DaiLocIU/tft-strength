# TFT Team Strength

Domain language for TFT match tracking, round progression, economy monitoring, and team strength analytics.

## Language

**Match Timeline**:
The aggregate tracking a complete TFT match game from start to finish, including its placement, comp label, game version, and sequential round snapshots.
_Avoid_: MatchSession, GameRecord, MatchLog

**Round Snapshot**:
A point-in-time capture of a player's board state during a specific TFT stage-round (e.g. 2-1, 3-5), recording HP, gold, level, and streak.
_Avoid_: GameRound, Turn, RoundState

**Stage-Round Identifier**:
The standard TFT designation combining stage number and round number within that stage (e.g. '2-3') or its numeric internal ID.
_Avoid_: RoundName, TurnIndex

**Match Timeline Store**:
The persistence seam decoupling match and round state operations from the database engine, with production Postgres and test in-memory adapters.
_Avoid_: DatabaseService, MatchDao, PrismaWrapper
