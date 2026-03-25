# Minimal, Auditable Contracts

These contract templates are intentionally small.

Design rules:
- Use standard token contracts only.
- No upgradeable proxies.
- No on-chain exchange, escrow, or rights engine.
- Royalties are the only economics enforced on-chain.
- Rich licensing, compliance, zoning, and marketplace flows stay in the backend.

Templates:
- `BuiltAtticPlanRegistry.sol`
  Standard: `ERC-721 + ERC-2981`
  Use: architectural plans and design ownership records
- `BuiltAtticProperty1155.sol`
  Standard: `ERC-1155 + ERC-2981`
  Use: tokenized property assets with optional fractional ownership

Audit posture:
- one contract per asset pattern
- owner-controlled minting
- fixed, simple state transitions
- metadata points to IPFS
- OpenZeppelin primitives only

What is intentionally off-chain:
- licensing enforcement
- exchange order matching
- offer acceptance
- escrow and settlement workflows
- legal-document verification
