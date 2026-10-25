# Measurements (design brief §7)

Every number here is **measured** unless it's marked as an estimate.

## Python Hub on GitHub Actions

| Date | Run | Trigger | Result | Build job | Whole run | Actions cost |
|---|---|---|---|---|---|---|
| 2026-10-25 | [40212287535](https://github.com/kkharrigan-ship-it/sports-hub/actions/runs/40212287535) | manual (wizard) | failed in setup: `astral-sh/setup-uv@v10` doesn't exist; fixed by pinning `v10.3.2`. The failure email arrived as designed. | 2 s | 18 s | $0 (public repo) |
| 2026-10-25 | [40212592965](https://github.com/kkharrigan-ship-it/sports-hub/actions/runs/40212592965) | manual | ✅ all 4 jobs; Hub live with 19 Sports; last-good state committed | 1 m 3 s | about 1 m 30 s | $0 (public repo) |
| 2026-10-25 | [40214138052](https://github.com/kkharrigan-ship-it/sports-hub/actions/runs/40214138052) | manual, `break-test` branch | ❌ as intended: a Season-file entry with no date was caught by the tests; publish and save were skipped; the finish job sent the failure email; the live Hub was unchanged | about 1 m (failed at Test) | about 1 m 20 s | $0 |

The scheduled runs (Mondays and Thursdays at 11:00 UTC) start on 2026-10-26.

## Cowork version (baseline)

Not measured yet. See ticket 34.
