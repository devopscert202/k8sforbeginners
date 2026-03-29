# Headlamp UI for Kubernetes

## Background

For many years, **Kubernetes Dashboard** was the best-known web UI for Kubernetes clusters. That situation has changed.

The Kubernetes Dashboard project was officially retired and archived on **January 21, 2026**. The official `kubernetes/dashboard` GitHub repository is now:

- archived
- no longer maintained
- recommending that users consider **Headlamp** instead

That makes Headlamp the more practical UI to teach for current Kubernetes environments.

## Why Kubernetes Dashboard Was Deprecated

The main upstream reason is that the Kubernetes Dashboard project no longer had enough active maintainers and contributors to keep moving forward, so the repository was archived.

That creates a few practical concerns for a cluster-access UI:

- weaker long-term maintenance confidence
- less certainty around future updates
- lower confidence for new feature development
- reduced confidence when choosing it as a current UI standard

## How Headlamp Addresses Those Concerns

Headlamp addresses those concerns through a more current and actively documented path:

- active installation and usage documentation
- alignment with the Kubernetes SIG UI direction
- plugin-based extensibility
- support for both in-cluster web access and desktop usage
- RBAC-aware access patterns that fit current Kubernetes operations

## What is Headlamp?

**Headlamp** is an easy-to-use and extensible Kubernetes web UI maintained under the Kubernetes SIG UI ecosystem. It can run:

- as an **in-cluster web application**
- as a **desktop application**
- with **plugins**
- with **OIDC or service-account based access**

For this repository, the most relevant mode is the **in-cluster deployment model**, where Headlamp runs inside the Kubernetes cluster and is exposed by port-forward or ingress.

---

## Why Headlamp Matters

Headlamp gives operators and platform users a modern visual interface for day-to-day Kubernetes work without replacing `kubectl`.

### Key benefits

- **Cleaner discovery of resources**: Easier navigation across Pods, Deployments, Services, Nodes, ConfigMaps, Secrets, and namespaces.
- **Faster troubleshooting**: Good for quickly spotting Pod failures, rollout issues, and unhealthy workloads.
- **Better learning experience**: New Kubernetes users can understand relationships between workloads and objects more easily in a visual UI.
- **Extensible design**: Headlamp supports plugins, which makes it more adaptable than a fixed dashboard experience.
- **Flexible deployment options**: Can be used in-cluster, on desktop, or behind enterprise authentication flows.
- **Multi-user friendly**: Works well with service accounts, OIDC, and ingress-based access patterns.

---

## Core Headlamp Features

### 1. Cluster and namespace exploration

Headlamp helps users browse:

- clusters
- namespaces
- workloads
- configuration objects
- RBAC resources
- storage resources
- node-level objects

This is useful when users want to understand "what is running where" without memorizing every `kubectl get` combination.

### 2. Workload visibility

Headlamp gives a visual view of:

- Pods
- Deployments
- ReplicaSets
- StatefulSets
- DaemonSets
- Jobs
- CronJobs

This helps users connect workload controllers to the Pods they manage.

### 3. Resource inspection

Users can inspect object details more easily than scrolling long CLI output:

- metadata
- labels
- annotations
- events
- YAML manifests
- relationships between resources

### 4. Logs and troubleshooting workflows

Headlamp is useful for:

- checking failing Pods
- viewing status quickly
- reading events
- following logs
- validating rollout state

It is especially valuable in demos and guided walkthroughs where a UI helps everyone follow the same troubleshooting path.

### 5. Extensibility through plugins

One of Headlamp's strongest design points is that it supports plugins. The in-cluster documentation also includes **plugin management** through Helm values and a sidecar-based plugin manager flow.

This is useful for:

- platform-specific dashboards
- internal tooling extensions
- GitOps integrations
- custom operational workflows

### 6. Flexible access patterns

Headlamp supports multiple access models:

- **port-forward** for fast local access
- **ingress** for shared browser access
- **service account** access
- **OIDC** for enterprise authentication

That makes it suitable both for labs and for production-style deployments.

---

## Headlamp UI Benefits for Learning

Headlamp is particularly useful in beginner and intermediate Kubernetes training.

### Visual learning advantages

- Learners can move from **namespace -> workload -> Pod -> logs/events** more naturally.
- It reduces the fear factor for users who are still learning `kubectl`.
- It helps demonstrate how Deployments, ReplicaSets, and Pods relate to each other.
- It makes namespace isolation and RBAC outcomes easier to show.

### Operational advantages

- Faster cluster walkthroughs during demos
- Easier validation after deployments
- Good for triage before switching to CLI
- Useful for platform teams who want a quick visual inspection layer

---

## Headlamp vs Kubernetes Dashboard

| Area | Kubernetes Dashboard | Headlamp |
|------|----------------------|----------|
| Current project status | Archived and no longer maintained | Active SIG UI direction |
| Recommendation status | Official repo now points users to Headlamp | Recommended alternative |
| Deployment style | Historically common, but project status is weak for new learning tracks | Actively documented in-cluster and desktop options |
| Extensibility | More limited | Plugin-friendly and extensible |
| Enterprise fit | Less compelling for new adoption | Better fit with OIDC, plugins, and modern UI workflows |
| Best use now | Legacy environments only | New labs, demos, and modern cluster UI access |

---

## Headlamp vs kubectl

Headlamp is **not** a replacement for `kubectl`.

### Use Headlamp when you want:

- visual exploration
- quick troubleshooting
- visual demonstrations
- easier navigation between related resources

### Use kubectl when you want:

- automation
- scripting
- precise output filtering
- CI/CD integration
- bulk changes
- repeatable admin workflows

The best operational model is:

1. use **Headlamp** to discover and inspect
2. use **kubectl** to automate and operate precisely

---

## Architecture Overview for In-Cluster Mode

In a typical in-cluster deployment:

1. Headlamp runs as a **Deployment** inside the cluster.
2. It is exposed through a **Service**.
3. Users access it by:
   - `kubectl port-forward`, or
   - an **Ingress**
4. Authentication can be done using:
   - a **ServiceAccount**, or
   - **OIDC**
5. Authorization is still controlled by **Kubernetes RBAC**.

That means Headlamp is a UI layer on top of normal Kubernetes authentication and authorization.

---

## Why We Should Teach Headlamp in This Repository

This repository is aimed at hands-on Kubernetes practice. Headlamp is a good fit because it:

- aligns with the current Kubernetes UI direction
- is easier to justify for new labs than an archived Dashboard project
- works well in VM-based clusters
- can be installed quickly with Helm
- supports a clean path from lab access today to enterprise auth later

---

## Recommended Lab Approach

For a **3-node VM-based cluster**, the simplest learning path is:

1. install Headlamp **in-cluster using Helm**
2. deploy it into `kube-system`
3. create a **Headlamp admin ServiceAccount** for the lab
4. generate a token
5. access it by **port-forward**
6. validate cluster, node, namespace, workload, and log views

This approach avoids unnecessary ingress and DNS complexity for the first exercise while remaining close to the official Headlamp documentation.

---

## Summary

Headlamp is the more relevant Kubernetes web UI to teach now because the old Dashboard project is archived and explicitly points users toward Headlamp. It provides a modern, extensible, and Kubernetes-native UI for visual exploration, troubleshooting, and operational visibility, while still relying on standard Kubernetes RBAC and authentication models underneath.

For this repository, Headlamp should be treated as the **current Kubernetes UI learning path** for web-based cluster access.

---

## Sources

- Headlamp docs: https://headlamp.dev/docs/latest/
- Headlamp in-cluster installation: https://headlamp.dev/docs/latest/installation/in-cluster/
- Archived Kubernetes Dashboard repository note: https://github.com/kubernetes/dashboard
