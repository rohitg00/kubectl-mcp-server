"""Dynamic CRD discovery and custom resource management tools.

Solves a critical gap: LLMs don't know what CRDs are installed in a cluster
or what they represent. When a user asks "show me databases in my cluster",
these tools let the LLM discover that CNPG, Percona, RDS operator CRDs exist,
understand they are database operators, and list their actual instances.

Tools:
    discover_crds       - Scan cluster CRDs with semantic categorization
    search_crds         - Natural language CRD search ("databases", "monitoring")
    list_custom_resources - List instances of any custom resource type
    get_custom_resource  - Get full details of a specific CR instance
    describe_crd        - Show CRD schema and field documentation
"""

import logging
from typing import Any, Dict, List, Optional

from mcp.types import ToolAnnotations

from kubectl_mcp_tool.k8s_config import (
    get_apiextensions_client,
    get_custom_objects_client,
)

logger = logging.getLogger("mcp-server")


CATEGORY_DATABASES = "databases"
CATEGORY_MESSAGING = "messaging"
CATEGORY_CERTIFICATES = "certificates"
CATEGORY_NETWORKING = "networking"
CATEGORY_SERVICE_MESH = "service_mesh"
CATEGORY_MONITORING = "monitoring"
CATEGORY_LOGGING = "logging"
CATEGORY_GITOPS = "gitops"
CATEGORY_PROGRESSIVE_DELIVERY = "progressive_delivery"
CATEGORY_AUTOSCALING = "autoscaling"
CATEGORY_STORAGE = "storage"
CATEGORY_SECURITY = "security"
CATEGORY_SECRETS = "secrets_management"
CATEGORY_VIRTUALIZATION = "virtualization"
CATEGORY_AI_ML = "ai_ml"
CATEGORY_WORKFLOWS = "workflows"
CATEGORY_CLUSTER_MGMT = "cluster_management"
CATEGORY_SERVERLESS = "serverless"
CATEGORY_DNS = "dns"
CATEGORY_CHAOS = "chaos_engineering"
CATEGORY_API_GATEWAY = "api_gateway"
CATEGORY_CONTAINER_REGISTRY = "container_registry"
CATEGORY_IDENTITY = "identity"


