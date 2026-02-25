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
  execute: ToolExecutor;
}

export type ToolExecutor = (
  params: Record<string, unknown>,
  client: BridgeClient
) => Promise<ToolResult>;

export interface ToolResult {
  ok: boolean;
  result?: unknown;
  error?: {
    code: number;
    message: string;
    data?: unknown;
  };
}

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

const PYMOL_TOOLS: Tool[] = [
  createTool(
    "load_structure",
    "Load a molecular structure from a file (PDB, PSE, MOL2, etc.)",
    {
      type: "object",
      properties: {
        source: {
          type: "string",
          description: "Path to the structure file",
          required: true,
        },
        name: {
          type: "string",
          description: "Optional object name (defaults to filename stem)",
        },
      },
    },
    async (params: Record<string, unknown>, client: BridgeClient): Promise<ToolResult> => {
      const source = params.source as string;
      const name = (params.name as string) || undefined;
      const response = await client.call("load_structure", { source, name });
      if (response.error) {
        return error(response.error.code || -32602, response.error.message, response.error.data);
      }
      return success(response.result);
    }
  ),

  createTool(
    "set_representation",
    "Set the representation style for a selection (cartoon, stick, sphere, etc.)",
    {
      type: "object",
      properties: {
        selection: {
          type: "string",
          description: "Atom selection expression",
          required: true,
        },
        representation: {
          type: "string",
          description: "Representation style (cartoon, stick, sphere, surface, etc.)",
          required: true,
        },
        color: {
          type: "string",
          description: "Optional color name",
        },
      },
    },
    async (params: Record<string, unknown>, client: BridgeClient): Promise<ToolResult> => {
      const selection = params.selection as string;
      const representation = params.representation as string;
      const color = params.color as string | undefined;
      const response = await client.call("set_representation", {
        selection,
        representation,
        color,
      });
      if (response.error) {
        return error(response.error.code || -32602, response.error.message, response.error.data);
      }
      return success(response.result);
    }
  ),

  createTool(
    "color_object",
    "Apply color to an object or selection",
    {
      type: "object",
      properties: {
        selection: {
          type: "string",
          description: "Atom selection expression",
          required: true,
        },
        color: {
          type: "string",
          description: "Color name",
          required: true,
        },
      },
    },
    async (params: Record<string, unknown>, client: BridgeClient): Promise<ToolResult> => {
      const selection = params.selection as string;
      const color = params.color as string;
      const response = await client.call("color_object", { selection, color });
      if (response.error) {
        return error(response.error.code || -32602, response.error.message, response.error.data);
      }
      return success(response.result);
    }
  ),

  createTool(
    "screenshot",
    "Capture a screenshot of the current PyMOL view",
    {
      type: "object",
      properties: {
        filename: {
          type: "string",
          description: "Output file path (PNG)",
          required: true,
        },
        width: {
          type: "number",
          description: "Image width in pixels (default 1280)",
        },
        height: {
          type: "number",
          description: "Image height in pixels (default 720)",
        },
        ray: {
          type: "boolean",
          description: "Use ray tracing for high quality (default true)",
        },
      },
    },
    async (params: Record<string, unknown>, client: BridgeClient): Promise<ToolResult> => {
      const filename = params.filename as string;
      const width = (params.width as number) ?? 1280;
      const height = (params.height as number) ?? 720;
      const ray = (params.ray as boolean) ?? true;
      const response = await client.call("screenshot", {
        filename,
        width,
        height,
        ray,
      });
      if (response.error) {
        return error(response.error.code || -32602, response.error.message, response.error.data);
      }
      return success(response.result);
    }
  ),

  createTool(
    "zoom",
    "Zoom the camera to fit a selection",
    {
      type: "object",
      properties: {
        selection: {
          type: "string",
          description: "Atom selection to zoom to (default 'all')",
        },
        buffer: {
          type: "number",
          description: "Buffer around selection in Angstroms (default 0.0)",
        },
        complete: {
          type: "boolean",
          description: "Complete animation (default false)",
        },
      },
    },
    async (params: Record<string, unknown>, client: BridgeClient): Promise<ToolResult> => {
      const selection = (params.selection as string) ?? "all";
      const buffer = (params.buffer as number) ?? 0.0;
      const complete = (params.complete as boolean) ?? false;
      const response = await client.call("zoom", {
        selection,
        buffer,
        complete,
      });
      if (response.error) {
        return error(response.error.code || -32602, response.error.message, response.error.data);
      }
      return success(response.result);
    }
  ),

  createTool(
    "list_objects",
    "List all objects currently loaded in PyMOL",
    {
      type: "object",
      properties: {},
    },
    async (params: Record<string, unknown>, client: BridgeClient): Promise<ToolResult> => {
      const response = await client.call("list_objects", {});
      if (response.error) {
        return error(response.error.code || -32602, response.error.message, response.error.data);
      }
      return success(response.result);
    }
  ),

  createTool(
    "select_atoms",
    "Create a named atom selection",
    {
      type: "object",
      properties: {
        name: {
          type: "string",
          description: "Name for the selection",
          required: true,
        },
        selection: {
          type: "string",
          description: "Atom selection expression",
          required: true,
        },
      },
      required: ["name", "selection"],
    },
    async (params: Record<string, unknown>, client: BridgeClient): Promise<ToolResult> => {
      const name = params.name as string;
      const selection = params.selection as string;
      const response = await client.call("select_atoms", { name, selection });
      if (response.error) {
        return error(response.error.code || -32602, response.error.message, response.error.data);
      }
      return success(response.result);
    }
  ),

  createTool(
    "measure_distance",
    "Measure distance between two atoms",
    {
      type: "object",
      properties: {
        atom1: {
          type: "string",
          description: "First atom identifier (e.g., 'chain A and resi 1 and name CA')",
          required: true,
        },
        atom2: {
          type: "string",
          description: "Second atom identifier",
          required: true,
        },
      },
      required: ["atom1", "atom2"],
    },
    async (params: Record<string, unknown>, client: BridgeClient): Promise<ToolResult> => {
      const atom1 = params.atom1 as string;
      const atom2 = params.atom2 as string;
      const response = await client.call("measure_distance", { atom1, atom2 });
      if (response.error) {
        return error(response.error.code || -32602, response.error.message, response.error.data);
      }
      return success(response.result);
    }
  ),

  createTool(
    "get_scene_state",
    "Get the current scene state including view and object count",
    {
      type: "object",
      properties: {},
    },
    async (params: Record<string, unknown>, client: BridgeClient): Promise<ToolResult> => {
      const response = await client.call("get_scene_state", {});
      if (response.error) {
        return error(response.error.code || -32602, response.error.message, response.error.data);
      }
      return success(response.result);
    }
  ),

  createTool(
    "get_object_info",
    "Get information about a specific object",
    {
      type: "object",
      properties: {
        object: {
          type: "string",
          description: "Name of the object",
          required: true,
        },
      },
      required: ["object"],
    },
    async (params: Record<string, unknown>, client: BridgeClient): Promise<ToolResult> => {
      const objectName = params.object as string;
      const response = await client.call("get_object_info", { object: objectName });
      if (response.error) {
        return error(response.error.code || -32602, response.error.message, response.error.data);
      }
      return success(response.result);
    }
  ),
];

export function registerPyMOLTools(client: BridgeClient): Map<string, Tool> {
  const registry = new Map<string, Tool>();
  for (const tool of PYMOL_TOOLS) {
    registry.set(tool.name, tool);
  }
  return registry;
}

export { PYMOL_TOOLS };

