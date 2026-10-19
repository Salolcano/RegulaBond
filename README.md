# RegulaBond

RegulaBond is a contract-first GenLayer primitive for funded review of regulatory requirement claims. A sponsor locks one official Federal Register document and a precise requirement definition. A claimant submits a claim. GenLayer validators assess the locked requirement against the official source, and the contract settles the funded bounty based on an exact canonical verdict.

## Lifecycle

`create_bounty → fund_bounty → submit_claim → adjudicate_case → withdraw_credit`

If source access or assessment is unreliable, the canonical result is `RETRYABLE`; the bounty remains locked and either the claimant or sponsor can retry. No credit is created for a retryable result.

## Single live case per bounty

A bounty accepts exactly one case, ever. `submit_claim` requires the bounty to be `ACTIVE` with no attached case, and records that case in `bounty_case`. Bounty status then mirrors the case while it is live:

`ACTIVE (no case) → CASE_OPEN ⇄ RETRYABLE → SETTLED`

A `RETRYABLE` result moves the bounty to `RETRYABLE` (not back to `ACTIVE`), so no other claimant can open a second case on the same locked funds. `adjudicate_case` and `retry_case` act only on the bounty's attached case and reject any state where the case and bounty statuses disagree. `get_bounty` returns the attached `case_id`.

## Important validator remediation

The consensus-critical function returns exactly one of:

- `SUPPORTS_REQUIREMENT`
- `DOES_NOT_SUPPORT`
- `RETRYABLE`

There are no scores, percentages, floating-point values, numeric thresholds, or tolerance-based comparisons. The contract uses strict equality on the canonical enum and derives the payout recipient in contract code. The free-form claim and source text are treated as untrusted input and cannot set the payout address or change the locked requirement.

## Source policy

Only HTTPS URLs beginning with `https://www.federalregister.gov/documents/` are accepted as the locked source. Validators fetch the sponsor-locked official document. The claimant's claim text is not treated as an authoritative source.

## Network configuration

The uploaded Studio notes specify GenLayer Studio Network:

- RPC: `https://studio.genlayer.com/api`
- Chain ID: `61999`
- Explorer: `https://explorer-studio.genlayer.com`

Confirm the target network in Studio before deployment. This package has **not** been deployed from this environment.

## Deploy in Studio

1. Open GenLayer Studio and select the network specified above.
2. Create a contract using `contracts/regulabond.py`.
3. Run the Studio compiler/linter. Fix any network-version API incompatibility reported by Studio before deploying.
4. Deploy the contract with no constructor arguments.
5. Copy the deployed address and transaction hash into `docs/deployment-evidence.md`.
6. Run the lifecycle below with two separate wallets.

## Test lifecycle

1. Sponsor calls `create_bounty` with a unique ID, title, official Federal Register document URL, a stable requirement ID, and a precise requirement definition.
2. Sponsor calls payable `fund_bounty` with a nonzero GEN amount.
3. Claimant calls `submit_claim` with the bounty ID and a short claim. Save the returned case ID.
4. Any account calls `adjudicate_case(case_id)`. Inspect `get_case`, `get_bounty`, and `get_accounting`.
5. For `SUPPORTS_REQUIREMENT`, the claimant receives a credit. For `DOES_NOT_SUPPORT`, the sponsor receives a credit. For `RETRYABLE`, neither side receives a credit and the locked amount remains unchanged.
6. The credit owner calls `withdraw_credit(bounty_id)`.
7. Confirm `received = locked + credited` and `withdrawn <= credited` in `get_accounting`.

## Contract methods

Writes: `create_bounty`, `fund_bounty`, `submit_claim`, `adjudicate_case`, `retry_case`, `withdraw_credit`.

Views: `get_bounty`, `get_case`, `get_credit`, `get_accounting`.

## Local checks

```bash
python -m compileall contracts tests
python -m pytest -q
```

`tests/fake_genlayer.py` is a minimal in-memory SDK stand-in that lets `tests/test_case_lifecycle.py` execute the contract's state machine and accounting. These checks validate Python syntax, source-level invariants, and lifecycle logic only. They do not replace Studio compilation, a real validator-consensus transaction, or a live GEN settlement test.

## Scope limits

- Version 1 supports exactly one case per bounty, enforced in contract state, to keep the settlement model simple.
- This is not legal advice and does not determine whether an agency will enforce a regulation.
- A public URL check does not by itself guarantee that validators can fetch the source. Failed or inconclusive source assessment must remain non-penalizing.
- The claim is evaluated against the sponsor-locked official document and requirement; it does not prove real-world compliance by a company.
