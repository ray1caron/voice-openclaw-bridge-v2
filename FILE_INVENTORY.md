# Voice Bridge v2 - File Inventory

**Total Files:** 199 (including .pyc cache files)
**Source Files Only:** ~130 (excluding .pyc cache)

---

## Root Directory (1-100)

**Key Documentation:**
1. BUG_TRACKER.md
2. COMMERCIAL_READINESS_ASSESSMENT.md
17. IMPLEMENTATION_PLAN.md
18. INSTALL.md
26. README.md
90. STATUS.md
92. SYSTEM_TEST_PLAN.md
93. TEST_ENVIRONMENT.md
196. USER_GUIDE.md

**Phase Documentation:**
8. DAY_1_STT_COMPLETE.md
9. DAY_2_TTS_COMPLETE.md
10. DAY_3_WAKE_WORD_COMPLETE.md
11. DAY_4_ORCHESTRATOR_COMPLETE.md

**Other Docs:**
19. MVP.md
20. PROJECT.md
21. PROJECT_STATUS_2026-02-26.md
24. QUICKSTART.md
25. QUICK_STATUS.md
91. SYSTEM_DESIGN_REVIEW_2026-02-26.md
198. voice-assistant-plan-v2.md
199. VOICE_BRIDGE_V2_IMPLEMENTATION_PLAN_V2.md

**Config Files:**
3. config/config.yaml.template
4. config/default.yaml
5. config/.env.template
6. config.example.yaml
22. pyproject.toml
16. .github/workflows/ci.yml

**Root Scripts:**
27. run_tests.py
28. run_tests.sh
31. spike_openclaw.py
89. start_bridge.sh
94. test_import.py
95. test_installation.sh
195. update_to_real_audio.py
197. validate_imports.py

**Configuration:**
15. CONTRIBUTING.md
14. GITHUB_VERIFICATION_CHECKLIST.md
23. PYTHON_312_TESTING_REQUIREMENTS.md

---

## Source Code (32-86)

**Audio Module (4 .py files):**
32. src/audio/barge_in.py
41. src/audio/stt_worker.py
42. src/audio/tts_worker.py
43. src/audio/wake_word.py
34. src/audio/interrupt_filter.py

**Bridge Module (25 .py files):**
44. src/bridge/audio_buffer.py
45. src/bridge/audio_discovery.py
46. src/bridge/audio_pipeline.py
47. src/bridge/barge_in_integration.py
48. src/bridge/bug_cli.py
49. src/bridge/bug_tracker.py
50. src/bridge/config.py
51. src/bridge/context_window.py
52. src/bridge/conversation_store.py
53. src/bridge/history_manager.py
55. src/bridge/main.py
56. src/bridge/middleware_context_integration.py
57. src/bridge/middleware_integration.py
58. src/bridge/openclaw_middleware.py
80. src/bridge/response_filter.py
81. src/bridge/session_manager.py
82. src/bridge/session_recovery.py
83. src/bridge/tool_chain_manager.py
84. src/bridge/vad.py
85. src/bridge/voice_orchestrator.py
86. src/bridge/websocket_client.py

**Docs in src/:**
12. docs/openclaw-api-notes.md
13. docs/OPENCLAW_GATEWAY_FINDINGS.md

---

## Test Fixtures (97-113)

**Audio Test Files (16 files):**
97. tests/fixtures/audio/README.md
98-99. silence_2s.flac/.wav
102-103. speech_like_2s.flac/.wav (main test file)
104-105. speech_long_5s.flac/.wav
108-109. speech_short_1s.flac/.wav
106-107. speech_low_volume.flac/.wav
100-101. speech_high_volume.flac/.wav
110-111. speech_stereo_2s.flac/.wav
112-113. tone_440hz_2s.flac/.wav

---

## Integration Tests (114-142)

**Test Results:**
115. BUG_TRACKER_TEST_RESULTS.md
146. test_plan_bug_tracker.md
147. TEST_PLAN.md

**Integration Tests (11 .py files):**
131. test_audio_integration.py
132. test_barge_in_integration.py
133. test_barge_in.py
134. test_bug_tracker_github.py
135. test_config_integration.py
136. test_e2e_workflow.py
137. test_performance.py
138. test_response_filter_integration.py
139. test_session_integration.py
140. test_session_recovery_integration.py
141. test_voice_e2e.py (E2E tests - 5/8 passing)
142. test_websocket_integration.py

**Manual Tests:**
143. manual_test_bug_tracker.py

---

## Unit Tests (148-194)

**Setup:**
96. tests/conftest.py
148. tests/unit/conftest.py

**Unit Tests (24 .py files):**
175. test_audio_buffer.py
176. test_audio_pipeline.py
177. test_barge_in.py
178. test_config.py
179. test_context_window.py
180. test_conversation_store.py
181. test_history_manager.py
182. test_middleware_context_integration.py
183. test_middleware_integration.py
184. test_openclaw_middleware.py
185. test_response_filter.py
186. test_session_manager.py
187. test_session_recovery.py
188. test_stt_worker.py
189. test_tool_chain_manager.py
190. test_tts_worker.py
191. test_vad.py
192. test_voice_orchestrator.py
193. test_wake_word.py
194. test_websocket_client.py

---

## Compiled Files (Excluded from Reference)

All **.pyc** files in:
- src/audio/__pycache__/ (6 files)
- src/bridge/__pycache__/ (20 files)
- tests/integration/__pycache__/ (14 files)
- tests/__pycache__/ (2 files)
- tests/unit/__pycache__/ (24 files)

**Total: 66 .pyc files** (auto-generated, not part of source code)

---

## Summary

**Key Files by Role:**

**Documentation:** 24 files
- Main docs: README, INSTALL, USER_GUIDE, STATUS
- Plans: IMPLEMENTATION_PLAN.md, SYSTEM_TEST_PLAN.md
- Assessments: COMMERCIAL_READINESS_ASSESSMENT.md

**Production Code:** 29 .py files
- src/audio/ (4 files)
- src/bridge/ (25 files)

**Tests:**
- Unit tests: 24 .py files (~400 tests)
- Integration tests: 11 .py files (~70+ tests)
- E2E tests: 1 .py file (8 tests, 5 passing)

**Fixtures:** 16 audio files (synthetic test audio)

**Configuration:** 5 config files + pyproject.toml

**Scripts:** 8 root scripts (test runners, installers)

---

**Generated:** 2026-02-28 11:50 PST
**File Count:** 199 total, 133 source files (excluding .pyc)