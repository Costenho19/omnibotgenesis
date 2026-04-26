"use strict";
var __create = Object.create;
var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __getProtoOf = Object.getPrototypeOf;
var __hasOwnProp = Object.prototype.hasOwnProperty;
var __esm = (fn, res) => function __init() {
  return fn && (res = (0, fn[__getOwnPropNames(fn)[0]])(fn = 0)), res;
};
var __export = (target, all) => {
  for (var name in all)
    __defProp(target, name, { get: all[name], enumerable: true });
};
var __copyProps = (to, from, except, desc) => {
  if (from && typeof from === "object" || typeof from === "function") {
    for (let key of __getOwnPropNames(from))
      if (!__hasOwnProp.call(to, key) && key !== except)
        __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
  }
  return to;
};
var __toESM = (mod, isNodeMode, target) => (target = mod != null ? __create(__getProtoOf(mod)) : {}, __copyProps(
  // If the importer is in node compatibility mode or this is not an ESM
  // file that has been converted to a CommonJS file using a Babel-
  // compatible transform (i.e. "__esModule" has not been set), then set
  // "default" to the CommonJS "module.exports" for node compatibility.
  isNodeMode || !mod || !mod.__esModule ? __defProp(target, "default", { value: mod, enumerable: true }) : target,
  mod
));
var __toCommonJS = (mod) => __copyProps(__defProp({}, "__esModule", { value: true }), mod);

// src/exceptions.ts
var OmnixError, OmnixAuthError, OmnixValidationError, OmnixGovernanceBlock, OmnixRateLimitError, OmnixServerError, OmnixNetworkError;
var init_exceptions = __esm({
  "src/exceptions.ts"() {
    "use strict";
    OmnixError = class extends Error {
      constructor(message) {
        super(message);
        this.name = "OmnixError";
        Object.setPrototypeOf(this, new.target.prototype);
      }
    };
    OmnixAuthError = class extends OmnixError {
      constructor(message = "Invalid or missing API key.") {
        super(message);
        this.name = "OmnixAuthError";
      }
    };
    OmnixValidationError = class extends OmnixError {
      constructor(message, errors = []) {
        super(message);
        this.name = "OmnixValidationError";
        this.errors = errors;
      }
    };
    OmnixGovernanceBlock = class extends OmnixError {
      constructor(receipt) {
        const vetoes = receipt.veto_chain ?? [];
        super(
          `Decision BLOCKED by OMNIX governance. Veto chain: ${JSON.stringify(vetoes)}. Receipt: ${receipt.receipt_id}`
        );
        this.name = "OmnixGovernanceBlock";
        this.receipt = receipt;
      }
    };
    OmnixRateLimitError = class extends OmnixError {
      constructor(retryAfter = 60) {
        super(`Rate limit exceeded. Retry after ${retryAfter}s.`);
        this.name = "OmnixRateLimitError";
        this.retryAfter = retryAfter;
      }
    };
    OmnixServerError = class extends OmnixError {
      constructor(statusCode, message) {
        super(`Server error ${statusCode}: ${message}`);
        this.name = "OmnixServerError";
        this.statusCode = statusCode;
      }
    };
    OmnixNetworkError = class extends OmnixError {
      constructor(message) {
        super(message);
        this.name = "OmnixNetworkError";
      }
    };
  }
});

