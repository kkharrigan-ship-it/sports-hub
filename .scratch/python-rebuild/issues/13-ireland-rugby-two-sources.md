# 13: Ireland rugby from two sources

**What to build:** Ireland Rugby appears on the Hub with two kinds of matches in one list:
- the November 2026 tests, from the Season file, since there is no structured source for them;
- the 2027 Six Nations kickoffs, from the official fixtures page.

This is the first Sport with more than one source, so the Refresh learns to combine them. If one source fails, the other still shows, with an Alert.

**Blocked by:** 07 (Season file, starting with WEC and SailGP)

**Status:** ready-for-agent

- [x] `ireland-rugby` is in the Sports config (category `rugby`) with Watch options from the 2026-27 watch guide (RugbyPass TV free for November; Peacock `have` for the Six Nations), and is flagged rights-unconfirmed for 2027.
- [x] A Sport can list several sources. Its Events are the combined list, in time order.
- [x] Only Ireland's Six Nations matches are included, each named "Ireland v X" or "X v Ireland" with its venue and UTC kickoff.
- [x] The November tests are in the Season file with source links.
- [x] If one of a Sport's sources fails, Events from the other still appear, the failed part falls back to its last-good Events, and an error Alert names the failed source.
- [x] Tests use a saved real Six Nations fixtures page and the Season file, go through the Refresh entry point, and need no network.
