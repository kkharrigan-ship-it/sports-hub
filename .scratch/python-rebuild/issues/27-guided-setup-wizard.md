# 27: Guided setup wizard

**What to build:** A step-by-step walkthrough Katie runs in her terminal that takes her from "nothing on GitHub" to "first run started". It is built with the `wizard` skill. Each step explains in plain words what it does and why, does what it safely can by itself (using the `gh` command-line tool she already has), and checks that the step worked before moving on. Steps:
1. sign in to GitHub with `gh`
2. create the public `sports-hub` repo and push the project
3. turn on GitHub Pages, with GitHub Actions as its source
4. turn on Google 2-Step Verification (if needed) and create a Gmail app password
5. add the secrets: typed into the wizard's hidden prompt and passed straight to GitHub, never stored in a file
6. start the first run and open the live Hub link

**Blocked by:** 26 (The GitHub workflow)

**Status:** ready-for-agent

- [x] The wizard can be stopped and re-run safely. It skips steps that are already done (e.g. the repo exists, Pages is on, a secret is set).
- [x] Passwords and the app password are never shown on screen, written to files, put in shell history or sent to chat. The wizard reads them with a hidden prompt and pipes them straight to `gh secret set`.
- [x] Steps that only Katie can do in a browser (Google account settings) open the right page and wait for her to confirm, with a short description of what to click.
- [x] Every step that changes something outside her Mac (creating the repo, setting secrets, starting a run) says what it's about to do and asks before doing it.
- [x] At the end it prints the live Hub link and the Actions page link.
- [ ] It is tried end to end with Katie in a session where I'm there to help.

## Comments

**2026-10-24 (implementation):** Added a privacy stage before going public:
- It switches the commit author to Katie's GitHub noreply address.
- It offers to publish one fresh commit, keeping the full history in a local-only `pre-publish-history` branch. The earlier commits carried the Mac's name and old FIS test data with organisers' contact details (since removed from the saved feeds).

Checked statically: `bash -n` passes, and the secret names match the workflow. shellcheck isn't installed. The end-to-end run still waits for Katie.
