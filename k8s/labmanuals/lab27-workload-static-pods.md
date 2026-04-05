# Lab 27: Static Pods in Kubernetes

## Overview
In this lab, you will learn about Static Pods - a special type of Pod managed directly by the kubelet daemon on a specific node, rather than by the Kubernetes API server. You'll understand how static pods work, their use cases, and how they differ from regular pods managed by controllers like Deployments or ReplicaSets.

## Prerequisites
- A running Kubernetes cluster (Minikube, Kind, or any K8s cluster)
- `kubectl` CLI tool installed and configured
- Basic understanding of Pods (Lab 01)
- SSH or node access to your Kubernetes nodes (for some exercises)

## Learning Objectives
By the end of this lab, you will be able to:
- Understand what static pods are and how they work
- Differentiate between static pods and regular pods
- Configure and deploy static pods using the kubelet
- Locate and manage the static pod manifest directory
- Understand real-world use cases for static pods
- Troubleshoot static pod issues
- Identify which control plane components run as static pods

## Repository YAML Files

Under `k8s/labs/workloads/`:

| File | Description |
|------|-------------|
| `staticapache.yaml` | Example static Pod manifest (`Pod` `staticapache`, httpd) to copy to the node `staticPodPath` (e.g. Minikube `/etc/kubernetes/manifests/`). |

---

## What are Static Pods?

**Static Pods** are pods that are managed directly by the kubelet daemon on a specific node, without the API server observing them. The kubelet watches each static pod and restarts it if it crashes.

### Key Characteristics

1. **Kubelet-Managed**: Static pods are created and managed by the kubelet, not the Kubernetes control plane
2. **Node-Specific**: Each static pod is bound to a specific node
3. **Mirror Pods**: The kubelet creates a mirror pod on the API server for visibility (read-only)
4. **Auto-Restart**: If a static pod crashes, the kubelet automatically restarts it
5. **No Controllers**: Cannot be managed by Deployments, ReplicaSets, or other controllers

### Static Pods vs Regular Pods

| Feature | Static Pods | Regular Pods |
|---------|-------------|--------------|
| **Managed By** | Kubelet on specific node | Kubernetes API server |
| **Creation** | YAML files in manifest directory | API calls, kubectl commands |
| **Scheduling** | Cannot be scheduled elsewhere | Scheduled by kube-scheduler |
| **Deletion** | Delete manifest file | kubectl delete command |
| **Controllers** | No controller support | Can be managed by Deployments, etc. |
| **Visibility** | Mirror pod visible in API | Full API object |
| **Use Case** | Control plane components | Application workloads |

---

## How Static Pods Work

### The Static Pod Lifecycle

```
┌─────────────────────────────────────────────────────────┐
│                    Kubernetes Node                       │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │  /etc/kubernetes/manifests/                       │  │
│  │  ├── staticapache.yaml                            │  │
│  │  ├── etcd.yaml                                    │  │
│  │  └── kube-apiserver.yaml                          │  │
│  └──────────────────┬───────────────────────────────┘  │
│                     │                                    │
│                     │ Watches directory                  │
│                     ▼                                    │
│  ┌──────────────────────────────────────────────────┐  │
│  │            Kubelet Process                        │  │
│  │  • Reads manifest files                           │  │
│  │  • Creates/updates pods                           │  │
│  │  • Monitors pod health                            │  │
│  │  • Restarts failed pods                           │  │
│  │  • Creates mirror pods in API                     │  │
│  └──────────────────┬───────────────────────────────┘  │
│                     │                                    │
│                     │ Creates mirror pod                 │
│                     ▼                                    │
└─────────────────────────────────────────────────────────┘
                      │
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│              Kubernetes API Server                       │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Mirror Pod (Read-Only)                           │  │
│  │  • Visible via kubectl get pods                   │  │
│  │  • Cannot be deleted via API                      │  │
│  │  • Shows pod status and logs                      │  │
│  │  • Name suffix: -<node-name>                      │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### Static Pod Manifest Directory

The kubelet monitors a directory for static pod manifests. Common locations:
- `/etc/kubernetes/manifests/` (default on most distributions)
- Configured via kubelet's `--pod-manifest-path` flag
- Or via kubelet config file: `staticPodPath` field

---

## Exercise 1: Understanding Static Pod Configuration

### Step 1: Check Kubelet Configuration

First, let's find where the kubelet is configured to look for static pod manifests.

```bash
# On a Kubernetes node, check kubelet configuration
# Note: This requires node access (SSH to node or run in Minikube/Kind)

