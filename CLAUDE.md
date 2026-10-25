# Sports Hub (Python)

Python rebuild of the weekly Sports Hub refresh. The original Cowork skill
lives at ../../Scheduled/sports-hub-refresh/SKILL.md; past HTML snapshots
are in ../../Outputs/Sports Hub/.

## Agent skills

### Issue tracker

Issues and specs live as local markdown files under `.scratch/<feature>/`. See `docs/agents/issue-tracker.md`.

### Triage labels

Default five-role vocabulary (needs-triage, needs-info, ready-for-agent, ready-for-human, wontfix), recorded as `Status:` lines. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: one `CONTEXT.md` + `docs/adr/` at the project root, created as decisions get made. See `docs/agents/domain.md`.
