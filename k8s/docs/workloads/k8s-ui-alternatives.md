# Kubernetes UIs: Landscape, Headlamp, and Alternatives

## Introduction

Kubernetes is primarily operated through APIs and `kubectl`, but a graphical or structured UI still matters for onboarding, demos, shared visibility, and fast triage. Teams differ: some need a **browser-based** console inside the cluster, others a **desktop IDE**, and many combine either with a **terminal UI** for day-to-day speed.

The ecosystem has shifted. What was once the default web UI is now a **legacy** path, while **SIG UI–aligned** tools such as Headlamp represent the current direction for Kubernetes-native web interfaces. This document summarizes that landscape, compares common options, and aligns with the hands-on labs in this repository.

---

## Kubernetes Dashboard (legacy)

For many years, **Kubernetes Dashboard** was the best-known open-source web UI for Kubernetes. It provided a browser-based way to inspect workloads, view cluster resources, access logs and metrics, and perform some management tasks visually—useful for learners and for demonstrations without relying only on `kubectl`.

### Brief history and retirement

The **Kubernetes Dashboard** project was officially **retired and archived on January 21, 2026**. The official `kubernetes/dashboard` GitHub repository states that the project is **no longer maintained** and recommends that users consider **Headlamp** instead. Deprecation reflected insufficient active maintainers to sustain the project, which weakens confidence in long-term fixes, security updates, and new features.

### What it offered

Historically, Dashboard was used to:

- view Pods, Deployments, Services, ConfigMaps, and Secrets  
- inspect cluster resource health  
- troubleshoot workloads visually  
- create resources from forms or YAML  
- access a browser-based management view alongside `kubectl`  

**Benefits it provided:** visibility into object graphs; a gentler entry point for new users; quick access to logs, status, and details; strong demonstration value for namespaces and workloads.

### Why not to use it for new setups

- The upstream repository is **archived** and **unmaintained**.  
- New learning paths and production-style choices should not standardize on a frozen UI.  
- Official guidance points to **Headlamp** as the successor direction for a Kubernetes-focused web experience.  

### Legacy installation (historical context only)

Older material often installed Dashboard into a dedicated namespace (for example `kubernetes-dashboard`), created a **ServiceAccount** and **token** (or kubeconfig) for sign-in, and reached the UI through **port-forward** or **Ingress**. Chart names and Service names varied by release. Treat such instructions as **historical context** only; do not extend them for new learning tracks.

For a guided legacy exercise in this repo, see [Lab 33: Kubernetes Dashboard (legacy)](../../labmanuals/lab33-workload-kubernetes-dashboard-legacy.md).

---

## Headlamp (recommended)

**Headlamp** is an extensible Kubernetes web UI maintained under the **Kubernetes SIG UI** ecosystem. It is the **recommended** web-oriented UI path in this repository: actively documented, RBAC-aligned, and suitable for in-cluster labs as well as desktop and enterprise-style access patterns.

Headlamp is **not** a full substitute for `kubectl` automation; it complements the CLI for discovery, inspection, and troubleshooting.

### Why Headlamp matters

- **Cleaner discovery** of resources across namespaces and object types.  
- **Faster troubleshooting** for Pod failures, rollouts, and unhealthy workloads.  
- **Stronger learning experience** when showing relationships among Deployments, ReplicaSets, and Pods.  
- **Extensible design** via plugins, compared with a fixed dashboard experience.  
- **Flexible deployment**: in-cluster web app, desktop app, port-forward, Ingress, service accounts, OIDC.  
- **Multi-user friendly** patterns that map to normal Kubernetes authn/authz.

### Core features

**Cluster and namespace exploration** — Browse clusters, namespaces, workloads, configuration objects, RBAC resources, storage, and nodes without memorizing every `kubectl get` variant.

**Workload visibility** — Visual views of Pods, Deployments, ReplicaSets, StatefulSets, DaemonSets, Jobs, and CronJobs to connect controllers to the Pods they manage.