CRD_CATEGORIES: Dict[str, Dict[str, Any]] = {
    CATEGORY_DATABASES: {
        "description": "Database operators and managed database instances",
        "patterns": [
            "postgresql", "postgres", "cnpg", "mysql", "mariadb",
            "mongodb", "mongo", "redis", "memcached", "cassandra",
            "cockroachdb", "cockroach", "couchbase", "couchdb",
            "elasticsearch", "opensearch", "clickhouse", "timescaledb",
            "vitess", "tidb", "yugabyte", "percona", "rds",
            "database", "dbinstance", "dbcluster", "sql",
            "singlestore", "scylladb", "scylla", "foundationdb",
            "dragonfly",
        ],
        "known_crds": {
            "clusters.postgresql.cnpg.io": "CloudNativePG — deploys and manages PostgreSQL clusters with automated failover, continuous backup to S3/GCS, point-in-time recovery, and read replicas via streaming replication",
            "poolers.postgresql.cnpg.io": "CloudNativePG PgBouncer connection pooler — manages connection pooling for PostgreSQL to reduce connection overhead and improve scalability",
            "scheduledbackups.postgresql.cnpg.io": "CloudNativePG scheduled backup — configures automated periodic backups of PostgreSQL clusters to object storage (S3/GCS/Azure Blob)",
            "postgresqls.acid.zalan.do": "Zalando Postgres Operator — provisions highly-available PostgreSQL clusters with patroni-based failover, logical backups, and connection pooling",
            "perconaservermysqls.ps.percona.com": "Percona Server for MySQL — deploys MySQL instances with Percona enhancements including InnoDB improvements, audit logging, and encryption",
            "perconaxtradbclusters.pxc.percona.com": "Percona XtraDB Cluster — deploys synchronous multi-primary MySQL clusters using Galera replication for high availability and zero data loss",
            "perconapgclusters.pgv2.percona.com": "Percona PostgreSQL cluster — manages PostgreSQL with pgBackRest backups, pgBouncer pooling, and automated failover",
            "perconaservermongodbbackups.psmdb.percona.com": "Percona MongoDB backup — configures scheduled and on-demand backups for Percona MongoDB clusters to S3-compatible storage",
            "perconaservermongodbs.psmdb.percona.com": "Percona Server for MongoDB — deploys MongoDB replica sets or sharded clusters with automated failover, backups, and encryption at rest",
            "innodbclusters.mysql.oracle.com": "MySQL InnoDB Cluster — deploys MySQL Group Replication clusters with automatic failover, managed by the Oracle MySQL Operator",
            "mysqlbackups.mysql.oracle.com": "MySQL Operator backup — configures scheduled backups of MySQL InnoDB Clusters to object storage or persistent volumes",
            "mongodbs.mongodbcommunity.mongodb.com": "MongoDB Community Operator — deploys MongoDB replica sets with TLS, authentication, and automated member recovery",
            "mongodbmulticlusters.mongodb.com": "MongoDB Enterprise Multi-Cluster — manages MongoDB deployments spanning multiple Kubernetes clusters for geo-distributed databases",
            "opsmanagers.mongodb.com": "MongoDB Ops Manager — deploys the MongoDB management platform for monitoring, backup, and automation of MongoDB deployments",
            "redisfailovers.databases.spotahome.com": "Redis Failover (Spotahome) — deploys Redis with Sentinel-based automatic failover for high availability in-memory caching and data storage",
            "redisclusters.redis.redis.opstreelabs.in": "Redis Cluster (OpsTree) — deploys Redis in cluster mode with automatic sharding across multiple nodes for horizontal scalability",
            "redis.redis.redis.opstreelabs.in": "Redis standalone (OpsTree) — deploys a single Redis instance for caching, session storage, or message brokering",
            "redissentinels.redis.redis.opstreelabs.in": "Redis Sentinel (OpsTree) — deploys Redis Sentinel for monitoring Redis masters and automating failover to replicas",
            "cassandradatacenters.cassandra.datastax.com": "K8ssandra / DataStax Cassandra — deploys Apache Cassandra datacenters with Medusa backups, Reaper repairs, and Stargate APIs",
            "elasticsearches.elasticsearch.k8s.elastic.co": "Elastic Cloud on Kubernetes (ECK) — deploys Elasticsearch clusters for full-text search, log analytics, and APM with automated rolling upgrades and snapshot backups",
            "clickhouseinstallations.clickhouse.altinity.com": "Altinity ClickHouse Operator — deploys ClickHouse columnar database clusters for real-time analytics and OLAP workloads with automatic shard/replica management",
            "dbinstances.rds.services.k8s.aws": "AWS RDS Instance (ACK) — provisions and manages Amazon RDS database instances (MySQL, PostgreSQL, MariaDB, Oracle, SQL Server) from Kubernetes via AWS Controllers for Kubernetes",
            "dbclusters.rds.services.k8s.aws": "AWS RDS Aurora Cluster (ACK) — provisions Amazon Aurora MySQL/PostgreSQL clusters with multi-AZ failover and read replicas via AWS Controllers for Kubernetes",
            "dbinstances.rds.aws.crossplane.io": "AWS RDS via Crossplane — provisions Amazon RDS instances using Crossplane's infrastructure-as-code approach with drift detection and reconciliation",
            "cloudsqldatabases.sql.cnrm.cloud.google.com": "GCP Cloud SQL (Config Connector) — provisions Google Cloud SQL databases (MySQL, PostgreSQL, SQL Server) from Kubernetes using Google's Config Connector",
            "flexibleservers.dbforpostgresql.azure.com": "Azure Database for PostgreSQL Flexible Server — provisions managed PostgreSQL on Azure with zone-redundant HA and intelligent performance tuning",
            "vitessclusters.planetscale.com": "PlanetScale Vitess Cluster — deploys Vitess for horizontal scaling of MySQL with automated sharding, online DDL, and multi-cell replication",
            "tidbclusters.pingcap.com": "TiDB Cluster Operator — deploys TiDB distributed NewSQL databases with HTAP capability (OLTP + OLAP), horizontal scaling, and MySQL compatibility",
            "ybclusters.yugabyte.com": "YugabyteDB Cluster — deploys YugabyteDB distributed SQL databases with PostgreSQL compatibility, geo-partitioning, and automatic sharding",
            "cockroachdb.crdb.cockroachlabs.com": "CockroachDB Operator — deploys CockroachDB distributed SQL clusters with automatic rebalancing, geo-replication, and serializable transactions",
            "scylladatacenters.scylla.scylladb.com": "ScyllaDB Datacenter — deploys ScyllaDB (high-performance Cassandra-compatible) datacenters with shard-per-core architecture for low-latency NoSQL workloads",
            "scyllaclusters.scylla.scylladb.com": "ScyllaDB Cluster — manages multi-datacenter ScyllaDB clusters with automatic scaling and CQL-compatible API",
            "foundationdbclusters.apps.foundationdb.org": "FoundationDB Cluster — deploys FoundationDB distributed key-value stores providing ACID transactions at scale (powers Apple's iCloud infrastructure)",
        },
    },
    CATEGORY_MESSAGING: {
        "description": "Message queues, event streaming, and pub/sub systems",
        "patterns": [
            "kafka", "rabbitmq", "nats", "pulsar", "activemq",
            "strimzi", "queue", "stream", "messaging", "pubsub",
            "eventbus", "amqp", "mqtt", "emqx",
        ],
        "known_crds": {
            "kafkas.kafka.strimzi.io": "Strimzi Apache Kafka — deploys and manages Kafka clusters for high-throughput event streaming with automated broker scaling, rack awareness, and cruise control rebalancing",
            "kafkatopics.kafka.strimzi.io": "Strimzi Kafka Topic — declaratively manages Kafka topics including partitions, replication factor, and retention configuration",
            "kafkausers.kafka.strimzi.io": "Strimzi Kafka User — manages Kafka user authentication (SCRAM-SHA/TLS) and ACL-based authorization for topic access control",
            "kafkaconnects.kafka.strimzi.io": "Strimzi Kafka Connect — deploys Kafka Connect clusters for streaming data between Kafka and external systems (databases, S3, Elasticsearch)",
            "kafkabridges.kafka.strimzi.io": "Strimzi Kafka Bridge — provides HTTP/REST API access to Kafka for producing and consuming messages without native Kafka clients",
            "kafkamirrormaker2s.kafka.strimzi.io": "Strimzi MirrorMaker 2 — replicates data between Kafka clusters for disaster recovery, geo-replication, and hybrid cloud migration",
            "rabbitmqclusters.rabbitmq.com": "RabbitMQ Cluster Operator — deploys RabbitMQ message broker clusters with quorum queues, automatic peer discovery, and TLS for reliable AMQP messaging",
            "queues.rabbitmq.com": "RabbitMQ Queue — declaratively manages RabbitMQ queues with configurable durability, TTL, dead-letter routing, and queue type (classic/quorum/stream)",
            "exchanges.rabbitmq.com": "RabbitMQ Exchange — manages RabbitMQ exchanges for routing messages to queues using direct, topic, fanout, or headers-based patterns",
            "bindings.rabbitmq.com": "RabbitMQ Binding — configures routing rules between RabbitMQ exchanges and queues with binding keys for message filtering",
            "pulsarclusters.pulsar.streamnative.io": "StreamNative Pulsar — deploys Apache Pulsar clusters for multi-tenant messaging with built-in geo-replication, tiered storage, and schema registry",
            "natsaccounts.nats.io": "NATS Account — manages NATS.io accounts for multi-tenant access control in NATS high-performance cloud-native messaging systems",
        },
    },
    CATEGORY_CERTIFICATES: {
        "description": "TLS certificate management and PKI",
        "patterns": [
            "cert-manager", "certificate", "issuer", "tls", "pki",
            "acme", "letsencrypt", "certrequest",
        ],
        "known_crds": {
            "certificates.cert-manager.io": "cert-manager Certificate — automates TLS certificate provisioning and renewal from CAs (Let's Encrypt, Vault, Venafi) with automatic secret creation",
            "issuers.cert-manager.io": "cert-manager Issuer (namespace-scoped) — configures a certificate authority source for issuing TLS certificates within a single namespace",
            "clusterissuers.cert-manager.io": "cert-manager ClusterIssuer — configures a cluster-wide certificate authority source available to all namespaces for TLS certificate issuance",
            "certificaterequests.cert-manager.io": "cert-manager CertificateRequest — represents an in-flight request for a signed TLS certificate from a configured issuer",
            "orders.acme.cert-manager.io": "cert-manager ACME Order — tracks the lifecycle of an ACME certificate order with Let's Encrypt or other ACME-compliant CAs",
            "challenges.acme.cert-manager.io": "cert-manager ACME Challenge — manages HTTP-01 or DNS-01 domain validation challenges required to prove domain ownership for certificate issuance",
        },
    },
    CATEGORY_NETWORKING: {
        "description": "Ingress controllers, Gateway API, and network policies",
        "patterns": [
            "ingress", "httproute", "grpcroute", "tcproute",
            "tlsroute", "udproute", "ingressroute", "middleware",
            "traefik", "networkpolicy", "ipaddresspool", "l2advertisement",
            "bgppeer", "metallb",
        ],
        "known_crds": {
            "httproutes.gateway.networking.k8s.io": "Gateway API HTTPRoute — defines HTTP routing rules (path/header matching, traffic splitting, request mirroring) for the Kubernetes Gateway API standard",
            "grpcroutes.gateway.networking.k8s.io": "Gateway API GRPCRoute — defines gRPC-specific routing rules with method matching and header-based traffic management",
            "tcproutes.gateway.networking.k8s.io": "Gateway API TCPRoute — defines raw TCP routing for non-HTTP protocols through Gateway API load balancers",
            "tlsroutes.gateway.networking.k8s.io": "Gateway API TLSRoute — defines TLS passthrough routing based on SNI for encrypted traffic without termination",
            "gateways.gateway.networking.k8s.io": "Gateway API Gateway — defines a load balancer instance with listeners for accepting traffic on specific ports and protocols",
            "gatewayclasses.gateway.networking.k8s.io": "Gateway API GatewayClass — defines the controller implementation (Envoy, Istio, NGINX, Traefik) that provisions Gateway infrastructure",
            "referencegrants.gateway.networking.k8s.io": "Gateway API ReferenceGrant — enables cross-namespace references allowing routes in one namespace to target services in another",
            "ingressroutes.traefik.io": "Traefik IngressRoute — defines HTTP/HTTPS routing rules with middleware chains, TLS termination, and weighted load balancing for Traefik proxy",
            "ingressroutetcps.traefik.io": "Traefik TCP IngressRoute — defines raw TCP routing with SNI-based matching and TLS passthrough for Traefik proxy",
            "middlewares.traefik.io": "Traefik Middleware — configures request/response transformations (rate limiting, authentication, headers, compression, circuit breakers) in the Traefik proxy chain",
            "ipaddresspools.metallb.io": "MetalLB IP Address Pool — defines a pool of IP addresses that MetalLB can assign to LoadBalancer services in bare-metal clusters",
            "l2advertisements.metallb.io": "MetalLB L2 Advertisement — configures Layer 2 (ARP/NDP) mode for MetalLB to advertise service IPs on the local network",
            "bgppeers.metallb.io": "MetalLB BGP Peer — configures BGP peering sessions for MetalLB to advertise service IPs to upstream routers in production networks",
            "ciliumnetworkpolicies.cilium.io": "Cilium Network Policy — defines L3/L4/L7 network policies using eBPF for high-performance pod traffic filtering with DNS-aware and identity-based rules",
            "ciliumclusterwidenetworkpolicies.cilium.io": "Cilium Cluster-wide Network Policy — enforces network policies across all namespaces using Cilium's eBPF-based networking",
        },
    },
    CATEGORY_SERVICE_MESH: {
        "description": "Service mesh for traffic management, mTLS, and observability",
        "patterns": [
            "virtualservice", "destinationrule", "sidecar",
            "peerauthentication", "authorizationpolicy", "envoyfilter",
            "serviceentry", "workloadentry", "telemetry",
            "linkerd", "consul", "servicemesh", "mesh",
        ],
        "known_crds": {
            "virtualservices.networking.istio.io": "Istio VirtualService — defines traffic routing rules (canary splits, header-based routing, retries, timeouts, fault injection) for services in the mesh",
            "destinationrules.networking.istio.io": "Istio DestinationRule — configures load balancing algorithms, connection pool settings, and mTLS policies for traffic to specific service versions",
            "gateways.networking.istio.io": "Istio Gateway — configures ingress/egress load balancers at the mesh edge with TLS termination, SNI routing, and protocol selection",
            "serviceentries.networking.istio.io": "Istio ServiceEntry — registers external services (APIs, databases, legacy systems) into the mesh for traffic management and observability",
            "sidecars.networking.istio.io": "Istio Sidecar — fine-tunes Envoy proxy configuration per workload to limit scope of service discovery and reduce proxy memory usage",
            "peerauthentications.security.istio.io": "Istio PeerAuthentication — enforces mutual TLS (mTLS) between services for zero-trust network security within the mesh",
            "authorizationpolicies.security.istio.io": "Istio AuthorizationPolicy — defines L7 access control rules based on source identity, HTTP methods, paths, and headers for service-to-service authorization",
            "requestauthentications.security.istio.io": "Istio RequestAuthentication — validates JWT tokens on incoming requests and extracts claims for use in authorization policies",
            "envoyfilters.networking.istio.io": "Istio EnvoyFilter — applies custom Envoy proxy configuration patches for advanced use cases (custom filters, protocol handling, Wasm plugins)",
            "telemetries.telemetry.istio.io": "Istio Telemetry — configures metrics collection, distributed tracing, and access logging for services in the mesh",
            "servicemeshes.linkerd.io": "Linkerd service mesh — configures the Linkerd ultra-lightweight service mesh with automatic mTLS, golden metrics, and zero-config traffic management",
            "serviceprofiles.linkerd.io": "Linkerd ServiceProfile — defines per-route metrics, retries, and timeouts for fine-grained traffic management on individual HTTP routes",
            "servers.policy.linkerd.io": "Linkerd Server — defines inbound policy for a pod's ports specifying which traffic sources are allowed and what protocols are expected",
            "serverauthorizations.policy.linkerd.io": "Linkerd ServerAuthorization — grants specific client identities access to a Linkerd Server for zero-trust workload authorization",
        },
    },
    CATEGORY_MONITORING: {
        "description": "Metrics collection, alerting, and dashboards",
        "patterns": [
            "prometheus", "servicemonitor", "podmonitor",
            "alertmanager", "thanosruler", "grafana",
            "alerting", "metrics", "thanos",
            "victoriametrics",
        ],
        "known_crds": {
            "prometheuses.monitoring.coreos.com": "Prometheus Operator — deploys Prometheus time-series database instances for metrics collection, long-term storage, and PromQL-based querying",
            "servicemonitors.monitoring.coreos.com": "Prometheus ServiceMonitor — auto-discovers and configures Prometheus scrape targets for Kubernetes services based on label selectors",
            "podmonitors.monitoring.coreos.com": "Prometheus PodMonitor — auto-discovers and configures Prometheus scrape targets at the pod level for metrics collection from sidecars or non-service pods",
            "alertmanagers.monitoring.coreos.com": "Alertmanager — deploys Alertmanager instances that handle deduplication, grouping, silencing, and routing of Prometheus alerts to receivers (Slack, PagerDuty, email)",
            "alertmanagerconfigs.monitoring.coreos.com": "Alertmanager config fragment — defines per-namespace alert routing and receiver configurations that are merged into the global Alertmanager config",
            "prometheusrules.monitoring.coreos.com": "Prometheus alerting/recording rules — defines PromQL-based alerting rules (fire alerts when conditions are met) and recording rules (pre-compute expensive queries)",
            "thanosrulers.monitoring.coreos.com": "Thanos Ruler — deploys Thanos rule evaluation components for alerting and recording rules across multiple Prometheus instances with global view",
            "probes.monitoring.coreos.com": "Prometheus blackbox probe — configures blackbox monitoring to check endpoint availability, latency, and TLS certificate expiry from outside the application",
            "grafanas.grafana.integreatly.org": "Grafana Operator — deploys Grafana visualization instances with automated dashboard and datasource provisioning",
            "grafanadashboards.grafana.integreatly.org": "Grafana Dashboard — manages Grafana dashboards as Kubernetes resources for version-controlled, GitOps-friendly monitoring visualization",
            "grafanadatasources.grafana.integreatly.org": "Grafana DataSource — configures Grafana data sources (Prometheus, Loki, Tempo, Elasticsearch) as Kubernetes resources",
            "vmsingles.operator.victoriametrics.com": "VictoriaMetrics single-node — deploys a VictoriaMetrics instance for cost-effective, high-performance metrics storage as a Prometheus-compatible alternative",
            "vmclusters.operator.victoriametrics.com": "VictoriaMetrics cluster — deploys a distributed VictoriaMetrics cluster with separate storage, insert, and select components for horizontal scaling",
            "vmagents.operator.victoriametrics.com": "VictoriaMetrics Agent — deploys vmagent for scraping Prometheus-compatible targets and remote-writing metrics to VictoriaMetrics or other TSDB backends",
        },
    },
    CATEGORY_LOGGING: {
        "description": "Log collection, aggregation, and storage",
        "patterns": [
            "loki", "fluentbit", "fluentd", "logging",
            "logpipeline", "clusterlogforwarder", "clusterlogging",
            "output", "clusteroutput",
        ],
        "known_crds": {
            "lokistacks.loki.grafana.com": "Grafana Loki stack — deploys Loki for horizontally-scalable, multi-tenant log aggregation with label-based indexing and S3/GCS storage",
            "recordingrules.loki.grafana.com": "Loki recording rules — pre-computes LogQL queries into metrics for faster dashboards and reduced query load",
            "alertingrules.loki.grafana.com": "Loki alerting rules — defines LogQL-based alert conditions that fire when log patterns match (error spikes, security events)",
            "clusterloggings.logging.openshift.io": "OpenShift Cluster Logging — configures the full logging stack (collector, store, visualization) for OpenShift clusters",
            "clusterlogforwarders.logging.openshift.io": "OpenShift Log Forwarder — routes cluster logs to multiple outputs (Elasticsearch, Kafka, Loki, CloudWatch, Splunk) with filtering and transformation",
            "loggings.logging.banzaicloud.io": "Banzai Cloud Logging Operator — deploys Fluentd/Fluent Bit logging pipelines with automatic configuration based on Kubernetes metadata",
            "flows.logging.banzaicloud.io": "Banzai Cloud Logging Flow — defines namespace-scoped log routing rules with filters (grep, parser, throttle) and output destinations",
            "outputs.logging.banzaicloud.io": "Banzai Cloud Logging Output — configures namespace-scoped log destinations (S3, Elasticsearch, Kafka, Loki, Splunk, Datadog)",
            "clusterflows.logging.banzaicloud.io": "Banzai Cloud Cluster Flow — defines cluster-wide log routing rules that match pods across all namespaces",
            "clusteroutputs.logging.banzaicloud.io": "Banzai Cloud Cluster Output — configures cluster-wide log destinations available to all namespaces",
            "opentelemetrycollectors.opentelemetry.io": "OpenTelemetry Collector — deploys OTel Collector instances for receiving, processing, and exporting traces, metrics, and logs in a vendor-neutral format",
            "instrumentations.opentelemetry.io": "OpenTelemetry auto-instrumentation — injects language-specific auto-instrumentation (Java, Python, Node.js, .NET, Go) into pods for zero-code distributed tracing",
        },
    },
    CATEGORY_GITOPS: {
        "description": "GitOps controllers and continuous delivery from Git",
        "patterns": [
            "flux", "argocd", "gitops", "kustomization",
            "helmrelease", "gitrepository", "helmrepository",
            "ocirepository", "applicationset", "appproject",
        ],
        "known_crds": {
            "applications.argoproj.io": "ArgoCD Application — deploys and syncs Kubernetes resources from Git repositories, Helm charts, or Kustomize overlays with drift detection and auto-remediation",
            "applicationsets.argoproj.io": "ArgoCD ApplicationSet — generates multiple ArgoCD Applications from templates for multi-cluster, multi-tenant, and monorepo deployment patterns",
            "appprojects.argoproj.io": "ArgoCD AppProject — defines RBAC boundaries for ArgoCD Applications restricting which Git repos, clusters, and namespaces they can target",
            "kustomizations.kustomize.toolkit.fluxcd.io": "Flux Kustomization — reconciles Kubernetes manifests from Git using Kustomize overlays with health checks, dependency ordering, and variable substitution",
            "helmreleases.helm.toolkit.fluxcd.io": "Flux HelmRelease — deploys Helm charts with automated upgrades, rollback on failure, drift detection, and values from ConfigMaps/Secrets",
            "gitrepositories.source.toolkit.fluxcd.io": "Flux GitRepository — tracks a Git repository branch/tag and makes its contents available as an artifact for Kustomizations and HelmReleases",
            "helmrepositories.source.toolkit.fluxcd.io": "Flux HelmRepository — indexes a Helm chart repository (HTTP or OCI) and makes charts available for HelmRelease installations",
            "helmcharts.source.toolkit.fluxcd.io": "Flux HelmChart — fetches a specific Helm chart version from a HelmRepository and makes it available as a deployable artifact",
            "ocirepositories.source.toolkit.fluxcd.io": "Flux OCI Repository — pulls artifacts from OCI-compliant container registries (GHCR, ECR, ACR) for GitOps deployment",
            "buckets.source.toolkit.fluxcd.io": "Flux Bucket source — fetches manifests from S3-compatible or GCS object storage buckets for GitOps reconciliation",
            "receivers.notification.toolkit.fluxcd.io": "Flux webhook receiver — handles incoming webhooks (GitHub, GitLab, Harbor) to trigger immediate reconciliation instead of waiting for poll intervals",
            "alerts.notification.toolkit.fluxcd.io": "Flux alert notification — sends notifications about Flux reconciliation events (success, failure, drift) to external systems (Slack, Teams, PagerDuty)",
            "providers.notification.toolkit.fluxcd.io": "Flux notification provider — configures external notification targets (Slack, Discord, Teams, PagerDuty, generic webhook) for Flux alerts",
            "imagepolicies.image.toolkit.fluxcd.io": "Flux image update policy — defines rules for automatically updating container image tags in Git (semver ranges, alphabetical, numerical ordering)",
            "imagerepositories.image.toolkit.fluxcd.io": "Flux image repository scan — monitors container registries for new image tags and makes them available to image update automation",
        },
    },
    CATEGORY_PROGRESSIVE_DELIVERY: {
        "description": "Canary deployments, blue-green, and progressive rollouts",
        "patterns": [
            "rollout", "analysistemplate", "analysisrun",
            "experiment", "canary", "flagger",
        ],
        "known_crds": {
            "rollouts.argoproj.io": "Argo Rollouts — manages progressive deployment strategies (canary, blue-green, analysis-driven) with automated promotion and rollback based on metrics",
            "analysistemplates.argoproj.io": "Argo Rollouts AnalysisTemplate — defines metric queries (Prometheus, Datadog, Kayenta) and success criteria for automated canary analysis during rollouts",
            "clusteranalysistemplates.argoproj.io": "Argo Rollouts ClusterAnalysisTemplate — cluster-wide analysis templates reusable across namespaces for standardized canary validation criteria",
            "analysisruns.argoproj.io": "Argo Rollouts AnalysisRun — represents an in-progress or completed metric analysis that determines if a rollout should be promoted or rolled back",
            "experiments.argoproj.io": "Argo Rollouts Experiment — runs ephemeral ReplicaSets with different configurations side-by-side for A/B testing with metric comparison",
            "canaries.flagger.app": "Flagger Canary — automates canary deployments with progressive traffic shifting, metric analysis, and automated rollback for Deployments, DaemonSets, and custom resources",
            "metrictemplates.flagger.app": "Flagger MetricTemplate — defines reusable metric queries for canary analysis across multiple Canary resources with templated Prometheus/Datadog queries",
            "alertproviders.flagger.app": "Flagger AlertProvider — configures alert destinations (Slack, Teams, Discord, Rocket) for canary deployment status notifications",
        },
    },
    CATEGORY_AUTOSCALING: {
        "description": "Horizontal, vertical, and event-driven pod autoscaling",
        "patterns": [
            "scaledobject", "scaledjob", "keda", "triggerauth",
            "verticalpodautoscaler", "vpa",
        ],
        "known_crds": {
            "scaledobjects.keda.sh": "KEDA ScaledObject — enables event-driven autoscaling of Deployments/StatefulSets based on external metrics (Kafka lag, RabbitMQ queue depth, Prometheus queries, cron schedules)",
            "scaledjobs.keda.sh": "KEDA ScaledJob — creates Kubernetes Jobs in response to events (queue messages, scheduled triggers) and scales them based on event volume",
            "triggerauthentications.keda.sh": "KEDA TriggerAuthentication — stores credentials for KEDA scalers to authenticate with external event sources (MSK, SQS, Azure Event Hubs)",
            "clustertriggerauthentications.keda.sh": "KEDA ClusterTriggerAuthentication — cluster-wide authentication configuration for KEDA scalers available across all namespaces",
            "verticalpodautoscalers.autoscaling.k8s.io": "Vertical Pod Autoscaler (VPA) — automatically recommends and applies optimal CPU/memory requests for pods based on historical usage patterns",
            "verticalpodautoscalercheckpoints.autoscaling.k8s.io": "VPA checkpoint — stores VPA's learned resource usage histogram data for fast recommendation recovery after restarts",
        },
    },
    CATEGORY_STORAGE: {
        "description": "Distributed storage, backup/restore, and data protection",
        "patterns": [
            "ceph", "rook", "longhorn", "openebs",
            "volumesnapshot", "snapshot", "backup",
            "velero", "stash", "minio", "objectbucket",
            "restore", "schedule", "backupstorage",
        ],
        "known_crds": {
            "cephclusters.ceph.rook.io": "Rook Ceph Cluster — deploys Ceph distributed storage providing block, file, and object storage with automatic data replication and self-healing",
            "cephblockpools.ceph.rook.io": "Rook Ceph Block Pool — creates RBD block storage pools for persistent volumes with configurable replication factor and failure domains",
            "cephfilesystems.ceph.rook.io": "Rook CephFS — deploys a POSIX-compliant distributed filesystem for shared read-write-many access across pods",
            "cephobjectstores.ceph.rook.io": "Rook Ceph Object Store — deploys S3-compatible object storage (RGW) for applications needing bucket-based storage within the cluster",
            "volumes.longhorn.io": "Longhorn Volume — manages distributed block storage volumes with synchronous replication across nodes for high availability persistent storage",
            "replicas.longhorn.io": "Longhorn Replica — represents a replica of a Longhorn volume on a specific node for data redundancy and availability",
            "engines.longhorn.io": "Longhorn Engine — manages the iSCSI target that serves a Longhorn volume to the workload pod for read/write operations",
            "backups.velero.io": "Velero Backup — captures point-in-time snapshots of Kubernetes resources and persistent volume data for disaster recovery",
            "restores.velero.io": "Velero Restore — restores Kubernetes resources and persistent volume data from a Velero backup to recover from disasters or migrate clusters",
            "schedules.velero.io": "Velero Schedule — configures automated periodic backups with retention policies for continuous data protection",
            "backupstoragelocations.velero.io": "Velero Backup Storage Location — configures object storage targets (S3, GCS, Azure Blob, MinIO) where Velero stores backup data",
            "volumesnapshotclasses.snapshot.storage.k8s.io": "CSI VolumeSnapshotClass — defines the CSI driver and deletion policy for creating persistent volume snapshots",
            "volumesnapshots.snapshot.storage.k8s.io": "CSI VolumeSnapshot — creates a point-in-time snapshot of a persistent volume for backup or cloning purposes",
            "volumesnapshotcontents.snapshot.storage.k8s.io": "CSI VolumeSnapshot Content — represents the actual storage-level snapshot provisioned by the CSI driver",
            "objectbucketclaims.objectbucket.io": "Object Bucket Claim — requests S3-compatible object storage buckets from providers (Ceph, MinIO, NooBaa) similar to PVCs for block storage",
        },
    },
    CATEGORY_SECURITY: {
        "description": "Policy enforcement, admission control, and compliance",
        "patterns": [
            "policy", "clusterpolicy", "constraint",
            "constrainttemplate", "kyverno", "gatekeeper",
            "policyreport", "falco", "vulnerability", "scan",
            "trivy", "aqua",
        ],
        "known_crds": {
            "clusterpolicies.kyverno.io": "Kyverno ClusterPolicy — enforces cluster-wide admission policies that can validate, mutate, generate, or clean up Kubernetes resources without Rego",
            "policies.kyverno.io": "Kyverno Policy — enforces namespace-scoped admission policies for resource validation, mutation, and generation using Kyverno's declarative YAML rules",
            "policyreports.wgpolicyk8s.io": "Policy Report (wg-policy standard) — provides audit results from policy engines showing which resources pass or fail policy checks",
            "clusterpolicyreports.wgpolicyk8s.io": "Cluster Policy Report — provides cluster-wide audit results from policy engines for compliance dashboards and governance reporting",
            "constrainttemplates.templates.gatekeeper.sh": "OPA Gatekeeper ConstraintTemplate — defines reusable policy templates written in Rego that can be instantiated as admission control constraints",
            "configs.config.gatekeeper.sh": "OPA Gatekeeper Config — configures which resources Gatekeeper should sync for auditing and which namespaces to exempt from policy enforcement",
            "vulnerabilityreports.aquasecurity.github.io": "Trivy vulnerability report — stores CVE scan results for container images running in the cluster with severity ratings and fix availability",
            "configauditreports.aquasecurity.github.io": "Trivy config audit report — stores Kubernetes resource misconfigurations found by Trivy (privileged containers, missing security contexts, etc.)",
            "exposedsecretreports.aquasecurity.github.io": "Trivy exposed secret report — detects hardcoded secrets, API keys, and tokens found in container images running in the cluster",
            "sbomreports.aquasecurity.github.io": "Trivy SBOM report — stores Software Bill of Materials for container images listing all packages and dependencies for supply chain security",
            "falcorules.falcosecurity.org": "Falco runtime security rule — defines rules for detecting suspicious runtime behavior (shell spawning, file access, network activity) in containers",
        },
    },
    CATEGORY_SECRETS: {
        "description": "External secret management and secret synchronization",
        "patterns": [
            "externalsecret", "secretstore", "vault",
            "sealedsecret", "passwordpolicy", "secretproviderclass",
        ],
        "known_crds": {
            "externalsecrets.external-secrets.io": "External Secrets Operator — syncs secrets from external providers (AWS Secrets Manager, GCP Secret Manager, Azure Key Vault, HashiCorp Vault) into Kubernetes Secrets",
            "secretstores.external-secrets.io": "External Secrets SecretStore — configures namespace-scoped connection to an external secret management provider with authentication credentials",
            "clustersecretstores.external-secrets.io": "External Secrets ClusterSecretStore — configures a cluster-wide connection to an external secret provider available to all namespaces",
            "sealedsecrets.bitnami.com": "Bitnami Sealed Secrets — stores encrypted secrets that are safe to commit to Git and can only be decrypted by the Sealed Secrets controller in the cluster",
            "secretproviderclasses.secrets-store.csi.x-k8s.io": "Secrets Store CSI Driver — mounts secrets from external providers (Vault, AWS, Azure, GCP) directly as volumes in pods without creating Kubernetes Secrets",
            "vaultsecrets.secrets.hashicorp.com": "HashiCorp Vault Secrets Operator — syncs secrets from HashiCorp Vault into Kubernetes Secrets with automatic rotation and lease management",
            "vaultauths.secrets.hashicorp.com": "HashiCorp Vault Auth — configures authentication methods (Kubernetes, AppRole, JWT) for the Vault Secrets Operator to authenticate with Vault",
            "vaultconnections.secrets.hashicorp.com": "HashiCorp Vault Connection — configures the network connection (address, TLS, CA certs) to a HashiCorp Vault server for secret synchronization",
        },
    },
    CATEGORY_VIRTUALIZATION: {
        "description": "Virtual machines running on Kubernetes via KubeVirt",
        "patterns": [
            "virtualmachine", "kubevirt", "vmi",
            "datavolume", "instancetype",
        ],
        "known_crds": {
            "virtualmachines.kubevirt.io": "KubeVirt VirtualMachine — runs traditional virtual machines on Kubernetes for workloads that cannot be containerized (legacy apps, Windows, custom kernels)",
            "virtualmachineinstances.kubevirt.io": "KubeVirt VMI — represents a running VM instance with runtime state, IP address, and guest OS information",
            "virtualmachineinstancemigrations.kubevirt.io": "KubeVirt live migration — performs live migration of a running VM between nodes with zero downtime for maintenance or rebalancing",
            "virtualmachineinstancereplicasets.kubevirt.io": "KubeVirt VM ReplicaSet — manages multiple identical VM instances for stateless VM workloads similar to Kubernetes ReplicaSets",
            "virtualmachineinstancepresets.kubevirt.io": "KubeVirt VM preset — defines reusable VM configuration templates (CPU, memory, devices) applied to matching VMs at creation",
            "datavolumes.cdi.kubevirt.io": "KubeVirt DataVolume — imports virtual machine disk images from HTTP, S3, or container registries into PVCs for VM boot disks",
            "virtualmachineinstancetypes.instancetype.kubevirt.io": "KubeVirt VM instance type — defines namespace-scoped VM size profiles (vCPUs, memory, devices) similar to cloud instance types (t2.micro, n1-standard-4)",
            "virtualmachineclusterinstancetypes.instancetype.kubevirt.io": "KubeVirt cluster VM instance type — defines cluster-wide VM size profiles available to all namespaces for standardized VM sizing",
        },
    },
    CATEGORY_AI_ML: {
        "description": "ML training, model serving, notebooks, and AI pipelines",
        "patterns": [
            "notebook", "inferenceservice", "kubeflow",
            "tfjob", "pytorchjob", "mpijob", "xgboostjob",
            "training", "serving", "seldon",
            "kserve", "mlflow", "ray", "rayjob", "rayservice",
        ],
        "known_crds": {
            "inferenceservices.serving.kserve.io": "KServe InferenceService — deploys ML model serving endpoints with autoscaling, canary rollouts, model explainability, and GPU scheduling for TensorFlow/PyTorch/ONNX/XGBoost models",
            "inferencegraphs.serving.kserve.io": "KServe InferenceGraph — chains multiple models into an inference pipeline (ensemble, A/B test, sequential processing) for complex ML serving workflows",
            "trainedmodels.serving.kserve.io": "KServe TrainedModel — registers a trained model artifact from object storage for serving by an InferenceService with model versioning",
            "notebooks.kubeflow.org": "Kubeflow Notebook — deploys persistent Jupyter/VSCode/RStudio notebook servers on Kubernetes with GPU access for interactive ML development",
            "tfjobs.kubeflow.org": "Kubeflow TFJob — runs distributed TensorFlow training jobs across multiple workers, parameter servers, and evaluators on Kubernetes",
            "pytorchjobs.kubeflow.org": "Kubeflow PyTorchJob — runs distributed PyTorch training with support for elastic training, DDP, and GPU/TPU scheduling across nodes",
            "mpijobs.kubeflow.org": "Kubeflow MPIJob — runs distributed training using MPI (Message Passing Interface) for Horovod-based data-parallel training across multiple GPUs",
            "xgboostjobs.kubeflow.org": "Kubeflow XGBoostJob — runs distributed XGBoost gradient boosting training jobs with master/worker topology for large tabular datasets",
            "experiments.kubeflow.org": "Kubeflow Experiment — orchestrates hyperparameter tuning and neural architecture search using Bayesian optimization, random search, or grid search",
            "seldondeployments.machinelearning.seldon.io": "Seldon Deployment — deploys ML models with pre/post-processing pipelines, A/B testing, multi-armed bandits, and model explainability on Kubernetes",
            "rayclusters.ray.io": "KubeRay Cluster — deploys Ray distributed computing clusters for scalable ML training, hyperparameter tuning, and reinforcement learning workloads",
            "rayjobs.ray.io": "KubeRay Job — submits batch Ray jobs that automatically provision a Ray cluster, run the computation, and clean up resources on completion",
            "rayservices.ray.io": "KubeRay Service — deploys Ray Serve applications for online ML model serving with dynamic batching, model composition, and autoscaling",
        },
    },
    CATEGORY_WORKFLOWS: {
        "description": "Workflow engines, CI/CD pipelines, and job orchestration",
        "patterns": [
            "workflow", "cronworkflow", "tekton", "pipeline",
            "taskrun", "pipelinerun", "task.tekton",
        ],
        "known_crds": {
            "workflows.argoproj.io": "Argo Workflows — runs multi-step DAG/step-based workflows on Kubernetes for CI/CD, data processing, ETL, and ML pipelines with artifact passing between steps",
            "cronworkflows.argoproj.io": "Argo CronWorkflow — schedules recurring workflow executions on cron schedules for periodic data pipelines, batch jobs, and maintenance tasks",
            "workflowtemplates.argoproj.io": "Argo WorkflowTemplate — defines reusable workflow definitions that can be referenced from other workflows for DRY pipeline composition",
            "clusterworkflowtemplates.argoproj.io": "Argo ClusterWorkflowTemplate — defines cluster-wide reusable workflow templates available to all namespaces for shared pipeline logic",
            "workfloweventbindings.argoproj.io": "Argo WorkflowEventBinding — triggers workflow execution in response to external events (webhooks, NATS, Kafka messages, SNS notifications)",
            "pipelines.tekton.dev": "Tekton Pipeline — defines Kubernetes-native CI/CD pipelines as a series of tasks with dependency ordering, parallel execution, and conditional steps",
            "tasks.tekton.dev": "Tekton Task — defines a reusable unit of CI/CD work (build, test, deploy, scan) with parameterized steps running in separate containers",
            "pipelineruns.tekton.dev": "Tekton PipelineRun — represents a specific execution of a Pipeline with bound parameters, workspaces, and service accounts",
            "taskruns.tekton.dev": "Tekton TaskRun — represents a specific execution of a Task with bound inputs, outputs, and runtime configuration",
            "triggerbindings.triggers.tekton.dev": "Tekton TriggerBinding — extracts fields from incoming webhook payloads (Git push, PR events) and maps them to Pipeline/Task parameters",
            "triggertemplates.triggers.tekton.dev": "Tekton TriggerTemplate — defines the resource templates (PipelineRuns, TaskRuns) created when an event trigger fires",
            "eventlisteners.triggers.tekton.dev": "Tekton EventListener — deploys a webhook endpoint that receives events (GitHub, GitLab, Bitbucket) and triggers CI/CD pipeline executions",
        },
    },
    CATEGORY_CLUSTER_MGMT: {
        "description": "Cluster lifecycle, multi-tenancy, and infrastructure provisioning",
        "patterns": [
            "cluster.x-k8s", "machine.cluster", "machinedeployment",
            "machineset", "machinepool", "machinehealthcheck",
            "vcluster", "crossplane", "composition",
            "compositeresourcedefinition", "tenant", "karmada",
        ],
        "known_crds": {
            "clusters.cluster.x-k8s.io": "Cluster API Cluster — declaratively manages the lifecycle of Kubernetes clusters (create, upgrade, scale, delete) across any infrastructure provider",
            "machines.cluster.x-k8s.io": "Cluster API Machine — represents a single Kubernetes node with its infrastructure (VM, bare metal) and bootstrap configuration",
            "machinedeployments.cluster.x-k8s.io": "Cluster API MachineDeployment — manages rolling updates of a group of Machines similar to Kubernetes Deployments for node lifecycle management",
            "machinesets.cluster.x-k8s.io": "Cluster API MachineSet — maintains a desired number of identical Machines for a node pool similar to Kubernetes ReplicaSets",
            "machinepools.cluster.x-k8s.io": "Cluster API MachinePool — manages a pool of infrastructure-provider-managed nodes (AWS ASG, Azure VMSS) for elastic node scaling",
            "machinehealthchecks.cluster.x-k8s.io": "Cluster API MachineHealthCheck — monitors node health conditions and automatically remediates unhealthy nodes by replacing them",
            "clusterclasses.cluster.x-k8s.io": "Cluster API ClusterClass — defines reusable cluster topology templates for standardized cluster creation across an organization",
            "compositions.apiextensions.crossplane.io": "Crossplane Composition — maps a composite resource to infrastructure resources (VPC, subnet, RDS, S3) defining how cloud infrastructure is provisioned",
            "compositeresourcedefinitions.apiextensions.crossplane.io": "Crossplane XRD — defines custom platform APIs that abstract cloud infrastructure into self-service developer-facing resources",
            "providers.pkg.crossplane.io": "Crossplane Provider — installs a Crossplane provider package (AWS, GCP, Azure, Terraform) that enables provisioning of specific cloud resources",
            "configurations.pkg.crossplane.io": "Crossplane Configuration — installs reusable infrastructure compositions and XRDs as packages for platform engineering",
            "providerconfigs.aws.crossplane.io": "Crossplane AWS ProviderConfig — configures AWS credentials and region for Crossplane to provision AWS resources (EC2, RDS, S3, EKS)",
            "providerconfigs.gcp.crossplane.io": "Crossplane GCP ProviderConfig — configures GCP credentials and project for Crossplane to provision Google Cloud resources (GKE, Cloud SQL, GCS)",
            "providerconfigs.azure.crossplane.io": "Crossplane Azure ProviderConfig — configures Azure credentials and subscription for Crossplane to provision Azure resources (AKS, Azure SQL, Blob Storage)",
        },
    },
    CATEGORY_SERVERLESS: {
        "description": "Serverless platforms and function-as-a-service on Kubernetes",
        "patterns": [
            "knative", "kservice", "revision", "route.serving",
            "configuration.serving", "openfaas", "function",
            "nuclio",
        ],
        "known_crds": {
            "services.serving.knative.dev": "Knative Service — deploys serverless workloads that automatically scale from zero to N based on HTTP traffic with per-revision routing and rollback",
            "revisions.serving.knative.dev": "Knative Revision — represents an immutable snapshot of code and configuration for point-in-time rollback and traffic splitting between versions",
            "routes.serving.knative.dev": "Knative Route — defines traffic splitting rules between Knative Revisions for blue-green and canary deployment patterns",
            "configurations.serving.knative.dev": "Knative Configuration — manages the desired state of a serverless workload and creates new Revisions when the template changes",
            "brokers.eventing.knative.dev": "Knative Eventing Broker — provides an event routing hub that receives CloudEvents and delivers them to subscribers based on filter criteria",
            "triggers.eventing.knative.dev": "Knative Eventing Trigger — subscribes to a Broker and routes matching CloudEvents to a specific service or function based on attribute filters",
            "channels.messaging.knative.dev": "Knative Messaging Channel — provides a durable event delivery channel backed by Kafka, NATS, or in-memory for decoupled event-driven architectures",
            "subscriptions.messaging.knative.dev": "Knative Messaging Subscription — connects a Channel to a subscriber service with optional reply and dead-letter destinations",
            "functions.core.openfunction.io": "OpenFunction — deploys serverless functions with automatic scaling, event-driven triggers, and support for multiple runtimes (Node.js, Python, Go, Java)",
        },
    },
    CATEGORY_DNS: {
        "description": "External DNS management and DNS record automation",
        "patterns": [
            "dnsendpoint", "externaldns", "dnsrecord",
        ],
        "known_crds": {
            "dnsendpoints.externaldns.k8s.io": "ExternalDNS — automatically manages DNS records (A, CNAME, TXT) in cloud DNS providers (Route53, CloudDNS, Azure DNS) based on Kubernetes Service/Ingress resources",
            "dnsrecords.ingress.operator.openshift.io": "OpenShift DNS record — manages cloud provider DNS records for OpenShift router endpoints and load balancers",
        },
    },
    CATEGORY_CHAOS: {
        "description": "Chaos engineering and resilience testing",
        "patterns": [
            "chaos", "chaosexperiment", "chaosmesh",
            "litmus", "iochaos", "networkchaos",
            "podchaos", "stresschaos",
        ],
        "known_crds": {
            "podchaos.chaos-mesh.org": "Chaos Mesh PodChaos — injects pod-level failures (kill, restart, container fault) to test application resilience and recovery mechanisms",
            "networkchaos.chaos-mesh.org": "Chaos Mesh NetworkChaos — injects network faults (latency, packet loss, partition, bandwidth limit) to test distributed system resilience",
            "iochaos.chaos-mesh.org": "Chaos Mesh IOChaos — injects filesystem faults (latency, errors, attribute overrides) to test data path resilience and error handling",
            "stresschaos.chaos-mesh.org": "Chaos Mesh StressChaos — generates CPU/memory stress on pods to test behavior under resource pressure and validate resource limits",
            "httpchaos.chaos-mesh.org": "Chaos Mesh HTTPChaos — injects HTTP-level faults (abort, delay, response modification) to test API client resilience and circuit breakers",
            "timechaos.chaos-mesh.org": "Chaos Mesh TimeChaos — skews system clock in containers to test time-dependent logic (TTL, cron, certificate expiry, token rotation)",
            "dnschaos.chaos-mesh.org": "Chaos Mesh DNSChaos — injects DNS resolution failures and random responses to test DNS-dependent service discovery and fallback behavior",
            "schedules.chaos-mesh.org": "Chaos Mesh Schedule — runs chaos experiments on recurring schedules for continuous resilience validation in staging or production environments",
            "workflows.chaos-mesh.org": "Chaos Mesh Workflow — orchestrates multi-step chaos experiments with serial/parallel execution and conditional branching for complex failure scenarios",
            "chaosengines.litmuschaos.io": "Litmus ChaosEngine — binds chaos experiments to target applications and defines the run configuration for Litmus chaos testing",
            "chaosexperiments.litmuschaos.io": "Litmus ChaosExperiment — defines a chaos test scenario (pod delete, disk fill, network loss) from the Litmus ChaosHub experiment library",
            "chaosresults.litmuschaos.io": "Litmus ChaosResult — stores the outcome (pass/fail/error) of a chaos experiment execution with detailed probe and steady-state results",
        },
    },
    CATEGORY_API_GATEWAY: {
        "description": "API gateways, rate limiting, and API management",
        "patterns": [
            "kong", "kongplugin", "apisix", "ambassador",
            "mapping", "ratelimit", "apiproduct",
        ],
        "known_crds": {
            "kongplugins.configuration.konghq.com": "Kong Plugin — configures API gateway plugins (rate limiting, authentication, CORS, request transformation, logging) on Kong routes and services",
            "kongconsumers.configuration.konghq.com": "Kong Consumer — manages API consumers with authentication credentials (API key, OAuth, JWT, basic auth) and rate limiting tiers",
            "kongingresses.configuration.konghq.com": "Kong Ingress config — customizes Kong proxy behavior for Kubernetes Ingress resources (timeouts, protocols, upstream settings)",
            "tcpingresses.configuration.konghq.com": "Kong TCP Ingress — routes raw TCP/TLS traffic through Kong for non-HTTP protocols (databases, gRPC, MQTT)",
            "apisixroutes.apisix.apache.org": "Apache APISIX Route — defines API routing rules with URI matching, traffic splitting, and plugin chains for the APISIX API gateway",
            "apisixupstreams.apisix.apache.org": "Apache APISIX Upstream — configures backend service endpoints with load balancing, health checks, and retry policies for APISIX gateway",
            "apisixpluginconfigs.apisix.apache.org": "Apache APISIX PluginConfig — defines reusable plugin configurations (auth, rate limit, transform) shared across multiple APISIX routes",
            "hosts.getambassador.io": "Emissary-ingress Host — configures TLS termination, ACME certificate provisioning, and hostname routing for the Emissary API gateway",
            "mappings.getambassador.io": "Emissary-ingress Mapping — routes traffic from URL prefixes to backend Kubernetes services with timeout, retry, and weight configuration",
            "ratelimitservices.getambassador.io": "Emissary-ingress RateLimitService — configures rate limiting for API endpoints using an external rate limit service (Envoy ratelimit)",
        },
    },
    CATEGORY_CONTAINER_REGISTRY: {
        "description": "Container image registries and artifact management",
        "patterns": [
            "harbor", "registry", "dragonfly",
        ],
        "known_crds": {
            "harborconfigurations.goharbor.io": "Harbor configuration — manages configuration for Harbor container registry including authentication, storage, and vulnerability scanning settings",
            "harborclusters.goharbor.io": "Harbor Cluster — deploys a highly-available Harbor container registry with image scanning, replication, RBAC, and artifact signing",
            "registries.goharbor.io": "Harbor Registry — deploys the container image registry component of Harbor for storing and distributing OCI-compliant container images and Helm charts",
        },
    },
    CATEGORY_IDENTITY: {
        "description": "Identity providers, SSO, and authentication services",
        "patterns": [
            "keycloak", "dex", "oidc", "oauth2proxy",
        ],
        "known_crds": {
            "keycloaks.k8s.keycloak.org": "Keycloak — deploys Keycloak identity provider for SSO, OAuth 2.0, OIDC, SAML, social login, and user federation across applications",
            "keycloakrealmimports.k8s.keycloak.org": "Keycloak RealmImport — imports Keycloak realm configurations (clients, roles, identity providers, authentication flows) from JSON definitions",
            "dexconfigs.dex.coreos.com": "Dex OIDC Provider — configures Dex as an OpenID Connect identity provider that federates authentication from LDAP, SAML, GitHub, Google, and other upstream IdPs",
        },
    },
}


