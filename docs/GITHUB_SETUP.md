# Upload to GitHub and publish container updates

The ZIP is now a repository-root archive: Dockerfile, run.py, app/ and .github/ are at the archive root. Extract into a new folder. Upload its contents, not a surrounding folder. No real settings/credentials are included.

1. Create the public GitHub repository **Magic-Mirror-UNRAID**. Do not upload your server's appdata or personal settings CSV.
2. Upload all project contents, including `.github/workflows/publish.yml`, `.gitignore` and `.dockerignore`. Some file pickers hide dot-prefixed folders: verify the workflow exists in GitHub afterward. If necessary use Add file → Create new file and paste the supplied workflow into that exact path.
3. Open Actions → Test and publish Docker image → Run workflow on your default branch. Tests run first, then GitHub builds and publishes to `ghcr.io/YOUR-LOWERCASE-USERNAME/magic-mirror-unraid` using the built-in GITHUB_TOKEN. No manually entered registry password is needed for this workflow.
4. Under your profile/organization's Packages, open the new container package → Package settings and make it Public if Unraid should pull without a login. Public repository visibility alone does not guarantee public package visibility.
5. In Unraid, edit the container Repository to `ghcr.io/YOUR-LOWERCASE-USERNAME/magic-mirror-unraid:latest`. Preserve port 8765 and your existing appdata → /config mapping. Apply and get the new pairing token from Logs.
6. For future updates, commit the changed code then publish a GitHub release with a version tag. The workflow tests/builds/pushes `latest`, the full commit SHA tag and the release tag. In Unraid check for updates and update the container. No local image rebuild is required.

The Actions summary records the image SHA-256 content digest. Docker checks content integrity when pulling; the workflow does not provide publisher signature verification. Pin the repository to `ghcr.io/YOUR-LOWERCASE-USERNAME/magic-mirror-unraid@sha256:...` if you want one exact image; a pinned digest will not follow latest updates. Retain old commit/release tags for rollback.

The workflow builds the runner's default Linux/amd64 image, suitable for typical x86 Unraid servers. It is not a multi-architecture build. First publication may require repository/organization Actions/Packages permissions to be enabled. No image has been published by this ZIP itself. GitHub will perform the first actual container build; Docker is unavailable in the authoring environment.

For a new Unraid install, use unraid/my-magic-mirror-ghcr.xml after replacing YOUR-LOWERCASE-USERNAME with your GitHub username in lowercase. For your existing container, edit only its Repository field to the published image URL and preserve the settings mapping. The local-build template remains available separately.
