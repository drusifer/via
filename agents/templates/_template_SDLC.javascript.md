# SDLC Language Profile: JavaScript / TypeScript

This is a language-specific insert for sections 1–4 and 10 of `_template_SDLC.md`, not a separate
SDLC document. Copy the relevant facts into the shared SDLC template and remove this insert. Use the
package manager and lockfile already present in the repository; never mix managers.

## Toolchain and setup facts

- **Runtime:** Node `{version}`; record the repository's runtime pin and `engines.node` source.
- **Manifest:** `package.json`; list the actual package manager and its single committed lockfile.
- **Environment:** `node_modules/` (normally ignored).
- **Clean install:** `{manager-specific frozen install command}`. Examples: `npm ci`,
  `pnpm install --frozen-lockfile`, or `yarn install --immutable`.
- **Local commands:** invoke project scripts from Makefile targets; record exact existing targets
  and script names in the shared SDLC. Do not invent target names.
- **Dependencies:** document the selected manager's add/remove commands and commit `package.json`
  with its lockfile. Avoid global installs and hand-editing lockfiles.
- **Conformance:** verify the clean install leaves the lockfile unchanged, exactly one lockfile is
  tracked, and runtime pins agree.

<!-- RUBRIC-START -->
## Check — SDLC-JS

- [ ] **PASS** — The profile uses one manager, its matching lockfile, and that manager's exact clean-install command.
- [ ] **PASS** — Runtime pin, manifest scripts, Makefile targets, dependency commands, and conformance steps describe this repository.
- [ ] **FAIL** — Any manager/lockfile mismatch or unsupported command remains; correct the profile and shared SDLC references.
<!-- RUBRIC-END -->
