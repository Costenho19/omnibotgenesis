import {
  CheckpointResult,
  GovernanceReceipt,
  OmnixAuthError,
  OmnixClient,
  OmnixError,
  OmnixGovernanceBlock,
  OmnixNetworkError,
  OmnixRateLimitError,
  OmnixServerError,
  OmnixValidationError
} from "./chunk-FPZHJEY3.js";

// src/index.ts
async function evaluate(opts) {
  const { apiKey, domain, asset, signals, context, ...rest } = opts;
  const { OmnixClient: OmnixClient2 } = await import("./client-PO5OAL2Y.js");
  const client = new OmnixClient2({ apiKey, ...rest });
  return client.evaluate({ domain, asset, signals, context });
}
export {
  CheckpointResult,
  GovernanceReceipt,
  OmnixAuthError,
  OmnixClient,
  OmnixError,
  OmnixGovernanceBlock,
  OmnixNetworkError,
  OmnixRateLimitError,
  OmnixServerError,
  OmnixValidationError,
  evaluate
};
