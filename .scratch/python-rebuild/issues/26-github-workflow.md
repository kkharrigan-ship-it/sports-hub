# 26: The GitHub workflow

**What to build:** A scheduled GitHub Actions workflow that runs the Refresh on **Mondays and Thursdays at 11:00 UTC** (6am in Memphis in summer, 5am in winter), with a manual "Run workflow" button. Each run:
1. installs the project with uv on Python 3.12
2. runs the tests
3. runs the Refresh with alert email enabled
4. commits the updated last-good state back to the repo
5. publishes the Hub folder to GitHub Pages

If any step fails, including before Python starts, a final step still sends Katie the alert email (or GitHub's own failure notification as a backstop).

**Blocked by:** 25 (Failure-alert email)

**Status:** ready-for-agent

- [ ] The workflow runs on the Monday/Thursday schedule and can also be run by hand. *(Written; proven live in ticket 28.)*
- [ ] A failing test stops the run before anything is published, and Katie is alerted. *(Written; proven live in ticket 28.)*
- [x] Only the Hub folder (page, data.json, feeds) is published to Pages; nothing else from the repo is.
- [x] The last-good state is committed back with a clear bot commit message, and only when it changed. Runs never commit anything else.
- [x] Secrets are passed only as environment variables to the steps that need them, and the workflow has the minimum permissions it needs (contents write for the state commit, pages and id-token for publishing).
- [ ] Two runs can't overlap. A second run waits for the first. *(Written; proven live in ticket 28.)*
- [x] The workflow file is checked locally for syntax (parsed as YAML; action versions checked against each action's latest release: checkout v7, setup-uv v10, configure-pages v6, upload-pages-artifact v5, deploy-pages v5). No workflow linter is installed, so the real check is ticket 28.
- [x] The README explains the schedule, how to run it by hand, and where to see past runs.

## Comments

**2026-10-24 (review fixes):** The workflow is now four jobs with least-privilege permissions: build (read-only), publish (Pages), save (contents write) and finish. The Refresh's exit code (0 built, 1 stopped and emailed, 2 stopped and not emailed, 3 built but the Alert email unsent) decides what runs next. So a failed Alert email no longer blocks publishing, and the finish job sends at most one email, worded to match what happened. The Hub link is built from `GITHUB_REPOSITORY`, which scheduled runs always have.
