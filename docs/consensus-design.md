# Consensus and settlement design

## Canonical output

The only consensus-critical output is one exact token: `SUPPORTS_REQUIREMENT`, `DOES_NOT_SUPPORT`, or `RETRYABLE`. The validator function normalizes any unexpected output to `RETRYABLE`. `gl.eq_principle.strict_eq` compares the resulting token, not rationale text or a numeric score.

## Consequence mapping

| Canonical verdict | Contract state | Credit recipient | Locked bounty |
|---|---|---|---|
| `SUPPORTS_REQUIREMENT` | `ACCEPTED` / `SETTLED` | Claimant | Set to zero |
| `DOES_NOT_SUPPORT` | `NOT_ACCEPTED` / `SETTLED` | Sponsor | Set to zero |
| `RETRYABLE` | `RETRYABLE` / `ACTIVE` | None | Unchanged |

The contract does not publish any variable numeric result that downstream contracts could threshold. The locked requirement ID and definition are fixed at bounty creation. Payout address is derived from stored sponsor/claimant state, never from model output.

## Failure and retry

Source render failure, an oversized/empty page, irrelevant or contradictory evidence, and unexpected model output map to `RETRYABLE`. The contract creates no credit and leaves the bounty locked. The claimant or sponsor can call `retry_case` and then request adjudication again.

## Threat boundaries

- The sponsor controls the locked requirement but cannot change it after creation.
- The claimant controls only their claim text; it is labeled untrusted in the prompt.
- The model cannot choose the recipient, amount, or a threshold value.
- Terminal settlement is rejected on repeat because the case is no longer open/retryable and the locked amount is zero.
- Withdrawal zeroes the credit before requesting the transfer.
