# Kubernetes Interactive HTML Diagrams

This folder contains self-contained interactive HTML explainers for Kubernetes concepts, operations, and demos.

## Start Here

- Home page: [index.html](./index.html)
- Example direct page: [k8s-architecture-interactive.html](./k8s-architecture-interactive.html)

## Included Diagrams

### Foundations

- `k8s-architecture-interactive.html` - Control plane and worker node overview
- `service-types-comparison.html` - ClusterIP, NodePort, LoadBalancer, ExternalName
- `pod-lifecycle.html` - Pod phases, conditions, and lifecycle transitions
- `deployment-hierarchy.html` - Deployment to ReplicaSet to Pod hierarchy
- `rolling-update.html` - Rolling update behavior and rollout concepts
- `deployment-rollback.html` - Deployment rollback flow
- `pod-communication.html` - Pod-to-Pod and Service communication
- `dns-resolution.html` - Kubernetes DNS lookup flow
- `init-containers.html` - Init containers, sequencing, and startup preparation
- `k8s-dashboard.html` - Open-source Kubernetes Dashboard concept, install, and access flow

### Storage, Security, and Scheduling

- `pv-pvc-binding.html` - PersistentVolume and PersistentVolumeClaim binding
- `volume-types.html` - Kubernetes volume type comparison
- `rbac-flow.html` - RBAC authorization flow
- `security-context.html` - Security context behavior and hierarchy
- `network-policy.html` - Traffic filtering with NetworkPolicy
- `node-selection.html` - Node selection and scheduling constraints
- `taints-tolerations.html` - Taints, tolerations, and scheduling outcomes
- `affinity-antiaffinity.html` - Affinity and anti-affinity rules

### Workload Operations

- `replicaset-scaling.html` - ReplicaSet scaling behavior
- `statefulset-vs-deployment.html` - StatefulSet versus Deployment
- `daemonset-pattern.html` - DaemonSet placement model
- `service-lb-rollout.html` - Service load balancing during rollouts
- `cordon-drain.html` - Node maintenance workflow

### Cluster Upgrades and Recovery

- `upgrade-sequence.html` - Cluster upgrade sequencing
- `component-upgrade-order.html` - Safe component upgrade order
- `version-skew.html` - Version skew rules
- `etcd-backup-restore.html` - etcd backup and restore concepts

### Reference

- `k8s-objects-reference.html` - Kubernetes object reference page

## Technical Notes

- All pages are self-contained HTML, CSS, and JavaScript
- No CDN or external runtime dependencies
- Suitable for offline viewing and GitHub Pages hosting
- `.nojekyll` is present so static hosting is straightforward

## Local Usage

Open the home page directly in a browser:

```bash
# Windows
start index.html

# macOS
open index.html

# Linux
xdg-open index.html
```

## GitHub Pages Path Pattern

If published, pages are expected at:

```text
https://<your-site>/<repo>/k8s/docs/html/index.html
```

## Last Updated

March 2026
