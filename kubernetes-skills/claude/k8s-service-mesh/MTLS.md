# Istio mTLS Configuration

Mutual TLS setup and troubleshooting.

## mTLS Modes

| Mode | Behavior |
|------|----------|
| STRICT | Only accept mTLS traffic |
| PERMISSIVE | Accept both mTLS and plaintext |
| DISABLE | No mTLS |

## PeerAuthentication

### Namespace-Wide STRICT

```yaml
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: my-namespace
spec:
  mtls:
    mode: STRICT
```

### Workload-Specific

```yaml
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: my-app-mtls
  namespace: my-namespace
spec:
  selector:
    matchLabels:
      app: my-app
  mtls:
    mode: STRICT
```

### Port-Level Override

```yaml
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: my-app-mtls
spec:
  selector:
    matchLabels:
      app: my-app
  mtls:
    mode: STRICT
  portLevelMtls:
    8080:
      mode: PERMISSIVE  # Allow plaintext on this port
```

## DestinationRule for mTLS

Client-side mTLS configuration:

```yaml
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: my-app
spec:
  host: my-app.my-namespace.svc.cluster.local
  trafficPolicy:
    tls:
      mode: ISTIO_MUTUAL  # Use Istio certs
```

### TLS Modes in DestinationRule

| Mode | Description |
|------|-------------|
| DISABLE | No TLS |
| SIMPLE | TLS without client cert |
| MUTUAL | mTLS with client cert |
| ISTIO_MUTUAL | mTLS with Istio-managed certs |

## Mesh-Wide Policy

Enable STRICT mTLS for entire mesh:

```yaml
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: istio-system  # Mesh-wide
spec:
  mtls:
    mode: STRICT
```

## MCP Commands

```python
# List PeerAuthentications
istio_peerauthentications_list_tool(namespace)

# List DestinationRules
istio_destinationrules_list_tool(namespace)

# Check proxy status
istio_proxy_status_tool()

# Analyze for issues
istio_analyze_tool(namespace)
```

## Migration to STRICT mTLS

### Step 1: Inventory Non-Mesh Services

```python
istio_sidecar_status_tool(namespace)
# Identify services without sidecars
```

### Step 2: Enable PERMISSIVE (Default)

```yaml
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: my-namespace
spec:
  mtls:
    mode: PERMISSIVE
```

### Step 3: Verify All Traffic is mTLS

Monitor in Kiali or Prometheus that all traffic is encrypted.

### Step 4: Switch to STRICT

```yaml
spec:
  mtls:
    mode: STRICT
```

## Troubleshooting

### Connection Refused

**Cause:** Client not using mTLS, server requires STRICT.

**Check:**
```python
istio_peerauthentications_list_tool(namespace)
istio_sidecar_status_tool(namespace)  # Client has sidecar?
```

**Resolution:**
- Ensure client has sidecar
- Or set PERMISSIVE mode

### Certificate Errors

**Check:**
```python
istio_proxy_status_tool()
# Look for certificate sync issues
```

**Common Causes:**
- Certificate expired
- istiod not running
- Time sync issues

### Mixed mTLS Modes

**Symptoms:** Intermittent failures between services.

**Check:**
```python
istio_peerauthentications_list_tool(namespace)
istio_destinationrules_list_tool(namespace)
```

**Resolution:**
- Ensure consistent modes
- PeerAuthentication matches DestinationRule

## Best Practices

1. **Start with PERMISSIVE**
   - Enables gradual migration
   - No disruption to existing traffic

2. **Namespace-Level Policies**
   - Easier to manage than per-workload
   - Override only when necessary

3. **Audit Regularly**
   ```python
   for ns in namespaces:
       istio_peerauthentications_list_tool(ns)
   ```

4. **Monitor Certificate Expiry**
   - Istio auto-rotates certs
   - But check istiod health

5. **Test in Staging First**
   - STRICT mode can break connectivity
   - Verify all services have sidecars
