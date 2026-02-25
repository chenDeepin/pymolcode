/**
 * Bridge client for communicating with Python PyMOL bridge server.
 * 
 * Uses Content-Length framed JSON-RPC over stdio.
 */

import { spawn, ChildProcess } from "child_process";
import {
  JSONRPCRequest,
  JSONRPCResponse,
  JSONRPCError,
  BridgeCapabilities,
  BridgeClientOptions,
  CallOptions,
  JsonRpcErrorCode,
  JsonRpcErrorType,
  MethodTimeoutCategory,
  MethodTimeoutPolicy,
  PendingRequest,
} from "./types.js";

const DEFAULT_CONTROL_TIMEOUT_MS = 30_000;
const DEFAULT_ANALYSIS_TIMEOUT_MS = 60_000;
const DEFAULT_RENDER_TIMEOUT_MS = 120_000;
const HEADER_TERMINATOR = "\r\n\r\n";
const JSONRPC_CANCEL_METHOD = "$/cancelRequest";
const SERVER_ERROR_MIN = -32099;
const SERVER_ERROR_MAX = -32000;

type ResolvedBridgeClientOptions = {
  pythonPath: string;
  bridgeScript: string;
  timeout: number;
  timeoutPolicy: MethodTimeoutPolicy;
  methodTimeoutOverrides: Record<string, number>;
  methodCategoryOverrides: Partial<Record<string, MethodTimeoutCategory>>;
  debug: boolean;
};

type TimeoutResolution = {
  timeoutMs: number;
  category: MethodTimeoutCategory;
};

export class BridgeRpcError extends Error {
  public readonly code: number;
  public readonly type: JsonRpcErrorType;
  public readonly requestId: string | number | null;
  public readonly method: string;
  public readonly data?: unknown;

  constructor(args: {
    code: number;
    type: JsonRpcErrorType;
    message: string;
    requestId: string | number | null;
    method: string;
    data?: unknown;
  }) {
    super(args.message);
    this.name = "BridgeRpcError";
    this.code = args.code;
    this.type = args.type;
    this.requestId = args.requestId;
    this.method = args.method;
    this.data = args.data;
  }
}

export class BridgeTimeoutError extends Error {
  public readonly requestId: string | number;
  public readonly method: string;
  public readonly category: MethodTimeoutCategory;
  public readonly timeoutMs: number;
  public readonly elapsedMs: number;

  constructor(args: {
    requestId: string | number;
    method: string;
    category: MethodTimeoutCategory;
    timeoutMs: number;
    elapsedMs: number;
  }) {
    super(
      `Request timed out after ${args.elapsedMs}ms (limit ${args.timeoutMs}ms) for method: ${args.method}`
    );
    this.name = "BridgeTimeoutError";
    this.requestId = args.requestId;
    this.method = args.method;
    this.category = args.category;
    this.timeoutMs = args.timeoutMs;
    this.elapsedMs = args.elapsedMs;
  }
}

export class BridgeCancellationError extends Error {
  public readonly requestId: string | number;
  public readonly method: string;

  constructor(args: { requestId: string | number; method: string; reason: string }) {
    super(args.reason);
    this.name = "BridgeCancellationError";
    this.requestId = args.requestId;
    this.method = args.method;
  }
}

export class BridgeClient {
  private process: ChildProcess | null = null;
  private buffer: Buffer = Buffer.alloc(0);
  private pendingRequests: Map<string | number, PendingRequest> = new Map();
  private requestId = 0;
  private options: ResolvedBridgeClientOptions;
  private isShuttingDown = false;

  constructor(options: BridgeClientOptions = {}) {
    const timeoutPolicy: MethodTimeoutPolicy = {
      control: options.timeoutPolicy?.control ?? DEFAULT_CONTROL_TIMEOUT_MS,
      analysis: options.timeoutPolicy?.analysis ?? DEFAULT_ANALYSIS_TIMEOUT_MS,
      render: options.timeoutPolicy?.render ?? DEFAULT_RENDER_TIMEOUT_MS,
    };

    this.options = {
      pythonPath: options.pythonPath || "python3.11",
      bridgeScript: options.bridgeScript || "-m",
      timeout: options.timeout || timeoutPolicy.control,
      timeoutPolicy,
      methodTimeoutOverrides: { ...(options.methodTimeoutOverrides || {}) },
      methodCategoryOverrides: { ...(options.methodCategoryOverrides || {}) },
      debug: options.debug || false,
    };
  }

