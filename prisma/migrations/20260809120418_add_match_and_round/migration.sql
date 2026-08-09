-- CreateTable
CREATE TABLE "Match" (
    "id" SERIAL NOT NULL,
    "placement" INTEGER NOT NULL,
    "playedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "comp" TEXT,

    CONSTRAINT "Match_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Round" (
    "id" SERIAL NOT NULL,
    "matchId" INTEGER NOT NULL,
    "stage" INTEGER NOT NULL,
    "roundNumber" INTEGER NOT NULL,
    "gold" INTEGER NOT NULL,
    "hp" INTEGER NOT NULL,
    "level" INTEGER NOT NULL,
    "streak" INTEGER NOT NULL,

    CONSTRAINT "Round_pkey" PRIMARY KEY ("id")
);

-- AddForeignKey
ALTER TABLE "Round" ADD CONSTRAINT "Round_matchId_fkey" FOREIGN KEY ("matchId") REFERENCES "Match"("id") ON DELETE CASCADE ON UPDATE CASCADE;
