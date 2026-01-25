"""Cert-Manager toolset for kubectl-mcp-server."""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime

try:
    from fastmcp import FastMCP
    from fastmcp.tools import ToolAnnotations
except ImportError:
    from mcp.server.fastmcp import FastMCP
    from mcp.types import ToolAnnotations

from ..crd_detector import crd_exists
from .utils import run_kubectl


CERTIFICATE_CRD = "certificates.cert-manager.io"
ISSUER_CRD = "issuers.cert-manager.io"
CLUSTER_ISSUER_CRD = "clusterissuers.cert-manager.io"
CERTIFICATE_REQUEST_CRD = "certificaterequests.cert-manager.io"
ORDER_CRD = "orders.acme.cert-manager.io"
CHALLENGE_CRD = "challenges.acme.cert-manager.io"


class CertsResourceError(Exception):
    """Exception raised when fetching cert-manager resources fails."""
    pass


def _get_certs_resources(kind: str, namespace: str = "", context: str = "", label_selector: str = "") -> List[Dict]:
    """Get cert-manager resources with error handling.

    Raises:
        CertsResourceError: If kubectl command fails or output cannot be parsed
    """
    args = ["get", kind, "-o", "json"]
    if namespace:
        args.extend(["-n", namespace])
    else:
        args.append("-A")
    if label_selector:
        args.extend(["-l", label_selector])

    result = run_kubectl(args, context)
    if not result["success"]:
        error_msg = result.get("error", "Unknown error")
        raise CertsResourceError(
            f"Failed to get {kind} (namespace={namespace or 'all'}, context={context or 'current'}, "
            f"label_selector={label_selector or 'none'}): {error_msg}"
        )

    try:
        data = json.loads(result["output"])
        return data.get("items", [])
    except json.JSONDecodeError as e:
        raise CertsResourceError(
            f"Failed to parse JSON response for {kind} (namespace={namespace or 'all'}, "
            f"context={context or 'current'}): {e}"
        )


def _get_condition(conditions: List[Dict], condition_type: str) -> Optional[Dict]:
    """Get a specific condition from conditions list."""
    return next((c for c in conditions if c.get("type") == condition_type), None)


def _parse_timestamp(ts: str) -> Optional[datetime]:
    """Parse Kubernetes timestamp string."""
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception:
        return None


def certs_list(
    namespace: str = "",
    context: str = "",
    label_selector: str = ""
) -> Dict[str, Any]:
    """List cert-manager certificates with status.

    Args:
        namespace: Filter by namespace (empty for all namespaces)
        context: Kubernetes context to use (optional)
        label_selector: Label selector to filter certificates

    Returns:
        List of certificates with their status and expiry information
    """
    if not crd_exists(CERTIFICATE_CRD, context):
        return {
            "success": False,
            "error": "cert-manager is not installed (certificates.cert-manager.io CRD not found)"
        }

    try:
        resources = _get_certs_resources("certificates.cert-manager.io", namespace, context, label_selector)
    except CertsResourceError as e:
        return {"success": False, "error": str(e)}

    certs = []
    for item in resources:
        status = item.get("status", {})
        conditions = status.get("conditions", [])
        ready_cond = _get_condition(conditions, "Ready")
        spec = item.get("spec", {})

        not_after = _parse_timestamp(status.get("notAfter", ""))

        days_until_expiry = None
        if not_after:
            days_until_expiry = (not_after - datetime.now(timezone.utc)).days

        certs.append({
            "name": item["metadata"]["name"],
            "namespace": item["metadata"]["namespace"],
            "ready": ready_cond.get("status") == "True" if ready_cond else False,
            "status": ready_cond.get("reason", "Unknown") if ready_cond else "Unknown",
            "message": ready_cond.get("message", "") if ready_cond else "",
            "issuer": spec.get("issuerRef", {}).get("name", ""),
            "issuer_kind": spec.get("issuerRef", {}).get("kind", "Issuer"),
            "secret_name": spec.get("secretName", ""),
            "dns_names": spec.get("dnsNames", []),
            "common_name": spec.get("commonName", ""),
            "not_before": status.get("notBefore", ""),
            "not_after": status.get("notAfter", ""),
            "renewal_time": status.get("renewalTime", ""),
            "days_until_expiry": days_until_expiry,
            "revision": status.get("revision"),
        })

    expiring_soon = [c for c in certs if c.get("days_until_expiry") is not None and c["days_until_expiry"] < 30]

    return {
        "context": context or "current",
        "total": len(certs),
        "expiring_soon": len(expiring_soon),
        "certificates": certs,
    }


