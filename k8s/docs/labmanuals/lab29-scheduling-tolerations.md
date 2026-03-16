# Lab 29: Pod Scheduling with Taints and Tolerations

## Overview
In this lab, you will learn how to use Taints and Tolerations to control which pods can be scheduled on specific nodes. Taints repel pods from nodes, while tolerations allow pods to overcome those taints. This is the opposite of Node Affinity, which attracts pods to nodes.

## Prerequisites
- A running Kubernetes cluster with multiple nodes
- `kubectl` CLI tool installed and configured
- Basic understanding of Pods and scheduling
- Completion of Lab 09 (NodeSelector) recommended

## Learning Objectives
By the end of this lab, you will be able to:
- Understand taints and tolerations concepts
- Apply taints to nodes
- Create pods with tolerations
- Understand taint effects (NoSchedule, PreferNoSchedule, NoExecute)
- Use taints for dedicated nodes and workload isolation
- Troubleshoot taint-related scheduling issues

---

## Understanding Taints and Tolerations

### What are Taints?
**Taints** are properties applied to nodes that repel pods. They mark a node as unsuitable for certain pods unless those pods explicitly tolerate the taint.

### What are Tolerations?
**Tolerations** are applied to pods and allow (but do not require) pods to schedule onto nodes with matching taints.

### Key Analogy
Think of taints as "No Entry" signs on nodes, and tolerations as "special passes" that allow specific pods to enter anyway.

### Taints vs Node Affinity

| Feature | Taints & Tolerations | Node Affinity |
|---------|---------------------|---------------|
| **Direction** | Nodes repel pods (defensive) | Pods attracted to nodes (selective) |
| **Default Behavior** | Pods rejected unless they tolerate | Pods schedule anywhere unless affinity specified |
| **Primary Use** | Dedicated nodes, special hardware | Workload placement preferences |
| **Approach** | Negative (exclude by default) | Positive (include based on rules) |

---

## Understanding Taint Effects

### Three Taint Effects

| Effect | Description | Impact on Existing Pods |
|--------|-------------|------------------------|
| **NoSchedule** | New pods won't schedule unless they tolerate | Existing pods continue running |
| **PreferNoSchedule** | Scheduler tries to avoid, but not guaranteed | Existing pods continue running |
| **NoExecute** | New pods won't schedule; existing pods evicted if they don't tolerate | Evicts non-tolerant pods |

### Taint Syntax

```bash
kubectl taint nodes <node-name> <key>=<value>:<effect>
```

Examples:
```bash
kubectl taint nodes worker-1 environment=production:NoSchedule
kubectl taint nodes worker-2 hardware=gpu:PreferNoSchedule
kubectl taint nodes worker-3 maintenance=true:NoExecute
```

---

## Exercise 1: View Node Taints

### Step 1: Check Existing Taints

View all nodes and their taints:

```bash
kubectl get nodes -o custom-columns=NAME:.metadata.name,TAINTS:.spec.taints
```

### Step 2: Describe Node for Taints

Get detailed taint information:

```bash
kubectl describe node <node-name> | grep -A 5 Taints
```

Example output:
```
Taints:             node-role.kubernetes.io/control-plane:NoSchedule
```

**Note:** Control plane nodes typically have a taint preventing regular workloads from scheduling on them.

### Step 3: Check Control Plane Taint

View control plane node taints:

```bash
kubectl describe node <control-plane-node> | grep Taints
```

You'll see:
```
Taints:  node-role.kubernetes.io/control-plane:NoSchedule
```

This prevents user pods from scheduling on the control plane.

---

## Exercise 2: Apply Taints to Nodes

### Step 1: Taint a Node for Production Environment

Add a taint to mark a node as production-only:

```bash
kubectl taint nodes <node-name> environment=production:NoSchedule
```

Example:
```bash
kubectl taint nodes worker-1 environment=production:NoSchedule
```

Expected output:
```
node/worker-1 tainted
```

### Step 2: Verify the Taint

Check the taint was applied:

```bash
kubectl describe node worker-1 | grep -A 3 Taints
```

Expected output:
```
Taints:             environment=production:NoSchedule
```

### Step 3: Add Another Taint

You can add multiple taints to a node:

```bash
kubectl taint nodes worker-1 dedicated=database:NoSchedule
```

Verify:

```bash
kubectl get node worker-1 -o jsonpath='{.spec.taints}' | jq
```

---

