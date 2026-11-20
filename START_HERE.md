# Magic-Mirror-UNRAID — GitHub upload

1. Create the public repository **Magic-Mirror-UNRAID** in your GitHub account.
2. Extract this ZIP. Upload its **contents directly into the repository root**, including `.github`, `.gitignore`, and `.dockerignore`. Do not upload the ZIP itself or an enclosing directory.
3. Confirm `.github/workflows/publish.yml` exists in the repository. On GitHub open **Actions → Test and publish Docker image → Run workflow**.
4. After the workflow succeeds, make the new container **package Public** in package settings. This is separate from repository visibility.
5. In Unraid edit your existing container Repository to:

   `ghcr.io/YOUR-LOWERCASE-USERNAME/magic-mirror-unraid:latest`

   Replace the username placeholder. Preserve your existing `/config` mapping and port 8765. Apply, then read Logs for the current pairing token.
6. Future revisions: upload changed files and publish a GitHub release. After the workflow completes, update the Unraid container from its Docker page.

The workflow automatically derives your real username and repository name; no username edits are needed inside the workflow. The optional GHCR Unraid template does require replacing its username placeholder before installation.

No personal settings or real credentials are included. Do not upload your server appdata or exported settings. No container image has been published yet; GitHub will build it when you run the workflow.

See docs/GITHUB_SETUP.md for publishing, digest tags and rollback; PROGRAM.md for all components. README.md covers local use. Docker builds remain unverified in this authoring environment.
