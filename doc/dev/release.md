# Release Guide

1. Update `CHANGELOG.md` with the new version.
2. Bump the version in `pyproject.toml`.
3. Tag the release and push the tag:
   ```bash
   git tag -a vX.Y.Z -m "Release vX.Y.Z"
   git push origin vX.Y.Z
   ```
4. Build and publish to PyPI:
   ```bash
   python -m build
   twine upload dist/*
   ```
5. Create a GitHub Release linking to the changelog entry.
