# Measurements (design brief §7)

Every number here is **measured** unless it's marked as an estimate.

## Python Hub on GitHub Actions

| Date | Run | Trigger | Result | Build job | Whole run | Actions cost |
|---|---|---|---|---|---|---|
| 2026-10-25 | [40212287535](https://github.com/kkharrigan-ship-it/sports-hub/actions/runs/40212287535) | manual (wizard) | failed in setup: `astral-sh/setup-uv@v10` doesn't exist; fixed by pinning `v10.3.2`. The failure email arrived as designed. | 2 s | 18 s | $0 (public repo) |
| 2026-10-25 | [40212592965](https://github.com/kkharrigan-ship-it/sports-hub/actions/runs/40212592965) | manual | ✅ all 4 jobs; Hub live with 19 Sports; last-good state committed | 1 m 3 s | about 1 m 30 s | $0 (public repo) |
| 2026-10-25 | [40214138052](https://github.com/kkharrigan-ship-it/sports-hub/actions/runs/40214138052) | manual, `break-test` branch | ❌ as intended: a Season-file entry with no date was caught by the tests; publish and save were skipped; the finish job sent the failure email; the live Hub was unchanged | about 1 m (failed at Test) | about 1 m 20 s | $0 |
| 2026-10-26 | [40366339384](https://github.com/kkharrigan-ship-it/sports-hub/actions/runs/40366339384) | **scheduled** (Mon) | ✅ all 4 jobs; first Monday Notification sent to Katie and Jason; `notified_on` saved. GitHub started it at 17:11 UTC rather than the 11:00 UTC it was scheduled for, because scheduled runs can be delayed when GitHub is busy | 1 m 14 s | 1 m 41 s | $0 |
| 2026-10-29 | [40885982704](https://github.com/kkharrigan-ship-it/sports-hub/actions/runs/40885982704) | **scheduled** (Thu) | ✅ all 4 jobs; the live Hub's Last-Modified header moved to 13:54 UTC. Started at 13:52 UTC, about 7 hours after its 07:00 UTC slot | 58 s | 1 m 45 s | $0 |

Scheduled runs: Mondays and Thursdays at 11:00 UTC until 2026-10-28, then 07:00 UTC, moved earlier to absorb GitHub's delays.

## Season-file check: Claude step

The "API equivalent" column is what Claude Code's run log reports. It isn't a charge: these runs use Katie's Pro allowance, and the Pro meter wasn't read before or after them, so their share of the allowance is **not yet known**.

| Date | Run | Trigger | Result | Claude turns | API equivalent |
|---|---|---|---|---|---|
| 2026-10-30 | [41114948567](https://github.com/kkharrigan-ship-it/sports-hub/actions/runs/41114948567) | manual | ✅ all 6 jobs; found the Canadian Seniors entry a day out | 16 | $0.24 |
| 2026-10-30 | [41163092931](https://github.com/kkharrigan-ship-it/sports-hub/actions/runs/41163092931) | manual, test branch | ✅ all 6 jobs; caught the planted Scotties date | 13 | $0.21 |

## Cowork version (baseline)

Not measured yet. See ticket 34.
