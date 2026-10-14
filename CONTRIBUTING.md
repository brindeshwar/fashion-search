# Contributing

Thanks for helping. The short version:

1. **Open or pick an issue** using the bug or feature template.
2. **Set up** following [docs/SETUP.md](docs/SETUP.md) and
   [docs/DEVELOPMENT.md → Dev setup](docs/DEVELOPMENT.md#dev-setup).
3. **Branch from `main`:** `feat/…`, `fix/…`, `docs/…` or `chore/…`.
4. **Make the change with tests.** New logic needs a fast test. Anything that loads a model
   gets `@pytest.mark.slow`.
5. **Run all the checks** listed in [DEVELOPMENT.md → Checks](docs/DEVELOPMENT.md#checks).
   CI runs the same ones.
6. **Update the docs** your change affects:
   - `CHANGELOG.md` under _Unreleased_, for anything a user would notice
   - `docs/API.md` and `web/src/lib/api.ts` when the API changes
   - `docs/ARCHITECTURE.md` when modules or file formats change
   - `docs/DECISIONS.md` (a new ADR) when you choose between real alternatives
7. **Commit** with [Conventional Commits](https://www.conventionalcommits.org/) and **open a
   PR**. Fill in the template; CI must pass before merging.

Code style, testing approach and the release process are in [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).
