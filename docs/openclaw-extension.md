# OpenClaw Extension for PymolCode (Optional)

> Remote AI control of PymolCode from Telegram, Discord, or web interfaces

## Overview

### What It Is

The OpenClaw extension enables **remote AI control** of your PymolCode sessions. Instead of interacting with PymolCode only through its local CLI or GUI, you can:

- Command PyMOL from **Telegram** on your phone
- Control visualizations from **Discord** channels
- Run analyses through **web interfaces**
- Let an AI assistant manage complex workflows remotely

### Who Needs It

✅ **Install the extension if you:**
- Want to control PyMOL from mobile devices (Telegram)
- Collaborate with team members via Discord who need live molecular visualizations
- Prefer AI-assisted workflows from chat interfaces
- Need to trigger analyses remotely from automation tools
- Want an always-available AI agent managing your drug discovery workflows

### Who Doesn't Need It

❌ **Skip the extension if you:**
- Only use PymolCode locally through its CLI or PyMOL GUI plugin
- Are happy with PymolCode's built-in agent capabilities
- Don't need remote control or multi-platform access
- Prefer keeping all interactions within PyMOL itself

> **Note:** PymolCode works perfectly fine as a standalone platform. This extension adds optional remote control capabilities—it's not required for normal use.

---

## Installation

### Prerequisites

Before installing the extension, ensure you have:

| Requirement | Version | How to Check |
|-------------|---------|--------------|
| OpenClaw | Latest | `openclaw --version` |
| PymolCode | 2.0+ | `pymolcode --version` |
| PyMOL | 2.5+ | `pymol --version` |
| Git | Any | `git --version` |

