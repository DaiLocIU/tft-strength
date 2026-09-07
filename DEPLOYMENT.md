# V1 deployment: Vercel + Supabase

## Target architecture and current progress

Target: Vue requests authorized upload information from NestJS, sends the original directly to private Supabase Storage using TUS, then asks NestJS to analyze the owned image. NestJS creates a short-lived signed download URL and sends small JSON to Python. Python downloads the image, runs YOLO + Tesseract, deletes temporary files, and returns JSON for NestJS to persist.

**Implemented in this step:** Python `POST /board-state` accepts `application/json` with `{"imageUrl":"https://..."}`. NestJS creates a fresh 60-second signed download URL for each detection of a Supabase-backed draft and forwards only that URL. Python needs no Supabase key, database access or user authentication. Its shared `VISION_SERVICE_KEY` restricts service calls; `VISION_IMAGE_ORIGINS` permits only your configured HTTPS storage origins. Redirects are rejected and download errors never expose the signed URL.

Python downloads original files up to 10,000,000 bytes, checks actual PNG/JPEG/WebP content and a 20-megapixel limit, and uses temporary directories that are cleaned on success or failure. The original is not recompressed before downloading or persisted back to Storage. Inference still makes its normal lossless RGB working copy and board crop.

**Next step:** replace Vue's multipart upload with signed direct resumable uploads and add upload initialization/completion endpoints in NestJS. The current browser upload still goes through NestJS and retains the 4 MB limit. Do not raise that limit until direct upload is implemented. No automatic screenshot recompression has been added. Saved-image review must also switch to a signed URL to avoid Vercel's response-size limit for large originals.

The existing local filesystem flow temporarily uses `/board-state-bytes` for compatibility. Supabase-backed detection always uses `/board-state` with a URL, even when the original upload passed through NestJS. Failed attempts retain their draft; retry signs a new URL instead of reusing an expired token. A 60-second URL can expire during a long cold start; retry creates a fresh one.

Supabase recommends TUS for files over 6 MB and supports signed upload tokens through the `x-signature` header. See [resumable upload documentation](https://supabase.com/docs/guides/storage/uploads/resumable-uploads).

## Configuration

Create a **private** Supabase Storage bucket named `board-screenshots`. Apply the existing Prisma migrations to Supabase PostgreSQL before starting the API. Keep all server secrets out of `VITE_*` variables.

NestJS environment:

```dotenv
SUPABASE_URL=https://YOUR_PROJECT.supabase.co
SUPABASE_SERVICE_ROLE_KEY=YOUR_SERVER_ONLY_SERVICE_ROLE_KEY
SUPABASE_STORAGE_BUCKET=board-screenshots
DATABASE_URL=YOUR_SUPABASE_POSTGRES_CONNECTION_STRING
VISION_BOARD_STATE_URL=https://YOUR_VISION_PROJECT.vercel.app
VISION_SERVICE_KEY=YOUR_RANDOM_SHARED_SECRET
HOST=0.0.0.0
```

Also configure the existing JWT and Google OAuth settings for production. If the Python deployment has Vercel Deployment Protection enabled, add its automation bypass token as `VISION_VERCEL_BYPASS_TOKEN` on NestJS. The service key is still required.

Python environment:

```dotenv
VISION_SERVICE_KEY=THE_SAME_RANDOM_SHARED_SECRET
VISION_IMAGE_ORIGINS=https://YOUR_PROJECT.supabase.co
```

The Dockerfile supplies `HOST=0.0.0.0` and `PORT=80`. Python exposes `GET /health`, URL inference at `POST /board-state`, and the temporary local compatibility endpoint `POST /board-state-bytes`. Training and correction routes are excluded. It processes one inference at a time per instance and responds 503 when busy so the UI can retry.

Vue environment:

```dotenv
VITE_API_URL=https://YOUR_NESTJS_PROJECT.vercel.app
```

For local development, start the inference service instead of the filename-based `board_state_api.py` server. Set matching `VISION_SERVICE_KEY` values in NestJS's `.env` and the shell running Python, then:

```bash
cd vision-board-detector
.venv/bin/python scripts/inference_api.py
```

It listens at `127.0.0.1:8095` by default. Without `SUPABASE_URL`, NestJS saves screenshots locally for development; on Vercel, missing Storage configuration fails explicitly.

## Deployment setup and remaining verification

Use separate Vercel projects for Vue (`frontend` root), NestJS (repository root), and Python (`vision-board-detector` root). The Python project contains `Dockerfile.vercel` and a restricted Docker build context containing inference code and model weights. CPU-only PyTorch avoids CUDA dependencies.

Set both API and CV function maximum durations to 300 seconds and enable Fluid Compute. NestJS allows 240 seconds for the CV request; Vue allows 290 seconds for the upload/detection request. Confirm these values in the deployed project settings.

This change prepares URL-based inference and the Python container definition; it does not provision or deploy cloud projects. Before publishing:

- Build/run the Linux container and measure cold-start time and peak memory against the Hobby limit of 2 GB. Docker was unavailable during local validation, so image size and Linux runtime compatibility remain unverified.
- Verify each compressed Docker layer is below the registry's 500 MB layer limit.
- Resolve the frontend's explicit macOS-only `@rollup/rollup-darwin-arm64` dependency for a Linux build, and verify NestJS's production build includes its Prisma client and TFT data assets.
- Test a production upload, saved-image review, failed-detection retry and Google login against the actual Supabase and Vercel projects.

## Free allowance

Target cost is $0 **within the free quotas**, not unlimited inference. Vercel Hobby lists 4 active CPU-hours, 360 GB-hours of memory, 1,000,000 invocations, and 10 GB Container Registry storage per month. Registry storage includes retained image versions/layers, not just the latest image. NestJS and Python both consume compute allowances.

Services can be reachable without leaving your Mac on, but container functions scale to zero when idle and have cold starts. Free quota exhaustion can interrupt availability; this is not a guaranteed 24/7 service level.

Sources checked September 7, 2026: [Vercel pricing](https://vercel.com/pricing), [Hobby plan](https://vercel.com/docs/plans/hobby), [function limits](https://vercel.com/docs/functions/limitations), [Docker deployments](https://vercel.com/kb/guide/does-vercel-support-docker-deployments), [registry limits](https://vercel.com/docs/container-registry/limits-and-pricing).