# For Minikube:
minikube ssh

# Check kubelet config file
sudo cat /var/lib/kubelet/config.yaml | grep staticPodPath
```

**Expected Output:**
```yaml
staticPodPath: /etc/kubernetes/manifests
```

### Step 2: List Existing Static Pods

```bash
# List files in the static pod directory
ls -la /etc/kubernetes/manifests/

# Exit back to your local machine
exit
```

**Expected Output:**
```
total 16
drwxr-xr-x 2 root root 4096 Mar 16 10:00 .
drwxr-xr-x 4 root root 4096 Mar 16 09:55 ..
-rw------- 1 root root 2310 Mar 16 09:55 etcd.yaml
-rw------- 1 root root 3867 Mar 16 09:55 kube-apiserver.yaml
-rw------- 1 root root 3394 Mar 16 09:55 kube-controller-manager.yaml
-rw------- 1 root root 1435 Mar 16 09:55 kube-scheduler.yaml
```

### Step 3: View Control Plane Static Pods

Most Kubernetes control plane components run as static pods!

```bash
# List all pods in kube-system namespace
kubectl get pods -n kube-system

# Filter for control plane pods (static pods have node name suffix)
kubectl get pods -n kube-system -o wide | grep -E "(apiserver|etcd|controller|scheduler)"
```

**Expected Output:**
```
NAME                               READY   STATUS    RESTARTS   AGE   NODE
etcd-minikube                      1/1     Running   0          5m    minikube
kube-apiserver-minikube            1/1     Running   0          5m    minikube
kube-controller-manager-minikube   1/1     Running   0          5m    minikube
kube-scheduler-minikube            1/1     Running   0          5m    minikube
```

**Key Observation**: Notice the `-minikube` suffix (or your node name). This indicates these are mirror pods of static pods.

---

## Exercise 2: Creating Your First Static Pod

### Step 1: Review the Static Pod Manifest

Navigate to the workloads directory:
```bash
cd k8s/labs/workloads
```

Examine `staticapache.yaml`:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: staticapache
  labels:
    Type: static
spec:
  containers:
  - name: mycontainer
    image: docker.io/httpd
    ports:
    - containerPort: 80
```

**Understanding the Manifest:**
- **apiVersion: v1**: Uses core Pod API
- **kind: Pod**: Static pods must be Pod kind (no Deployments/ReplicaSets)
- **name: staticapache**: Base name (will get node suffix)
- **labels.Type: static**: Custom label for identification
- **image: docker.io/httpd**: Apache HTTP server
- **containerPort: 80**: Exposes HTTP port

### Step 2: Deploy the Static Pod (Method 1: Copy to Node)

```bash
# For Minikube: Copy manifest to static pod directory
minikube ssh "sudo cp /hosthome/<your-user>/k8sforbeginners/k8s/labs/workloads/staticapache.yaml /etc/kubernetes/manifests/"

# Alternative: Use kubectl to copy file to node
# First, get the file content
cat staticapache.yaml | minikube ssh "sudo tee /etc/kubernetes/manifests/staticapache.yaml"
```

### Step 3: Verify the Static Pod

Wait a few seconds for the kubelet to detect and create the pod.

```bash
# List all pods (should see the static pod with node suffix)
kubectl get pods -A | grep staticapache

# Get detailed information
kubectl get pod staticapache-<node-name> -o wide

# Example for Minikube:
kubectl get pod staticapache-minikube -o wide
```

**Expected Output:**
```
NAME                   READY   STATUS    RESTARTS   AGE   NODE
staticapache-minikube  1/1     Running   0          30s   minikube
```

### Step 4: Inspect the Pod Details

```bash
# Describe the pod
kubectl describe pod staticapache-minikube

# Check the annotations
kubectl get pod staticapache-minikube -o yaml | grep -A 5 annotations
```

**Key Annotations to Notice:**
```yaml
annotations:
  kubernetes.io/config.source: file
  kubernetes.io/config.mirror: <node-ip>
```

These annotations indicate this is a mirror pod for a static pod.

