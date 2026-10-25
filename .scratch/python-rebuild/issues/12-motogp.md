# 12: MotoGP from Pulselive

**What to build:** MotoGP appears on the Hub with its upcoming Grand Prix weekends. The data comes from the Pulselive API that motogp.com uses. Where the API gives session times (Sprint, Race), each becomes its own Event. Otherwise the weekend is one Event across its dates.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [x] `motogp` is in the Sports config (category `motor`) with Watch options from the 2026-27 watch guide. FOX over the air is `free` for the Austin round; FS1/FS2 and FOX One are `consider` with a price.
- [x] Only MotoGP-class Grand Prix events are included, with tests and other classes excluded.
- [x] Event times are converted to UTC from the API's own offset or zone.
- [x] Once the season has ended and next year isn't published, MotoGP shows off-season with its label.
- [x] Tests use saved real Pulselive responses, go through the Refresh entry point, and need no network.