  /**
   * Start the Python bridge process and initialize connection.
   */
  async start(): Promise<BridgeCapabilities> {
    if (this.process) {
      throw new Error("Bridge process already started");
    }

    return new Promise((resolve, reject) => {
      this.process = spawn(this.options.pythonPath, [this.options.bridgeScript, "python.bridge.server"], {
        stdio: ["pipe", "pipe", "pipe"],
      });

      if (!this.process.stdin || !this.process.stdout || !this.process.stderr) {
        reject(new Error("Failed to create stdio streams"));
        return;
      }

      // Handle stderr (logs from Python)
      this.process.stderr.on("data", (data: Buffer) => {
        if (this.options.debug) {
          console.error("[bridge stderr]", data.toString());
        }
      });

      // Handle stdout (JSON-RPC responses)
      this.process.stdout.on("data", (data: Buffer) => {
        this.handleData(data);
      });

      // Handle process exit
      this.process.on("exit", (code, signal) => {
        if (!this.isShuttingDown && code !== 0) {
          this.rejectAllPending(new Error(`Bridge process exited with code ${code}, signal ${signal}`));
        }
        this.process = null;
      });

      // Handle process error
      this.process.on("error", (error) => {
        reject(new Error(`Failed to start bridge process: ${error.message}`));
      });

      // Initialize connection
        this.initialize()
          .then((caps) => {
            resolve(caps);
          })
        .catch(reject);
    });
  }

  /**
   * Shutdown the bridge process gracefully.
   */
  async shutdown(): Promise<void> {
    if (!this.process) {
      return;
    }

    this.isShuttingDown = true;

    try {
      await this.call("shutdown");
    } catch {
      // Ignore shutdown errors
    }

    // Give process time to exit gracefully
    await new Promise<void>((resolve) => {
      if (!this.process) {
        resolve();
        return;
      }

      const timeout = setTimeout(() => {
        if (this.process) {
          this.process.kill("SIGTERM");
        }
        resolve();
      }, 5000);

      this.process.on("exit", () => {
        clearTimeout(timeout);
        resolve();
      });
    });

    this.rejectAllPending(new Error("Bridge shutting down"));
    this.process = null;
  }

  /**
   * Initialize the bridge connection.
   */
  async initialize(): Promise<BridgeCapabilities> {
    const response = await this.call<{ protocolVersion: string; capabilities: string[] }>("initialize");
    return {
      protocolVersion: response.result?.protocolVersion || "1.0.0",
      capabilities: response.result?.capabilities || [],
    };
  }