// src/models.ts
var CheckpointResult, GovernanceReceipt;
var init_models = __esm({
  "src/models.ts"() {
    "use strict";
    CheckpointResult = class {
      constructor(data) {
        this.id = String(data.id ?? "");
        this.name = data.name ?? "";
        this.result = data.result ?? "";
        this.score = data.score ?? null;
        this.threshold = data.threshold ?? null;
        this.condition = data.condition ?? null;
      }
      get passed() {
        return this.result === "PASS" || this.result === "PASSED";
      }
    };
    GovernanceReceipt = class {
      constructor(data) {
        const cpRaw = data.checkpoint_proof ?? data.checkpoints ?? [];
        const cps = cpRaw.map((cp) => new CheckpointResult(cp));
        this.receiptId = data.receipt_id ?? "";
        this.decision = data.decision ?? "";
        this.timestamp = data.timestamp ?? "";
        this.domain = data.domain ?? "";
        this.asset = data.asset ?? "";
        this.policyVersion = data.policy_version ?? "";
        this.contentHash = data.content_hash ?? "";
        this.signature = data.signature ?? null;
        this.signatureAlgorithm = data.signature_algorithm ?? data.integrity?.algorithm ?? null;
        this.publicKey = data.public_key ?? null;
        this.jurisdiction = data.jurisdiction ?? data.authority_binding?.jurisdiction ?? null;
        this.checkpointsPassed = data.checkpoints_passed ?? cps.filter((c) => c.passed).length;
        this.checkpointsBlocked = data.checkpoints_blocked ?? cps.filter((c) => !c.passed).length;
        this.vetoChain = data.veto_chain ?? [];
        this.checkpoints = cps;
        this.verifyUrl = data.verify_url ?? null;
        this.raw = data;
      }
      get approved() {
        return this.decision === "APPROVED";
      }
      get blocked() {
        return this.decision === "BLOCKED";
      }
      get held() {
        return this.decision === "HOLD";
      }
      toString() {
        const icon = this.approved ? "\u2705" : this.blocked ? "\u{1F6AB}" : "\u23F8\uFE0F";
        return `${icon} ${this.decision} | ${this.receiptId} | ${this.checkpointsPassed}/11 gates passed | sig: ${this.signatureAlgorithm ?? "N/A"}`;
      }
      toJSON() {
        return this.raw;
      }
    };
  }
});

