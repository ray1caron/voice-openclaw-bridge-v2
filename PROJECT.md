# PROJECT.md - Voice-OpenClaw Bridge v2

**Quick Reference for Development Sessions**

---

## Repository
🔗 **https://github.com/ray1caron/voice-openclaw-bridge-v2**

## Current Status
- ✅ Repository created and scaffolded
- ✅ Labels configured (priority, component)
- ✅ 8 issues created in Backlog
- ✅ Project board: "Voice Bridge v2 Development"
- ✅ Sprint 1 Complete (4/4 issues merged)
- ✅ Sprint 2 Complete (2/2 issues in PR #19)
- ✅ Issue #17 (Middleware) - COMPLETE (PR #19)
- ✅ Issue #18 (Tool Chain) - COMPLETE (PR #19)

## GitHub Workflow (IMPORTANT)

### Before Adding New Issues
1. Check existing issues: https://github.com/ray1caron/voice-openclaw-bridge-v2/issues
2. Check project board: https://github.com/ray1caron/voice-openclaw-bridge-v2/projects
3. Reference issue numbers in discussions
4. Create new issues via API (token in ~/.github_token)

### Creating Issues
```bash
export GITHUB_TOKEN=$(cat ~/.github_token)
curl -s -X POST -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  https://github.com/ray1caron/voice-openclaw-bridge-v2/issues \
  -d '{"title":"[TASK] Task Name","body":"Description...","labels":["priority::P0","component::bridge"]}'
```

### Updating Project Board
- Move issues between columns as work progresses
- Add sprint labels when starting work
- Mark as Done when complete

## Sprint Structure

| Sprint | Focus | Issues | Status |
|--------|-------|--------|--------|
| Sprint 1 | Foundation | #10, #1, #2, #3 | ✅ **COMPLETE** (4/4) |
| Sprint 2 | Tool Integration | #17, #18 | ✅ **COMPLETE** (2/2) |
| Sprint 3 | Memory | #7 | 📋 **PENDING** |
| Sprint 4 | Polish | #8 | 📋 **PENDING** |

**Sprint 1 Progress:** 100% complete (4/4 issues done) ✅  
**Sprint 2 Progress:** 100% complete (2/2 issues done) ✅

## Label System

**Priority:**
- `priority::P0` (Red) - Critical path blocking
- `priority::P1` (Orange) - Important feature  
- `priority::P2` (Green) - Nice to have

**Component:**
- `component::bridge` - WebSocket, filtering, orchestration
- `component::audio` - Audio I/O, VAD, barge-in
- `component::openclaw` - OpenClaw integration, middleware
- `component::stt` - Speech-to-text
- `component::tts` - Text-to-speech
- `component::wake` - Wake word detection

## Architecture

```
Voice Input → [Audio Pipeline] → STT → WebSocket → OpenClaw
                ↑                                    ↓
           Wake Word                        Response Filter
           Detection                               ↓
                ↑                            [TTS Text]
                ↓                                   ↓
         Barge-in Control              [Audio Pipeline] → Speaker
```

**Key Innovation:** Audio Pipeline bridges hardware and processing layers with VAD and barge-in.

## Local Development

**Workspace:** `/home/hal/.openclaw/workspace/voice-bridge-v2/`
**Token:** `~/.github_token`
**Docs:**
- `voice-assistant-plan-v2.md` - Architecture specification
- `PROJECT_SUMMARY.md` - Complete setup summary
- `GITHUB_SETUP.md` - GitHub configuration guide

## Session Startup

**On new sessions:**
1. Read TOOLS.md for GitHub token location
2. Read MEMORY.md for project context
3. Check GitHub repo for current sprint status
4. Reference existing issues before creating new ones
5. Update project board as work progresses

---

**Last Updated:** 2026-02-22  
**Current Status:** Sprint 2 Complete (2/2 issues) ✅  
**Next Actions:** Review PR #19, prepare for Sprint 3 planning  
**Status:** Ready for review 🚀