## Exercise 3: Deploy Pod Without Toleration

### Step 1: Review the No-Toleration Pod

Navigate to the tolerations labs directory:

```bash
cd k8s/labs/scheduling/tolerations
```

Examine `no-tolerations-pod.yaml`:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: no-tolerations-pod
spec:
  containers:
  - name: nginx
    image: nginx
    ports:
    - containerPort: 80
#this will not run anywhere
```

This pod has NO tolerations defined.

### Step 2: Deploy the Pod

Apply the manifest:

```bash
kubectl apply -f no-tolerations-pod.yaml
```

Expected output:
```
pod/no-tolerations-pod created
```

### Step 3: Check Pod Status

View pod status:

```bash
kubectl get pod no-tolerations-pod
```

Expected output (if all nodes are tainted):
```
NAME                 READY   STATUS    RESTARTS   AGE
no-tolerations-pod   0/1     Pending   0          30s
```

The pod remains **Pending** because it cannot tolerate any tainted nodes.

### Step 4: Investigate Scheduling Failure

Check why the pod isn't scheduling:

```bash
kubectl describe pod no-tolerations-pod
```

Look for events:
```
Events:
  Type     Reason            Age   From               Message
  ----     ------            ----  ----               -------
  Warning  FailedScheduling  45s   default-scheduler  0/3 nodes are available: 1 node(s) had untolerated taint {environment: production}, 2 node(s) had untolerated taint {node-role.kubernetes.io/control-plane: }
```

This tells us the pod cannot schedule because it doesn't tolerate the node taints.

---

## Exercise 4: Deploy Pod With Toleration

### Step 1: Review the Toleration Pod

Examine `tolerations-pod.yaml`:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: toleration-production-pod
spec:
  tolerations:
  - key: "environment"
    operator: "Equal"
    value: "production"
    effect: "NoSchedule"
  containers:
  - name: nginx
    image: nginx
    ports:
    - containerPort: 80
```

**Understanding the toleration:**
- `key: "environment"` - Matches taint key
- `operator: "Equal"` - Exact match required
- `value: "production"` - Matches taint value
- `effect: "NoSchedule"` - Tolerates NoSchedule effect

This toleration matches the taint: `environment=production:NoSchedule`

### Step 2: Deploy the Pod

Apply the manifest:

```bash
kubectl apply -f tolerations-pod.yaml
```

Expected output:
```
pod/toleration-production-pod created
```

### Step 3: Verify Pod Scheduling

Check pod status:

```bash
kubectl get pod toleration-production-pod -o wide
```

Expected output:
```
NAME                        READY   STATUS    RESTARTS   AGE   IP           NODE
toleration-production-pod   1/1     Running   0          15s   10.244.1.7   worker-1
```

The pod successfully scheduled on the tainted node because it has a matching toleration!

### Step 4: Compare Both Pods

View both pods:

```bash
kubectl get pods -o custom-columns=NAME:.metadata.name,STATUS:.status.phase,NODE:.spec.nodeName
```

Expected output:
```
NAME                        STATUS    NODE
no-tolerations-pod          Pending   <none>
toleration-production-pod   Running   worker-1
```

---

## Exercise 5: Toleration Operators

### Understanding Toleration Operators

| Operator | Behavior | Use Case |
|----------|----------|----------|
| **Equal** | key, value, and effect must match exactly | Specific taint matching |
| **Exists** | key and effect must match (any value) | Match any value for a key |

### Step 1: Create Toleration with Exists Operator

Create a pod that tolerates any value for the `environment` key:

```bash
cat <<EOF > exists-toleration-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: exists-toleration-pod
spec:
  tolerations:
  - key: "environment"
    operator: "Exists"
    effect: "NoSchedule"
  containers:
  - name: nginx
    image: nginx
EOF
```

**This toleration matches:**
- `environment=production:NoSchedule`
- `environment=staging:NoSchedule`
- `environment=<any-value>:NoSchedule`

### Step 2: Deploy and Verify

Apply the manifest:

```bash
kubectl apply -f exists-toleration-pod.yaml
```

Check where it scheduled:

```bash
kubectl get pod exists-toleration-pod -o wide
```

This pod can schedule on any node with `environment` taint, regardless of value.

---

## Exercise 6: Wildcard Toleration

### Step 1: Create a Pod That Tolerates All Taints

Create a pod with a wildcard toleration:

```bash
cat <<EOF > wildcard-toleration-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: wildcard-toleration-pod
spec:
  tolerations:
  - operator: "Exists"
  containers:
  - name: nginx
    image: nginx
EOF
```

**This toleration:**
- Has NO key specified
- `operator: Exists`
- Matches ALL taints on ALL nodes

### Step 2: Deploy the Pod

Apply the manifest:

```bash
kubectl apply -f wildcard-toleration-pod.yaml
```

### Step 3: Verify Scheduling

Check pod placement:

```bash
kubectl get pod wildcard-toleration-pod -o wide
```

This pod can schedule on ANY node, even those with taints, including the control plane!

**Warning:** Use wildcard tolerations carefully. They bypass all taint restrictions.

---

## Exercise 7: NoExecute Taint Effect

### Step 1: Understanding NoExecute

**NoExecute** effect:
- Prevents new pods from scheduling
- Evicts existing pods that don't tolerate the taint
- Pods can specify `tolerationSeconds` to delay eviction

### Step 2: Deploy Pods Before Tainting

First, deploy pods without tolerations:

```bash
cat <<EOF > test-pods.yaml
apiVersion: v1
kind: Pod
metadata:
  name: test-pod-1
spec:
  containers:
  - name: nginx
    image: nginx
  nodeSelector:
    kubernetes.io/hostname: <node-name>
---
apiVersion: v1
kind: Pod
metadata:
  name: test-pod-2
spec:
  containers:
  - name: nginx
    image: nginx
  nodeSelector:
    kubernetes.io/hostname: <node-name>
EOF
```

Replace `<node-name>` with your worker node name (e.g., `worker-2`), then apply:

```bash
kubectl apply -f test-pods.yaml
```

Verify both pods are running:

```bash
kubectl get pods -o wide
```

### Step 3: Apply NoExecute Taint

Now taint the node with NoExecute:

```bash
kubectl taint nodes <node-name> maintenance=true:NoExecute
```

Example:
```bash
kubectl taint nodes worker-2 maintenance=true:NoExecute
```

### Step 4: Observe Pod Eviction

Immediately check pods:

```bash
kubectl get pods -o wide
```

Expected behavior:
- `test-pod-1` and `test-pod-2` will be Terminating
- Pods are evicted because they don't tolerate the NoExecute taint

Watch real-time eviction:

```bash
kubectl get pods -w
```

Press Ctrl+C to stop watching.

### Step 5: Deploy Pod With NoExecute Toleration

Create a pod that tolerates NoExecute:

```bash
cat <<EOF > noexecute-toleration-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: noexecute-toleration-pod
spec:
  tolerations:
  - key: "maintenance"
    operator: "Equal"
    value: "true"
    effect: "NoExecute"
  containers:
  - name: nginx
    image: nginx
  nodeSelector:
    kubernetes.io/hostname: <node-name>
EOF
```

Replace `<node-name>` with the tainted node, then apply:

```bash
kubectl apply -f noexecute-toleration-pod.yaml
```

Verify it runs on the tainted node:

```bash
kubectl get pod noexecute-toleration-pod -o wide
```

---

## Exercise 8: TolerationSeconds (Delayed Eviction)

### Step 1: Understanding TolerationSeconds

`tolerationSeconds` specifies how long a pod can remain on a node after the taint is added before being evicted.

**Use Cases:**
- Graceful degradation
- Time for horizontal scaling to add capacity
- Temporary taint conditions

### Step 2: Create Pod With TolerationSeconds

Create a pod that tolerates NoExecute for 30 seconds:

```bash
cat <<EOF > delayed-eviction-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: delayed-eviction-pod
spec:
  tolerations:
  - key: "maintenance"
    operator: "Equal"
    value: "true"
    effect: "NoExecute"
    tolerationSeconds: 30
  containers:
  - name: nginx
    image: nginx
EOF
```

**Behavior:**
- Pod can schedule on nodes with `maintenance=true:NoExecute` taint
- If taint is added after pod is running, pod has 30 seconds before eviction

### Step 3: Test Delayed Eviction (Optional)

Remove the existing taint:

```bash
kubectl taint nodes <node-name> maintenance:NoExecute-
```

Deploy the pod:

```bash
kubectl apply -f delayed-eviction-pod.yaml
```

Wait for it to be running, then re-apply the taint:

```bash
kubectl taint nodes <node-name> maintenance=true:NoExecute
```

Watch the pod:

```bash
kubectl get pods -w
```

