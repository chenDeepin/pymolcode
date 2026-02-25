import { BridgeClient } from "../bridge-client.js";

export interface ToolParameter {
  type: "string" | "number" | "boolean" | "object" | "array";
  description?: string;
  required?: boolean;
  default?: unknown;
}

export interface ToolSchema {
  type: "object";
  properties: Record<string, ToolParameter>;
  required?: string[];
}

export interface Tool {
  name: string;
  description: string;
  parameters: ToolSchema;
  execute: (params: Record<string, unknown>, client: BridgeClient) => Promise<ToolResult>;
}

export interface ToolResult {
  ok: boolean;
  result?: unknown;
  error?: {
    code: number;
    message: string;
    data?: unknown;
  };
}

export type ToolExecutor = (params: Record<string, unknown>, client: BridgeClient) => Promise<ToolResult>;

export function createTool(
  name: string,
  description: string,
  parameters: ToolSchema,
  execute: ToolExecutor
): Tool {
  return { name, description, parameters, execute };
}

export function success(result: unknown): ToolResult {
  return { ok: true, result };
}

export function error(code: number, message: string, data?: unknown): ToolResult {
  return { ok: false, error: { code, message, data } };
}