// src/client.ts
var client_exports = {};
__export(client_exports, {
  OmnixClient: () => OmnixClient
});
var import_https, import_http, import_url, SDK_VERSION, DEFAULT_BASE, DEFAULT_TIMEOUT, OmnixClient;
var init_client = __esm({
  "src/client.ts"() {
    "use strict";
    import_https = __toESM(require("https"), 1);
    import_http = __toESM(require("http"), 1);
    import_url = require("url");
    init_exceptions();
    init_models();
    SDK_VERSION = "1.0.0";
    DEFAULT_BASE = "https://omnixquantum.net";
    DEFAULT_TIMEOUT = 3e4;
    OmnixClient = class {
      constructor(opts) {
        if (!opts.apiKey || !opts.apiKey.startsWith("OMNIX-")) {
          throw new OmnixAuthError(
            "Invalid API key format. Expected: OMNIX-<key>. Get yours at omnixquantum.net."
          );
        }
        this.apiKey = opts.apiKey;
        this.baseUrl = (opts.baseUrl ?? DEFAULT_BASE).replace(/\/$/, "");
        this.timeout = opts.timeout ?? DEFAULT_TIMEOUT;
        this.raiseOnBlock = opts.raiseOnBlock ?? false;
      }
      // ── Public API ─────────────────────────────────────────────────────────
      /**
       * Evaluate a governance decision through OMNIX.
       *
       * @param opts.domain  - Governance domain (trading | islamic_credit | insurance | ...)
       * @param opts.asset   - Asset or subject identifier
       * @param opts.signals - Domain-specific signals
       * @param opts.context - Optional extra context
       *
       * @returns GovernanceReceipt — signed, immutable governance receipt
       */
      async evaluate(opts) {
        const body = {
          domain: opts.domain,
          asset: opts.asset,
          signals: opts.signals
        };
        if (opts.context) body.context = opts.context;
        const raw = await this.post("/api/governance/evaluate", body);
        const receipt = new GovernanceReceipt(raw);
        if (this.raiseOnBlock && receipt.blocked) {
          throw new OmnixGovernanceBlock(raw);
        }
        return receipt;
      }
      /**
       * Verify a receipt by ID — purely cryptographic, no DB access required.
       */
      async verify(receiptId) {
        return this.get(`/api/trust/verify/${receiptId}`);
      }
      /**
       * Fetch a receipt by ID from the OMNIX explorer.
       */
      async getReceipt(receiptId) {
        const raw = await this.get(`/api/explorer/receipt/${receiptId}`);
        return new GovernanceReceipt(raw);
      }
      /**
       * Fetch the public OMNIX trust registry. No authentication required.
       */
      async trustRegistry() {
        return this.get("/api/trust/registry", false);
      }
      /**
       * Fetch the current OMNIX signing public key (RFC 8615 well-known).
       * No authentication required.
       */
      async publicKey() {
        return this.get("/.well-known/omnix-public-key.json", false);
      }
      // ── Internal ───────────────────────────────────────────────────────────
      headers(authenticated = true) {
        const h = {
          "Content-Type": "application/json",
          "Accept": "application/json",
          "User-Agent": `omnix-node-sdk/${SDK_VERSION}`
        };
        if (authenticated) h["X-API-Key"] = this.apiKey;
        return h;
      }
      post(path, body) {
        return this.request("POST", path, body, true);
      }
      get(path, authenticated = true) {
        return this.request("GET", path, void 0, authenticated);
      }
      request(method, path, body, authenticated) {
        return new Promise((resolve, reject) => {
          const url = new import_url.URL(`${this.baseUrl}${path}`);
          const isHttps = url.protocol === "https:";
          const transport = isHttps ? import_https.default : import_http.default;
          const bodyStr = body ? JSON.stringify(body) : void 0;
          const reqOpts = {
            hostname: url.hostname,
            port: url.port || (isHttps ? 443 : 80),
            path: url.pathname + url.search,
            method,
            headers: {
              ...this.headers(authenticated),
              ...bodyStr ? { "Content-Length": Buffer.byteLength(bodyStr) } : {}
            }
          };
          const req = transport.request(reqOpts, (res) => {
            let data = "";
            res.on("data", (chunk) => {
              data += chunk.toString();
            });
            res.on("end", () => {
              let parsed = {};
              try {
                parsed = JSON.parse(data);
              } catch {
              }
              const status = res.statusCode ?? 0;
              if (status >= 200 && status < 300) {
                return resolve(parsed);
              }
              if (status === 401) return reject(new OmnixAuthError("Invalid API key. Check your OMNIX-... key."));
              if (status === 422) {
                return reject(new OmnixValidationError(
                  String(parsed.detail ?? "Validation error"),
                  parsed.errors ?? []
                ));
              }
              if (status === 429) {
                const retryAfter = parseInt(String(res.headers["retry-after"] ?? "60"), 10);
                return reject(new OmnixRateLimitError(retryAfter));
              }
              return reject(new OmnixServerError(status, String(parsed.error ?? data)));
            });
          });
          req.setTimeout(this.timeout, () => {
            req.destroy();
            reject(new OmnixNetworkError(`Request timed out after ${this.timeout}ms.`));
          });
          req.on("error", (err) => {
            reject(new OmnixNetworkError(`Cannot reach OMNIX at ${this.baseUrl}: ${err.message}`));
          });
          if (bodyStr) req.write(bodyStr);
          req.end();
        });
      }
    };
  }
});

// src/index.ts
var index_exports = {};
__export(index_exports, {
  CheckpointResult: () => CheckpointResult,
  GovernanceReceipt: () => GovernanceReceipt,
  OmnixAuthError: () => OmnixAuthError,
  OmnixClient: () => OmnixClient,
  OmnixError: () => OmnixError,
  OmnixGovernanceBlock: () => OmnixGovernanceBlock,
  OmnixNetworkError: () => OmnixNetworkError,
  OmnixRateLimitError: () => OmnixRateLimitError,
  OmnixServerError: () => OmnixServerError,
  OmnixValidationError: () => OmnixValidationError,
  evaluate: () => evaluate
});
module.exports = __toCommonJS(index_exports);
init_client();
init_models();
init_exceptions();
async function evaluate(opts) {
  const { apiKey, domain, asset, signals, context, ...rest } = opts;
  const { OmnixClient: OmnixClient2 } = await Promise.resolve().then(() => (init_client(), client_exports));
  const client = new OmnixClient2({ apiKey, ...rest });
  return client.evaluate({ domain, asset, signals, context });
}
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
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
});
