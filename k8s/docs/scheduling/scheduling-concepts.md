# Kubernetes Scheduling Concepts

This guide covers the essential scheduling concepts in Kubernetes, focusing on beginner to intermediate topics relevant to the CKA exam. You'll learn about the scheduler's responsibilities, scheduling workflow, node selection, pod allocation, and practical scheduling policies.

---

## Introduction to Kubernetes Scheduler

The **Kubernetes Scheduler** is a core control plane component responsible for assigning pods to suitable nodes within the cluster. It evaluates constraints and conditions to find the best node where the pod can run.

### Scheduler Responsibilities
- Identify pods without assigned nodes
- Evaluate available nodes against scheduling policies
- Bind pods to the most suitable nodes

### Key Inputs
- Pod specification (resource requests, affinity rules, etc.)
- Cluster state (nodes, resources, taints/tolerations, etc.)

---

## Scheduling Workflow

The Kubernetes Scheduler uses a **modular and pluggable framework** to support complex scheduling use cases.

### Key Phases of Scheduling

1. **PreFilter**: Checks whether the pod is eligible for scheduling
   - Example: Resource requests and limits, pod affinity/anti-affinity

2. **Filter**: Filters out nodes that cannot run the pod
   - Example: Node taints, pod tolerations, and node selectors

3. **Score**: Scores nodes based on their suitability
   - Example: Least resource usage, locality to existing pods

4. **Reserve**: Temporarily reserves resources for the pod

5. **Permit**: Optionally validates scheduling decisions

6. **Bind**: Binds the pod to the selected node

---

## Node Selection

Node selection is a critical process where nodes are evaluated for compatibility with the pod's requirements.

### Key Factors for Node Selection

1. **Node Conditions**: Nodes must be "Ready" and schedulable

2. **Resource Availability**: Nodes must have sufficient CPU, memory, and other resources

3. **Node Affinity/Anti-Affinity**: Specify nodes the pod should prefer or avoid

4. **Taints and Tolerations**: Control whether a pod can tolerate node-specific conditions

5. **Topology Spread Constraints**: Ensure even distribution of pods across failure domains (zones, racks)

---

## Pod Allocation

Pod allocation is the final stage of scheduling, where the selected node is bound to the pod.

### Steps in Pod Allocation

1. **Pod Admission**: Ensure the pod complies with the cluster's policies

2. **Node Scoring**: Use scoring plugins to rank nodes

3. **Node Binding**: Assign the pod to the chosen node

### Common Constraints in Pod Allocation

- **Resource Requests and Limits**:
  - Ensure nodes can accommodate the pod's CPU and memory requirements

- **Pod Affinity/Anti-Affinity**:
  - Influence where pods are placed based on proximity to other pods

---

## Scheduling Policies

Scheduling policies define rules and preferences for assigning pods to nodes.

### Common Policy Types

1. **Node Affinity**: Place pods on nodes with specific labels
   - Example: Prefer nodes with `disktype=ssd`

2. **Taints and Tolerations**: Prevent scheduling pods on certain nodes unless explicitly allowed

3. **Pod Affinity/Anti-Affinity**: Place pods near or away from other pods

### Node Affinity Policy Example

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: affinity-demo
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: "disktype"
            operator: In
            values:
            - "ssd"
  containers:
  - name: app
    image: nginx
```

**Use Case**: Workloads requiring specialized hardware like GPUs or SSDs.

---

## Resource Requests and Limits Impact on Scheduling

Resource requests and limits play a crucial role in scheduling decisions.

### How They Affect Scheduling

- **Requests**: Minimum resources guaranteed to a pod
  - The scheduler only places pods on nodes with sufficient available resources

- **Limits**: Maximum resources a pod can consume
  - Helps prevent resource exhaustion but doesn't affect scheduling

### Example with Resource Constraints

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: resource-demo
spec:
  containers:
  - name: nginx
    image: nginx
    resources:
      requests:
        memory: "64Mi"
        cpu: "250m"
      limits:
        memory: "128Mi"
        cpu: "500m"
```

---

## Pod Topology Spread Constraints

Pod topology spread constraints distribute pods evenly across failure domains (e.g., zones, racks). This improves fault tolerance and resource utilization.

### Key Parameters

- **`topologyKey`**: The node label to spread across (e.g., `zone`)
- **`maxSkew`**: Maximum difference in pod count between failure domains

### Practical Example

Spread pods evenly across zones:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: spread-demo
spec:
  replicas: 6
  selector:
    matchLabels:
      app: demo
  template:
    metadata:
      labels:
        app: demo
    spec:
      topologySpreadConstraints:
      - maxSkew: 1
        topologyKey: topology.kubernetes.io/zone
        whenUnsatisfiable: DoNotSchedule
        labelSelector:
          matchLabels:
            app: demo
      containers:
      - name: app
        image: nginx
```

**Use Case**: Ensuring high availability by spreading pods across zones and avoiding resource hotspots.

---

## Hands-On Example: Scheduling a Pod

Here is a complete example demonstrating how the scheduler assigns a pod using node affinity and tolerations.

### Node Configuration

Label a node:
```bash
kubectl label nodes node1 disktype=ssd
```

Taint the node:
```bash
kubectl taint nodes node1 key=value:NoSchedule
```

### Pod YAML with Scheduling Constraints

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: scheduling-demo
spec:
  tolerations:
  - key: "key"
    operator: "Equal"
    value: "value"
    effect: "NoSchedule"
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: "disktype"
            operator: "In"
            values:
            - "ssd"
  containers:
  - name: nginx
    image: nginx
    resources:
      requests:
        memory: "64Mi"
        cpu: "250m"
```

### Apply and Verify

1. Apply the pod manifest:
   ```bash
   kubectl apply -f pod.yaml
   ```

2. Check the pod's node:
   ```bash
   kubectl get pods -o wide
   ```

Expected output:
```
NAME             READY   STATUS    NODE    AGE
scheduling-demo  1/1     Running   node1   2m
```

---

## Summary

| Component | Description |
|-----------|-------------|
| **Scheduler** | Assigns pods to nodes based on constraints and policies |
| **Scheduling Framework** | Extensible phases (PreFilter, Filter, Score, etc.) for custom scheduling logic |
| **Node Selection** | Filters and scores nodes based on constraints like affinity, taints, etc. |
| **Pod Allocation** | Final binding of a pod to a selected node |
| **Scheduling Policies** | Defines rules for affinity, taints, and custom logic |
| **Resource Requests** | Minimum resources guaranteed; affects scheduling decisions |
| **Topology Spread** | Distributes pods across failure domains for high availability |

---

## Use Cases

1. **High Availability**: Ensuring workloads are distributed across failure domains using topology constraints

2. **Specialized Workloads**: Allocating specific workloads to nodes with specialized hardware (GPUs, SSDs)

3. **Workload Isolation**: Enforcing policies like taints and tolerations for isolating workloads

4. **Resource Optimization**: Using resource requests to ensure efficient node utilization

5. **Compliance**: Restricting workloads to specific zones or environments based on organizational requirements

---

This guide provides a solid foundation for understanding Kubernetes scheduling concepts essential for the CKA exam and practical cluster management.
