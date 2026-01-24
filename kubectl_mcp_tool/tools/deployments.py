import logging
import subprocess
from typing import Any, Dict, List, Optional

from mcp.types import ToolAnnotations

from ..k8s_config import (
    get_apps_client,
    get_batch_client,
    get_autoscaling_client,
    get_policy_client,
    _load_config_for_context,
)

logger = logging.getLogger("mcp-server")


def _get_kubectl_context_args(context: str) -> List[str]:
    """Get kubectl context arguments if context is specified."""
    if context:
        return ["--context", context]
    return []


def register_deployment_tools(server, non_destructive: bool):
    """Register deployment and workload management tools."""

    @server.tool(
        annotations=ToolAnnotations(
            title="Get Deployments",
            readOnlyHint=True,
        ),
    )
    def get_deployments(
        namespace: Optional[str] = None,
        context: str = ""
    ) -> Dict[str, Any]:
        """Get all deployments in the specified namespace.

        Args:
            namespace: Namespace to list deployments from (all namespaces if not specified)
            context: Kubernetes context to use (uses current context if not specified)
        """
        try:
            apps = get_apps_client(context)

            if namespace:
                deployments = apps.list_namespaced_deployment(namespace)
            else:
                deployments = apps.list_deployment_for_all_namespaces()

            return {
                "success": True,
                "context": context or "current",
                "deployments": [
                    {
                        "name": d.metadata.name,
                        "namespace": d.metadata.namespace,
                        "replicas": d.spec.replicas,
                        "ready": d.status.ready_replicas or 0,
                        "available": d.status.available_replicas or 0
                    }
                    for d in deployments.items
                ]
            }
        except Exception as e:
            logger.error(f"Error getting deployments: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Create Deployment",
            destructiveHint=True,
        ),
    )
    def create_deployment(
        name: str,
        image: str,
        replicas: int,
        namespace: Optional[str] = "default",
        context: str = ""
    ) -> Dict[str, Any]:
        """Create a new deployment.

        Args:
            name: Name of the deployment
            image: Container image to deploy
            replicas: Number of replicas
            namespace: Namespace to create deployment in (default: "default")
            context: Kubernetes context to use (uses current context if not specified)
        """
        if non_destructive:
            return {"success": False, "error": "Blocked: non-destructive mode"}
        try:
            from kubernetes import client

            apps = get_apps_client(context)

            deployment = client.V1Deployment(
                metadata=client.V1ObjectMeta(name=name),
                spec=client.V1DeploymentSpec(
                    replicas=replicas,
                    selector=client.V1LabelSelector(
                        match_labels={"app": name}
                    ),
                    template=client.V1PodTemplateSpec(
                        metadata=client.V1ObjectMeta(labels={"app": name}),
                        spec=client.V1PodSpec(
                            containers=[
                                client.V1Container(
                                    name=name,
                                    image=image
                                )
                            ]
                        )
                    )
                )
            )

            apps.create_namespaced_deployment(namespace, deployment)
            return {
                "success": True,
                "context": context or "current",
                "message": f"Deployment {name} created"
            }
        except Exception as e:
            logger.error(f"Error creating deployment: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Scale Deployment",
            destructiveHint=True,
        ),
    )
    def scale_deployment(
        name: str,
        replicas: int,
        namespace: Optional[str] = "default",
        context: str = ""
    ) -> Dict[str, Any]:
        """Scale a deployment to a specified number of replicas.

        Args:
            name: Name of the deployment
            replicas: Target number of replicas
            namespace: Namespace of the deployment (default: "default")
            context: Kubernetes context to use (uses current context if not specified)
        """
        if non_destructive:
            return {"success": False, "error": "Blocked: non-destructive mode"}
        try:
            cmd = ["kubectl", "scale", "deployment", name, f"--replicas={replicas}", "-n", namespace]
            cmd.extend(_get_kubectl_context_args(context))

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                return {
                    "success": True,
                    "context": context or "current",
                    "message": f"Deployment {name} scaled to {replicas} replicas"
                }
            return {"success": False, "error": result.stderr}
        except Exception as e:
            logger.error(f"Error scaling deployment: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Restart Deployment",
            destructiveHint=True,
        ),
    )
    def restart_deployment(
        name: str,
        namespace: str = "default",
        context: str = ""
    ) -> Dict[str, Any]:
        """Restart a deployment by triggering a rolling update.

        Args:
            name: Name of the deployment
            namespace: Namespace of the deployment (default: "default")
            context: Kubernetes context to use (uses current context if not specified)
        """
        if non_destructive:
            return {"success": False, "error": "Blocked: non-destructive mode"}
        try:
            cmd = ["kubectl", "rollout", "restart", "deployment", name, "-n", namespace]
            cmd.extend(_get_kubectl_context_args(context))

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                return {
                    "success": True,
                    "context": context or "current",
                    "message": f"Deployment {name} restarted"
                }
            return {"success": False, "error": result.stderr}
        except Exception as e:
            logger.error(f"Error restarting deployment: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Get ReplicaSets",
            readOnlyHint=True,
        ),
    )
    def get_replicasets(
        namespace: Optional[str] = None,
        context: str = ""
    ) -> Dict[str, Any]:
        """Get ReplicaSets in a namespace or cluster-wide.

        Args:
            namespace: Namespace to list ReplicaSets from (all namespaces if not specified)
            context: Kubernetes context to use (uses current context if not specified)
        """
        try:
            apps = get_apps_client(context)

            if namespace:
                rs_list = apps.list_namespaced_replica_set(namespace)
            else:
                rs_list = apps.list_replica_set_for_all_namespaces()

            return {
                "success": True,
                "context": context or "current",
                "replicaSets": [
                    {
                        "name": rs.metadata.name,
                        "namespace": rs.metadata.namespace,
                        "desired": rs.spec.replicas,
                        "ready": rs.status.ready_replicas or 0,
                        "available": rs.status.available_replicas or 0,
                        "ownerReferences": [
                            {"kind": ref.kind, "name": ref.name}
                            for ref in (rs.metadata.owner_references or [])
                        ]
                    }
                    for rs in rs_list.items
                ]
            }
        except Exception as e:
            logger.error(f"Error getting ReplicaSets: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Get StatefulSets",
            readOnlyHint=True,
        ),
    )
    def get_statefulsets(
        namespace: Optional[str] = None,
        context: str = ""
    ) -> Dict[str, Any]:
        """Get StatefulSets in a namespace or cluster-wide.

        Args:
            namespace: Namespace to list StatefulSets from (all namespaces if not specified)
            context: Kubernetes context to use (uses current context if not specified)
        """
        try:
            apps = get_apps_client(context)

            if namespace:
                sts_list = apps.list_namespaced_stateful_set(namespace)
            else:
                sts_list = apps.list_stateful_set_for_all_namespaces()

            return {
                "success": True,
                "context": context or "current",
                "statefulSets": [
                    {
                        "name": sts.metadata.name,
                        "namespace": sts.metadata.namespace,
                        "replicas": sts.spec.replicas,
                        "ready": sts.status.ready_replicas or 0,
                        "currentReplicas": sts.status.current_replicas or 0,
                        "serviceName": sts.spec.service_name,
                        "updateStrategy": sts.spec.update_strategy.type if sts.spec.update_strategy else None
                    }
                    for sts in sts_list.items
                ]
            }
        except Exception as e:
            logger.error(f"Error getting StatefulSets: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Get DaemonSets",
            readOnlyHint=True,
        ),
    )
    def get_daemonsets(
        namespace: Optional[str] = None,
        context: str = ""
    ) -> Dict[str, Any]:
        """Get DaemonSets in a namespace or cluster-wide.

        Args:
            namespace: Namespace to list DaemonSets from (all namespaces if not specified)
            context: Kubernetes context to use (uses current context if not specified)
        """
        try:
            apps = get_apps_client(context)

            if namespace:
                ds_list = apps.list_namespaced_daemon_set(namespace)
            else:
                ds_list = apps.list_daemon_set_for_all_namespaces()

            return {
                "success": True,
                "context": context or "current",
                "daemonSets": [
                    {
                        "name": ds.metadata.name,
                        "namespace": ds.metadata.namespace,
                        "desired": ds.status.desired_number_scheduled,
                        "current": ds.status.current_number_scheduled,
                        "ready": ds.status.number_ready,
                        "available": ds.status.number_available or 0,
                        "nodeSelector": ds.spec.template.spec.node_selector
                    }
                    for ds in ds_list.items
                ]
            }
        except Exception as e:
            logger.error(f"Error getting DaemonSets: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Get Jobs and CronJobs",
            readOnlyHint=True,
        ),
    )
    def get_jobs(
        namespace: Optional[str] = None,
        include_cronjobs: bool = True,
        context: str = ""
    ) -> Dict[str, Any]:
        """Get Jobs and optionally CronJobs.

        Args:
            namespace: Namespace to list Jobs from (all namespaces if not specified)
            include_cronjobs: Whether to include CronJobs in the result
            context: Kubernetes context to use (uses current context if not specified)
        """
        try:
            batch = get_batch_client(context)

            if namespace:
                jobs = batch.list_namespaced_job(namespace)
            else:
                jobs = batch.list_job_for_all_namespaces()

            result = {
                "success": True,
                "context": context or "current",
                "jobs": [
                    {
                        "name": job.metadata.name,
                        "namespace": job.metadata.namespace,
                        "completions": job.spec.completions,
                        "succeeded": job.status.succeeded or 0,
                        "failed": job.status.failed or 0,
                        "active": job.status.active or 0,
                        "startTime": job.status.start_time.isoformat() if job.status.start_time else None,
                        "completionTime": job.status.completion_time.isoformat() if job.status.completion_time else None
                    }
                    for job in jobs.items
                ]
            }

            if include_cronjobs:
                if namespace:
                    cronjobs = batch.list_namespaced_cron_job(namespace)
                else:
                    cronjobs = batch.list_cron_job_for_all_namespaces()

                result["cronJobs"] = [
                    {
                        "name": cj.metadata.name,
                        "namespace": cj.metadata.namespace,
                        "schedule": cj.spec.schedule,
                        "suspend": cj.spec.suspend,
                        "lastScheduleTime": cj.status.last_schedule_time.isoformat() if cj.status.last_schedule_time else None,
                        "activeJobs": len(cj.status.active or [])
                    }
                    for cj in cronjobs.items
                ]

            return result
        except Exception as e:
            logger.error(f"Error getting Jobs: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Get HorizontalPodAutoscalers",
            readOnlyHint=True,
        ),
    )
    def get_hpa(
        namespace: Optional[str] = None,
        context: str = ""
    ) -> Dict[str, Any]:
        """Get HorizontalPodAutoscalers in a namespace or cluster-wide.

        Args:
            namespace: Namespace to list HPAs from (all namespaces if not specified)
            context: Kubernetes context to use (uses current context if not specified)
        """
        try:
            from kubernetes import client

            api_client = _load_config_for_context(context)
            autoscaling = client.AutoscalingV2Api(api_client=api_client)

            if namespace:
                hpas = autoscaling.list_namespaced_horizontal_pod_autoscaler(namespace)
            else:
                hpas = autoscaling.list_horizontal_pod_autoscaler_for_all_namespaces()

            return {
                "success": True,
                "context": context or "current",
                "hpas": [
                    {
                        "name": hpa.metadata.name,
                        "namespace": hpa.metadata.namespace,
                        "targetRef": {
                            "kind": hpa.spec.scale_target_ref.kind,
                            "name": hpa.spec.scale_target_ref.name
                        },
                        "minReplicas": hpa.spec.min_replicas,
                        "maxReplicas": hpa.spec.max_replicas,
                        "currentReplicas": hpa.status.current_replicas,
                        "desiredReplicas": hpa.status.desired_replicas
                    }
                    for hpa in hpas.items
                ]
            }
        except Exception as e:
            logger.error(f"Error getting HPAs: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Get PodDisruptionBudgets",
            readOnlyHint=True,
        ),
    )
    def get_pdb(
        namespace: Optional[str] = None,
        context: str = ""
    ) -> Dict[str, Any]:
        """Get PodDisruptionBudgets in a namespace or cluster-wide.

        Args:
            namespace: Namespace to list PDBs from (all namespaces if not specified)
            context: Kubernetes context to use (uses current context if not specified)
        """
        try:
            policy = get_policy_client(context)

            if namespace:
                pdbs = policy.list_namespaced_pod_disruption_budget(namespace)
            else:
                pdbs = policy.list_pod_disruption_budget_for_all_namespaces()

            return {
                "success": True,
                "context": context or "current",
                "pdbs": [
                    {
                        "name": pdb.metadata.name,
                        "namespace": pdb.metadata.namespace,
                        "minAvailable": str(pdb.spec.min_available) if pdb.spec.min_available else None,
                        "maxUnavailable": str(pdb.spec.max_unavailable) if pdb.spec.max_unavailable else None,
                        "currentHealthy": pdb.status.current_healthy,
                        "desiredHealthy": pdb.status.desired_healthy,
                        "disruptionsAllowed": pdb.status.disruptions_allowed,
                        "expectedPods": pdb.status.expected_pods
                    }
                    for pdb in pdbs.items
                ]
            }
        except Exception as e:
            logger.error(f"Error getting PDBs: {e}")
            return {"success": False, "error": str(e)}
