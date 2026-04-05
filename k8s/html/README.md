# Kubernetes Interactive HTML Diagrams

This folder contains self-contained interactive HTML explainers for Kubernetes concepts, operations, and lab walkthroughs.

## Start Here

- Home page: [index.html](./index.html)
- Example reference style: [deployment-hierarchy.html](./deployment-hierarchy.html)

## Current Coverage

- 72 HTML pages total in this folder
- 71 concept explainers plus the home page
- All pages are self-contained and work offline

## Diagram Catalog (11 Categories)

### 1. Foundations (9 pages)

- `k8s-architecture-interactive.html` - Control plane and worker node overview
- `k8s-objects-reference.html` - Kubernetes object quick reference
- `yaml-k8s-part1-syntax.html` - YAML syntax and indentation (Part 1 of 3)
- `yaml-k8s-part2-objects-editing.html` - Objects, labels, editing (Part 2)
- `yaml-k8s-part3-tools-troubleshooting.html` - Tools, validation, troubleshooting (Part 3)
- `pod-lifecycle.html` - Pod phases, restarts, and lifecycle transitions
- `pods-vs-deployments.html` - Beginner path from Pods to Deployments
- `workloads-pod-concepts.html` - Pod and workload concept landscape
- `linux-cheat-sheet.html` - Ubuntu Linux basics for K8s learners

### 2. Installation (3 pages)

- `kubernetes-installation.html` - Cluster installation and bootstrap flow
- `kind-local-kubernetes.html` - Learning-focused local Kubernetes with Kind
- `helm-charts-overview.html` - Helm chart overview, architecture, and commands

### 3. Workload Management (13 pages)

- `deployment-hierarchy.html` - Deployment to ReplicaSet to Pod hierarchy
- `replicaset-scaling.html` - ReplicaSet scaling behavior
- `replicaset-vs-daemonset.html` - ReplicaSet vs DaemonSet comparison
- `rolling-update.html` - Rolling update behavior and rollout concepts
- `deployment-rollback.html` - Deployment rollback flow
- `deployment-strategies.html` - Rolling, blue-green, and canary comparison
- `multi-container-pod-patterns.html` - Sidecar and helper-container patterns
- `init-containers.html` - Init container sequencing and startup preparation
- `daemonset-pattern.html` - DaemonSet placement model
- `statefulset-vs-deployment.html` - StatefulSet versus Deployment
- `jobs-batch-processing.html` - Jobs and run-to-completion workloads
- `cronjobs-scheduling.html` - CronJob scheduling flow
- `static-pods.html` - Kubelet-managed static Pod model

### 4. Networking (9 pages)

- `service-types-comparison.html` - ClusterIP, NodePort, LoadBalancer
- `services-networking-deep-dive.html` - Services, selectors, endpoints, and ports
- `multi-port-services.html` - Multi-port Services and named-port mapping
- `pod-communication.html` - Pod-to-Pod and Service communication
- `dns-resolution.html` - Kubernetes DNS lookup flow
- `service-lb-rollout.html` - Service load balancing during rollouts
- `ingress-endpointslices.html` - Ingress routing and EndpointSlice scaling
- `gateway-api-routing.html` - GatewayClass, Gateway, and HTTPRoute model
- `network-policy.html` - Traffic filtering with NetworkPolicy

### 5. Configuration and Secrets (4 pages)

- `configmaps-patterns.html` - ConfigMap creation and consumption patterns
- `configmap-volume.html` - Mounting ConfigMap keys as files inside Pods
- `secrets-management.html` - Secret types, consumption patterns, and security
- `secret-volume.html` - Mounting Secrets as read-only files inside Pods

### 6. Security and Policy (6 pages)

- `rbac-flow.html` - RBAC authorization flow
- `rbac-user-certificate-flow.html` - Certificate to kubeconfig to RBAC testing
- `ldap-k8s-rbac-poc.html` - LDAP/AD to OIDC to Kubernetes RBAC POC
- `security-context.html` - Security context behavior and hierarchy
- `pod-security-standards.html` - Privileged, Baseline, and Restricted profiles
- `opa-gatekeeper-policy.html` - Admission policy with Gatekeeper

### 7. Scheduling (4 pages)

- `node-selection.html` - Node selection and scheduling constraints
- `taints-tolerations.html` - Taints, tolerations, and scheduling outcomes
- `affinity-antiaffinity.html` - Affinity and anti-affinity rules
- `resource-quotas-limits.html` - Requests, limits, and namespace quotas

### 8. Scaling and Health (3 pages)

- `metrics-server-architecture.html` - Metrics pipeline for `kubectl top` and HPA
- `hpa-autoscaling.html` - Horizontal Pod Autoscaling control loop
- `health-probes.html` - Liveness, readiness, and startup probes

### 9. Cluster Operations (6 pages)

- `cluster-administration.html` - Core administration responsibilities and flows
- `cordon-drain.html` - Node maintenance workflow
- `upgrade-sequence.html` - Cluster upgrade sequencing
- `component-upgrade-order.html` - Safe component upgrade order
- `version-skew.html` - Version skew rules
- `etcd-backup-restore.html` - etcd backup and restore concepts

### 10. Storage (9 pages)

- `k8s-storage-complete.html` - Ephemeral, persistent, CSI, StorageClasses, and design thinking
- `volume-types.html` - Kubernetes volume type comparison (temporary, projected, local, persistent)
- `pv-pvc-binding.html` - PersistentVolume and PersistentVolumeClaim lifecycle and binding
- `accessmode-storageclasses.html` - Access modes (RWO, ROX, RWX, RWOP) and StorageClasses
- `hostpath-pv-pvc.html` - HostPath-backed PV and PVC for labs and development
- `nfs-pv-pvc-complete.html` - NFS-backed PV and PVC for shared multi-node storage
- `csi-aws-ebs-efs.html` - CSI driver flow with AWS EBS and EFS examples
- `sharingdata.html` - Sharing data between containers using emptyDir
- `readwrite-pod.html` - Multi-container Pod sharing a persistent NFS claim

### 11. Tools and Reference (5 pages)

- `kubectl-essentials.html` - kubectl command-line mental model
- `k8s-dashboard.html` - Legacy Kubernetes Dashboard explainer
- `k8s-ui-headlamp.html` - Headlamp in-cluster installation and access
- `k8s-ui-alternatives.html` - Headlamp, FreeLens, Portainer, K9s comparison
- `custom-resource-definitions.html` - CRDs, custom resources, and API extension

## Technical Notes

- All pages are self-contained HTML, CSS, and JavaScript
- No CDN or external runtime dependencies
- Suitable for offline viewing and static hosting
- `.nojekyll` is present so GitHub Pages hosting is straightforward

## Local Usage

Open the home page directly in a browser:

```bash
# Windows
start index.html
```

## Last Updated

March 2026
