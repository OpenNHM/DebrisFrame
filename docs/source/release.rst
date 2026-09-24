Release procedure
-----------------

DebrisFrame is versioned from git tags via ``hatch-vcs`` and published to PyPI by the
``Build and upload to PyPI`` GitHub Actions workflow. Releases follow a release-first flow:
the GitHub release is created first (triggering Zenodo), then the PyPI workflow is run
against that release tag.

Prerequisites (one-time)
^^^^^^^^^^^^^^^^^^^^^^^^

- PyPI and TestPyPI trusted publishers configured for the repository:

  - owner: ``OpenNHM``
  - repository: ``DebrisFrame``
  - workflow filename: ``buildAndUploadPyPi.yml``
  - environment: ``pypi`` (PyPI) and ``testpypi`` (TestPyPI)

- GitHub environments ``pypi`` and ``testpypi`` created in the repository settings.
- The repository linked to Zenodo, with ``.zenodo.json`` present on ``master``.

Create a release
^^^^^^^^^^^^^^^^

1. Make sure all packaging changes are merged into ``master``.
2. Create a new GitHub release and set its tag to the new version, e.g. ``X.Y.Z`` (GitHub
   creates the tag if it does not exist). Publishing the release makes Zenodo archive it
   and mint the DOI.
3. Run the ``Build and upload to PyPI`` workflow from the Actions tab
   (``workflow_dispatch``). In the "Use workflow from" dropdown, select the release tag
   ``X.Y.Z`` so the build runs on the tagged commit.
4. The workflow builds the sdist and wheel, checks the metadata, publishes to TestPyPI,
   and then to PyPI.

The version is taken from the git tag. If the workflow does not run on a version tag,
hatch-vcs adds a local version segment (e.g. ``+g<hash>``) that PyPI rejects; the workflow
fails early in that case.
