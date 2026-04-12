# Kubernetes Introduction — Complete Guide

Kubernetes (K8s) is an **open-source container orchestration platform** that automates **deployment, scaling, and management** of containerized applications. It schedules work across a cluster of nodes, reconciles **desired state** (declarative manifests) with what is actually running, and provides built-in networking, storage hooks, and recovery when things fail. That matters because raw containers alone do not solve multi-node placement, upgrades without downtime, or service discovery at scale.

**Official documentation:** [https://kubernetes.io/docs](https://kubernetes.io/docs)

Use the numbered path below in order the first time through; skip or revisit sections based on what you already know. Each step points to a deeper guide in this repo.

---

## Learning path

### 1. Containers and images

Containers package an app with its dependencies; images are the immutable templates you run. You need that mental model before orchestration makes sense.

**Next:** [Container basics](./container-basics.md)

### 2. Why orchestration (and Kubernetes)

Docker and similar tools run containers on a host; **orchestration** decides *where* they run, *how many* copies to keep, *how* to roll out new versions, and *how* traffic finds healthy backends. Kubernetes provides horizontal scaling, service discovery and load balancing, self-healing for failed Pods, rollouts/rollbacks, resource-aware scheduling, storage abstractions (PV/PVC), Jobs/CronJobs, and ConfigMaps/Secrets—topics spelled out in the linked guides below rather than duplicated here.

### 3. Cluster architecture

A cluster has a **control plane** (API server, etcd, scheduler, controllers) and **worker nodes** (kubelet, kube-proxy, container runtime) that run your Pods.

**Next:** [Kubernetes architecture](./k8s-architecture.md)

### 4. Local cluster with kind

A disposable local cluster is the safest place to practice `kubectl` and manifests without cloud cost.

**Next:** [Kind local cluster](./kind-local-cluster.md)

### 5. YAML manifests

Real work in Kubernetes is mostly declarative YAML: `apiVersion`, `kind`, `metadata`, `spec`, and (read-only) `status`.

**Next:** [YAML basics](./yaml-basics.md)

### 6. Kubernetes API and kubectl

The API is how the control plane represents resources; `kubectl` (and other clients) talk to the API server to read and change that state.

**Next:** [Kubernetes API](./k8s-apis.md)

### 7. Objects, workloads, and controllers

Resources like Pods, ReplicaSets, Deployments, Services, Ingress, ConfigMaps, Secrets, PVs/PVCs, and Namespaces are **objects** in the API; controllers continuously drive the cluster toward the desired state.

**Next:** [Kubernetes objects (complete guide)](./k8s-objects-complete.md)

### 8. Container runtimes and crictl

Nodes run containers through a **CRI**-compatible runtime (for example containerd or CRI-O). **crictl** is the standard CLI for inspecting workloads at the runtime layer when `kubectl` is not enough.

**Next:** [crictl](./crictl.md)

### 9. Networking

Pods get cluster IPs; Services provide stable virtual IPs and DNS names; a **CNI** plugin implements the Pod network. These ideas connect directly to how you design and debug applications on the cluster.

**Next:** [Networking basics](../networking/networking-basics.md) · Deeper dive: [Kubernetes networking and services](../networking/k8s-networking.services.md)

### 10. Scheduling (placement rules)

Beyond default scheduling, you can constrain which nodes run a workload using affinities, anti-affinities, and related mechanisms.

**Next:** [Affinity and anti-affinity](../scheduling/affinity_antiaffinity.md)

### 11. Cluster lifecycle and administration

Production clusters involve topology choices, adding/removing nodes, upgrades, backups, and securing node/API access (certificates, RBAC, kubelet auth). **kubeadm** is a common bootstrap path: `kubeadm init` on the first control plane node (with a pod network CIDR aligned to your CNI) and `kubeadm join` on additional nodes with a join token—full sequences and prerequisites are in the installation and administration labs linked below.

---

## Web UIs

Treat the legacy **Kubernetes Dashboard** as a reference only; upstream maintenance has wound down. Prefer current UI options documented in this repo.

**Next:** [Kubernetes UIs: landscape and alternatives](../workloads/k8s-ui-alternatives.md) · [Headlamp HTML guide](../../html/k8s-ui-headlamp.html)

---

## When Kubernetes helps — and when it does not

### Advantages

- **Scalability and self-healing** — replica counts and restarts without manual babysitting.
- **Rolling updates and rollbacks** — reduce downtime during version changes.
- **Portability** — same API and patterns across on-prem and cloud.
- **Declarative operations** — versioned desired state instead of one-off imperative steps.
- **Extensibility** — CRDs and operators for custom automation.

### Disadvantages

- **Complexity** — steep learning curve and many moving parts.
- **Operational cost** — control plane and tooling need care and capacity.
- **Setup and integration** — networking, security, and storage must be correct for your environment.
- **Debugging** — distributed failures are harder to trace than on a single host.

### Where it is used

Kubernetes underpins major managed offerings (Google GKE, AWS EKS, Microsoft AKS). It is also used at scale by many product companies (for example Spotify, Airbnb, Shopify, and Netflix). Adoption always depends on team skills, workload fit, and operational maturity—not on name recognition alone.

---

## Helpful external references

- [Kubernetes components (official)](https://kubernetes.io/docs/concepts/overview/components/)
- [kubectl cheat sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)
- [Play with Kubernetes](https://labs.play-with-k8s.com/)

---

## Hands-On Labs

| Lab | Description |
|-----|-------------|
| [Lab 01: Creating pods](../../labmanuals/lab01-basics-creating-pods.md) | Pods, manifests, and basic workload concepts. |
| [Lab 02: Creating services](../../labmanuals/lab02-basics-creating-services.md) | Services, selectors, and cluster networking basics. |
| [Lab 03: kubectl essentials](../../labmanuals/lab03-basics-kubectl-essentials.md) | Core `kubectl` workflows for daily cluster work. |
| [Lab 04: Docker build and run](../../labmanuals/lab04-basics-docker-build-run.md) | Container images aligned with [container basics](./container-basics.md). |
| [Lab 05: Kind local Kubernetes](../../labmanuals/lab05-install-kind-local-kubernetes.md) | Local cluster aligned with [Kind guide](./kind-local-cluster.md). |
| [Lab 06: Install Kubernetes with kubeadm](../../labmanuals/lab06-install-kubernetes-kubeadm.md) | Bootstrap a multi-node-style cluster; complements **§11** above. |
| [Lab 08: Cluster administration](../../labmanuals/lab08-cluster-administration.md) | Day-2 operations and cluster-wide tasks. |
| [Lab 46: YAML manifests](../../labmanuals/lab46-basics-yaml-manifests.md) | Hands-on practice for [YAML basics](./yaml-basics.md). |
| [Lab 59: crictl](../../labmanuals/lab59-basics-crictl.md) | Runtime-level inspection; pairs with [crictl](./crictl.md). |
| [Lab 60: Kubernetes APIs](../../labmanuals/lab60-basics-k8s-apis.md) | API exploration; pairs with [Kubernetes API](./k8s-apis.md). |

---

## Summary

Kubernetes is an **ecosystem** for running containerized workloads: declarative configuration, controllers that enforce desired state, built-in networking and storage abstractions, and a path from a laptop cluster to production platforms. This page is the map; the linked guides and labs are the territory.