def certs_get(
    name: str,
    namespace: str,
    context: str = ""
) -> Dict[str, Any]:
    """Get detailed information about a certificate.

    Args:
        name: Name of the certificate
        namespace: Namespace of the certificate
        context: Kubernetes context to use (optional)

    Returns:
        Detailed certificate information
    """
    if not crd_exists(CERTIFICATE_CRD, context):
        return {"success": False, "error": "cert-manager is not installed"}

    args = ["get", "certificates.cert-manager.io", name, "-n", namespace, "-o", "json"]
    result = _run_kubectl(args, context)

    if result["success"]:
        try:
            data = json.loads(result["output"])
            return {
                "success": True,
                "context": context or "current",
                "certificate": data,
            }
        except json.JSONDecodeError:
            return {"success": False, "error": "Failed to parse response"}

    return {"success": False, "error": result.get("error", "Unknown error")}


def certs_issuers_list(
    namespace: str = "",
    context: str = "",
    include_cluster_issuers: bool = True
) -> Dict[str, Any]:
    """List cert-manager Issuers and ClusterIssuers.

    Args:
        namespace: Filter by namespace for Issuers (empty for all)
        context: Kubernetes context to use (optional)
        include_cluster_issuers: Include ClusterIssuers in the list

    Returns:
        List of issuers with their status
    """
    issuers = []

    if crd_exists(ISSUER_CRD, context):
        try:
            issuer_resources = _get_certs_resources("issuers.cert-manager.io", namespace, context)
        except CertsResourceError as e:
            return {"success": False, "error": str(e)}

        for item in issuer_resources:
            status = item.get("status", {})
            conditions = status.get("conditions", [])
            ready_cond = _get_condition(conditions, "Ready")
            spec = item.get("spec", {})

            issuer_type = "Unknown"
            if "acme" in spec:
                issuer_type = "ACME"
            elif "ca" in spec:
                issuer_type = "CA"
            elif "selfSigned" in spec:
                issuer_type = "SelfSigned"
            elif "vault" in spec:
                issuer_type = "Vault"
            elif "venafi" in spec:
                issuer_type = "Venafi"

            issuers.append({
                "name": item["metadata"]["name"],
                "namespace": item["metadata"]["namespace"],
                "kind": "Issuer",
                "type": issuer_type,
                "ready": ready_cond.get("status") == "True" if ready_cond else False,
                "status": ready_cond.get("reason", "Unknown") if ready_cond else "Unknown",
                "message": ready_cond.get("message", "") if ready_cond else "",
            })

    if include_cluster_issuers and crd_exists(CLUSTER_ISSUER_CRD, context):
        try:
            cluster_issuer_resources = _get_certs_resources("clusterissuers.cert-manager.io", "", context)
        except CertsResourceError as e:
            return {"success": False, "error": str(e)}

        for item in cluster_issuer_resources:
            status = item.get("status", {})
            conditions = status.get("conditions", [])
            ready_cond = _get_condition(conditions, "Ready")
            spec = item.get("spec", {})

            issuer_type = "Unknown"
            if "acme" in spec:
                issuer_type = "ACME"
            elif "ca" in spec:
                issuer_type = "CA"
            elif "selfSigned" in spec:
                issuer_type = "SelfSigned"
            elif "vault" in spec:
                issuer_type = "Vault"
            elif "venafi" in spec:
                issuer_type = "Venafi"

            issuers.append({
                "name": item["metadata"]["name"],
                "namespace": "",
                "kind": "ClusterIssuer",
                "type": issuer_type,
                "ready": ready_cond.get("status") == "True" if ready_cond else False,
                "status": ready_cond.get("reason", "Unknown") if ready_cond else "Unknown",
                "message": ready_cond.get("message", "") if ready_cond else "",
            })

    return {
        "context": context or "current",
        "total": len(issuers),
        "issuers": issuers,
    }