def _classify_crd(crd_name: str, group: str, kind: str) -> Dict[str, Any]:
    """Classify a CRD into semantic categories using known CRDs and pattern matching.

    Returns:
        Dict with 'categories' list and optional 'description' string.
    """
    matched_categories: List[str] = []
    description: Optional[str] = None

    crd_lower = crd_name.lower()
    group_lower = group.lower()
    kind_lower = kind.lower()
    search_text = f"{crd_lower} {group_lower} {kind_lower}"

    for category, info in CRD_CATEGORIES.items():
        known = info.get("known_crds", {})
        if crd_name in known:
            if category not in matched_categories:
                matched_categories.append(category)
            if description is None:
                description = known[crd_name]
            continue

        for pattern in info["patterns"]:
            if pattern in search_text:
                if category not in matched_categories:
                    matched_categories.append(category)
                break

    return {
        "categories": matched_categories if matched_categories else ["other"],
        "description": description,
    }


def register_custom_resource_tools(server, non_destructive: bool):
    """Register dynamic CRD discovery and custom resource tools."""

    @server.tool(
        annotations=ToolAnnotations(
            title="Discover Cluster CRDs",
            readOnlyHint=True,
        ),
    )
    def discover_crds(
        category: str = "",
        context: str = ""
    ) -> Dict[str, Any]:
        """Discover all CRDs in the cluster with semantic categorization.

        Scans the cluster for every installed CRD and categorizes them into
        human-readable groups. Use this to answer questions like:
        - "What databases are in this cluster?"
        - "Is there a service mesh installed?"
        - "What monitoring stack is running?"

        Categories: databases, messaging, certificates, networking, service_mesh,
        monitoring, logging, gitops, progressive_delivery, autoscaling, storage,
        security, secrets_management, virtualization, ai_ml, workflows,
        cluster_management, serverless, dns, chaos_engineering, api_gateway,
        container_registry, identity

        Args:
            category: Filter by category (e.g., "databases"). Empty returns all.
            context: Kubernetes context (uses current if not specified)
        """
        try:
            api = get_apiextensions_client(context)
            all_crds = api.list_custom_resource_definition()

            categorized: Dict[str, Dict[str, Any]] = {}
            uncategorized: List[Dict[str, Any]] = []
            total = 0

            for crd in all_crds.items:
                total += 1
                name = crd.metadata.name
                group = crd.spec.group
                kind = crd.spec.names.kind
                plural = crd.spec.names.plural
                scope = crd.spec.scope
                version = crd.spec.versions[0].name if crd.spec.versions else "v1"

                classification = _classify_crd(name, group, kind)
                crd_info = {
                    "name": name,
                    "group": group,
                    "version": version,
                    "kind": kind,
                    "plural": plural,
                    "scope": scope,
                    "description": classification["description"],
                }

                is_other = classification["categories"] == ["other"]

                for cat in classification["categories"]:
                    if category and cat != category:
                        continue
                    if cat == "other":
                        continue
                    if cat not in categorized:
                        cat_desc = CRD_CATEGORIES.get(cat, {}).get("description", cat)
                        categorized[cat] = {"description": cat_desc, "crds": []}
                    categorized[cat]["crds"].append(crd_info)

                if not category and is_other:
                    uncategorized.append(crd_info)

            result: Dict[str, Any] = {
                "success": True,
                "context": context or "current",
                "totalCRDs": total,
                "categories": {},
            }

            for cat_name in sorted(categorized.keys()):
                cat_data = categorized[cat_name]
                result["categories"][cat_name] = {
                    "description": cat_data["description"],
                    "count": len(cat_data["crds"]),
                    "crds": cat_data["crds"],
                }

            if not category and uncategorized:
                result["uncategorized"] = {
                    "count": len(uncategorized),
                    "crds": uncategorized[:50],
                    "truncated": len(uncategorized) > 50,
                }

            categorized_count = sum(
                len(c["crds"]) for c in categorized.values()
            )
            result["categorizedCount"] = categorized_count

            return result
        except Exception as e:
            logger.error(f"Error discovering CRDs: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Search CRDs by Keyword",
            readOnlyHint=True,
        ),
    )
    def search_crds(
        query: str,
        context: str = ""
    ) -> Dict[str, Any]:
        """Search for CRDs by keyword, category, or concept.

        Natural language search across all CRDs in the cluster. Examples:
        - "databases"    -> CNPG, MySQL, MongoDB, Redis operators
        - "certificates" -> cert-manager CRDs
        - "monitoring"   -> Prometheus, Grafana, VictoriaMetrics
        - "kafka"        -> Strimzi Kafka CRDs
        - "chaos"        -> Chaos Mesh, Litmus experiments
        - "machine learning" -> Kubeflow, KServe, Ray

        Args:
            query: Search keyword or concept
            context: Kubernetes context (uses current if not specified)
        """
        try:
            query_lower = query.lower().strip()
            query_tokens = query_lower.split()

            matching_categories: List[str] = []
            for cat_name, cat_info in CRD_CATEGORIES.items():
                if query_lower in cat_name or cat_name.replace("_", " ") in query_lower:
                    matching_categories.append(cat_name)
                    continue
                if any(tok in cat_info["description"].lower() for tok in query_tokens):
                    matching_categories.append(cat_name)
                    continue
                if any(query_lower in p or p in query_lower for p in cat_info["patterns"]):
                    matching_categories.append(cat_name)

            api = get_apiextensions_client(context)
            all_crds = api.list_custom_resource_definition()

            matches: List[Dict[str, Any]] = []
            for crd in all_crds.items:
                name = crd.metadata.name
                group = crd.spec.group
                kind = crd.spec.names.kind
                plural = crd.spec.names.plural
                version = crd.spec.versions[0].name if crd.spec.versions else "v1"

                classification = _classify_crd(name, group, kind)

                is_match = False
                if any(cat in matching_categories for cat in classification["categories"]):
                    is_match = True
                elif any(tok in name.lower() for tok in query_tokens):
                    is_match = True
                elif any(tok in kind.lower() for tok in query_tokens):
                    is_match = True
                elif any(tok in group.lower() for tok in query_tokens):
                    is_match = True

                if is_match:
                    matches.append({
                        "name": name,
                        "group": group,
                        "version": version,
                        "kind": kind,
                        "plural": plural,
                        "scope": crd.spec.scope,
                        "categories": classification["categories"],
                        "description": classification["description"],
                        "shortNames": crd.spec.names.short_names or [],
                        "listUsage": f'list_custom_resources(group="{group}", version="{version}", plural="{plural}")',
                    })

            matches.sort(key=lambda x: (0 if x["description"] else 1, x["name"]))

            return {
                "success": True,
                "context": context or "current",
                "query": query,
                "matchedCategories": matching_categories,
                "count": len(matches),
                "results": matches,
            }
        except Exception as e:
            logger.error(f"Error searching CRDs: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="List Custom Resource Instances",
            readOnlyHint=True,
        ),
    )
    def list_custom_resources(
        group: str,
        version: str,
        plural: str,
        namespace: str = "",
        label_selector: str = "",
        limit: int = 100,
        context: str = ""
    ) -> Dict[str, Any]:
        """List instances of any custom resource type.

        Use discover_crds or search_crds first to find the group/version/plural,
        then call this to list actual instances.

        Example: to list CloudNativePG database clusters:
          list_custom_resources(group="postgresql.cnpg.io", version="v1", plural="clusters")

        Args:
            group: API group (e.g., "postgresql.cnpg.io")
            version: API version (e.g., "v1", "v1beta1")
            plural: Plural resource name (e.g., "clusters", "certificates")
            namespace: Namespace (empty = all namespaces / cluster-scoped)
            label_selector: Label selector to filter
            limit: Maximum number of results
            context: Kubernetes context (uses current if not specified)
        """
        try:
            custom_api = get_custom_objects_client(context)

            kwargs: Dict[str, Any] = {}
            if label_selector:
                kwargs["label_selector"] = label_selector
            if limit:
                kwargs["limit"] = limit

            if namespace:
                raw = custom_api.list_namespaced_custom_object(
                    group=group, version=version, namespace=namespace,
                    plural=plural, **kwargs,
                )
            else:
                raw = custom_api.list_cluster_custom_object(
                    group=group, version=version, plural=plural, **kwargs,
                )

            items = raw.get("items", [])
            resources: List[Dict[str, Any]] = []

            for item in items:
                metadata = item.get("metadata", {})
                status = item.get("status", {})
                spec = item.get("spec", {})

                entry: Dict[str, Any] = {
                    "name": metadata.get("name"),
                    "namespace": metadata.get("namespace"),
                    "creationTimestamp": metadata.get("creationTimestamp"),
                    "labels": metadata.get("labels") or {},
                }

                phase = status.get("phase") or status.get("state")
                if phase:
                    entry["phase"] = phase

                conditions = status.get("conditions", [])
                if conditions:
                    ready = next(
                        (c for c in conditions
                         if c.get("type") in ("Ready", "Available", "Established", "Healthy")),
                        None
                    )
                    if ready:
                        entry["ready"] = ready.get("status") == "True"

                    entry["conditions"] = [
                        {
                            "type": c.get("type"),
                            "status": c.get("status"),
                            "reason": c.get("reason"),
                            "message": (c.get("message") or "")[:200],
                        }
                        for c in conditions[:5]
                    ]

                replicas = (
                    status.get("replicas")
                    or status.get("readyReplicas")
                    or spec.get("replicas")
                    or spec.get("instances")
                )
                if replicas is not None:
                    entry["replicas"] = replicas

                resources.append(entry)

            return {
                "success": True,
                "context": context or "current",
                "resource": f"{plural}.{group}/{version}",
                "namespace": namespace or "all",
                "count": len(resources),
                "items": resources,
            }
        except Exception as e:
            error_msg = str(e)
            if "404" in error_msg or "not found" in error_msg.lower():
                return {
                    "success": False,
                    "error": f"Resource type {plural}.{group}/{version} not found",
                    "hint": "Use discover_crds or search_crds to find available types",
                }
            logger.error(f"Error listing custom resources: {e}")
            return {"success": False, "error": error_msg}

    @server.tool(
        annotations=ToolAnnotations(
            title="Get Custom Resource",
            readOnlyHint=True,
        ),
    )
    def get_custom_resource(
        group: str,
        version: str,
        plural: str,
        name: str,
        namespace: str = "",
        context: str = ""
    ) -> Dict[str, Any]:
        """Get full details of a specific custom resource instance.

        Returns the complete spec, status, and metadata of a single resource.
        Use list_custom_resources first to find the name and namespace.

        Args:
            group: API group (e.g., "postgresql.cnpg.io")
            version: API version (e.g., "v1")
            plural: Plural resource name (e.g., "clusters")
            name: Resource instance name
            namespace: Namespace (required for namespaced resources)
            context: Kubernetes context (uses current if not specified)
        """
        try:
            custom_api = get_custom_objects_client(context)

            if namespace:
                resource = custom_api.get_namespaced_custom_object(
                    group=group, version=version, namespace=namespace,
                    plural=plural, name=name,
                )
            else:
                resource = custom_api.get_cluster_custom_object(
                    group=group, version=version, plural=plural, name=name,
                )

            metadata = resource.get("metadata", {})
            annotations = metadata.get("annotations") or {}
            clean_annotations = {
                k: v for k, v in annotations.items()
                if not k.startswith("kubectl.kubernetes.io/")
                and not k.startswith("meta.helm.sh/")
            }

            clean_metadata = {
                "name": metadata.get("name"),
                "namespace": metadata.get("namespace"),
                "uid": metadata.get("uid"),
                "creationTimestamp": metadata.get("creationTimestamp"),
                "labels": metadata.get("labels") or {},
                "annotations": clean_annotations,
                "ownerReferences": [
                    {"kind": ref.get("kind"), "name": ref.get("name")}
                    for ref in (metadata.get("ownerReferences") or [])
                ],
            }

            return {
                "success": True,
                "context": context or "current",
                "resource": f"{plural}.{group}/{version}",
                "metadata": clean_metadata,
                "spec": resource.get("spec", {}),
                "status": resource.get("status", {}),
            }
        except Exception as e:
            error_msg = str(e)
            if "404" in error_msg or "not found" in error_msg.lower():
                return {
                    "success": False,
                    "error": f"Resource '{name}' not found in {namespace or 'cluster'} ({plural}.{group}/{version})",
                }
            logger.error(f"Error getting custom resource: {e}")
            return {"success": False, "error": error_msg}

    @server.tool(
        annotations=ToolAnnotations(
            title="Describe CRD Schema",
            readOnlyHint=True,
        ),
    )
    def describe_crd(
        crd_name: str,
        context: str = ""
    ) -> Dict[str, Any]:
        """Get schema and documentation for a CRD.

        Shows the OpenAPI schema so the LLM understands what fields a custom
        resource accepts. Useful for explaining what a resource type does
        and what configuration options are available.

        Args:
            crd_name: Full CRD name (e.g., "clusters.postgresql.cnpg.io")
            context: Kubernetes context (uses current if not specified)
        """
        try:
            api = get_apiextensions_client(context)
            crd = api.read_custom_resource_definition(crd_name)

            versions_info: List[Dict[str, Any]] = []
            for ver in (crd.spec.versions or []):
                ver_info: Dict[str, Any] = {
                    "name": ver.name,
                    "served": ver.served,
                    "storage": ver.storage,
                }

                if ver.schema and ver.schema.open_api_v3_schema:
                    schema = ver.schema.open_api_v3_schema
                    schema_dict = schema.to_dict() if hasattr(schema, "to_dict") else {}
                    properties = schema_dict.get("properties", {})

                    top_level: Dict[str, Any] = {}
                    for section in ("spec", "status"):
                        prop = properties.get(section, {})
                        if not prop:
                            continue
                        prop_fields = prop.get("properties", {})
                        top_level[section] = {
                            "description": prop.get("description", ""),
                            "required": prop.get("required", []),
                            "fields": {
                                k: {
                                    "type": v.get("type", "object"),
                                    "description": (v.get("description") or "")[:200],
                                    "enum": v.get("enum"),
                                    "default": v.get("default"),
                                }
                                for k, v in list(prop_fields.items())[:40]
                            },
                        }

                    ver_info["schema"] = top_level

                versions_info.append(ver_info)

            classification = _classify_crd(
                crd_name, crd.spec.group, crd.spec.names.kind
            )

            return {
                "success": True,
                "context": context or "current",
                "crd": {
                    "name": crd_name,
                    "group": crd.spec.group,
                    "kind": crd.spec.names.kind,
                    "plural": crd.spec.names.plural,
                    "singular": crd.spec.names.singular,
                    "scope": crd.spec.scope,
                    "shortNames": crd.spec.names.short_names or [],
                    "categories": classification["categories"],
                    "description": classification["description"],
                },
                "versions": versions_info,
            }
        except Exception as e:
            error_msg = str(e)
            if "404" in error_msg or "not found" in error_msg.lower():
                return {
                    "success": False,
                    "error": f"CRD '{crd_name}' not found",
                    "hint": "Use discover_crds or search_crds to find available CRDs",
                }
            logger.error(f"Error describing CRD: {e}")
            return {"success": False, "error": error_msg}

    @server.tool(
        annotations=ToolAnnotations(
            title="Detect CRD API Availability",
            readOnlyHint=True,
        ),
    )
    def detect_crds(
        context: str = ""
    ) -> Dict[str, Any]:
        """Detect if the CRD API is available in the cluster.

        Lightweight check that verifies the apiextensions.k8s.io API group
        is accessible. Use before calling discover_crds or search_crds.

        Args:
            context: Kubernetes context (uses current if not specified)
        """
        try:
            api = get_apiextensions_client(context)
            crd_list = api.list_custom_resource_definition(limit=1)
            count = len(crd_list.items)
            return {
                "installed": True,
                "available": True,
                "message": "CRD API (apiextensions.k8s.io) is accessible",
                "hasCRDs": count > 0,
            }
        except Exception as e:
            logger.error(f"Error detecting CRD API: {e}")
            return {
                "installed": False,
                "available": False,
                "error": str(e),
            }
