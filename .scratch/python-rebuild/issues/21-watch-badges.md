# 21: Watch badges

**What to build:** Each Sport (and each Event, compactly) shows how to watch it, as coloured badges in the old Hub's style:
- **Order:** owned (`have`) first, then free, then paid (`consider`, with its price).
- **VPN options** appear only when the Sport has no owned or free legal option, clearly tagged as VPN.
- **Recheck badge:** Sports flagged as rights-unconfirmed show "Recheck before the season".
- **Legend:** a small key explains the badge colours.

**Blocked by:** 16 (Hub skeleton)

**Status:** ready-for-agent

- [x] The badge order follows the rule above for every Sport; a Sport with only VPN and paid options shows VPN after paid, tagged.
- [x] Notes (e.g. "Saturday playoffs only") are shown with their badge, and paid options show their price.
- [x] Every rights-unconfirmed Sport has the recheck badge; no other Sport does.
- [x] The legend matches the four Watch option types.
- [x] It is checked in a browser preview with a fixed `data.json` that covers a Sport with VPN-only free options.
