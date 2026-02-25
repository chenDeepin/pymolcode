import { homedir } from "os";
import { join } from "path";

export interface PyMOLCodeConfig {
  sessionDir: string;
  pluginDir: string;
  logLevel: "debug" | "info" | "warn" | "error";
  pythonPath: string;
  timeoutMs: number;
  bridgeScript: string;
}

export function createDefaultConfig(): PyMOLCodeConfig {
  return {
    sessionDir: process.env.PYMOLCODE_SESSION_DIR || join(homedir(), ".pymolcode", "sessions"),
    pluginDir: process.env.PYMOLCODE_PLUGIN_DIR || join(homedir(), ".pymolcode", "plugins"),
    logLevel: (process.env.PYMOLCODE_LOG_LEVEL as PyMOLCodeConfig["logLevel"]) || "info",
    pythonPath: process.env.PYMOLCODE_PYTHON_PATH || "python3",
    timeoutMs: parseInt(process.env.PYMOLCODE_TIMEOUT_MS || "30000", 10),
    bridgeScript: process.env.PYMOLCODE_BRIDGE_SCRIPT || "-m",
  };
}

export function loadConfig(overrides?: Partial<PyMOLCodeConfig>): PyMOLCodeConfig {
  return { ...createDefaultConfig(), ...overrides };
}

export const DEFAULT_CONFIG: PyMOLCodeConfig = createDefaultConfig();
