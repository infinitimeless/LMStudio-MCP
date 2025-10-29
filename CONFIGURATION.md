# LMStudio-MCP Bridge Configuration

## Overview
The LMStudio-MCP Bridge now supports configurable host and port settings, allowing you to connect to LM Studio instances running on different machines or ports.

## Configuration via Environment Variables

### Available Variables

| Variable | Default | Description | Example |
|----------|---------|-------------|---------|
| `LMSTUDIO_HOST` | `localhost` | Hostname or IP address where LM Studio is running | `192.168.1.100` |
| `LMSTUDIO_PORT` | `1234` | Port number where LM Studio API is exposed | `5678` |

### Usage Examples

#### 1. Default Configuration (Local LM Studio)
If no environment variables are set, the bridge connects to `http://localhost:1234/v1`:

```bash
# No configuration needed for local default setup
python lmstudio_bridge.py
```

#### 2. Remote LM Studio Instance
Connect to LM Studio running on a different machine:

```bash
export LMSTUDIO_HOST=192.168.1.100
export LMSTUDIO_PORT=1234
python lmstudio_bridge.py
```

Or set inline:

```bash
LMSTUDIO_HOST=192.168.1.100 python lmstudio_bridge.py
```

#### 3. Custom Port (Same Machine)
Connect to LM Studio running on a non-default port:

```bash
export LMSTUDIO_PORT=5678
python lmstudio_bridge.py
```

#### 4. Both Custom Host and Port
Full custom configuration:

```bash
export LMSTUDIO_HOST=10.0.0.50
export LMSTUDIO_PORT=8080
python lmstudio_bridge.py
```

## MCP Configuration

When configuring the bridge as an MCP server in your `.mcp.json`, you can pass environment variables:

```json
{
  "mcpServers": {
    "lmstudio-bridge": {
      "command": "python",
      "args": ["/path/to/lmstudio_bridge.py"],
      "env": {
        "LMSTUDIO_HOST": "192.168.1.100",
        "LMSTUDIO_PORT": "5678"
      }
    }
  }
}
```

## Use Cases

### 1. Development Team Sharing
Multiple developers can connect to a shared LM Studio instance running on a powerful server:

```bash
# Developer workstation
export LMSTUDIO_HOST=ml-server.company.com
export LMSTUDIO_PORT=1234
```

### 2. Container Deployment
When running LM Studio in Docker with port mapping:

```bash
# LM Studio in Docker exposed on host port 8080
docker run -p 8080:1234 lmstudio/server
```

```bash
# Bridge configuration
export LMSTUDIO_PORT=8080
```

### 3. Multiple LM Studio Instances
Run multiple LM Studio instances on different ports:

```bash
# Instance 1 (default models)
LMSTUDIO_PORT=1234 python lmstudio_bridge.py

# Instance 2 (experimental models)
LMSTUDIO_PORT=5678 python lmstudio_bridge.py
```

### 4. Cloud/Remote Server
Connect to LM Studio running on a cloud instance:

```bash
export LMSTUDIO_HOST=lmstudio.example.com
export LMSTUDIO_PORT=443  # If using HTTPS proxy
```

## Testing Configuration

The test suite automatically handles configuration:

```bash
# Tests default to localhost:1234
pytest tests/

# Test with custom configuration
LMSTUDIO_HOST=192.168.1.100 LMSTUDIO_PORT=5678 pytest tests/

# Run configuration-specific tests
pytest tests/test_configuration.py -v
```

## Troubleshooting

### Connection Issues

1. **Verify LM Studio is running:**
   ```bash
   curl http://{LMSTUDIO_HOST}:{LMSTUDIO_PORT}/v1/models
   ```

2. **Check firewall settings** - Ensure the port is open on the target machine

3. **Network connectivity** - Verify you can reach the host:
   ```bash
   ping {LMSTUDIO_HOST}
   ```

### Port Already in Use

If LM Studio can't start on the default port:

```bash
# Check what's using the port
lsof -i :1234  # macOS/Linux
netstat -ano | findstr :1234  # Windows

# Start LM Studio on different port and update config
export LMSTUDIO_PORT=5678
```

## Security Considerations

### Production Deployments

1. **Use HTTPS** - If exposing LM Studio over network, use a reverse proxy with TLS
2. **Firewall** - Restrict access to trusted IP ranges
3. **Authentication** - Consider adding API key authentication
4. **VPN** - Use VPN for remote access instead of exposing ports directly

### Example Secure Setup (nginx reverse proxy)

```nginx
server {
    listen 443 ssl;
    server_name lmstudio.example.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:1234;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Then configure bridge:

```bash
export LMSTUDIO_HOST=lmstudio.example.com
export LMSTUDIO_PORT=443
```

## Backwards Compatibility

The default configuration (`localhost:1234`) ensures existing deployments continue to work without any changes. Configuration is opt-in via environment variables.

## Implementation Details

The configuration is loaded at module import time:

```python
LMSTUDIO_HOST = os.getenv("LMSTUDIO_HOST", "localhost")
LMSTUDIO_PORT = os.getenv("LMSTUDIO_PORT", "1234")
LMSTUDIO_API_BASE = f"http://{LMSTUDIO_HOST}:{LMSTUDIO_PORT}/v1"
```

All endpoints use `LMSTUDIO_API_BASE` for constructing URLs:

```python
response = requests.post(f"{LMSTUDIO_API_BASE}/chat/completions", ...)
```

This ensures consistent configuration across all bridge functions.
