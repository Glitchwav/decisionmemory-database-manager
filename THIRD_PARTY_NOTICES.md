# Third-Party Notices

This repository depends on third-party software with separate licenses.

- SurrealDB: installed separately; see https://surrealdb.com/
- LanceDB: installed from PyPI or Cargo; see https://lancedb.com/
- FastEmbed and `all-MiniLM-L6-v2`: the experimental Rust prototype downloads model artifacts on first use
- Python and Rust dependencies: see `pyproject.toml`, `requirements.txt`, and the Cargo manifests

No SurrealDB database, LanceDB dataset, embedding-model cache, or user memory content is distributed in this repository.

Before publishing a release, generate and review a complete dependency-license inventory and record the exact embedding-model revision and license.