**Resource inspection** — Metadata, labels, annotations, events, YAML, and relationships in a structured UI instead of only long CLI output.

**Logs and triage** — Failing Pods, status, events, log follow, and rollout state; valuable in guided walkthroughs where everyone follows the same path.

**Plugins** — Headlamp supports a **plugin ecosystem**. In-cluster documentation covers **plugin management** (for example via Helm values and sidecar-oriented flows), enabling platform-specific views, internal extensions, GitOps-related tooling, and custom operational workflows.

**Flexible access patterns** — **Port-forward** for quick local access; **Ingress** for shared browser access; **ServiceAccount** tokens; **OIDC** for enterprise authentication. Authorization remains **Kubernetes RBAC** underneath—the UI does not bypass cluster security.

### Headlamp vs kubectl

| Use Headlamp when you want | Use kubectl when you want |
|----------------------------|---------------------------|
| Visual exploration and navigation | Automation and scripting |
| Quick troubleshooting and demos | Precise filtering and bulk changes |
| Showing relationships in the UI | CI/CD and repeatable admin workflows |

A practical model: use **Headlamp** to discover and inspect, and **kubectl** to automate and operate precisely.

### Architecture (in-cluster mode)

1. Headlamp runs as a **Deployment** inside the cluster.  
2. It is exposed through a **Service**.  
3. Users reach it via **kubectl port-forward** or an **Ingress**.  
4. Authentication may use a **ServiceAccount** or **OIDC**.  
5. **RBAC** enforces what the UI can do.  

Headlamp is a UI layer on top of standard Kubernetes authentication and authorization.

### Deployment patterns

- **Helm** — Common for lab and production-style installs; chart and values evolve with upstream docs.  
- **In-cluster** — Shared browser UI; typical pattern on small lab clusters: Helm install, dedicated or lab **ServiceAccount**, **port-forward** first, then optional Ingress. Exact namespaces and values follow the linked lab and current Headlamp documentation.  
- **Desktop** — Local app using **kubeconfig**; no in-cluster Deployment required; strong for administrators and multi-cluster workstation use.  

### RBAC integration

Headlamp respects cluster RBAC: the identities you use (tokens, kubeconfig users, OIDC) determine visible resources and permitted actions. Narrow **ServiceAccount**-backed roles support read-only or scoped operational UIs; broader bindings are appropriate only where policy allows.

### Why this repository teaches Headlamp

- Aligns with current Kubernetes UI direction and upstream maintenance.  
- Easier to justify for **new labs** than an archived Dashboard.  
- Works well on VM-based lab clusters and quick Helm-based setup.  
- Clear path from lab access to enterprise authentication later.

**HTML walkthrough:** [k8s-ui-headlamp.html](../../html/k8s-ui-headlamp.html)

---

## Other alternatives

### FreeLens

**FreeLens** is a free, open-source Kubernetes IDE with a **desktop-first** model: local GUI, **multi-cluster** access, and an extension-oriented workflow without deploying a shared web UI in the cluster.

**Best fit:** users who want a **GUI on the workstation**, multi-cluster kubeconfig workflows, and open-source desktop tooling.

### K9s

**K9s** is a **terminal UI** for Kubernetes: fast navigation, real-time resource watching, and a shell-native operational style.

**Best fit:** SRE and platform engineers, terminal-heavy environments, and speed-focused troubleshooting without a browser.

### Portainer

**Portainer** is broader than Kubernetes-only UIs: a **container management platform** for Kubernetes, Docker, and Podman, with centralized visibility and governance across environments.

**Best fit:** enterprise IT, **mixed** container estates, and teams that need fleet-level or multi-environment control beyond Kubernetes-only tooling.

### Lens

**Lens** (including the broader Lens desktop ecosystem) is a **desktop Kubernetes IDE** oriented around **kubeconfig**, **multi-cluster** views, and **extensions**. It targets developers and operators who want an integrated graphical environment on their machine. **FreeLens** is an open-source option in a similar desktop-IDE space for teams that standardize on OSS; choose based on license, support, and organizational policy.

