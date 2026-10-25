# 15: All 19 Sports check

**What to build:** Proof that Milestone 2 is complete. The Hub has exactly the 19 agreed Sports, each fully configured, and one live Refresh shows each one either in season with Events or off-season with a label.

**Blocked by:** 08, 09, 10, 11, 12, 13, 14

**Status:** ready-for-agent

- [x] A test confirms the Sports config contains exactly these ids: pwhl, curling-ca, curling-intl, speed-skating, short-track, swimming, diving, gymnastics, alpine, snowboard, freestyle, biathlon, f1, motogp, sailgp, wec, diamond-league, world-skate, ireland-rugby.
- [x] Every Sport has at least one Watch option. Every `consider` option has a price.
- [x] Every Sport has a "Returns" label for when it's off-season, held in the Season file or produced by its source.
- [x] The rights-unconfirmed flags match the watch guide's "recheck before each season opener" list.
- [x] One live Refresh runs without errors. Its output is summarised (each Sport's status and next Event) for Katie to spot-check against the official sites.
- [x] The full test suite passes offline, and type checks are clean.
