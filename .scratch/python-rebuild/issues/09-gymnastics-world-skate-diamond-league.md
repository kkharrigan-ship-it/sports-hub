# 09: Gymnastics, World Skate and Diamond League in the Season file

**What to build:** Gymnastics (FIG), World Skate and the Wanda Diamond League appear on the Hub. Their 2026-27 dates are researched into the Season file with source links. Diamond League is likely between seasons until about April, so it shows off-season with a "Returns" label and note.

**Blocked by:** 07 (Season file, starting with WEC and SailGP)

**Status:** ready-for-agent

- [x] `gymnastics`, `world-skate` and `diamond-league` are in the Sports config with Watch options and rights flags from the 2026-27 watch guide.
- [x] The Season file lists their 2026-27 events that are already announced, each with a source link. Anything unannounced is left out rather than guessed.
- [x] A Sport with nothing inside the window but announced events later shows its next 6 Events. A Sport with nothing announced shows off-season with its label.
- [x] A Refresh test covers one in-season Sport and Diamond League off-season.

## Comments

**2026-10-24 (implementation):** This ticket contradicts itself. It expects Diamond League to show off-season, but also says "a Sport with nothing inside the window but announced events later shows its next 6 Events". The 2027 Diamond League calendar is already announced (Doha, 7 May), so the next-6 rule applies: Diamond League shows in-season with its first six 2027 meetings. World Skate, which has nothing announced after November, covers the off-season case in the tests instead.
