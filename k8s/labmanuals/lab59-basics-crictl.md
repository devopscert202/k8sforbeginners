# Lab 59: Container Runtime Interface — Hands-On with `crictl`

## Overview

When you troubleshoot Kubernetes at the **node level**, `kubectl` is not enough — it talks to the API server, not to the container runtime on a specific node. That is where **`crictl`** comes in.

`crictl` is a CLI tool that speaks directly to any container runtime that implements the **Container Runtime Interface (CRI)** — `containerd`, `CRI-O`, etc. Since Kubernetes removed Docker support in v1.24 and now uses `containerd` as the standard runtime, `crictl` is the go-to tool for inspecting pods, containers, and images at the runtime level.

In this lab you will install and configure `crictl`, practice its core commands for listing, inspecting, and troubleshooting pods and containers, and compare the output with what `kubectl` shows.

## Prerequisites

- A running Kubernetes cluster with SSH access to at least one node (Minikube, Kind with `docker exec`, kubeadm cluster, etc.)
- `kubectl` CLI tool installed and configured
- Root or sudo access on the node (most `crictl` commands require it)
- Completion of [Lab 03: kubectl Essentials](lab03-basics-kubectl-essentials.md) (recommended)

## Learning Objectives

By the end of this lab, you will be able to:

- Install and configure `crictl` on a Kubernetes node
- List pods and containers at the runtime level
- Inspect container details, view logs, and exec into containers using `crictl`
- Compare `crictl` output with `kubectl` output to understand the difference
- Use `crictl` to troubleshoot node-level container issues

---

## Concepts

### Why `crictl` and not Docker?

Kubernetes deprecated Docker as a container runtime starting from **v1.20** and removed support in **v1.24**. The standard runtime is now **containerd** (CNCF-graduated), which implements the CRI directly without a shim layer.

| Aspect | Docker (legacy) | containerd (current) |
|--------|-----------------|---------------------|
| CRI support | Needed dockershim | Native CRI |
| Resource usage | Higher (Docker daemon overhead) | Lower (lightweight) |
| Kubernetes support | Removed in v1.24 | Default runtime |
| CLI tool | `docker` | `crictl` |

### What is `crictl`?

- **Runtime-agnostic** — works with `containerd`, `CRI-O`, or any CRI-compliant runtime
- Provides **node-level** visibility into pods, containers, and images
- Think of it as the runtime counterpart to `kubectl`: `kubectl` shows cluster intent, `crictl` shows runtime reality on a single node

### When to use `crictl` vs `kubectl`

| Scenario | Use |
|----------|-----|
| Check if a Pod is scheduled and running | `kubectl get pods` |
| Check if the container actually started on a node | `crictl ps` |
| View container logs from the runtime | `crictl logs <container-id>` |
| Debug image pull issues on a node | `crictl images`, `crictl pull` |
| Inspect container resource usage on a node | `crictl stats` |
| Get runtime and version info | `crictl info`, `crictl version` |

---

## Exercise 1: Installing and Configuring `crictl`

### Step 1: Check if `crictl` is already installed

SSH into a node (or use `docker exec` for Kind nodes) and check:

```bash
crictl version
```

If installed, you'll see output like:

```
Version:  0.1.0
RuntimeName:  containerd
RuntimeVersion:  1.7.x
RuntimeApiVersion:  v1
```

If not found, proceed to Step 2.

### Step 2: Install `crictl`

Download and install the latest release:

```bash
VERSION="v1.29.0"
curl -L https://github.com/kubernetes-sigs/cri-tools/releases/download/${VERSION}/crictl-${VERSION}-linux-amd64.tar.gz -o crictl.tar.gz
sudo tar -C /usr/local/bin -xzf crictl.tar.gz
rm crictl.tar.gz
```

Verify:

```bash
crictl --version
```

### Step 3: Configure the runtime endpoint

`crictl` needs to know which socket to talk to. Create or verify the config file:

```bash
sudo cat /etc/crictl.yaml
```

For containerd (most common):

```yaml
runtime-endpoint: unix:///run/containerd/containerd.sock
image-endpoint: unix:///run/containerd/containerd.sock
timeout: 10
debug: false
```

