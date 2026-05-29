# Codex-primary symmetry implementation plan (merged)

**Merged 2026-05-28 into [`2026-05-16-agent-fungibility-refactor-plan.md`](2026-05-16-agent-fungibility-refactor-plan.md).**

This standalone plan's three steps (a Codex-primary runbook, an `AGENTS.md` Codex-primary section, and `bootstrap --primary codex`) were the parent plan's Phases 3 and 4 plus a runbook. They are now concretized there, together with the gaps the symmetry review surfaced:

- Phase 6 (reviewer-agnostic health-check) reclassified as symmetry-blocking and highest priority, because a Codex-tuned health-check is blind to the silent Claude-reviewer hang that motivated the Phase 2 rework.
- Phase 1 (SKILL.md narrative) reclassified as symmetry-blocking, since a Codex-primary session reads SKILL.md first and sees Codex-as-reviewer framing.
- Phase 2.5 (a `dispatch-review` reviewer-selection primitive) and Phase 7.5 (an automated live-dispatch smoke) added.
- The degradation list reframed as function-mapping (banner via Codex first-response, destructive-command gating via Codex approval policy) rather than flat loss.

See the parent file for the current plan, the symmetry priority tiers, and status. This file is kept as a pointer rather than deleted so existing references resolve; it is safe to delete once nothing else links here.