---

## Exercise 3: Static Pod Behavior and Management

### Step 1: Try to Delete the Static Pod (Via kubectl)

```bash
# Attempt to delete the mirror pod
kubectl delete pod staticapache-minikube
```

**What Happens:**
1. The mirror pod is deleted from the API server
2. The kubelet detects the missing pod
3. The kubelet recreates the pod immediately
4. A new mirror pod appears in the API server

```bash
# Verify the pod is back
kubectl get pods | grep staticapache

# Check the AGE - it should be very recent
```

### Step 2: Proper Way to Delete a Static Pod

To truly delete a static pod, remove its manifest file:

```bash
# SSH to the node
minikube ssh

# Remove the manifest file
sudo rm /etc/kubernetes/manifests/staticapache.yaml

# Exit the node
exit

# Verify the pod is gone (wait 30-60 seconds)
kubectl get pods -A | grep staticapache
```

**Expected Output:**
```
No resources found
```

### Step 3: Modify a Static Pod

Let's recreate and then modify the static pod:

```bash
# Recreate the static pod
cat k8s/labs/workloads/staticapache.yaml | minikube ssh "sudo tee /etc/kubernetes/manifests/staticapache.yaml"

# Wait for pod to be running
kubectl wait --for=condition=ready pod -l Type=static --timeout=60s

# Now modify the manifest on the node
minikube ssh "sudo sed -i 's/docker.io\/httpd/nginx:1.21/g' /etc/kubernetes/manifests/staticapache.yaml"

# Watch the pod get recreated with new image
kubectl get pods -w | grep staticapache
```

**What Happens:**
- The kubelet detects the manifest change
- The old pod is terminated
- A new pod is created with the updated configuration
- The mirror pod reflects the changes

---

## Exercise 4: Static Pods vs Regular Pods - Practical Comparison

### Step 1: Deploy a Regular Pod

```bash
# Create a regular pod using kubectl
kubectl run regular-apache --image=httpd --port=80

# List both pods
kubectl get pods
```

### Step 2: Compare Pod Characteristics

```bash
# Compare the two pods
kubectl get pods -o custom-columns=\
NAME:.metadata.name,\
NODE:.spec.nodeName,\
OWNER:.metadata.ownerReferences[0].kind,\
CONFIG-SOURCE:.metadata.annotations.'kubernetes\.io/config\.source'
```

**Expected Output:**
```
NAME                   NODE       OWNER   CONFIG-SOURCE
regular-apache         minikube   <none>  api
staticapache-minikube  minikube   Node    file
```

### Step 3: Try to Modify Pods

```bash
# Try to scale the regular pod (works)
kubectl scale deployment regular-apache --replicas=3
# Note: This fails because we created a pod, not a deployment

# Try to edit the static pod mirror (fails)
kubectl edit pod staticapache-minikube
# Any changes are rejected or overwritten by kubelet
```

### Step 4: Node Affinity Test

```bash
# Static pods are tied to their node
kubectl get pod staticapache-minikube -o yaml | grep nodeName

# Try to describe scheduling info
kubectl describe pod staticapache-minikube | grep -A 5 "Node:"
```

**Key Observation**: Static pods cannot be scheduled to different nodes.

---

## Exercise 5: Real-World Static Pod Use Cases

### Use Case 1: Control Plane Components

As we've seen, Kubernetes control plane components run as static pods:

```bash
# View control plane static pods
kubectl get pods -n kube-system -o wide | grep -E "apiserver|etcd|controller|scheduler"

# Examine the etcd static pod manifest (on node)
minikube ssh "sudo cat /etc/kubernetes/manifests/etcd.yaml" | head -30
```

**Why Static Pods for Control Plane?**
- **Bootstrapping**: Control plane must start before API server is available
- **Reliability**: Kubelet ensures critical components restart automatically
- **Node-Local**: Control plane components need to run on control plane nodes
- **No Dependencies**: Don't require Deployments or ReplicaSets

### Use Case 2: Node-Local Monitoring Agents

Create a static pod for node monitoring:

```bash
# Create a node exporter static pod manifest
cat <<EOF > node-exporter-static.yaml
apiVersion: v1
kind: Pod
metadata:
  name: node-exporter
  labels:
    app: node-exporter
    type: static-monitoring
spec:
  hostNetwork: true
  hostPID: true
  containers:
  - name: node-exporter
    image: prom/node-exporter:v1.5.0
    args:
    - --path.procfs=/host/proc
    - --path.sysfs=/host/sys
    - --collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)
    ports:
    - containerPort: 9100
      hostPort: 9100
      protocol: TCP
    volumeMounts:
    - name: proc
      mountPath: /host/proc
      readOnly: true
    - name: sys
      mountPath: /host/sys
      readOnly: true
  volumes:
  - name: proc
    hostPath:
      path: /proc
  - name: sys
    hostPath:
      path: /sys
EOF

# Deploy as static pod
cat node-exporter-static.yaml | minikube ssh "sudo tee /etc/kubernetes/manifests/node-exporter.yaml"

# Verify deployment
kubectl get pods | grep node-exporter
```

**Why Static Pod for Node Exporter?**
- Guaranteed to run on every node
- Survives cluster upgrades
- Direct access to host metrics
- No scheduler dependency

### Use Case 3: Emergency Debug Pod

Static pods can serve as emergency access when the control plane is unhealthy:

```bash
# Create an emergency debug pod
cat <<EOF > debug-static.yaml
apiVersion: v1
kind: Pod
metadata:
  name: debug-pod
  labels:
    purpose: emergency-debug
spec:
  hostNetwork: true
  hostPID: true
  containers:
  - name: debug
    image: nicolaka/netshoot:latest
    command: ["/bin/bash"]
    args: ["-c", "sleep infinity"]
    securityContext:
      privileged: true
EOF

# Deploy only when needed
cat debug-static.yaml | minikube ssh "sudo tee /etc/kubernetes/manifests/debug-pod.yaml"
```

---

## Exercise 6: Troubleshooting Static Pods

### Problem 1: Static Pod Not Appearing

```bash
# Check if kubelet is watching the correct directory
minikube ssh "sudo systemctl status kubelet | grep staticPodPath"

# Verify manifest file exists and has correct permissions
minikube ssh "ls -la /etc/kubernetes/manifests/"

# Check for YAML syntax errors
minikube ssh "sudo cat /etc/kubernetes/manifests/staticapache.yaml"

# View kubelet logs
minikube ssh "sudo journalctl -u kubelet -n 50 | grep static"
```

### Problem 2: Static Pod CrashLooping

```bash
# Check pod status
kubectl get pod staticapache-minikube

# View pod logs
kubectl logs staticapache-minikube

# Describe for events
kubectl describe pod staticapache-minikube

# Check container runtime logs on node
minikube ssh "sudo crictl ps -a | grep staticapache"
```

### Problem 3: Cannot Delete Static Pod

```bash
# Verify you're deleting the manifest, not the mirror pod
minikube ssh "ls /etc/kubernetes/manifests/ | grep staticapache"

# Remove the manifest file
minikube ssh "sudo rm /etc/kubernetes/manifests/staticapache.yaml"

# Verify deletion (wait 60 seconds)
kubectl get pods -A | grep staticapache
```

---

## Key Concepts Summary

### What Are Static Pods?
- Pods managed by kubelet, not the API server
- Defined by manifest files in a directory
- Automatically restarted by kubelet if they fail
- Visible in API as read-only mirror pods

### When to Use Static Pods
1. **Control Plane Components**: API server, etcd, scheduler, controller manager
2. **Node-Local Services**: Monitoring agents, log collectors
3. **Bootstrapping**: Components needed before API server is available
4. **Critical Infrastructure**: Must-run services on specific nodes

### When NOT to Use Static Pods
1. **Application Workloads**: Use Deployments instead
2. **Scalable Services**: Use ReplicaSets or StatefulSets
3. **Load-Balanced Apps**: Use Services with Deployments
4. **Multi-Node Apps**: Use DaemonSets for all-node deployment

### Static Pod Characteristics
- **Location**: `/etc/kubernetes/manifests/` (default)
- **Management**: Via file system operations
- **Naming**: Base name + node name suffix
- **Deletion**: Remove manifest file
- **Modification**: Edit manifest file (pod recreates)

---

## Best Practices

### 1. Use Appropriate Pod Types

```bash
# Static Pods: Control plane, node-specific services
# DaemonSets: All-node services (monitoring, logging)
# Deployments: Application workloads
# StatefulSets: Stateful applications
```