If the file doesn't exist, create it:

```bash
sudo tee /etc/crictl.yaml <<EOF
runtime-endpoint: unix:///run/containerd/containerd.sock
image-endpoint: unix:///run/containerd/containerd.sock
timeout: 10
debug: false
EOF
```

For CRI-O, use `unix:///var/run/crio/crio.sock` instead.

### Step 4: Verify connectivity

```bash
sudo crictl info
```

Expected: JSON output showing runtime status, conditions, and configuration.

---

## Exercise 2: Listing Pods and Containers

### Step 1: List all pods on the node

```bash
sudo crictl pods
```

Expected output:

```
POD ID          CREATED        STATE   NAME                          NAMESPACE       ATTEMPT   RUNTIME
a1b2c3d4e5f6    2 hours ago    Ready   coredns-7db6d8ff4d-abc12      kube-system     0         (default)
f6e5d4c3b2a1    2 hours ago    Ready   kube-proxy-xyz98              kube-system     0         (default)
```

### Step 2: Filter pods by namespace

```bash
sudo crictl pods --namespace kube-system
```

### Step 3: Filter pods by name

```bash
sudo crictl pods --name coredns
```

### Step 4: Filter pods by state

```bash
sudo crictl pods --state ready
sudo crictl pods --state notready
```

### Step 5: List all containers

```bash
sudo crictl ps
```

This shows running containers. To include stopped containers:

```bash
sudo crictl ps -a
```

### Step 6: Compare with kubectl

Open a second terminal and compare:

```bash
kubectl get pods -A -o wide
```

Notice that `kubectl` shows the cluster view (all nodes), while `crictl` only shows pods on the current node.

---

## Exercise 3: Inspecting Containers and Pods

### Step 1: Get detailed pod information

Pick a pod ID from `crictl pods` and inspect it:

```bash
sudo crictl inspectp <pod-id>
```

This returns JSON with the pod's sandbox configuration, network namespace, labels, and annotations.

### Step 2: Get detailed container information

Pick a container ID from `crictl ps` and inspect it:

```bash
sudo crictl inspect <container-id>
```

Look for:
- **Image**: Which image is running
- **State**: Current state and exit code (if stopped)
- **Mounts**: Volume mounts attached to the container
- **Resources**: CPU/memory limits applied by the runtime

### Step 3: View container logs

```bash
sudo crictl logs <container-id>
```

Add flags for more control:

```bash
sudo crictl logs --tail 20 <container-id>
sudo crictl logs --since 2024-01-01T00:00:00Z <container-id>
```

### Step 4: Exec into a running container

```bash
sudo crictl exec -it <container-id> /bin/sh
```

Once inside, you can run diagnostic commands (`ls`, `cat /etc/resolv.conf`, `env`, etc.), then type `exit` to leave.

---

## Exercise 4: Working with Images

### Step 1: List images on the node

```bash
sudo crictl images
```

Expected output:

```
IMAGE                                TAG       IMAGE ID        SIZE
registry.k8s.io/coredns/coredns      v1.11.1   sha256:abc123   16.2MB
registry.k8s.io/etcd                  3.5.10    sha256:def456   102MB
registry.k8s.io/kube-apiserver        v1.29.0   sha256:ghi789   33.4MB
```

### Step 2: Pull an image

```bash
sudo crictl pull nginx:1.25-alpine
```

Verify it appears in the list:

```bash
sudo crictl images | grep nginx
```

### Step 3: Remove an unused image

```bash
sudo crictl rmi nginx:1.25-alpine
```

**Caution**: Do not remove images that are in use by running containers.

---

## Exercise 5: Runtime Information and Resource Stats

### Step 1: Check runtime version

```bash
sudo crictl version
```

### Step 2: View runtime configuration

```bash
sudo crictl info
```

This shows the runtime's status conditions (RuntimeReady, NetworkReady), CNI configuration, and more.

### Step 3: View container resource usage

```bash
sudo crictl stats
```

Expected output:

```
CONTAINER       CPU %   MEM            DISK          INODES
a1b2c3d4e5f6    0.15    12.34MB        0B            15
f6e5d4c3b2a1    0.05    8.12MB         0B            8
```

### Step 4: View stats for a specific container

```bash
sudo crictl stats <container-id>
```

---

## Exercise 6: Troubleshooting with `crictl`

### Scenario 1: Pod stuck in ContainerCreating

When `kubectl` shows a pod stuck in `ContainerCreating`, use `crictl` on the node:

```bash
sudo crictl pods --state notready
sudo crictl pods --name <pod-name>
```

Check the pod sandbox status — if there's no sandbox, the issue is likely network (CNI) or image-related.

### Scenario 2: Container keeps restarting (CrashLoopBackOff)

```bash
sudo crictl ps -a | grep <pod-name>
```

Look for exited containers. Get the last container's logs:

```bash
sudo crictl logs <exited-container-id>
```

Check the exit code:

```bash
sudo crictl inspect <exited-container-id> | grep -i exitcode
```

### Scenario 3: Image pull issues

Check what images are cached locally:

```bash
sudo crictl images | grep <image-name>
```

Try pulling manually to see the error:

```bash
sudo crictl pull <image:tag>
```

### Scenario 4: Cleaning up stopped containers and unused images

```bash
sudo crictl rm <stopped-container-id>
sudo crictl rmi <unused-image>
```

---

## `crictl` vs `docker` — Command Reference

| Operation | `docker` (legacy) | `crictl` |
|-----------|-------------------|----------|
| List containers | `docker ps` | `crictl ps` |
| List all (incl. stopped) | `docker ps -a` | `crictl ps -a` |
| View logs | `docker logs <cid>` | `crictl logs <cid>` |
| Exec into container | `docker exec -it <cid> sh` | `crictl exec -it <cid> sh` |
| Remove container | `docker rm <cid>` | `crictl rm <cid>` |
| List images | `docker images` | `crictl images` |
| Pull image | `docker pull <image>` | `crictl pull <image>` |
| Remove image | `docker rmi <image>` | `crictl rmi <image>` |
| Inspect container | `docker inspect <cid>` | `crictl inspect <cid>` |
| Container stats | `docker stats` | `crictl stats` |
| List pods | N/A | `crictl pods` |
| Inspect pod | N/A | `crictl inspectp <pod-id>` |
| Runtime info | `docker info` | `crictl info` |

---

## Lab Cleanup

No cluster-level cleanup is needed — `crictl` commands only interact with the local node runtime.

If you pulled a test image:

```bash
sudo crictl rmi nginx:1.25-alpine
```

---

## Key Takeaways

1. **`crictl` is the standard CLI** for troubleshooting containers at the node/runtime level
2. It works with any CRI-compliant runtime (`containerd`, `CRI-O`)
3. Use `kubectl` for cluster-level operations; use `crictl` for **node-level** investigation
4. Configure the runtime endpoint in `/etc/crictl.yaml`
5. Essential for debugging `ContainerCreating`, `CrashLoopBackOff`, and image pull issues at the source
6. `crictl pods` shows sandbox-level info that `kubectl` cannot provide

---

## Next Steps

1. **kubectl essentials**: Review [Lab 03: kubectl Essentials](lab03-basics-kubectl-essentials.md) for cluster-level commands
2. **Troubleshooting**: Apply `crictl` skills in [Lab 51: Kubelet and Node Troubleshooting](lab51-ts-kubelet-node.md)
3. **Pod failures**: Use runtime-level debugging in [Lab 50: Pod Failures](lab50-ts-pod-failures.md)

---

## Additional Reading

- [crictl documentation](https://github.com/kubernetes-sigs/cri-tools/blob/master/docs/crictl.md)
- [Kubernetes Container Runtimes](https://kubernetes.io/docs/setup/production-environment/container-runtimes/)
- [Debugging Kubernetes Nodes](https://kubernetes.io/docs/tasks/debug/debug-cluster/crictl/)

---

**Lab Created**: March 2026
**Compatible with**: Kubernetes 1.24+ (containerd as default runtime)
**Tested on**: kubeadm clusters, Kind (via docker exec)
