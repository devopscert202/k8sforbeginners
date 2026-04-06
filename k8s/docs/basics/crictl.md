# CRI-based Kubernetes operations with `crictl`

## Table of Contents

1. [Background: Why `containerd` and not Docker?](#1-background-why-containerd-and-not-docker)
2. [Understanding `containerd`](#2-understanding-containerd)
3. [What is `crictl`?](#3-what-is-crictl)
4. [Installing `crictl`](#4-installing-crictl)
5. [Using `crictl`: Common Operations](#5-using-crictl-common-operations)
6. [Comparison: `crictl` vs `docker`](#6-comparison-crictl-vs-docker)
7. [Summary](#7-summary)

---

## 1. Background: Why `containerd` and not Docker?

* Kubernetes deprecated Docker as a container runtime starting from **v1.20** and removed support in **v1.24**.
* Docker was never the actual container runtime for Kubernetes. It used **dockershim** as a middle layer.
* **containerd** is a CNCF-graduated project, lightweight, and directly implements the **Container Runtime Interface (CRI)**.

**Benefits of containerd over Docker:**

* Native CRI support (no shim layer)
* Lower resource consumption
* Faster startup and better stability
* Actively maintained by CNCF

---

## 2. Understanding `containerd`

* `containerd` is an industry-standard container runtime.
* Used by Kubernetes to manage the lifecycle of containers (run, stop, pull images).
* Designed to be embedded into a larger system, like Kubernetes.

Official site: [https://containerd.io](https://containerd.io)

---

## 3. What is `crictl`?

* `crictl` is a CLI tool to interact with container runtimes that implement the Kubernetes **CRI**.
* It is **runtime-agnostic** — works with `containerd`, `CRI-O`, etc.
* Think of it as a replacement for `docker` commands when troubleshooting Kubernetes nodes.

---

## 4. Installing `crictl`

Typical pattern: download the release binary for your OS/architecture and install it on the node where you troubleshoot. Configure the **runtime endpoint** (for example containerd’s socket) in `/etc/crictl.yaml` or via flags so the CLI talks to the same runtime the kubelet uses.

---

## 5. Using `crictl`: Common Operations

### View Pods

```bash
crictl pods            # List all pods on the node
crictl inspectp <podID> # Get detailed info on a specific pod
```

### View Containers

```bash
crictl ps -a           # List all containers (running and exited)
crictl inspect <cid>   # Get container details
```

### View Images

```bash
crictl images          # List all pulled images
```

### Logs, Exec, Stats

```bash
crictl logs <cid>              # View logs from container
crictl exec -it <cid> /bin/sh  # Exec into container
crictl stats                   # Resource usage (CPU/mem) by containers
```

### Troubleshooting Node Issues

```bash
crictl info                   # Show runtime info
crictl version                # Show CLI and runtime version
crictl rm <cid>               # Remove container
crictl rmi <image>            # Remove image
```

---

## 6. Comparison: `crictl` vs `docker`

| Operation           | `docker`                   | `crictl`                   |
| ------------------- | -------------------------- | -------------------------- |
| List containers     | `docker ps`                | `crictl ps`                |
| View logs           | `docker logs <cid>`        | `crictl logs <cid>`        |
| Exec into container | `docker exec -it <cid> sh` | `crictl exec -it <cid> sh` |
| Remove container    | `docker rm <cid>`          | `crictl rm <cid>`          |
| View images         | `docker images`            | `crictl images`            |
| Remove image        | `docker rmi <image>`       | `crictl rmi <image>`       |
| Inspect container   | `docker inspect <cid>`     | `crictl inspect <cid>`     |
| Container stats     | `docker stats`             | `crictl stats`             |

---

## 7. Summary

* `crictl` is an essential tool when working on Kubernetes nodes with CRI-compliant runtimes like `containerd`.
* It provides visibility into the low-level container and pod management.
* Understanding `crictl` helps when `kubectl` shows cluster intent but you need runtime-level evidence on a specific node.

---

## Hands-On Labs

Practice these concepts with guided lab exercises:

| Lab | Description |
|-----|-------------|
| [Lab 59: Container Runtime Interface — crictl](../../labmanuals/lab59-basics-crictl.md) | Install, configure, and use `crictl` for node-level container and pod troubleshooting |
| [Lab 03: kubectl Essentials](../../labmanuals/lab03-basics-kubectl-essentials.md) | Cluster-level interaction and troubleshooting workflows that complement node-level CRI tools |