The pod will remain Running for 30 seconds, then transition to Terminating.

---

## Exercise 9: PreferNoSchedule Taint Effect

### Step 1: Understanding PreferNoSchedule

**PreferNoSchedule** is a soft constraint:
- Scheduler tries to avoid the node
- If no other nodes available, pod can still schedule there
- Does NOT evict existing pods

### Step 2: Create PreferNoSchedule Taint

Remove previous taints and add PreferNoSchedule:

```bash
# Remove old taints
kubectl taint nodes worker-1 environment:NoSchedule-
kubectl taint nodes worker-1 dedicated:NoSchedule-

# Add PreferNoSchedule taint
kubectl taint nodes worker-1 disktype=slow:PreferNoSchedule
```

### Step 3: Deploy Multiple Pods

Deploy several pods without tolerations:

```bash
cat <<EOF > multiple-pods.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: test-deployment
spec:
  replicas: 5
  selector:
    matchLabels:
      app: test-app
  template:
    metadata:
      labels:
        app: test-app
    spec:
      containers:
      - name: nginx
        image: nginx
EOF
```

Apply it:

```bash
kubectl apply -f multiple-pods.yaml
```

### Step 4: Observe Scheduling Behavior

Check pod distribution:

```bash
kubectl get pods -l app=test-app -o wide
```

**Expected behavior:**
- Most pods schedule on nodes without the taint
- Some pods MAY schedule on the tainted node if resources are constrained

The scheduler prefers to avoid the tainted node but doesn't strictly prohibit it.

---

## Exercise 10: Dedicated Nodes Use Case

### Step 1: Create Dedicated GPU Node

Simulate a dedicated GPU node:

```bash
kubectl taint nodes <node-name> hardware=gpu:NoSchedule
kubectl label nodes <node-name> hardware=gpu
```

### Step 2: Deploy GPU Workload

Create a pod that requires GPU:

```bash
cat <<EOF > gpu-workload.yaml
apiVersion: v1
kind: Pod
metadata:
  name: gpu-workload
spec:
  tolerations:
  - key: "hardware"
    operator: "Equal"
    value: "gpu"
    effect: "NoSchedule"
  nodeSelector:
    hardware: gpu
  containers:
  - name: cuda-app
    image: nvidia/cuda:11.0-base
    command: ["sleep", "3600"]
EOF
```

**This configuration:**
- Toleration: Allows scheduling on GPU-tainted nodes
- NodeSelector: Requires nodes with `hardware=gpu` label
- Together: Ensures pod ONLY runs on GPU nodes

Apply it:

```bash
kubectl apply -f gpu-workload.yaml
```

### Step 3: Verify Exclusive Scheduling

Check that only GPU workloads run on the GPU node:

```bash
kubectl get pods -o wide --field-selector spec.nodeName=<gpu-node-name>
```

Only pods with the GPU toleration should be on that node.

---

## Exercise 11: Multiple Tolerations

### Step 1: Create Node with Multiple Taints

Add multiple taints to a node:

```bash
kubectl taint nodes <node-name> environment=production:NoSchedule
kubectl taint nodes <node-name> tier=frontend:NoSchedule
kubectl taint nodes <node-name> region=us-west:NoSchedule
```

### Step 2: Create Pod with Multiple Tolerations

Create a pod that tolerates all taints:

```bash
cat <<EOF > multi-toleration-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: multi-toleration-pod
spec:
  tolerations:
  - key: "environment"
    operator: "Equal"
    value: "production"
    effect: "NoSchedule"
  - key: "tier"
    operator: "Equal"
    value: "frontend"
    effect: "NoSchedule"
  - key: "region"
    operator: "Equal"
    value: "us-west"
    effect: "NoSchedule"
  containers:
  - name: nginx
    image: nginx
EOF
```

**Important:** Pod must tolerate ALL taints on a node to schedule there.

Apply it:

```bash
kubectl apply -f multi-toleration-pod.yaml
```

Verify:

```bash
kubectl get pod multi-toleration-pod -o wide
```

---

## Lab Cleanup

Remove all resources and taints created in this lab:

