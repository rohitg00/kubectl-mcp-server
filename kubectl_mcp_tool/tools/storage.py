import logging
from typing import Any, Dict, List, Optional

from mcp.types import ToolAnnotations

from ..k8s_config import get_k8s_client, get_storage_client

logger = logging.getLogger("mcp-server")


def register_storage_tools(server, non_destructive: bool):
    """Register storage-related tools."""

    @server.tool(
        annotations=ToolAnnotations(
            title="Get Persistent Volumes",
            readOnlyHint=True,
        ),
    )
    def get_persistent_volumes(
        name: Optional[str] = None,
        context: str = ""
    ) -> Dict[str, Any]:
        """Get Persistent Volumes in the cluster.

        Args:
            name: Specific PV name to get (all PVs if not specified)
            context: Kubernetes context to use (uses current context if not specified)
        """
        try:
            v1 = get_k8s_client(context)

            if name:
                pv = v1.read_persistent_volume(name)
                pvs = [pv]
            else:
                pvs = v1.list_persistent_volume().items

            def get_pv_source(spec):
                sources = ['nfs', 'hostPath', 'gcePersistentDisk', 'awsElasticBlockStore',
                          'azureDisk', 'azureFile', 'csi', 'local', 'fc', 'iscsi']
                for source in sources:
                    source_attr = getattr(spec, source.replace('P', '_p').replace('D', '_d'), None)
                    if source_attr:
                        return {"type": source, "details": str(source_attr)[:100]}
                return {"type": "unknown"}

            return {
                "success": True,
                "context": context or "current",
                "persistentVolumes": [
                    {
                        "name": pv.metadata.name,
                        "capacity": pv.spec.capacity.get("storage") if pv.spec.capacity else None,
                        "accessModes": pv.spec.access_modes,
                        "reclaimPolicy": pv.spec.persistent_volume_reclaim_policy,
                        "status": pv.status.phase,
                        "storageClass": pv.spec.storage_class_name,
                        "claimRef": {
                            "name": pv.spec.claim_ref.name,
                            "namespace": pv.spec.claim_ref.namespace
                        } if pv.spec.claim_ref else None,
                        "source": get_pv_source(pv.spec)
                    }
                    for pv in pvs
                ]
            }
        except Exception as e:
            logger.error(f"Error getting PVs: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Get Persistent Volume Claims",
            readOnlyHint=True,
        ),
    )
    def get_pvcs(
        namespace: Optional[str] = None,
        context: str = ""
    ) -> Dict[str, Any]:
        """Get Persistent Volume Claims in a namespace or cluster-wide.

        Args:
            namespace: Namespace to list PVCs from (all namespaces if not specified)
            context: Kubernetes context to use (uses current context if not specified)
        """
        try:
            v1 = get_k8s_client(context)

            if namespace:
                pvcs = v1.list_namespaced_persistent_volume_claim(namespace)
            else:
                pvcs = v1.list_persistent_volume_claim_for_all_namespaces()

            return {
                "success": True,
                "context": context or "current",
                "pvcs": [
                    {
                        "name": pvc.metadata.name,
                        "namespace": pvc.metadata.namespace,
                        "status": pvc.status.phase,
                        "capacity": pvc.status.capacity.get("storage") if pvc.status.capacity else None,
                        "accessModes": pvc.spec.access_modes,
                        "storageClass": pvc.spec.storage_class_name,
                        "volumeName": pvc.spec.volume_name
                    }
                    for pvc in pvcs.items
                ]
            }
        except Exception as e:
            logger.error(f"Error getting PVCs: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Get Storage Classes",
            readOnlyHint=True,
        ),
    )
    def get_storage_classes(context: str = "") -> Dict[str, Any]:
        """Get Storage Classes in the cluster.

        Args:
            context: Kubernetes context to use (uses current context if not specified)
        """
        try:
            storage = get_storage_client(context)

            scs = storage.list_storage_class()

            return {
                "success": True,
                "context": context or "current",
                "storageClasses": [
                    {
                        "name": sc.metadata.name,
                        "provisioner": sc.provisioner,
                        "reclaimPolicy": sc.reclaim_policy,
                        "volumeBindingMode": sc.volume_binding_mode,
                        "allowVolumeExpansion": sc.allow_volume_expansion,
                        "default": sc.metadata.annotations.get(
                            "storageclass.kubernetes.io/is-default-class"
                        ) == "true" if sc.metadata.annotations else False
                    }
                    for sc in scs.items
                ]
            }
        except Exception as e:
            logger.error(f"Error getting Storage Classes: {e}")
            return {"success": False, "error": str(e)}