### 2. Label Static Pods Clearly

```yaml
metadata:
  labels:
    component: control-plane
    tier: infrastructure
    managed-by: kubelet
```

### 3. Document Static Pod Purpose

```yaml
metadata:
  annotations:
    description: "Critical monitoring agent - do not remove"
    owner: "platform-team@example.com"
    documentation: "https://wiki.example.com/static-pods"
```

### 4. Monitor Static Pod Health

```bash
# Create alerts for static pod failures
kubectl get pods -l managed-by=kubelet -o json | \
  jq '.items[] | select(.status.phase != "Running") | .metadata.name'
```

### 5. Backup Static Pod Manifests

```bash
# Backup manifests regularly
minikube ssh "sudo tar -czf /tmp/static-pods-backup.tar.gz /etc/kubernetes/manifests/"
minikube cp minikube:/tmp/static-pods-backup.tar.gz ./static-pods-backup.tar.gz
```

---

## Cleanup

Remove all static pods we created:

```bash
# Remove static pods
minikube ssh "sudo rm /etc/kubernetes/manifests/staticapache.yaml"
minikube ssh "sudo rm /etc/kubernetes/manifests/node-exporter.yaml"
minikube ssh "sudo rm /etc/kubernetes/manifests/debug-pod.yaml"

# Remove regular pod
kubectl delete pod regular-apache --ignore-not-found

# Verify cleanup
kubectl get pods -A | grep -E "(staticapache|node-exporter|debug-pod|regular-apache)"
```

---

## Additional Resources

### Official Documentation
- [Kubernetes Static Pods](https://kubernetes.io/docs/tasks/configure-pod-container/static-pod/)
- [Kubelet Configuration](https://kubernetes.io/docs/reference/command-line-tools-reference/kubelet/)
- [Pod Lifecycle](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/)

### Related Labs
- Lab 01: Basic Pod Operations
- Lab 26: DaemonSets (alternative to static pods for all-node deployment)
- Lab 09: Health Probes (applicable to static pods)

### Troubleshooting Resources
- [Debugging Kubernetes Nodes](https://kubernetes.io/docs/tasks/debug/debug-cluster/)
- [Kubelet Logs](https://kubernetes.io/docs/tasks/debug/debug-cluster/crictl/)

---

## Challenge Exercises

### Challenge 1: Multi-Container Static Pod
Create a static pod with an nginx container and a sidecar container that serves logs.

**Hints:**
- Use `emptyDir` volume for shared logs
- Configure nginx to write access logs to shared volume
- Create a second container to tail the logs

### Challenge 2: Static Pod with Init Container
Deploy a static pod that uses an init container to check if the API server is reachable before starting.

**Hints:**
- Use `initContainers` in the manifest
- Use `kubectl` or `curl` to check API server
- Configure proper service account permissions

### Challenge 3: Static Pod Monitoring Dashboard
Create a script that monitors all static pods across the cluster and reports their health.

**Hints:**
- Identify static pods by annotations
- Check pod status and restart counts
- Output formatted report (CSV or JSON)

### Challenge 4: Migrate from Static Pod to DaemonSet
Convert the node-exporter static pod to a DaemonSet deployment.

**Hints:**
- Create DaemonSet manifest
- Use node selectors for control plane nodes
- Remove static pod manifest
- Verify DaemonSet deployment

---

## Conclusion

In this lab, you've learned about Kubernetes Static Pods - a fundamental concept for running critical infrastructure components. You now understand:

- How static pods differ from regular pods
- The kubelet's role in managing static pods
- When and why to use static pods
- How to create, modify, and delete static pods
- Real-world use cases and best practices

Static pods are essential for Kubernetes control plane operations and provide a reliable way to run node-specific infrastructure components. While most application workloads should use Deployments or StatefulSets, static pods remain crucial for the foundational components that make Kubernetes work.

**Next Steps:**
- Explore Lab 36 for frontend application deployment patterns
- Review DaemonSet lab for cluster-wide service deployment
- Study control plane architecture to understand static pod usage
- Practice troubleshooting static pod issues in a test cluster

---

**Lab Complete!** You now have a solid understanding of Kubernetes Static Pods and their role in the Kubernetes ecosystem.
