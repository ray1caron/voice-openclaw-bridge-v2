# Phase 7 - Ready Commands (After Git Commit)

## Step 2: Create Deployment Bundle

```bash
cd /home/hal/.openclaw/workspace/voice-bridge-v2
./scripts/create_bundle.sh
```

## Step 3: Verify Bundle

```bash
cd /home/hal/.openclaw/workspace/voice-bridge-v2
ls -lh dist/voice-bridge-v2-1.0.0-beta.tar.gz
sha256sum dist/SHA256SUMS
```

## Step 4: Create Git Tag

```bash
cd /home/hal/.openclaw/workspace/voice-bridge-v2
git tag -a v1.0.0-beta -m "Release v1.0.0-beta - Production-ready beta"
```

## Step 5: Push to GitHub

```bash
git push origin cleanup-master
git push origin v1.0.0-beta
```

## Step 6: Create GitHub Release

Visit: https://github.com/ray1caron/voice-openclaw-bridge-v2/releases/new
- Tag: v1.0.0-beta
- Title: v1.0.0-beta - Production-ready
- Description: Copy from RELEASENOTES.md
- Upload: dist/voice-bridge-v2-1.0.0-beta.tar.gz

---

**After git commit completes, run these in order**