**Best fit:** workstation-centric GUI users who live in a desktop IDE model rather than an in-cluster web service.

---

## Comparison tables

### Headlamp vs Kubernetes Dashboard (legacy)

| Area | Kubernetes Dashboard | Headlamp |
|------|----------------------|----------|
| Project status | Archived, unmaintained | Active SIG UI direction |
| Upstream recommendation | Points users to Headlamp | Current recommended web UI direction |
| Deployment | Historical in-cluster patterns only for legacy | Actively documented in-cluster and desktop |
| Extensibility | More limited | Plugin ecosystem |
| Enterprise fit | Poor for new adoption | OIDC, plugins, modern access patterns |
| Use today | Legacy comparison, old environments | New labs, demos, current web UI access |

### Tools at a glance

| Tool | Primary mode | Best for | Main strength |
|------|----------------|----------|---------------|
| Kubernetes Dashboard | In-cluster web (legacy) | Historical reference only | Former default; unmaintained |
| Headlamp Web | In-cluster web UI | Shared browser access | Current Kubernetes-focused web path |
| Headlamp Desktop | Desktop app | Local workstation | No in-cluster deployment required |
| FreeLens | Desktop app | GUI-first local usage | Open-source Kubernetes IDE-style experience |
| Lens | Desktop app | Multi-cluster desktop IDE | Integrated GUI, extensions (evaluate license/support) |
| Portainer | Web platform | Enterprise platform ops | Broader governance, multi-environment |
| K9s | Terminal UI | Shell-first operations | Speed, real-time, terminal-native |

---

## Best practices for choosing

**Choose Headlamp (in-cluster web)** when a **shared browser UI** inside the cluster is acceptable and you want a **Kubernetes-first** web console aligned with current upstream guidance.

**Choose Headlamp Desktop or FreeLens (or Lens where policy allows)** when **desktop**, **kubeconfig-driven** access is enough and you do not want to run a shared web service in-cluster first.

**Choose Portainer** when **governance across Kubernetes and other runtimes** matters more than a Kubernetes-only UI.

**Choose K9s** when the **terminal** is the primary environment and **speed** matters more than graphical navigation.

**Default direction for this repository:** (1) **Headlamp in-cluster** for shared browser-based learning; (2) **Headlamp Desktop** or **FreeLens** for local GUI workflows; (3) **K9s** as a terminal-first companion. **Portainer** remains strong where scope exceeds Kubernetes alone. **Do not** standardize new material on **Kubernetes Dashboard**.

---

## Hands-on labs

| Lab | Description |
|-----|-------------|
| [Lab 32: Headlamp Kubernetes UI](../../labmanuals/lab32-workload-headlamp-kubernetes-ui.md) | Recommended path: deploy Headlamp (Helm, in-cluster), authenticate, explore workloads, RBAC, and navigation. |
| [Lab 33: Kubernetes Dashboard (legacy)](../../labmanuals/lab33-workload-kubernetes-dashboard-legacy.md) | Legacy Dashboard-oriented steps for historical comparison or maintenance of older environments only. |

---

## Sources

- Archived Kubernetes Dashboard repository: https://github.com/kubernetes/dashboard  
- Headlamp documentation: https://headlamp.dev/docs/latest/  
- Headlamp in-cluster installation: https://headlamp.dev/docs/latest/installation/in-cluster/  
- Headlamp installation (overview): https://headlamp.dev/docs/latest/installation/  
- Headlamp desktop: https://headlamp.dev/docs/latest/installation/desktop  
- FreeLens: https://github.com/freelensapp/freelens  
- Portainer: https://www.portainer.io/  
- Portainer Kubernetes dashboard: https://docs.portainer.io/user/kubernetes/dashboard  
- K9s: https://k9scli.io/  
