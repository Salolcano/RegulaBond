# Consensus and settlement design

## Canonical output

The only consensus-critical output is one exact token: `SUPPORTS_REQUIREMENT`, `DOES_NOT_SUPPORT`, or `RETRYABLE`. The validator function normalizes any unexpected output to `RETRYABLE`. `gl.eq_principle.strict_eq` compares the resulting token, not rationale text or a numeric score.

## Consequence mapping

| Canonical verdict | Contract state | Credit recipient | Locked bounty |
|---|---|---|---|
| `SUPPORTS_REQUIREMENT` | `ACCEPTED` / `SETTLED` | Claimant | Set to zero |
| `DOES_NOT_SUPPORT` | `NOT_ACCEPTED` / `SETTLED` | Sponsor | Set to zero |
| `RETRYABLE` | `RETRYABLE` / `RETRYABLE` | None | Unchanged |

The contract does not publish any variable numeric result that downstream contracts could threshold. The locked requirement ID and definition are fixed at bounty creation. Payout address is derived from stored sponsor/claimant state, never from model output.

## Failure and retry

Source render failure, an oversized/empty page, irrelevant or contradictory evidence, and unexpected model output map to `RETRYABLE`. The contract creates no credit and leaves the bounty locked. The bounty stays attached to the same case (bounty status `RETRYABLE`), so no other claimant can open a case on the locked funds. The claimant or sponsor can call `retry_case` (which sets case and bounty to `CASE_OPEN`), or anyone can call `adjudicate_case` directly on the retryable case.

## Threat boundaries

- The sponsor controls the locked requirement but cannot change it after creation.
- The claimant controls only their claim text; it is labeled untrusted in the prompt.
- The model cannot choose the recipient, amount, or a threshold value.
- A bounty has one attached case (`bounty_case`), set once and never reassigned. Writes reject a case that is not that attached case, or whose status differs from the bounty's, rather than repairing it.
- Terminal settlement is rejected on repeat because the case is no longer open/retryable and the locked amount is zero.
- Withdrawal zeroes the credit before requesting the transfer.