```bash
# Delete all test pods
kubectl delete pod no-tolerations-pod toleration-production-pod exists-toleration-pod --ignore-not-found
kubectl delete pod wildcard-toleration-pod noexecute-toleration-pod delayed-eviction-pod --ignore-not-found
kubectl delete pod gpu-workload multi-toleration-pod --ignore-not-found
kubectl delete pod test-pod-1 test-pod-2 --ignore-not-found

# Delete deployments
kubectl delete deployment test-deployment --ignore-not-found

# Remove all custom taints from nodes
kubectl taint nodes <node-name> environment-
kubectl taint nodes <node-name> dedicated-
kubectl taint nodes <node-name> maintenance-
kubectl taint nodes <node-name> disktype-
kubectl taint nodes <node-name> hardware-
kubectl taint nodes <node-name> tier-
kubectl taint nodes <node-name> region-

# Remove labels
kubectl label nodes <node-name> hardware-

# Clean up manifest files
rm -f exists-toleration-pod.yaml wildcard-toleration-pod.yaml
rm -f test-pods.yaml noexecute-toleration-pod.yaml delayed-eviction-pod.yaml
rm -f multiple-pods.yaml gpu-workload.yaml multi-toleration-pod.yaml
```

**Note:** The `-` suffix removes taints and labels.

Verify cleanup:

```bash
kubectl get pods
kubectl get nodes -o custom-columns=NAME:.metadata.name,TAINTS:.spec.taints
```

---

## Key Takeaways

1. **Taints repel pods** from nodes; **tolerations allow pods** to overcome taints
2. **Three taint effects**:
   - `NoSchedule`: Prevents new pods (hard requirement)
   - `PreferNoSchedule`: Tries to avoid (soft preference)
   - `NoExecute`: Prevents new pods AND evicts existing ones
3. **Tolerations must match** taint key, value (if operator is Equal), and effect
4. **Operator types**:
   - `Equal`: Exact match required
   - `Exists`: Matches any value for the key
5. **Pods must tolerate ALL taints** on a node to schedule there
6. **Use taints for**:
   - Dedicated nodes
   - Special hardware
   - Maintenance windows
   - Workload isolation
7. **TolerationSeconds** allows delayed eviction with NoExecute

---

## Taints vs Affinity Decision Guide

| Scenario | Use Taints | Use Node Affinity |
|----------|------------|-------------------|
| Dedicated nodes for specific workloads | Yes | No |
| Prevent unauthorized workloads | Yes | No |
| Attract pods to preferred nodes | No | Yes |
| Complex placement logic | No | Yes |
| Maintenance mode | Yes (NoExecute) | No |
| Guarantee pod placement | No (combine with nodeSelector) | Yes |

**Best Practice:** Often combine both:
- Taint: Prevents unwanted pods
- Node Affinity/NodeSelector: Ensures pod goes to specific nodes
- Together: Exclusive scheduling on dedicated nodes

---

## Troubleshooting

### Pod Stuck in Pending with Taints

**Problem:** Pod remains Pending indefinitely

**Diagnosis:**
```bash
kubectl describe pod <pod-name>
```

Look for:
```
Warning  FailedScheduling  0/3 nodes are available: 3 node(s) had untolerated taint
```

**Solutions:**
1. Add tolerations to pod spec matching node taints
2. Remove taints from nodes: `kubectl taint nodes <node> <key>-`
3. Ensure operator and effect match exactly
4. Check for multiple taints requiring multiple tolerations

### Toleration Not Working

**Problem:** Pod with toleration still Pending

**Check:**
1. Taint key, value, and effect match exactly
2. Operator is correct (Equal vs Exists)
3. Other constraints (affinity, node selectors, resources)
4. Taints actually exist on nodes

**Verify:**
```bash
# Check pod's tolerations
kubectl get pod <pod-name> -o yaml | grep -A 10 tolerations

# Check node's taints
kubectl describe node <node-name> | grep Taints
```

### Pod Unexpectedly Evicted

**Problem:** Pod terminated unexpectedly

**Possible Causes:**
1. NoExecute taint added to node
2. Pod doesn't tolerate NoExecute effect
3. TolerationSeconds expired

**Investigation:**
```bash
# Check events
kubectl get events --sort-by=.metadata.creationTimestamp | grep -i evict

# Check node taints
kubectl describe node <node-name> | grep Taints
```

### Can't Remove Taint

**Problem:** Taint removal command doesn't work

**Common Issues:**
1. Syntax error (missing `-` at end)
2. Incorrect key or effect
3. Permissions issue

**Correct syntax:**
```bash
kubectl taint nodes <node> <key>:<effect>-
# or
kubectl taint nodes <node> <key>-
```

