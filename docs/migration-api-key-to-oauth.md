# Migration Guide: API-key-only to OAuth/API-key Hybrid

> **Status: PLANNED FEATURE** - Not yet implemented

## Overview

This document describes a planned feature for credential management. The current implementation uses direct API key configuration.

## Current State

API keys are configured directly in settings:

```yaml
# ~/.config/pymolcode/config.yaml
llm:
  provider: anthropic
  model: claude-3-opus-20240229
  api_key: ${ANTHROPIC_API_KEY}
```

## Planned Architecture

### Goal

Move provider auth from raw API keys to credential references managed by an auth broker.

### Planned API

```python
# NOT YET IMPLEMENTED - This is the planned interface
from python.auth import ProviderAuthBroker  # Does not exist yet

broker = ProviderAuthBroker()
session = broker.login(
    provider="openai",
    mode="api_key",
    api_key="<key>",
    reference="openai:default",
)
```

### Planned Features

- API key storage with encryption
- OAuth flow for providers that support it
- Credential reference system
- Session management
- Token refresh

## Current Implementation

For now, use environment variables:

```bash
export ANTHROPIC_API_KEY="your-key"
export OPENAI_API_KEY="your-key"
pymolcode
```

Or in config:

```yaml
llm:
  api_key: ${ANTHROPIC_API_KEY}
```

## Timeline

This feature is planned for a future release. See the project roadmap for updates.
