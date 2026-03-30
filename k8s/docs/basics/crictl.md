# CRI-based Kubernetes Operations with `crictl` - Lab Guide for Learners

## Table of Contents

1. [Background: Why `containerd` and not Docker?](#background)
2. [Understanding `containerd`](#understanding-containerd)
3. [What is `crictl`?](#what-is-crictl)
4. [Installing `crictl`](#installing-crictl)
5. [Using `crictl`: Common Operations](#using-crictl)

   * [View Pods](#view-pods)
   * [View Containers](#view-containers)
   * [View Images](#view-images)
   * [Logs, Exec, Stats](#logs-exec-stats)
   * [Troubleshooting Node Issues](#troubleshooting-node-issues)
6. [Comparison: `crictl` vs `docker`](#comparison-table)
7. [Hands-On Lab Exercises](#hands-on-lab-exercises)
8. [Summary](#summary)

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

```bash
# Download the binary
VERSION="v1.28.0"
curl -LO https://github.com/kubernetes-sigs/cri-tools/releases/download/$VERSION/crictl-$VERSION-linux-amd64.tar.gz

# Extract and move
sudo tar -C /usr/local/bin -xzf crictl-$VERSION-linux-amd64.tar.gz
```

Optionally, configure default runtime endpoint:

```bash
echo 'runtime-endpoint: unix:///run/containerd/containerd.sock' | sudo tee /etc/crictl.yaml
```

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

## 6. Comparison Table: `crictl` vs `docker`

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

## 7. Hands-On Lab Exercises

### Lab 1: List All Pods and Inspect One

```bash
crictl pods
crictl inspectp <podID>
```

### Lab 2: Find Container of a Pod and Check Logs

```bash
crictl ps -a | grep nginx
crictl logs <cid>
```

### Lab 3: Troubleshoot Node Container Issues

```bash
crictl info
crictl stats
crictl exec -it <cid> sh
```

### Lab 4: Remove Unused Containers and Images

```bash
crictl ps -a
crictl rm <cid>
crictl images
crictl rmi <image>
```

---

## 8. Summary

* `crictl` is an essential tool when working on Kubernetes nodes with CRI-compliant runtimes like `containerd`.
* It provides visibility into the low-level container and pod management.
* Understanding and practicing with `crictl` ensures you're comfortable even when `kubectl` isn't enough.