def certs_issuer_get(
    name: str,
    namespace: str = "",
    kind: str = "Issuer",
    context: str = ""
) -> Dict[str, Any]:
    """Get detailed information about an Issuer or ClusterIssuer.

    Args:
        name: Name of the issuer
        namespace: Namespace (only for Issuer, not ClusterIssuer)
        kind: Issuer or ClusterIssuer
        context: Kubernetes context to use (optional)

    Returns:
        Detailed issuer information
    """
    if kind.lower() == "clusterissuer":
        crd = "clusterissuers.cert-manager.io"
        args = ["get", crd, name, "-o", "json"]
    else:
        # Issuers are namespaced resources, namespace is required
        if not namespace or not namespace.strip():
            return {"success": False, "error": "namespace is required for Issuer lookups"}
        crd = "issuers.cert-manager.io"
        args = ["get", crd, name, "-n", namespace, "-o", "json"]

    if not crd_exists(crd, context):
        return {"success": False, "error": f"{crd} not found"}

    result = _run_kubectl(args, context)

    if result["success"]:
        try:
            data = json.loads(result["output"])
            return {
                "success": True,
                "context": context or "current",
                "issuer": data,
            }
        except json.JSONDecodeError:
            return {"success": False, "error": "Failed to parse response"}

    return {"success": False, "error": result.get("error", "Unknown error")}


def certs_renew(
    name: str,
    namespace: str,
    context: str = ""
) -> Dict[str, Any]:
    """Trigger certificate renewal by adding renew annotation.

    Args:
        name: Name of the certificate
        namespace: Namespace of the certificate
        context: Kubernetes context to use (optional)

    Returns:
        Renewal trigger result
    """
    if not crd_exists(CERTIFICATE_CRD, context):
        return {"success": False, "error": "cert-manager is not installed"}

    cmctl_available = False
    try:
        check = subprocess.run(["cmctl", "version"], capture_output=True, timeout=5)
        cmctl_available = check.returncode == 0
    except Exception:
        pass

    if cmctl_available:
        cmd = ["cmctl", "renew", name, "-n", namespace]
        if context:
            cmd.extend(["--context", context])
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                return {
                    "success": True,
                    "context": context or "current",
                    "message": f"Triggered renewal for certificate {name} using cmctl",
                    "output": result.stdout,
                }
        except Exception:
            pass

    # Fallback: Delete the certificate's secret to trigger cert-manager to reissue
    # This is the recommended way to trigger renewal without cmctl
    # First, get the secret name from the certificate spec
    get_args = [
        "get", "certificates.cert-manager.io", name,
        "-n", namespace,
        "-o", "jsonpath={.spec.secretName}"
    ]
    secret_result = _run_kubectl(get_args, context)

    if not secret_result["success"]:
        return {"success": False, "error": f"Failed to get certificate: {secret_result.get('error', 'Unknown error')}"}

    secret_name = secret_result.get("output", "").strip()
    if not secret_name:
        return {"success": False, "error": "Certificate does not have a secretName configured"}

    # Delete the secret to trigger renewal
    delete_args = ["delete", "secret", secret_name, "-n", namespace, "--ignore-not-found"]
    result = _run_kubectl(delete_args, context)

    if result["success"]:
        return {
            "success": True,
            "context": context or "current",
            "message": f"Deleted secret '{secret_name}' to trigger renewal for certificate {name}",
            "note": "cert-manager will automatically reissue the certificate",
        }

    return {"success": False, "error": result.get("error", "Failed to trigger renewal")}


