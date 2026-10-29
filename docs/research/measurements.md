# Measurements (design brief §7)

Every number here is **measured** unless it's marked as an estimate.

## Python Hub on GitHub Actions

| Date | Run | Trigger | Result | Build job | Whole run | Actions cost |
|---|---|---|---|---|---|---|
| 2026-10-25 | [40212287535](https://github.com/kkharrigan-ship-it/sports-hub/actions/runs/40212287535) | manual (wizard) | failed in setup: `astral-sh/setup-uv@v10` doesn't exist; fixed by pinning `v10.3.2`. The failure email arrived as designed. | 2 s | 18 s | $0 (public repo) |
| 2026-10-25 | [40212592965](https://github.com/kkharrigan-ship-it/sports-hub/actions/runs/40212592965) | manual | ✅ all 4 jobs; Hub live with 19 Sports; last-good state committed | 1 m 3 s | about 1 m 30 s | $0 (public repo) |
| 2026-10-25 | [40214138052](https://github.com/kkharrigan-ship-it/sports-hub/actions/runs/40214138052) | manual, `break-test` branch | ❌ as intended: a Season-file entry with no date was caught by the tests; publish and save were skipped; the finish job sent the failure email; the live Hub was unchanged | about 1 m (failed at Test) | about 1 m 20 s | $0 |
| 2026-10-26 | [40366339384](https://github.com/kkharrigan-ship-it/sports-hub/actions/runs/40366339384) | **scheduled** (Mon) | ✅ all 4 jobs; first Monday Notification sent to Katie and Jason; `notified_on` saved. GitHub started it at 17:11 UTC rather than the 11:00 UTC it was scheduled for, because scheduled runs can be delayed when GitHub is busy | see run | see run | $0 |

Scheduled runs: Mondays and Thursdays at 11:00 UTC (GitHub may start them late).

## Cowork version (baseline)

Not measured yet. See ticket 34.
