# Helm Troubleshooting Guide

Common Helm issues and resolutions.

## Installation Failures

### Error: INSTALLATION FAILED: cannot re-use a name

**Cause:** Release with same name exists (possibly failed).

**Diagnosis:**
```python
list_helm_releases(namespace)
get_helm_history(name, namespace)
```

**Resolution:**
```python
uninstall_helm_chart(name, namespace)
install_helm_chart(name, chart, namespace, values)
```

### Error: timed out waiting for condition

**Cause:** Pods not becoming ready within timeout.

**Diagnosis:**
```python
get_pods(namespace, label_selector="app.kubernetes.io/instance=<release>")
describe_pod(name, namespace)
get_events(namespace)
```

**Common Causes:**
- Image pull failure
- Insufficient resources
- Failed health checks
- Missing ConfigMaps/Secrets

**Resolution:**
```python
# Fix the issue, then upgrade
upgrade_helm_release(name, chart, namespace, values)
```

### Error: rendered manifests contain a resource that already exists

**Cause:** Resource exists outside Helm management.

**Diagnosis:**
```python
# Check if resource exists
get_deployments(namespace)  # or other resource type
```

**Resolution:**
- Delete existing resource manually
- Or use `--force` flag

## Upgrade Failures

### Error: UPGRADE FAILED: another operation in progress

**Cause:** Previous operation didn't complete cleanly.

**Diagnosis:**
```python
get_helm_history(name, namespace)
# Look for pending-* status
```

**Resolution:**
```python
# If stuck in pending-install
uninstall_helm_chart(name, namespace)
install_helm_chart(name, chart, namespace, values)

# If stuck in pending-upgrade, rollback first
rollback_helm_release(name, namespace, revision=<last-good>)
```

### Error: "spec.selector" is immutable

**Cause:** Trying to change selector labels.

**Resolution:**
- Delete deployment and reinstall
- Or use a new release name

## Rollback Issues

### Rollback doesn't restore old values

**Cause:** Values are tied to revision, not chart version.

**Diagnosis:**
```python
get_helm_values(name, namespace)
get_helm_history(name, namespace)
```

**Resolution:**
```python
rollback_helm_release(name, namespace, revision=<specific>)
```

## Chart Development Issues

### Template rendering fails

**Diagnosis:**
```python
template_helm_chart(name, chart, namespace, values)
lint_helm_chart(chart)
```

**Common Causes:**
- Syntax errors in templates
- Missing values
- Incorrect indentation in YAML

### Values not applied

**Diagnosis:**
```python
get_helm_values(name, namespace)
template_helm_chart(name, chart, namespace, values)
```

**Common Causes:**
- Wrong key path in values
- Values overridden by defaults
- Type mismatch (string vs number)

## Release Status Reference

| Status | Meaning | Action |
|--------|---------|--------|
| deployed | Success | None |
| failed | Installation/upgrade failed | Fix and retry |
| pending-install | Install in progress | Wait or cleanup |
| pending-upgrade | Upgrade in progress | Wait or rollback |
| pending-rollback | Rollback in progress | Wait |
| superseded | Old revision | None |
| uninstalling | Uninstall in progress | Wait |

## Debug Commands

```python
# Full release info
get_helm_release(name, namespace)

# All revisions
get_helm_history(name, namespace)

# Current values
get_helm_values(name, namespace)

# Rendered manifests
get_helm_manifest(name, namespace)

# Dry-run to test
template_helm_chart(name, chart, namespace, values)

# Validate chart
lint_helm_chart(chart)
```

## Best Practices to Avoid Issues

1. **Always dry-run first**
   ```python
   template_helm_chart(name, chart, namespace, values)
   ```

2. **Check history before upgrade**
   ```python
   get_helm_history(name, namespace)
   ```

3. **Use specific versions**
   ```python
   install_helm_chart(name, chart, namespace, version="1.2.3", values)
   ```

4. **Keep values in version control**
   - values-dev.yaml
   - values-prod.yaml

5. **Test rollback procedure**
   ```python
   # Know which revision to rollback to
   get_helm_history(name, namespace)
   ```