> **OpenClaw** must be installed and running. See [OpenClaw Installation](#openclaw-setup) below if you don't have it yet.

### Steps

#### 1. Install OpenClaw (if not already installed)

```bash
# Install OpenClaw globally
npm install -g openclaw

# Initialize OpenClaw configuration
openclaw init

# Start the OpenClaw gateway daemon
openclaw gateway start
```

Verify OpenClaw is running:
```bash
openclaw gateway status
```

#### 2. Clone OpenClaw Skills Repository

The extension uses skill files that tell OpenClaw how to interact with PymolCode:

```bash
# Navigate to OpenClaw's skills directory
cd ~/clawd/skills  # or wherever your OpenClaw workspace is

# Clone the PymolCode skills (if not already present)
git clone https://github.com/chenDeepin/pymolcode-skills.git pymolcode
```

#### 3. Configure the Connection

Create or update the skill configuration to point to your PymolCode installation:

```bash
# Edit the skill configuration
nano ~/clawd/skills/pymolcode/SKILL.md
```

Ensure the configuration includes:
```yaml
# ~/clawd/skills/pymolcode/SKILL.md
name: pymolcode
description: Remote control of PyMOL molecular visualizations
endpoint: http://localhost:9876  # PymolCode JSON-RPC endpoint
```

#### 4. Configure PymolCode to Accept Connections

Start PymolCode with the JSON-RPC server enabled:

```bash
# Start PymolCode with remote access
pymolcode serve --port 9876

# Or with the GUI
pymolcode gui --enable-rpc --port 9876
```

#### 5. Test the Connection

Verify OpenClaw can communicate with PymolCode:

```bash
# Test via OpenClaw
openclaw skill test pymolcode

# Or send a test command from Telegram/Discord:
# "Load structure 1abc in PyMOL"
```

You should see the structure load in your PymolCode session.

---

## Usage Examples

Once installed, you can control PymolCode from any OpenClaw-connected platform.

### Telegram Examples

From your Telegram chat with OpenClaw:

```
"Show me 1abc colored by chain"
```

```
"Align these two structures and highlight the differences"
```

```
"Export a publication figure of the binding site at 300 DPI"
```

### Discord Examples

In a Discord channel with OpenClaw bot:

```
@OpenClaw analyze the binding pocket of 3KYS and rank by druggability
```

```
@OpenClaw load 4HHB and show heme in sticks, protein in cartoon
```

### Complex Workflows

```
"Load structures 1abc and 2def, align them, calculate RMSD, 
and generate a comparison figure with both in the same view"
```

```
"Analyze the binding site around residue ASP102, identify 
potential water molecules, and suggest hydrogen bond networks"
```

---

## Troubleshooting

### Connection Issues

**Problem:** OpenClaw cannot connect to PymolCode

**Solutions:**
1. Verify PymolCode RPC server is running:
   ```bash
   curl http://localhost:9876/health
   ```

2. Check OpenClaw gateway status:
   ```bash
   openclaw gateway status
   ```

3. Ensure correct port—check for conflicts:
   ```bash
   lsof -i :9876
   ```

4. Restart both services:
   ```bash
   openclaw gateway restart
   pymolcode serve --port 9876
   ```

### Authentication Errors

**Problem:** "Unauthorized" or "Authentication failed"

**Solutions:**
1. Verify OAuth tokens are valid:
   ```bash
   openclaw auth status
   ```

2. Re-authenticate if needed:
   ```bash
   openclaw auth login openai
   ```

3. Check that PymolCode has matching authentication:
   ```bash
   pymolcode auth status
   ```

### Commands Not Working

**Problem:** OpenClaw receives commands but PyMOL doesn't respond

**Solutions:**
1. Check PymolCode logs for errors:
   ```bash
   pymolcode logs --tail 50
   ```

2. Verify the skill is properly loaded:
   ```bash
   openclaw skill list | grep pymolcode
   ```

3. Test with a simple command first:
   ```bash
   # From Telegram/Discord:
   "Ping pymolcode"
   ```

### Slow Response Times

**Problem:** Commands take too long to execute

**Solutions:**
1. Large structures take time—be patient for complex operations
2. Reduce visualization complexity:
   ```
   "Show as cartoon only"  # instead of sticks
   ```
3. Use headless mode for batch operations:
   ```bash
   pymolcode serve --headless --port 9876
   ```

---

## Uninstallation

If you decide the extension isn't for you, removal is straightforward:

### Remove the Skills

```bash
# Delete the PymolCode skills directory
rm -rf ~/clawd/skills/pymolcode
```

### Stop the RPC Server

```bash
# If running PymolCode serve, stop it
pkill -f "pymolcode serve"

# Or disable RPC in your PymolCode config
pymolcode config set rpc.enabled false
```

### (Optional) Uninstall OpenClaw

If you only installed OpenClaw for PymolCode:

```bash
# Stop the gateway
openclaw gateway stop

# Uninstall OpenClaw
npm uninstall -g openclaw

# Remove configuration (optional)
rm -rf ~/.openclaw
```

> **Note:** PymolCode itself remains fully functional after removing the extension. You can continue using all PymolCode features through its CLI and GUI interfaces.

---

## FAQ

### Is this extension required for PymolCode?

**No.** PymolCode is a complete standalone platform. The extension only adds optional remote control capabilities.

### Does the extension send my data to external servers?

**No.** All communication stays on your local machine. OpenClaw connects to PymolCode's local JSON-RPC endpoint. Your molecular data never leaves your system unless you explicitly configure remote access.

### Can I use this on a headless server?

**Yes.** Use `pymolcode serve --headless` to run without a display. This is ideal for remote batch processing.

### Which LLM providers are supported?

OpenClaw supports the same providers as PymolCode: OpenAI, Google Gemini, GitHub Copilot, Anthropic, and Zhipu AI. Authentication is handled through OpenClaw's auth system.

---

## See Also

- [PymolCode README](../README.md) - Main project documentation
- [API Reference](./api.md) - JSON-RPC API details
- [Headless Rendering](./headless-rendering.md) - Running without display
- [OpenClaw Documentation](https://github.com/chenDeepin/openclaw) - OpenClaw project

---

*Last Updated: 2026-02-28*
