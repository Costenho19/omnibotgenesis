interface CheckpointResultData {
    id?: string;
    name?: string;
    result?: string;
    score?: number | null;
    threshold?: number | null;
    condition?: string | null;
}
declare class CheckpointResult {
    readonly id: string;
    readonly name: string;
    readonly result: string;
    readonly score: number | null;
    readonly threshold: number | null;
    readonly condition: string | null;
    constructor(data: CheckpointResultData);
    get passed(): boolean;
}
interface GovernanceReceiptData {
    receipt_id?: string;
    decision?: string;
    timestamp?: string;
    domain?: string;
    asset?: string;
    policy_version?: string;
    content_hash?: string;
    signature?: string | null;
    signature_algorithm?: string | null;
    integrity?: {
        algorithm?: string;
    };
    public_key?: string | null;
    jurisdiction?: string | null;
    authority_binding?: {
        jurisdiction?: string;
    };
    checkpoints_passed?: number;
    checkpoints_blocked?: number;
    veto_chain?: string[];
    checkpoint_proof?: CheckpointResultData[];
    checkpoints?: CheckpointResultData[];
    verify_url?: string | null;
    [key: string]: unknown;
}
/**
 * Cryptographically signed governance receipt issued by OMNIX.
 *
 * Every field is part of the canonical hash — any modification
 * invalidates the SHA-256 content_hash and the PQC signature.
 *
 * Verify offline:
 *   python omnix_verify.py receipt.json
 *   https://omnixquantum.net/verify-independently
 */
declare class GovernanceReceipt {
    readonly receiptId: string;
    readonly decision: 'APPROVED' | 'BLOCKED' | 'HOLD' | string;
    readonly timestamp: string;
    readonly domain: string;
    readonly asset: string;
    readonly policyVersion: string;
    readonly contentHash: string;
    readonly signature: string | null;
    readonly signatureAlgorithm: string | null;
    readonly publicKey: string | null;
    readonly jurisdiction: string | null;
    readonly checkpointsPassed: number;
    readonly checkpointsBlocked: number;
    readonly vetoChain: string[];
    readonly checkpoints: CheckpointResult[];
    readonly verifyUrl: string | null;
    readonly raw: GovernanceReceiptData;
    constructor(data: GovernanceReceiptData);
    get approved(): boolean;
    get blocked(): boolean;
    get held(): boolean;
    toString(): string;
    toJSON(): GovernanceReceiptData;
}

interface OmnixClientOptions {
    apiKey: string;
    baseUrl?: string;
    timeout?: number;
    /**
     * If true, throw OmnixGovernanceBlock when decision === 'BLOCKED'.
     * Default: false — returns the receipt normally.
     */
    raiseOnBlock?: boolean;
}
interface EvaluateOptions {
    domain: string;
    asset: string;
    signals: Record<string, unknown>;
    context?: Record<string, unknown>;
}
/**
 * OMNIX Governance SDK — Node.js / TypeScript client.
 *
 * ```typescript
 * import { OmnixClient } from 'omnix-quantum'
 *
 * const client = new OmnixClient({ apiKey: 'OMNIX-...' })
 * const receipt = await client.evaluate({
 *   domain:  'trading',
 *   asset:   'BTC/USD',
 *   signals: { price: 94200, volume: 1.5, volatility: 0.18 },
 * })
 *
 * console.log(receipt.toString())
 * // ✅ APPROVED | OMNIX-TRD-... | 11/11 gates passed | sig: Dilithium-3 (NIST FIPS 204)
 * console.log(receipt.approved)           // true
 * console.log(receipt.contentHash)        // "sha256:..."
 * console.log(receipt.signatureAlgorithm) // "Dilithium-3 (NIST FIPS 204)"
 * ```
 */
declare class OmnixClient {
    private readonly apiKey;
    private readonly baseUrl;
    private readonly timeout;
    private readonly raiseOnBlock;
    constructor(opts: OmnixClientOptions);
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
    evaluate(opts: EvaluateOptions): Promise<GovernanceReceipt>;
    /**
     * Verify a receipt by ID — purely cryptographic, no DB access required.
     */
    verify(receiptId: string): Promise<Record<string, unknown>>;
    /**
     * Fetch a receipt by ID from the OMNIX explorer.
     */
    getReceipt(receiptId: string): Promise<GovernanceReceipt>;
    /**
     * Fetch the public OMNIX trust registry. No authentication required.
     */
    trustRegistry(): Promise<Record<string, unknown>>;
    /**
     * Fetch the current OMNIX signing public key (RFC 8615 well-known).
     * No authentication required.
     */
    publicKey(): Promise<Record<string, unknown>>;
    private headers;
    private post;
    private get;
    private request;
}

declare class OmnixError extends Error {
    constructor(message: string);
}
declare class OmnixAuthError extends OmnixError {
    constructor(message?: string);
}
declare class OmnixValidationError extends OmnixError {
    readonly errors: unknown[];
    constructor(message: string, errors?: unknown[]);
}
/**
 * The decision was explicitly BLOCKED by OMNIX governance.
 * This is not an infrastructure error — it is a governance verdict.
 * Inspect `.receipt` for the full signed receipt and veto chain.
 */
declare class OmnixGovernanceBlock extends OmnixError {
    readonly receipt: Record<string, unknown>;
    constructor(receipt: Record<string, unknown>);
}
declare class OmnixRateLimitError extends OmnixError {
    readonly retryAfter: number;
    constructor(retryAfter?: number);
}
declare class OmnixServerError extends OmnixError {
    readonly statusCode: number;
    constructor(statusCode: number, message: string);
}
declare class OmnixNetworkError extends OmnixError {
    constructor(message: string);
}

/**
 * Convenience function — evaluate a governance decision.
 *
 * ```typescript
 * import { evaluate } from 'omnix-quantum'
 *
 * const receipt = await evaluate({
 *   apiKey:  'OMNIX-...',
 *   domain:  'islamic_credit',
 *   asset:   'SME-AE-001',
 *   signals: { debt_to_income: 32, collateral_ratio: 1.4, sharia_compliant: true },
 * })
 * console.log(receipt.decision) // 'APPROVED'
 * ```
 */
declare function evaluate(opts: {
    apiKey: string;
    domain: string;
    asset: string;
    signals: Record<string, unknown>;
    context?: Record<string, unknown>;
    baseUrl?: string;
    timeout?: number;
}): Promise<GovernanceReceipt>;

export { CheckpointResult, type CheckpointResultData, type EvaluateOptions, GovernanceReceipt, type GovernanceReceiptData, OmnixAuthError, OmnixClient, type OmnixClientOptions, OmnixError, OmnixGovernanceBlock, OmnixNetworkError, OmnixRateLimitError, OmnixServerError, OmnixValidationError, evaluate };
