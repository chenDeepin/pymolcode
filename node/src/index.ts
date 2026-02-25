/**
 * pymolcode Node.js bridge client.
 * 
 * Provides a client for communicating with the Python PyMOL bridge server
 * using Content-Length framed JSON-RPC over stdio.
 */

export {
  BridgeClient,
  BridgeRpcError,
  BridgeTimeoutError,
  BridgeCancellationError,
} from "./bridge-client.js";
export { JsonRpcErrorCode } from "./types.js";

export type {
  JSONRPCRequest,
  JSONRPCResponse,
  JSONRPCError,
  JsonRpcErrorType,
  MethodTimeoutCategory,
  MethodTimeoutPolicy,
  CallOptions,
  BridgeCapabilities,
  BridgeClientOptions,
  InitializeResult,
  LoadStructureResult,
  ExportImageResult,
  MeasureDistanceResult,
  PendingRequest,
} from "./types.js";

export {
  ToolParameter,
  ToolSchema,
  Tool,
  ToolExecutor,
  ToolResult,
  createTool,
  success,
  error,
  registerPyMOLTools,
  PYMOL_TOOLS,
} from "./tools/registry.js";

export { PyMOLCodeConfig, DEFAULT_CONFIG } from "./config.js";
