# Repository flow

This repository follows the contract-first shape of the reference project:

- `contracts/`: the Intelligent Contract source.
- `tests/`: local source-level regression checks.
- `scripts/`: a public-source reachability probe.
- `docs/`: consensus design and deployment evidence log.
- `README.md`: purpose, lifecycle, interface, and Studio deployment checklist.
- `.env.example`: non-secret network settings only.

It deliberately does not claim a deployment or contain fabricated transaction receipts. The Studio deployment and lifecycle evidence must be recorded after running the actual transactions.