def certs_status_explain(
    name: str,
    namespace: str,
    context: str = ""
) -> Dict[str, Any]:
    """Explain certificate status with diagnosis and recommendations.

    Args:
        name: Name of the certificate
        namespace: Namespace of the certificate
        context: Kubernetes context to use (optional)

    Returns:
        Status explanation with diagnosis and recommendations
    """
    cert_result = certs_get(name, namespace, context)
    if not cert_result.get("success"):
        return cert_result

    cert = cert_result["certificate"]
    status = cert.get("status", {})
    spec = cert.get("spec", {})
    conditions = status.get("conditions", [])

    diagnosis = []
    recommendations = []

    ready_cond = _get_condition(conditions, "Ready")
    issuing_cond = _get_condition(conditions, "Issuing")

    if ready_cond:
        if ready_cond.get("status") != "True":
            diagnosis.append(f"Certificate not ready: {ready_cond.get('message', 'Unknown reason')}")

            reason = ready_cond.get("reason", "")
            if "Pending" in reason:
                recommendations.append("Check if the Issuer is ready and properly configured")
                recommendations.append("Verify DNS records are correctly configured for ACME challenges")
            elif "Failed" in reason:
                recommendations.append("Check certificate request logs for detailed error")
                recommendations.append("Verify Issuer credentials and permissions")

    if issuing_cond and issuing_cond.get("status") == "True":
        diagnosis.append("Certificate is currently being issued")
        recommendations.append("Wait for issuance to complete")

    issuer_ref = spec.get("issuerRef", {})
    issuer_name = issuer_ref.get("name", "")
    issuer_kind = issuer_ref.get("kind", "Issuer")

    if issuer_name:
        if issuer_kind == "ClusterIssuer":
            issuer_result = certs_issuer_get(issuer_name, "", "ClusterIssuer", context)
        else:
            issuer_result = certs_issuer_get(issuer_name, namespace, "Issuer", context)

        if not issuer_result.get("success"):
            diagnosis.append(f"Referenced {issuer_kind} '{issuer_name}' not found")
            recommendations.append(f"Create the {issuer_kind} or update the certificate to reference an existing one")
        else:
            issuer = issuer_result["issuer"]
            issuer_conditions = issuer.get("status", {}).get("conditions", [])
            issuer_ready = _get_condition(issuer_conditions, "Ready")
            if issuer_ready and issuer_ready.get("status") != "True":
                diagnosis.append(f"{issuer_kind} '{issuer_name}' is not ready: {issuer_ready.get('message', '')}")
                recommendations.append(f"Fix the {issuer_kind} configuration before the certificate can be issued")

    not_after = _parse_timestamp(status.get("notAfter", ""))
    if not_after:
        days_left = (not_after - datetime.now(timezone.utc)).days
        if days_left < 0:
            diagnosis.append("Certificate has EXPIRED!")
            recommendations.append("Trigger immediate renewal or check why auto-renewal failed")
        elif days_left < 7:
            diagnosis.append(f"Certificate expires in {days_left} days - CRITICAL")
            recommendations.append("Check if auto-renewal is configured and working")
        elif days_left < 30:
            diagnosis.append(f"Certificate expires in {days_left} days")

    return {
        "success": True,
        "context": context or "current",
        "name": name,
        "namespace": namespace,
        "ready": ready_cond.get("status") == "True" if ready_cond else False,
        "status": ready_cond.get("reason", "Unknown") if ready_cond else "Unknown",
        "message": ready_cond.get("message", "") if ready_cond else "",
        "diagnosis": diagnosis,
        "recommendations": recommendations,
        "issuer": {
            "name": issuer_name,
            "kind": issuer_kind,
        },
        "expiry": {
            "not_after": status.get("notAfter", ""),
            "days_remaining": (not_after - datetime.now(timezone.utc)).days if not_after else None,
        },
    }


def certs_challenges_list(
    namespace: str = "",
    context: str = "",
    label_selector: str = ""
) -> Dict[str, Any]:
    """List ACME challenges (for debugging certificate issuance).

    Args:
        namespace: Filter by namespace (empty for all namespaces)
        context: Kubernetes context to use (optional)
        label_selector: Label selector to filter challenges

    Returns:
        List of ACME challenges with their status
    """
    if not crd_exists(CHALLENGE_CRD, context):
        return {
            "success": False,
            "error": "ACME challenges CRD not found (challenges.acme.cert-manager.io)"
        }

    challenges = []
    for item in _get_certs_resources("challenges.acme.cert-manager.io", namespace, context, label_selector):
        status = item.get("status", {})
        spec = item.get("spec", {})

        challenges.append({
            "name": item["metadata"]["name"],
            "namespace": item["metadata"]["namespace"],
            "state": status.get("state", "Unknown"),
            "reason": status.get("reason", ""),
            "type": spec.get("type", ""),
            "token": spec.get("token", "")[:20] + "..." if spec.get("token") else "",
            "dns_name": spec.get("dnsName", ""),
            "presented": status.get("presented", False),
            "processing": status.get("processing", False),
        })

    pending = [c for c in challenges if c["state"] not in ("valid", "ready")]

    return {
        "context": context or "current",
        "total": len(challenges),
        "pending": len(pending),
        "challenges": challenges,
    }


