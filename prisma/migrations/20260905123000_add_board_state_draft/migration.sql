-- CreateTable
CREATE TABLE "BoardStateDraft" (
    "id" SERIAL NOT NULL,
    "userId" INTEGER NOT NULL,
    "matchId" INTEGER,
    "roundId" INTEGER,
    "screenshotFilename" TEXT NOT NULL,
    "originalFilename" TEXT NOT NULL,
    "storagePath" TEXT NOT NULL,
    "status" TEXT NOT NULL DEFAULT 'uploaded',
    "boardState" JSONB,
    "errorMessage" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "BoardStateDraft_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "BoardStateDraft_userId_createdAt_idx" ON "BoardStateDraft"("userId", "createdAt");

-- CreateIndex
CREATE INDEX "BoardStateDraft_matchId_idx" ON "BoardStateDraft"("matchId");

-- CreateIndex
CREATE INDEX "BoardStateDraft_roundId_idx" ON "BoardStateDraft"("roundId");

-- AddForeignKey
ALTER TABLE "BoardStateDraft" ADD CONSTRAINT "BoardStateDraft_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "BoardStateDraft" ADD CONSTRAINT "BoardStateDraft_matchId_fkey" FOREIGN KEY ("matchId") REFERENCES "Match"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "BoardStateDraft" ADD CONSTRAINT "BoardStateDraft_roundId_fkey" FOREIGN KEY ("roundId") REFERENCES "Round"("id") ON DELETE SET NULL ON UPDATE CASCADE;
