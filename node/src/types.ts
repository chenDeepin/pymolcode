/**
 * TypeScript type definitions for pymolcode bridge protocol.
 */

export interface JSONRPCRequest {
  jsonrpc: "2.0";
  method: string;
  id?: string | number | null;
  params?: Record<string, unknown> | unknown[];
}

export interface JSONRPCResponse<TResult = unknown> {
  jsonrpc: "2.0";
  id: string | number | null;
  result?: TResult;
  error?: JSONRPCError;
}

export interface JSONRPCError {
  code: number;
  message: string;
  data?: unknown;
}

export enum JsonRpcErrorCode {
  ParseError = -32700,
  InvalidRequest = -32600,
  MethodNotFound = -32601,
  InvalidParams = -32602,
  InternalError = -32603,
}

export type JsonRpcErrorType =
  | "parse_error"
  | "invalid_request"
  | "method_not_found"
  | "invalid_params"
  | "internal_error"
  | "server_error"
  | "unknown";

export type MethodTimeoutCategory = "control" | "analysis" | "render";

export interface MethodTimeoutPolicy {
  control: number;
  analysis: number;
  render: number;
}

export interface CallOptions {
  timeoutMs?: number;
  signal?: BridgeAbortSignal;
  requestId?: string | number;
}

export interface BridgeAbortSignal {
  aborted: boolean;
  addEventListener(type: "abort", listener: () => void, options?: { once?: boolean }): void;
  removeEventListener(type: "abort", listener: () => void): void;
}

export interface BridgeCapabilities {
  protocolVersion: string;
  capabilities: string[];
}

export interface InitializeResult {
  protocolVersion: string;
  capabilities: string[];
}

export interface LoadStructureResult {
  objectName: string;
  atomCount: number;
  loadTime: number;
}

export interface ExportImageResult {
  path: string;
  size: number;
}

export interface MeasureDistanceResult {
  distance: number;
  atom1: string;
  atom2: string;
}

export interface BridgeClientOptions {
  pythonPath?: string;
  bridgeScript?: string;
  timeout?: number;
  timeoutPolicy?: Partial<MethodTimeoutPolicy>;
  methodTimeoutOverrides?: Record<string, number>;
  methodCategoryOverrides?: Partial<Record<string, MethodTimeoutCategory>>;
  debug?: boolean;
}

export interface PendingRequest {
  resolve: (value: unknown) => void;
  reject: (error: Error) => void;
  timeout: any;
  method: string;
  startedAt: number;
  timeoutMs: number;
  category: MethodTimeoutCategory;
  onAbort?: () => void;
}
