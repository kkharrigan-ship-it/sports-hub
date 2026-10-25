# 23: ESPN+ reminder for Grand Slams

**What to build:** Seven days before each Grand Slam of Curling event, using the Season file's slam tag, the Hub shows a banner reminding Katie to switch ESPN+ on for that month. It disappears once the Slam has ended.

**Blocked by:** 16 (Hub skeleton)

**Status:** ready-for-agent

- [x] `data.json` includes the upcoming Slam dates, so the page doesn't need to know curling's rules.
- [x] The banner shows from 7 days before a Slam starts until it ends, naming the Slam and its dates. It can be dismissed for that Slam on that device.
- [x] Back-to-back Slams don't stack banners; the nearest one is shown.
- [x] The Slam dates in `data.json` are tested through the Refresh entry point; the banner is checked in a browser preview with a known clock.
