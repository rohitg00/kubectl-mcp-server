#!/bin/bash
set -e

CHART_PATH="${1:-.}"

echo "=== Helm Chart Linting ==="
echo "Chart: $CHART_PATH"
echo ""

if [ ! -f "$CHART_PATH/Chart.yaml" ]; then
    echo "ERROR: Not a valid Helm chart directory (missing Chart.yaml)"
    exit 1
fi

CHART_NAME=$(grep '^name:' "$CHART_PATH/Chart.yaml" | awk '{print $2}')
echo "Chart Name: $CHART_NAME"
echo ""

echo "--- Step 1: Helm Lint ---"
if helm lint "$CHART_PATH"; then
    echo "✓ Helm lint passed"
else
    echo "✗ Helm lint failed"
    exit 1
fi
echo ""

echo "--- Step 2: Template Validation ---"
if helm template test-release "$CHART_PATH" > /dev/null 2>&1; then
    echo "✓ Template rendering passed"
else
    echo "✗ Template rendering failed"
    helm template test-release "$CHART_PATH"
    exit 1
fi
echo ""

echo "--- Step 3: Kubernetes Manifest Validation ---"
if command -v kubectl &> /dev/null; then
    if helm template test-release "$CHART_PATH" | kubectl apply --dry-run=client -f - > /dev/null 2>&1; then
        echo "✓ Kubernetes validation passed"
    else
        echo "⚠ Kubernetes validation failed (may be expected without cluster)"
    fi
else
    echo "⚠ kubectl not found, skipping Kubernetes validation"
fi
echo ""

echo "--- Step 4: Structure Check ---"
required_files=("Chart.yaml" "values.yaml" "templates")
for file in "${required_files[@]}"; do
    if [ -e "$CHART_PATH/$file" ]; then
        echo "✓ $file exists"
    else
        echo "✗ $file missing"
    fi
done

recommended_files=("README.md" "templates/NOTES.txt" "templates/_helpers.tpl")
for file in "${recommended_files[@]}"; do
    if [ -e "$CHART_PATH/$file" ]; then
        echo "✓ $file exists"
    else
        echo "⚠ $file recommended but missing"
    fi
done
echo ""

echo "--- Step 5: Values Schema Check ---"
if [ -f "$CHART_PATH/values.schema.json" ]; then
    echo "✓ values.schema.json exists"
    if command -v jsonschema &> /dev/null; then
        if jsonschema -i "$CHART_PATH/values.yaml" "$CHART_PATH/values.schema.json" 2>/dev/null; then
            echo "✓ Values match schema"
        else
            echo "⚠ Values may not match schema"
        fi
    fi
else
    echo "⚠ values.schema.json not found (recommended for validation)"
fi
echo ""

echo "--- Step 6: Security Check ---"
templates_dir="$CHART_PATH/templates"
if grep -r "securityContext" "$templates_dir" > /dev/null 2>&1; then
    echo "✓ Security contexts found"
else
    echo "⚠ No security contexts found (recommended)"
fi

if grep -r "resources:" "$templates_dir" > /dev/null 2>&1; then
    echo "✓ Resource limits found"
else
    echo "⚠ No resource limits found (recommended)"
fi
echo ""

echo "=== Linting Complete ==="
echo "Run 'helm template <name> $CHART_PATH' to preview rendered manifests"
