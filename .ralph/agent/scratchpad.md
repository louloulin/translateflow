## Fresh Iteration - Docker Build Recovery Plan

**Timestamp:** 2025-02-28 16:25 UTC+8

**Objective:** Build multi-platform Docker image (ARM64/AMD64) and start with docker-compose

---

### Current Status Analysis

**Existing State:**
- `translateflow:syntax-check` image exists (576MB, built 3 hours ago)
- Container `translateflow-app` is restarting (exit code 0, loop)
- buildx kit is running (46 minutes uptime)
- GitHub Actions workflow failed (wrong package names, now fixed)

**Key Problem from Previous Iteration:**
- mediapipe==0.10.31 doesn't support Linux ARM64
- uv.lock pins exact versions → frozen sync fails on ARM64
- Network timeouts aggravated the problem

**Root Cause:**
pyproject.toml line 17: `"mediapipe"` is unconditional → uv.lock saves ARM64-incompatible version

---

### Plan for This Iteration

**Strategy: Make mediapipe optional for ARM64 Linux**

**Why this approach:**
1. ✅ Fixes ARM64 build blocker (main issue)
2. ✅ Maintains functionality on x86_64 Linux (mediapipe still works)
3. ✅ Allows frozen lockfile builds (`uv sync --frozen`)
4. ✅ Enables multi-platform Docker images
5. ✅ No code changes required (only dependency constraint)

**Implementation:**
```toml
# In pyproject.toml dependencies
"mediapipe; sys_platform == 'linux' and platform_machine == 'x86_64'"
```

This uses PEP 508 environment markers to:
- Install mediapipe on: Linux x86_64 (AMD64)
- Skip mediapipe on: Linux ARM64, macOS, Windows

**Steps:**
1. Update pyproject.toml with platform constraint
2. Search for mediapipe usage in code
3. Regenerate uv.lock
4. Build single-platform AMD64 image first (verify fix)
5. (Future iteration) Build multi-platform with buildx

---

### Alternative Considered

**Cross-compile to AMD64 from ARM Mac:**
- ❌ Still requires fixing mediapipe dependency
- ❌ Doesn't solve ARM64 support
- ✅ Works with buildx `--platform linux/amd64`
- Decision: Fix dependency first, then cross-compile

---

### Risk Assessment

**Confidence Score: 85/100**

**Risks:**
- mediapipe might be optional (need to verify code usage)
- Other dependencies might have similar ARM64 issues

**Mitigation:**
- Search codebase for mediapipe imports
- If unused, can remove entirely
- If used, add graceful degradation

---

### Tasks to Execute

1. **[P1] Fix mediapipe dependency for ARM64 support** (THIS ITERATION)
   - Add platform marker to pyproject.toml
   - Search for mediapipe usage in code
   - Regenerate uv.lock
   - Test build

2. **[P1] Build AMD64 Docker image** (NEXT ITERATION)
   - `docker build -f Dockerfile.production -t translateflow:latest .`
   - Verify image builds successfully
   - Test container startup

3. **[P2] Build multi-platform images** (FUTURE)
   - Use buildx with --platform linux/amd64,linux/arm64
   - Push to GHCR or local registry

4. **[P2] Start services with docker-compose** (FUTURE)
   - Test docker-compose.production.yml
   - Verify health checks
   - Test API endpoints

---

### Verification Criteria

**Task 1 Complete When:**
- pyproject.toml has mediapipe platform marker
- uv.lock regenerated (check with `uv lock --check`)
- No mediapipe entries for ARM64 in lockfile
- Image builds without errors

**Task 2 Complete When:**
- Docker image builds successfully
- Container runs without restart loops
- Health check passes (`/api/system/status` returns 200)
- API is accessible on port 8000

---

### Notes

- Current container (translateflow-app) is in restart loop → will be replaced
- buildx kit can stay running (needed for multi-platform builds)
- Syntax check image is stale → rebuild after fix
