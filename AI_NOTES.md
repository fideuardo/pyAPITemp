# AI Notes — pyAPITemp / nxp_simtemp

## 1. Purpose
This document captures how AI assistance (ChatGPT/Codex) was used during development of the project. It supports traceability for RQ-DOC-01 and helps reviewers understand which artefacts originated from automated suggestions versus manual work.

## 2. AI-Assisted Activities
| Date | Topic | Outcome |
|------|-------|---------|
| 2025-04 | Cross-compilation support | Added Makefile targets (`modules_rpi`, `modules_rpi` helper variables) to ease Raspberry Pi builds. |
| 2025-04 | CLI enhancement | Implemented `--test` mode in `kernel/apitest/apitest.c`, including poll-based alert verification and state restoration. |
| 2025-04 | Packaging automation | Expanded `scripts/create_simtemp_rpi_package.sh` to include GUI files, installation scripts, permission setup, and uninstall logic. |
| 2025-04 | Self-test harness | Developed `kernel/scripts/run_selftest.sh`, adding overlay detection, module load/unload, stats logging, and recompile triggers. |
| 2025-04 | Helper scripts | Created `scripts/build.sh`, `scripts/run_demo.sh`, `scripts/lint.sh` to satisfy RQ-SCR-01 and streamline developer workflows. |
| 2025-04 | Documentation | Authored `DESIGN.md`, `TESTPLAN.md`, and this `AI_NOTES.md`; updated README to describe helper scripts. |

## 3. Interaction Summary
- **Environment**: All AI interactions happened via Codex CLI, with manual validation (builds, tests) performed directly on the developer's Ubuntu host and Raspberry Pi.
- **Validation**: AI-generated code/scripts were compiled and executed locally. Key tests (CLI `--test`, `run_selftest.sh`, packaging) produced logs captured in TESTPLAN evidence.
- **Review**: The developer reviewed each AI-generated change before applying it, ensuring compliance with project style and requirements.

## 4. Guidelines for Future AI Usage
1. **Keep control**: Treat AI suggestions as drafts. Review logic, security implications, and style before merging.
2. **Validate on-target**: For kernel modules and cross-compiled binaries, always run suggested changes on hardware that matches target deployment.
3. **Document outcomes**: Update this file (or release notes) whenever AI-generated content is adopted, especially for requirement-critical code.
4. **Respect licensing**: Ensure AI-generated code aligns with GPLv2 terms used by the kernel module.

## 5. Next Steps
- Capture the demo video (RQ-VID-01) and stress-test evidence (RQ-ROB-01).
- Continue logging significant AI interactions, particularly when adjusting driver core or user-space interfaces.