def certs_requests_list(
    namespace: str = "",
    context: str = "",
    label_selector: str = ""
) -> Dict[str, Any]:
    """List CertificateRequests.

    Args:
        namespace: Filter by namespace (empty for all namespaces)
        context: Kubernetes context to use (optional)
        label_selector: Label selector to filter requests

    Returns:
        List of certificate requests with their status
    """
    if not crd_exists(CERTIFICATE_REQUEST_CRD, context):
        return {
            "success": False,
            "error": "CertificateRequest CRD not found"
        }

    requests = []
    for item in _get_certs_resources("certificaterequests.cert-manager.io", namespace, context, label_selector):
        status = item.get("status", {})
        conditions = status.get("conditions", [])
        ready_cond = _get_condition(conditions, "Ready")
        approved_cond = _get_condition(conditions, "Approved")
        spec = item.get("spec", {})

        requests.append({
            "name": item["metadata"]["name"],
            "namespace": item["metadata"]["namespace"],
            "ready": ready_cond.get("status") == "True" if ready_cond else False,
            "approved": approved_cond.get("status") == "True" if approved_cond else False,
            "status": ready_cond.get("reason", "Unknown") if ready_cond else "Unknown",
            "message": ready_cond.get("message", "") if ready_cond else "",
            "issuer": spec.get("issuerRef", {}).get("name", ""),
            "issuer_kind": spec.get("issuerRef", {}).get("kind", ""),
            "created": item["metadata"].get("creationTimestamp", ""),
        })

    return {
        "context": context or "current",
        "total": len(requests),
        "requests": requests,
    }


def certs_detect(context: str = "") -> Dict[str, Any]:
    """Detect if cert-manager is installed and its components.

    Args:
        context: Kubernetes context to use (optional)

    Returns:
        Detection results for cert-manager
    """
    return {
        "context": context or "current",
        "installed": crd_exists(CERTIFICATE_CRD, context),
        "crds": {
            "certificates": crd_exists(CERTIFICATE_CRD, context),
            "issuers": crd_exists(ISSUER_CRD, context),
            "clusterissuers": crd_exists(CLUSTER_ISSUER_CRD, context),
            "certificaterequests": crd_exists(CERTIFICATE_REQUEST_CRD, context),
            "orders": crd_exists(ORDER_CRD, context),
            "challenges": crd_exists(CHALLENGE_CRD, context),
        },
    }


def register_certs_tools(mcp: FastMCP, non_destructive: bool = False):
    """Register cert-manager tools with the MCP server."""

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def certs_list_tool(
        namespace: str = "",
        context: str = "",
        label_selector: str = ""
    ) -> str:
        """List cert-manager certificates with status."""
        return json.dumps(certs_list(namespace, context, label_selector), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def certs_get_tool(
        name: str,
        namespace: str,
        context: str = ""
    ) -> str:
        """Get detailed information about a certificate."""
        return json.dumps(certs_get(name, namespace, context), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def certs_issuers_list_tool(
        namespace: str = "",
        context: str = "",
        include_cluster_issuers: bool = True
    ) -> str:
        """List cert-manager Issuers and ClusterIssuers."""
        return json.dumps(certs_issuers_list(namespace, context, include_cluster_issuers), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def certs_issuer_get_tool(
        name: str,
        namespace: str = "",
        kind: str = "Issuer",
        context: str = ""
    ) -> str:
        """Get detailed information about an Issuer or ClusterIssuer."""
        return json.dumps(certs_issuer_get(name, namespace, kind, context), indent=2)

    @mcp.tool()
    def certs_renew_tool(
        name: str,
        namespace: str,
        context: str = ""
    ) -> str:
        """Trigger certificate renewal."""
        if non_destructive:
            return json.dumps({"success": False, "error": "Operation blocked: non-destructive mode"})
        return json.dumps(certs_renew(name, namespace, context), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def certs_status_explain_tool(
        name: str,
        namespace: str,
        context: str = ""
    ) -> str:
        """Explain certificate status with diagnosis and recommendations."""
        return json.dumps(certs_status_explain(name, namespace, context), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def certs_challenges_list_tool(
        namespace: str = "",
        context: str = "",
        label_selector: str = ""
    ) -> str:
        """List ACME challenges for debugging certificate issuance."""
        return json.dumps(certs_challenges_list(namespace, context, label_selector), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def certs_requests_list_tool(
        namespace: str = "",
        context: str = "",
        label_selector: str = ""
    ) -> str:
        """List CertificateRequests."""
        return json.dumps(certs_requests_list(namespace, context, label_selector), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def certs_detect_tool(context: str = "") -> str:
        """Detect if cert-manager is installed and its components."""
        return json.dumps(certs_detect(context), indent=2)