**Example:**
```bash
kubectl taint nodes worker-1 environment:NoSchedule-
```

---

## Additional Commands Reference

```bash
# List all node taints
kubectl get nodes -o custom-columns=NAME:.metadata.name,TAINTS:.spec.taints

# Add taint
kubectl taint nodes <node> key=value:effect

# Remove taint by key and effect
kubectl taint nodes <node> key:effect-

# Remove all taints with specific key
kubectl taint nodes <node> key-

# View pod tolerations
kubectl get pod <pod> -o jsonpath='{.spec.tolerations}' | jq

# Find pods that can schedule on tainted node
kubectl get pods -o json | jq '.items[] | select(.spec.tolerations[]?.key=="environment")'

# Check if control plane is tainted
kubectl describe node <control-plane-node> | grep Taints

# List all taints across all nodes
kubectl get nodes -o json | jq '.items[] | {name: .metadata.name, taints: .spec.taints}'
```

---

## Best Practices

1. **Document taints**: Maintain inventory of which nodes are tainted and why
2. **Use meaningful keys**: Choose descriptive taint keys (environment, hardware, maintenance)
3. **Prefer NoSchedule**: Use NoSchedule for most cases; NoExecute only when needed
4. **Combine with labels**: Use labels + taints for dedicated nodes
5. **Test thoroughly**: Verify tolerations work before production deployment
6. **Plan for maintenance**: Use NoExecute with tolerationSeconds for graceful eviction
7. **Avoid wildcard tolerations**: Don't use `operator: Exists` without a key in production
8. **Monitor evictions**: Track NoExecute evictions for capacity planning
9. **Use with Deployments**: Apply tolerations to Deployment templates, not individual pods
10. **Control plane protection**: Keep control plane taint unless intentionally running workloads there

---

## Real-World Use Cases

### Use Case 1: GPU Node Dedication
```yaml
# Taint GPU nodes
kubectl taint nodes gpu-node hardware=gpu:NoSchedule

# GPU workload with toleration
spec:
  tolerations:
  - key: hardware
    value: gpu
    effect: NoSchedule
  nodeSelector:
    hardware: gpu
```

### Use Case 2: Maintenance Window
```yaml
# Add maintenance taint with NoExecute
kubectl taint nodes node-1 maintenance=true:NoExecute

# Critical pods tolerate with delay
spec:
  tolerations:
  - key: maintenance
    value: "true"
    effect: NoExecute
    tolerationSeconds: 300  # 5 minute grace period
```

### Use Case 3: Environment Isolation
```yaml
# Production nodes
kubectl taint nodes prod-node-1 environment=production:NoSchedule

# Only production pods run there
spec:
  tolerations:
  - key: environment
    value: production
    effect: NoSchedule
  nodeSelector:
    environment: production
```

### Use Case 4: Spot Instance Handling
```yaml
# Taint spot instances
kubectl taint nodes spot-node-1 node-lifecycle=spot:PreferNoSchedule

# Fault-tolerant workloads tolerate
spec:
  tolerations:
  - key: node-lifecycle
    value: spot
    effect: PreferNoSchedule
```

---

## Integration with Other Scheduling Features

### Combining Taints with Node Affinity
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: combined-scheduling
spec:
  # Toleration allows scheduling on tainted nodes
  tolerations:
  - key: environment
    value: production
    effect: NoSchedule
  # Affinity directs to specific nodes
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: disktype
            operator: In
            values:
            - ssd
  containers:
  - name: app
    image: myapp:latest
```

### Combining Taints with PriorityClass
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: high-priority-tolerant
spec:
  priorityClassName: high-priority
  tolerations:
  - key: dedicated
    value: critical
    effect: NoSchedule
  containers:
  - name: app
    image: critical-app:latest
```

---

## Next Steps

You have completed all scheduling labs! Review the scheduling concepts:
- [Lab 26: NodeSelector](lab26-scheduling-nodeselector.md) - Simple node selection
- [Lab 27: Node and Pod Affinity](lab27-scheduling-affinity.md) - Advanced attraction rules
- [Lab 28: PriorityClass](lab28-scheduling-priorityclass.md) - Scheduling priority and preemption
- [Lab 29: Taints and Tolerations](lab29-scheduling-tolerations.md) - Node repulsion and dedicated resources

Explore other Kubernetes topics in the lab manual collection.

---

**Lab Created**: March 2026
**Compatible with**: Kubernetes 1.24+
