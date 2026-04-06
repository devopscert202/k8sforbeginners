# Kubernetes for Beginners

<div align="center">

![Kubernetes](https://img.shields.io/badge/Kubernetes-v1.24--1.32-326CE5?logo=kubernetes&logoColor=white)
![Labs](https://img.shields.io/badge/Labs-62-blueviolet)
![HTML Guides](https://img.shields.io/badge/Interactive%20HTML-83-orange)
![Docs](https://img.shields.io/badge/Concept%20Docs-66-green)
![YAML](https://img.shields.io/badge/YAML%20Manifests-207-yellow)

**A structured, hands-on Kubernetes learning resource — 62 lab manuals, 83 interactive HTML explainers, 66 concept documents, and 207 ready-to-deploy YAML manifests.**

</div>

---

## What Is This Repository?

This repository is a self-contained Kubernetes curriculum built around three pillars:

| Pillar | Location | What It Provides |
|--------|----------|-----------------|
| **Concept Docs** | `k8s/docs/` | The *why* — architecture, theory, comparisons, best practices |
| **Lab Manuals** | `k8s/labmanuals/` | The *how* — step-by-step exercises you run on a real cluster |
| **Interactive HTML** | `k8s/html/` | The *visual* — self-contained browser pages with diagrams, tabs, and interactive walkthroughs |

Supporting these are **207 YAML manifests** (`k8s/labs/`) that every lab references, so you always apply real files rather than pasting inline snippets.

### Who Is This For?

- Beginners learning Kubernetes from scratch
- Engineers preparing for **CKA / CKAD** certification
- Teams onboarding developers onto Kubernetes
- Anyone who prefers learning by doing over reading documentation

---

## Repository Structure

```
k8sforbeginners/
├── README.md                  ← you are here
├── k8s/
│   ├── labmanuals/            62 step-by-step lab manuals (Lab 01–62)
│   │   └── README.md          Lab catalog with 7 learning paths
│   ├── docs/                  66 concept documents organized by topic
│   │   ├── basics/            Architecture, YAML, kubectl, APIs, crictl
│   │   ├── security/          RBAC, NetworkPolicy, Gatekeeper, PSS, hardening
│   │   ├── networking/        Services, DNS, Ingress, EndpointSlices
│   │   ├── workloads/         Deployments, DaemonSets, HPA, ConfigMaps, CronJobs
│   │   ├── storage/           Volumes, PV/PVC, NFS, StorageClasses
│   │   ├── scheduling/        Affinity, taints, node selection, priority
│   │   ├── upgrade/           Version-specific upgrade procedures (v1.27→v1.32)
│   │   ├── troubleshooting/   Common issues and debugging reference
│   │   ├── deployment/        Rollout strategies
│   │   ├── aks/               Azure AKS guides
│   │   ├── aws/               AWS EKS / EC2 guides
│   │   └── gcp/               Google GKE guide
│   ├── html/                  83 interactive HTML pages (work offline)
│   │   ├── index.html         Visual catalog of all HTML explainers
│   │   └── README.md          HTML page inventory by category
│   ├── labs/                  207 YAML manifests organized by category
│   │   ├── basics/            Pods, Services
│   │   ├── workloads/         Deployments, Jobs, CronJobs, StatefulSets
│   │   ├── networking/        DNS, Ingress, Gateway API, EndpointSlices
│   │   ├── security/          RBAC, NetworkPolicy, PSS, Gatekeeper
│   │   ├── scheduling/        Affinity, taints, priority
│   │   ├── storage/           PV, PVC, NFS, hostPath
│   │   ├── config/            ConfigMaps, Secrets
│   │   ├── administration/    etcd backup, node management
│   │   ├── advanced/          CRDs, custom resources
│   │   ├── yaml-lab/          Lab 46 YAML practice manifests
│   │   ├── troubleshooting/   Troubleshooting lab resources
│   │   └── ...                AKS, AWS, GCP, Docker, Helm, ecommerce-app
│   ├── architecture/          Architecture diagrams and use-case documents
│   └── projects/              End-to-end project scenario
```

---

## How to Use This Repository

### 1. Understand the Three Content Types

**Concept Docs** (`k8s/docs/`) explain *what* something is and *why* it matters. They are reference material — read them when you need background on a topic. Every doc ends with a **Hands-On Labs** section linking to the relevant lab manuals.

**Lab Manuals** (`k8s/labmanuals/`) are the primary learning resource. Each lab has an overview, prerequisites, numbered exercises, expected outputs, a cleanup section, and links to related labs. They reference YAML files from `k8s/labs/` so you apply real manifests.

**Interactive HTML** (`k8s/html/`) are self-contained browser pages that visualize concepts with tabs, diagrams, tables, and code blocks. Open `k8s/html/index.html` to browse the full catalog. Every page works offline — no server required.

### 2. Set Up a Cluster

You need a Kubernetes cluster to follow the labs. The recommended setup:

- **3 Linux VMs** (1 control plane + 2 worker nodes)
- **Ubuntu 22.04** with **2 CPU / 4 GB RAM** per VM (4 CPU / 8 GB recommended)
- **Kubernetes 1.28+** installed via kubeadm
- Follow [Lab 06: Kubernetes Installation with kubeadm](k8s/labmanuals/lab06-install-kubernetes-kubeadm.md)

> **Note:** This repository targets standalone kubeadm clusters where you have full control-plane access. Many labs require multi-node scheduling, direct etcd access, or node-level operations that managed services (EKS, GKE, AKS) or single-node tools (minikube) do not support. For local experimentation without VMs, [Lab 05: Kind](k8s/labmanuals/lab05-install-kind-local-kubernetes.md) works for most labs except cluster administration and node-specific exercises.

### 3. Pick a Learning Path

The [Lab Manuals README](k8s/labmanuals/README.md) defines **7 learning paths**. Here are the most common starting points:

| Goal | Path | Where to Start |
|------|------|---------------|
| **Brand new to Kubernetes** | Complete Beginner | [Lab 01: Creating Pods](k8s/labmanuals/lab01-basics-creating-pods.md) |
| **CKA exam preparation** | CKA Certification | [Lab Manuals README](k8s/labmanuals/README.md) — Path 2 |
| **Security focus** | Security Specialist | Labs 11–16 + 57 |
| **Day-to-day operations** | Production Readiness | Labs 09, 36, 30, 37, 40 |

### 4. Work Through Labs

```bash
git clone https://github.com/devopscert202/k8sforbeginners.git
cd k8sforbeginners

# Open a lab manual
cat k8s/labmanuals/lab01-basics-creating-pods.md

# Apply the referenced YAML
kubectl apply -f k8s/labs/basics/apache1.yaml

# Observe results
kubectl get pods -o wide

# Experiment, break things, fix them, move to the next lab
```

### 5. Use Docs and HTML as Companions

- Need background before a lab? Read the linked concept doc.
- Want a visual walkthrough? Open the corresponding HTML page in your browser.
- Looking for a kubectl command? See the [kubectl Reference](k8s/docs/basics/kubectl-reference.md) or the [interactive HTML version](k8s/html/kubectl-reference.html).
- Stuck on YAML? Start with [YAML Basics](k8s/docs/basics/yaml-basics.md), then [Lab 46](k8s/labmanuals/lab46-basics-yaml-manifests.md), then the [interactive YAML series](k8s/html/yaml-k8s-part1-syntax.html).

---

## Lab Manual Catalog (62 Labs)

| # | Category | Labs | Topics |
|---|----------|------|--------|
| 1 | **Basics** | 01–06, 46, 59–62 | Pods, Services, kubectl, Docker, Kind, kubeadm, YAML, crictl, APIs, contexts, advanced kubectl |
| 2 | **Cluster Operations** | 07–08 | etcd backup/restore, cluster administration |
| 3 | **Pod Lifecycle** | 09–10, 21 | Health probes, init containers, multi-container patterns |
| 4 | **Security** | 11–16, 57 | RBAC, security context, NetworkPolicy, Gatekeeper, image scanning, PSS, advanced NetworkPolicy |
| 5 | **Scheduling** | 17–20 | NodeSelector, affinity/anti-affinity, PriorityClass, taints and tolerations |
| 6 | **Deployments** | 22–24 | Strategies (rolling, blue-green, canary), rollouts, frontend deployment |
| 7 | **Workloads** | 25–33, 47 | ConfigMaps, DaemonSets, static pods, Jobs, CronJobs, HPA, StatefulSets, UIs, Secrets |
| 8 | **Networking** | 34–35, 44–45, 56, 58 | Multi-port services, Ingress, Gateway API, DNS, CoreDNS, EndpointSlices |
| 9 | **Observability** | 36 | Metrics Server |
| 10 | **Resource Management** | 37 | Resource quotas and LimitRanges |
| 11 | **Storage** | 38–39 | emptyDir, hostPath, PV/PVC, NFS |
| 12 | **Upgrades** | 40 | kubeadm cluster upgrade procedure |
| 13 | **Advanced** | 41–43, 48 | WordPress on K8s, HA cluster, CRDs, Helm charts |
| 14 | **Troubleshooting** | 49–55 | Control plane, pod failures, kubelet/node, networking, workloads, commands, CKA scenarios |

Full catalog with descriptions: [Lab Manuals README](k8s/labmanuals/README.md)

---

## Interactive HTML Pages (83 Pages)

All pages are self-contained, work offline, and require no build step — just open in a browser.

| Category | Pages | Highlights |
|----------|-------|-----------|
| Foundations | 9 | Architecture, pod concepts, YAML syntax (3-part series) |
| Installation | 4 | Kind, kubeadm, kubeconfig contexts |
| Workloads | 13 | Deployments, DaemonSets, StatefulSets, Jobs, CronJobs, HPA, init containers |
| Networking | 11 | Services, DNS, Ingress, Gateway API, EndpointSlices, NetworkPolicy |
| Configuration | 4 | ConfigMaps patterns, multi-container pods |
| Security | 6 | RBAC, security context, PSS, Gatekeeper, NetworkPolicy |
| Scheduling | 4 | Affinity, taints, node selection, cordon/drain |
| Scaling & Health | 3 | HPA, health probes, metrics server |
| Cluster Ops | 6 | etcd backup, upgrades, version skew, static pods |
| Storage | 9 | Volume types, PV/PVC binding, access modes |
| Tools & Reference | 6 | kubectl essentials, kubectl reference, dashboard, Headlamp, CRDs |
| Troubleshooting | 7 | Cluster admin, pod debugging, LDAP-RBAC PoC |

Browse them all: open [`k8s/html/index.html`](k8s/html/index.html) in your browser.

---

## Concept Documents (66 Docs)

Concept docs live under `k8s/docs/` in topic-based subdirectories:

| Directory | Docs | Coverage |
|-----------|------|----------|
| `basics/` | 11 | Architecture, intro, objects, YAML, kubectl, crictl, APIs, Kind |
| `security/` | 10 | RBAC, NetworkPolicy, Gatekeeper, PSS, hardening, scanning, contexts, policies |
| `networking/` | 7 | Services, DNS, Ingress, EndpointSlices, advanced networking |
| `workloads/` | 12 | Deployments, DaemonSets, HPA, ConfigMaps, CronJobs, observability, tuning, UIs |
| `storage/` | 8 | Volumes, PV/PVC, NFS, hostPath, ConfigMap/Secret volumes, access modes |
| `scheduling/` | 5 | Affinity, taints, node selector, node maintenance, scheduler internals |
| `upgrade/` | 6 | Upgrade procedure, version skew, v1.27→v1.28 through v1.31→v1.32 |
| `troubleshooting/` | 1 | Consolidated issues and debugging reference |
| `deployment/` | 1 | Rollout strategies |
| `aks/` `aws/` `gcp/` | 7 | Cloud-provider-specific guides |

Every doc focuses on concepts, comparisons, and best practices. Hands-on steps live in the lab manuals, and each doc links to its related labs at the bottom.

---

## YAML Manifests (207 Files)

All manifests live under `k8s/labs/` in 18 subdirectories. They are:

- Tested on Kubernetes v1.24–v1.32
- Referenced by lab manuals with direct file links
- Ready to apply: `kubectl apply -f <file>`
- Organized by topic to match the lab structure

---

## Version Compatibility

- Labs tested on **Kubernetes v1.24 through v1.32**
- Modern features (PSS, Gateway API, native sidecars) require **v1.25+** and are marked in their respective labs
- Use a `kubectl` version that matches your cluster's minor version

---

## Environment Requirements

This repository is designed for **standalone kubeadm clusters** in lab or development environments:

- Requires direct control-plane access (etcd backup, cluster upgrades)
- Requires multi-node setup (DaemonSets, affinity, taints/tolerations, scheduling)
- Some labs demonstrate intentionally insecure configurations for educational purposes

Not designed for managed services (EKS, GKE, AKS) or single-node tools (minikube) — though many individual labs will work on any cluster.

---

## Contributing

Contributions are welcome. If you find a broken command, unclear instruction, or missing topic:

1. [Open an issue](https://github.com/devopscert202/k8sforbeginners/issues) describing the problem
2. Or fork the repo, fix it, and submit a pull request

When submitting changes, test all commands on a real cluster and follow the existing formatting conventions.

---

## Quick Links

| Resource | Link |
|----------|------|
| Lab Manuals (start here) | [k8s/labmanuals/README.md](k8s/labmanuals/README.md) |
| Interactive HTML catalog | [k8s/html/index.html](k8s/html/index.html) |
| kubectl reference | [k8s/docs/basics/kubectl-reference.md](k8s/docs/basics/kubectl-reference.md) |
| YAML basics | [k8s/docs/basics/yaml-basics.md](k8s/docs/basics/yaml-basics.md) |
| Architecture overview | [k8s/docs/basics/k8s-architecture.md](k8s/docs/basics/k8s-architecture.md) |
| Troubleshooting | [k8s/docs/troubleshooting/k8s-issues.md](k8s/docs/troubleshooting/k8s-issues.md) |
| Kubernetes official docs | [kubernetes.io/docs](https://kubernetes.io/docs/) |
| kubectl cheat sheet | [kubernetes.io cheat sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/) |

---

<div align="center">

**62 labs** | **83 interactive HTML pages** | **66 concept docs** | **207 YAML manifests** | **Kubernetes v1.24–v1.32**

Last updated: March 2026

</div>