  /**
   * Ping the bridge server.
   */
  async ping(): Promise<boolean> {
    try {
      await this.call("bridge.ping");
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Call a method on the bridge server.
   */
  async call<TResult = unknown>(
    method: string,
    params?: Record<string, unknown>,
    callOptions: CallOptions = {}
  ): Promise<JSONRPCResponse<TResult>> {
    return new Promise((resolve, reject) => {
      if (!this.process || !this.process.stdin) {
        reject(new Error("Bridge process not started"));
        return;
      }

      const id = this.resolveRequestId(callOptions.requestId);
      if (this.pendingRequests.has(id)) {
        reject(new Error(`Request ID already in use: ${String(id)}`));
        return;
      }

      const timeoutInfo = this.resolveTimeoutForMethod(method, callOptions.timeoutMs);
      const startedAt = Date.now();

      const request: JSONRPCRequest = {
        jsonrpc: "2.0",
        method,
        id,
        params,
      };

      const timeout = setTimeout(() => {
        const elapsedMs = Date.now() - startedAt;
        this.sendCancellationNotification(id);
        this.rejectPendingRequest(
          id,
          new BridgeTimeoutError({
            requestId: id,
            method,
            category: timeoutInfo.category,
            timeoutMs: timeoutInfo.timeoutMs,
            elapsedMs,
          })
        );
      }, timeoutInfo.timeoutMs);

      if (callOptions.signal?.aborted) {
        clearTimeout(timeout);
        reject(
          new BridgeCancellationError({
            requestId: id,
            method,
            reason: `Request cancelled before dispatch: ${method}`,
          })
        );
        return;
      }

      let removeAbortListener: (() => void) | undefined;
      if (callOptions.signal) {
        const onAbort = () => {
          this.cancelRequest(id, `Request cancelled by abort signal for method: ${method}`);
        };
        callOptions.signal.addEventListener("abort", onAbort, { once: true });
        removeAbortListener = () => {
          callOptions.signal?.removeEventListener("abort", onAbort);
        };
      }

      this.pendingRequests.set(id, {
        resolve: resolve as (value: unknown) => void,
        reject,
        timeout,
        method,
        startedAt,
        timeoutMs: timeoutInfo.timeoutMs,
        category: timeoutInfo.category,
        onAbort: removeAbortListener,
      });

      const message = this.encodeMessage(request);
      try {
        this.process.stdin.write(message);
      } catch (error) {
        this.rejectPendingRequest(
          id,
          new Error(`Failed to send request ${String(id)} (${method}): ${(error as Error).message}`)
        );
      }
    });
  }

  cancelRequest(requestId: string | number, reason?: string): boolean {
    const pending = this.pendingRequests.get(requestId);
    if (!pending) {
      return false;
    }

    this.sendCancellationNotification(requestId);
    this.rejectPendingRequest(
      requestId,
      new BridgeCancellationError({
        requestId,
        method: pending.method,
        reason: reason || `Request cancelled for method: ${pending.method}`,
      })
    );
    return true;
  }

  /**
   * Send a notification (no response expected).
   */
  notify(method: string, params?: Record<string, unknown>): void {
    if (!this.process || !this.process.stdin) {
      throw new Error("Bridge process not started");
    }

    const request: JSONRPCRequest = {
      jsonrpc: "2.0",
      method,
      params,
    };

    const message = this.encodeMessage(request);
    this.process.stdin.write(message);
  }

  /**
   * Handle incoming data from stdout.
   */
  private handleData(data: Buffer): void {
    this.buffer = Buffer.concat([this.buffer, data]);
    this.processBuffer();
  }

  /**
   * Process buffered data for complete messages.
   */
  private processBuffer(): void {
    while (this.buffer.length > 0) {
      const message = this.decodeMessage();
      if (!message) {
        break;
      }
      this.handleMessage(message);
    }
  }

  /**
   * Decode a single message from the buffer.
   */
  private decodeMessage(): JSONRPCResponse | null {
    const headerEnd = this.buffer.indexOf(HEADER_TERMINATOR);
    if (headerEnd === -1) {
      return null;
    }

    const header = this.buffer.subarray(0, headerEnd).toString("ascii");
    const contentLengthMatch = header.match(/content-length:\s*(\d+)/i);
    if (!contentLengthMatch) {
      throw new Error("Missing Content-Length header");
    }

    const contentLength = parseInt(contentLengthMatch[1], 10);
    const bodyStart = headerEnd + HEADER_TERMINATOR.length;
    const bodyEnd = bodyStart + contentLength;

    if (this.buffer.length < bodyEnd) {
      return null;
    }

    const body = this.buffer.subarray(bodyStart, bodyEnd).toString("utf-8");
    this.buffer = this.buffer.subarray(bodyEnd);

    return JSON.parse(body) as JSONRPCResponse;
  }

  /**
   * Handle a decoded message.
   */
  private handleMessage(message: JSONRPCResponse): void {
    const requestId = message.id;
    if (requestId == null) {
      if (this.options.debug) {
        console.warn("Received response without request ID:", message);
      }
      return;
    }

    const pending = this.pendingRequests.get(requestId);
    if (!pending) {
      if (this.options.debug) {
        console.warn("Received response for unknown request ID:", requestId);
      }
      return;
    }

    if (message.error) {
      this.rejectPendingRequest(requestId, this.mapRpcError(message.error, requestId, pending.method));
    } else {
      this.resolvePendingRequest(requestId, message);
    }
  }

  /**
   * Encode a message with Content-Length framing.
   */
  private encodeMessage(message: JSONRPCRequest): string {
    const body = JSON.stringify(message);
    return `Content-Length: ${Buffer.byteLength(body)}\r\n\r\n${body}`;
  }

  /**
   * Reject all pending requests.
   */
  private rejectAllPending(error: Error): void {
    for (const id of this.pendingRequests.keys()) {
      this.rejectPendingRequest(id, error);
    }
  }

  private resolveRequestId(requestId?: string | number): string | number {
    if (requestId !== undefined) {
      if (typeof requestId === "number" && requestId > this.requestId) {
        this.requestId = requestId;
      }
      return requestId;
    }

    this.requestId += 1;
    return this.requestId;
  }

  private resolveTimeoutForMethod(method: string, timeoutMs?: number): TimeoutResolution {
    if (typeof timeoutMs === "number") {
      return {
        timeoutMs,
        category: this.resolveMethodCategory(method),
      };
    }

    const override = this.options.methodTimeoutOverrides[method];
    if (typeof override === "number") {
      return {
        timeoutMs: override,
        category: this.resolveMethodCategory(method),
      };
    }

    const category = this.resolveMethodCategory(method);
    return {
      timeoutMs: this.options.timeoutPolicy[category],
      category,
    };
  }

  private resolveMethodCategory(method: string): MethodTimeoutCategory {
    const override = this.options.methodCategoryOverrides[method];
    if (override) {
      return override;
    }

    const lower = method.toLowerCase();
    if (
      lower.includes("render") ||
      lower.includes("image") ||
      lower.includes("screenshot") ||
      lower.includes("export") ||
      lower.includes("ray")
    ) {
      return "render";
    }

    if (
      lower.includes("analysis") ||
      lower.includes("measure") ||
      lower.includes("distance") ||
      lower.includes("select") ||
      lower.includes("list") ||
      lower.includes("info") ||
      lower.includes("state") ||
      lower.includes("query")
    ) {
      return "analysis";
    }

    return "control";
  }

  private sendCancellationNotification(requestId: string | number): void {
    try {
      this.notify(JSONRPC_CANCEL_METHOD, { id: requestId });
    } catch {
      return;
    }
  }

  private resolvePendingRequest(requestId: string | number, response: JSONRPCResponse): void {
    const pending = this.pendingRequests.get(requestId);
    if (!pending) {
      return;
    }

    this.pendingRequests.delete(requestId);
    clearTimeout(pending.timeout);
    pending.onAbort?.();
    pending.resolve(response);
  }

  private rejectPendingRequest(requestId: string | number, error: Error): void {
    const pending = this.pendingRequests.get(requestId);
    if (!pending) {
      return;
    }

    this.pendingRequests.delete(requestId);
    clearTimeout(pending.timeout);
    pending.onAbort?.();
    pending.reject(error);
  }

  private mapRpcError(error: JSONRPCError, requestId: string | number, method: string): BridgeRpcError {
    return new BridgeRpcError({
      code: error.code,
      type: this.mapJsonRpcErrorType(error.code),
      message: error.message,
      data: error.data,
      requestId,
      method,
    });
  }

  private mapJsonRpcErrorType(code: number): JsonRpcErrorType {
    switch (code) {
      case JsonRpcErrorCode.ParseError:
        return "parse_error";
      case JsonRpcErrorCode.InvalidRequest:
        return "invalid_request";
      case JsonRpcErrorCode.MethodNotFound:
        return "method_not_found";
      case JsonRpcErrorCode.InvalidParams:
        return "invalid_params";
      case JsonRpcErrorCode.InternalError:
        return "internal_error";
      default:
        if (code >= SERVER_ERROR_MIN && code <= SERVER_ERROR_MAX) {
          return "server_error";
        }
        return "unknown";
    }
  }
}

export default BridgeClient;
