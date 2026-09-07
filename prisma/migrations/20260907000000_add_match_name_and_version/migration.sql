ALTER TABLE "Match"
  ADD COLUMN "name" TEXT;

ALTER TABLE "Match"
  ALTER COLUMN "version" TYPE INTEGER
    USING COALESCE(NULLIF(split_part("version", '.', 1), ''), '18')::INTEGER,
  ALTER COLUMN "version" SET DEFAULT 18,
  ALTER COLUMN "version" SET NOT NULL;

ALTER TABLE "Match"
  ALTER COLUMN "placement" DROP NOT NULL;
