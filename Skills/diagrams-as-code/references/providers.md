# Diagrams Providers and Node Categories

All nodes are imported as `from diagrams.<provider>.<category> import <Node>`.

## Cloud Providers

### aws (Amazon Web Services)
Categories: analytics, ar, blockchain, business, compute, cost, database, devtools, enablement, enduser, engagement, game, general, integration, iot, management, media, migration, ml, mobile, network, nfv, quantum, robotics, satellite, security, storage

Common nodes:
- `compute`: EC2, Lambda, ECS, EKS, Fargate, Batch, ElasticBeanstalk
- `database`: RDS, Aurora, DynamoDB, ElastiCache, Redshift, Neptune
- `network`: ELB, ALB, NLB, Route53, CloudFront, VPC, APIGateway, DirectConnect
- `storage`: S3, EBS, EFS, FSx
- `integration`: SQS, SNS, StepFunctions, EventBridge, MQ
- `security`: IAM, Cognito, WAF, KMS, SecretsManager
- `ml`: Sagemaker, Rekognition, Comprehend, Bedrock

### gcp (Google Cloud Platform)
Categories: analytics, api, compute, database, devtools, iot, ml, network, operations, security, storage

Common nodes:
- `compute`: AppEngine, GKE, Functions, Run, ComputeEngine
- `database`: BigTable, Datastore, Firestore, Memorystore, SQL
- `analytics`: BigQuery, Dataflow, PubSub, Dataproc
- `network`: LoadBalancing, CDN, DNS, VPC
- `storage`: GCS, Filestore

### azure (Microsoft Azure)
Categories: analytics, compute, database, devops, general, identity, integration, iot, migration, ml, mobile, network, security, storage, web

Common nodes:
- `compute`: FunctionApps, VM, AKS, ContainerInstances, BatchAccounts
- `database`: CosmosDb, SQLDatabases, BlobStorage
- `network`: LoadBalancers, ApplicationGateway, Firewall, VirtualNetworks

### alibabacloud
Categories: analytics, application, communication, compute, database, iot, network, security, storage, web

### digitalocean
Categories: compute, database, network, storage

### oci (Oracle Cloud Infrastructure)
Categories: compute, connectivity, database, devops, governance, monitoring, network, security, storage

### ibm
Categories: analytics, applications, blockchain, compute, data, devops, general, infrastructure, management, network, security, social, storage, user

### firebase
Categories: base, develop, extentions, grow, quality

### outscale
Categories: compute, network, security, storage

### openstack
Categories: apiproxies, applicationlifecycle, billing, compute, containerinfra, deployment, frontend, monitoring, multiregion, networking, nfv, objectstore, optimization, orchestration, packaging, sharedservices, storage, user, workloadprovisioning

## Infrastructure / On-Premises

### onprem
Categories: aggregator, analytics, auth, cd, certificates, ci, client, compute, container, database, dns, etl, gitops, groupware, iac, identity, inmemory, logging, messaging, mlops, monitoring, network, proxmox, queue, registry, search, security, storage, tracing, vcs, workflow

Common nodes:
- `compute`: Server, Nomad
- `container`: Docker, Containerd, LXC
- `database`: PostgreSQL, MySQL, MongoDB, Cassandra, CockroachDB, ClickHouse, Couchbase, MariaDB
- `network`: Nginx, HAProxy, Envoy, Istio, Traefik, Caddy, Apache, Consul
- `ci`: GithubActions, Jenkins, GitlabCI, CircleCI, TravisCI, Droneci
- `queue`: Kafka, RabbitMQ, Celery, ActiveMQ, Nats
- `monitoring`: Prometheus, Grafana, Datadog, Nagios, Zabbix, Splunk, Newrelic
- `inmemory`: Redis, Memcached
- `logging`: Fluentbit, Loki, Graylog
- `vcs`: Github, Gitlab, Gitea
- `iac`: Terraform, Ansible, Pulumi
- `search`: Elasticsearch, Solr
- `security`: Vault, Trivy, Falco
- `cd`: Spinnaker, Tekton
- `tracing`: Jaeger, Zipkin
- `mlops`: Mlflow

### k8s (Kubernetes)
Categories: clusterconfig, compute, controlplane, ecosystem, group, infra, network, others, podconfig, rbac, storage

Common nodes:
- `compute`: Pod, Deployment, DaemonSet, StatefulSet, ReplicaSet, Job, CronJob
- `network`: Service, Ingress, NetworkPolicy
- `storage`: PV, PVC, StorageClass
- `controlplane`: APIServer, CCM, ControllerManager, KProxy, Kubelet, Scheduler
- `rbac`: ClusterRole, ClusterRoleBinding, Role, RoleBinding, ServiceAccount
- `clusterconfig`: HPA, LimitRange, Quota
- `group`: Namespace

## Diagram Types

### c4 (C4 Model)
Import from `diagrams.c4`:
- `SystemBoundary`, `Container`, `Database`, `System`, `Person`, `SystemQueue`, `Relationship`

### generic
Categories: blank, compute, database, device, network, os, place, storage, virtualization

### programming
Categories: flowchart, framework, language, runtime

### saas (Software as a Service)
Categories: alerting, analytics, automation, cdn, chat, communication, crm, filesharing, identity, logging, media, payment, recommendation, security, social

Common nodes:
- `chat`: Slack, Teams, Discord, Telegram
- `cdn`: Cloudflare
- `identity`: Auth0, Okta
- `logging`: Datadog, Newrelic, Papertrail
- `analytics`: Snowflake, Stitch

### custom
```python
from diagrams.custom import Custom
node = Custom("Label", "/path/to/icon.png")
```

## Node Documentation

Full node listings per provider: https://diagrams.mingrammer.com/docs/nodes/aws (replace `aws` with any provider name).
