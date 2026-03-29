# Lab 19: Pod Scheduling with PriorityClass

## Overview
In this lab, you will learn how to use PriorityClass to control the relative importance of pods during scheduling. You'll create priority classes, assign them to pods, and observe how the scheduler handles resource contention and pod preemption.

## Prerequisites
- A running Kubernetes cluster
- `kubectl` CLI tool installed and configured
- Basic understanding of Pods and scheduling
- Completion of Lab 09 (recommended)

## Learning Objectives
By the end of this lab, you will be able to:
- Understand Kubernetes pod priority and preemption
- Create PriorityClass resources
- Assign priority classes to pods
- Observe pod preemption behavior
- Understand how priority affects scheduling decisions
- Implement priority-based scheduling strategies

---

## Understanding PriorityClass

### What is PriorityClass?
**PriorityClass** is a non-namespaced resource that defines a mapping between a priority class name and an integer value. The higher the value, the higher the priority.

### How Priority Works
1. **Scheduling Order**: Higher priority pods are scheduled before lower priority pods in the queue
2. **Preemption**: When resources are scarce, higher priority pods can evict (preempt) lower priority pods
3. **Resource Allocation**: Priority doesn't affect resource allocation after scheduling, only scheduling order

### Key Concepts

| Concept | Description |
|---------|-------------|
| **Priority Value** | Integer representing pod priority (higher = more important) |
| **Preemption** | Evicting lower-priority pods to make room for higher-priority ones |
| **PriorityClassName** | Reference to PriorityClass in pod spec |
| **globalDefault** | Marks a PriorityClass as default for pods without explicit priority |

### System Priority Classes

Kubernetes includes built-in priority classes:

| Priority Class | Value | Description |
|----------------|-------|-------------|
| **system-cluster-critical** | 2000000000 | Critical cluster components (e.g., kube-dns) |
| **system-node-critical** | 2000001000 | Critical node components (e.g., kubelet) |

**Important:** User-created priority classes should use values less than 1 billion (1000000000).

---

## Exercise 1: View System PriorityClasses

### Step 1: List Existing PriorityClasses

View all priority classes in the cluster:

```bash
kubectl get priorityclasses
```

Expected output:
```
NAME                      VALUE        GLOBAL-DEFAULT   AGE
system-cluster-critical   2000000000   false            5d
system-node-critical      2000001000   false            5d
```

**Note:** The `pc` alias works too:
```bash
kubectl get pc
```

### Step 2: Describe System Priority Class

View details of a system priority class:

```bash
kubectl describe priorityclass system-cluster-critical
```

Expected output:
```
Name:              system-cluster-critical
Value:             2000000000
GlobalDefault:     false
Description:       Used for system critical pods that must run in the cluster
Annotations:       <none>
Events:            <none>
```

### Step 3: Check Pods Using System Priorities

View pods with their priority classes:

```bash
kubectl get pods -A -o custom-columns=NAME:.metadata.name,NAMESPACE:.metadata.namespace,PRIORITY-CLASS:.spec.priorityClassName,PRIORITY:.spec.priority
```

You'll see system pods using system priority classes.

---

## Exercise 2: Create High Priority Class

### Step 1: Review High Priority Class Manifest

Navigate to the priority class labs directory:

```bash
cd k8s/labs/scheduling/priorityclass
```

Examine `high-priority-class.yaml`:

```yaml
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: high-priority
value: 1000000
globalDefault: false
description: "This priority class should be used for nginx service pods only."
```

**Understanding the manifest:**
- `apiVersion: scheduling.k8s.io/v1` - API version for PriorityClass
- `kind: PriorityClass` - Resource type
- `metadata.name: high-priority` - Name used by pods to reference this class
- `value: 1000000` - Priority value (higher = more important)
- `globalDefault: false` - Not the default for pods without explicit priority
- `description` - Human-readable description of intended use

### Step 2: Create the PriorityClass

Apply the manifest:

```bash
kubectl apply -f high-priority-class.yaml
```

Expected output:
```
priorityclass.scheduling.k8s.io/high-priority created
```

### Step 3: Verify Creation

List all priority classes:

```bash
kubectl get priorityclasses
```

Expected output:
```
NAME                      VALUE        GLOBAL-DEFAULT   AGE
high-priority             1000000      false            5s
system-cluster-critical   2000000000   false            5d
system-node-critical      2000001000   false            5d
```

View details:

```bash
kubectl describe priorityclass high-priority
```

---

## Exercise 3: Create Low Priority Class

### Step 1: Review Low Priority Class Manifest

Examine `low-priority-class.yaml`:

```yaml
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: low-priority
value: 500000
globalDefault: false
description: "This priority class is for less important workloads."
```

This priority class has a lower value (500000) than high-priority (1000000).

### Step 2: Create the PriorityClass

Apply the manifest:

```bash
kubectl apply -f low-priority-class.yaml
```

Expected output:
```
priorityclass.scheduling.k8s.io/low-priority created
```

### Step 3: Verify Both Priority Classes

List all priority classes sorted by value:

```bash
kubectl get priorityclasses --sort-by=.value
```

Expected output:
```
NAME                      VALUE        GLOBAL-DEFAULT   AGE
low-priority              500000       false            10s
high-priority             1000000      false            2m
system-cluster-critical   2000000000   false            5d
system-node-critical      2000001000   false            5d
```

---

## Exercise 4: Deploy High Priority Pod

### Step 1: Review High Priority Pod Manifest

Examine `high-priority-pod.yaml`:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx1
  labels:
    env: test
spec:
  containers:
  - name: nginx
    image: nginx
    imagePullPolicy: IfNotPresent
  priorityClassName: high-priority
```

**Key Configuration:**
- `priorityClassName: high-priority` - References the high-priority PriorityClass
- This pod will have priority value 1000000

### Step 2: Deploy the Pod

Apply the manifest:

```bash
kubectl apply -f high-priority-pod.yaml
```

Expected output:
```
pod/nginx1 created
```

### Step 3: Verify Pod Priority

Check pod with priority information:

```bash
kubectl get pod nginx1 -o custom-columns=NAME:.metadata.name,PRIORITY-CLASS:.spec.priorityClassName,PRIORITY:.spec.priority,STATUS:.status.phase
```

Expected output:
```
NAME     PRIORITY-CLASS   PRIORITY   STATUS
nginx1   high-priority    1000000    Running
```

View detailed pod information:

```bash
kubectl describe pod nginx1 | grep -i priority
```

Expected output:
```
Priority:         1000000
Priority Class Name:  high-priority
```

---

## Exercise 5: Deploy Low Priority Pod

### Step 1: Review Low Priority Pod Manifest

Examine `low-priority-pod.yaml`:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: low-priority-pod
spec:
  containers:
  - name: busybox
    image: busybox
    command: ["sh", "-c", "sleep 3600"]
  priorityClassName: low-priority
```

**Key Configuration:**
- `priorityClassName: low-priority` - References the low-priority PriorityClass
- `command: ["sh", "-c", "sleep 3600"]` - Keeps pod running for 1 hour
- This pod will have priority value 500000

### Step 2: Deploy the Pod

Apply the manifest:

```bash
kubectl apply -f low-priority-pod.yaml
```

Expected output:
```
pod/low-priority-pod created
```

### Step 3: Compare Pod Priorities

List both pods with priority information:

```bash
kubectl get pods -o custom-columns=NAME:.metadata.name,PRIORITY-CLASS:.spec.priorityClassName,PRIORITY:.spec.priority,STATUS:.status.phase
```

Expected output:
```
NAME               PRIORITY-CLASS   PRIORITY   STATUS
low-priority-pod   low-priority     500000     Running
nginx1             high-priority    1000000    Running
```

---

## Exercise 6: Demonstrate Priority-Based Scheduling

### Step 1: Create Multiple Priority Pods

Create a deployment with low priority:

```bash
cat <<EOF > low-priority-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: low-priority-deployment
spec:
  replicas: 5
  selector:
    matchLabels:
      app: low-priority-app
  template:
    metadata:
      labels:
        app: low-priority-app
    spec:
      containers:
      - name: nginx
        image: nginx
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
      priorityClassName: low-priority
EOF
```

Apply it:

```bash
kubectl apply -f low-priority-deployment.yaml
```

### Step 2: Create High Priority Deployment

Create a deployment with high priority:

```bash
cat <<EOF > high-priority-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: high-priority-deployment
spec:
  replicas: 3
  selector:
    matchLabels:
      app: high-priority-app
  template:
    metadata:
      labels:
        app: high-priority-app
    spec:
      containers:
      - name: nginx
        image: nginx
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
      priorityClassName: high-priority
EOF
```

Apply it:

```bash
kubectl apply -f high-priority-deployment.yaml
```

### Step 3: Monitor Scheduling Order

Watch pods being created:

```bash
kubectl get pods -o custom-columns=NAME:.metadata.name,PRIORITY:.spec.priority,STATUS:.status.phase,AGE:.metadata.creationTimestamp --sort-by=.metadata.creationTimestamp
```

**Observation:** When resources are available, all pods schedule normally. Priority matters most during resource contention.

---

## Exercise 7: Simulate Preemption (Advanced)

### Step 1: Understanding Preemption

**Preemption** occurs when:
1. A high-priority pod cannot be scheduled due to resource constraints
2. The scheduler identifies lower-priority pods that, if evicted, would free enough resources
3. The scheduler evicts those lower-priority pods
4. The high-priority pod is scheduled

### Step 2: Create Resource Constraints (Optional)

To observe preemption, you need resource pressure. This works best on a cluster with limited resources.

**Note:** Skip this if your cluster has abundant resources or if you're using a production cluster.

Create pods that consume resources:

```bash
cat <<EOF > resource-consumer.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: resource-consumer
spec:
  replicas: 10
  selector:
    matchLabels:
      app: resource-consumer
  template:
    metadata:
      labels:
        app: resource-consumer
    spec:
      containers:
      - name: busybox
        image: busybox
        command: ["sh", "-c", "sleep 7200"]
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
      priorityClassName: low-priority
EOF
```

Apply it:

```bash
kubectl apply -f resource-consumer.yaml
```

Wait for pods to fill available resources:

```bash
kubectl get pods -l app=resource-consumer
```

Some pods may be Pending if resources are constrained.

### Step 3: Create High Priority Pod Under Resource Pressure

Create a high-priority pod with substantial resource requests:

```bash
cat <<EOF > preemption-test-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: preemption-test-pod
spec:
  containers:
  - name: nginx
    image: nginx
    resources:
      requests:
        memory: "512Mi"
        cpu: "500m"
  priorityClassName: high-priority
EOF
```

Apply it:

```bash
kubectl apply -f preemption-test-pod.yaml
```

### Step 4: Observe Preemption Events

Watch for preemption events:

```bash
kubectl get events --sort-by=.metadata.creationTimestamp | grep -i preempt
```

Expected events:
```
Normal   Preempted   pod/resource-consumer-xxx   Preempted by default/preemption-test-pod on node worker-1
```

Check which pods were evicted:

```bash
kubectl get pods -l app=resource-consumer
```

Some pods will show status as `Terminating` or have restarted recently.

Verify the high-priority pod scheduled:

```bash
kubectl get pod preemption-test-pod -o wide
```

---

## Exercise 8: Default PriorityClass

### Step 1: Create a Default PriorityClass

Create a priority class as the global default:

```bash
cat <<EOF > default-priority-class.yaml
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: default-priority
value: 100000
globalDefault: true
description: "Default priority for pods without explicit priorityClassName"
EOF
```

Apply it:

```bash
kubectl apply -f default-priority-class.yaml
```

**Important:** Only ONE PriorityClass can have `globalDefault: true`.

### Step 2: Deploy Pod Without Priority

Create a pod without specifying priorityClassName:

```bash
cat <<EOF > no-priority-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: no-priority-specified
spec:
  containers:
  - name: nginx
    image: nginx
EOF
```

Apply it:

```bash
kubectl apply -f no-priority-pod.yaml
```

### Step 3: Verify Default Priority Applied

Check the pod's priority:

```bash
kubectl get pod no-priority-specified -o custom-columns=NAME:.metadata.name,PRIORITY-CLASS:.spec.priorityClassName,PRIORITY:.spec.priority
```

Expected output:
```
NAME                   PRIORITY-CLASS     PRIORITY
no-priority-specified  default-priority   100000
```

The default priority class was automatically assigned!

---

## Exercise 9: Priority and QoS Classes

### Understanding Priority vs QoS

**Priority** and **QoS (Quality of Service)** are independent:
- **Priority**: Affects scheduling order and preemption
- **QoS**: Affects pod eviction during node resource pressure

| QoS Class | Resource Specification | Eviction Priority |
|-----------|----------------------|-------------------|
| **Guaranteed** | Requests = Limits for all containers | Last to evict |
| **Burstable** | Requests < Limits (or only requests set) | Middle priority |
| **BestEffort** | No requests or limits | First to evict |

### Create Pods with Different Combinations

Create a high-priority BestEffort pod:

```bash
cat <<EOF > high-priority-besteffort.yaml
apiVersion: v1
kind: Pod
metadata:
  name: high-priority-besteffort
spec:
  containers:
  - name: nginx
    image: nginx
  priorityClassName: high-priority
EOF
```

Create a low-priority Guaranteed pod:

```bash
cat <<EOF > low-priority-guaranteed.yaml
apiVersion: v1
kind: Pod
metadata:
  name: low-priority-guaranteed
spec:
  containers:
  - name: nginx
    image: nginx
    resources:
      requests:
        memory: "256Mi"
        cpu: "250m"
      limits:
        memory: "256Mi"
        cpu: "250m"
  priorityClassName: low-priority
EOF
```

Apply both:

```bash
kubectl apply -f high-priority-besteffort.yaml
kubectl apply -f low-priority-guaranteed.yaml
```

Check their configurations:

```bash
kubectl get pods -o custom-columns=NAME:.metadata.name,PRIORITY:.spec.priority,QOS:.status.qosClass
```

**Key Point:**
- For **scheduling preemption**, Priority matters most
- For **node resource eviction**, QoS matters most

---

## Lab Cleanup

Remove all resources created in this lab:

```bash
# Delete individual pods
kubectl delete pod nginx1 low-priority-pod preemption-test-pod --ignore-not-found
kubectl delete pod no-priority-specified high-priority-besteffort low-priority-guaranteed --ignore-not-found

# Delete deployments
kubectl delete deployment low-priority-deployment high-priority-deployment --ignore-not-found
kubectl delete deployment resource-consumer --ignore-not-found

# Delete custom PriorityClasses
kubectl delete priorityclass high-priority low-priority default-priority --ignore-not-found

# Clean up manifest files
rm -f low-priority-deployment.yaml high-priority-deployment.yaml
rm -f resource-consumer.yaml preemption-test-pod.yaml
rm -f default-priority-class.yaml no-priority-pod.yaml
rm -f high-priority-besteffort.yaml low-priority-guaranteed.yaml
```

Verify cleanup:

```bash
kubectl get pods
kubectl get priorityclasses
```

---

## Key Takeaways

1. **PriorityClass** determines pod scheduling order and preemption behavior
2. **Higher priority values** mean more important pods
3. **Preemption** allows high-priority pods to evict lower-priority pods
4. **globalDefault: true** makes a PriorityClass the default for pods without explicit priority
5. **System priority classes** (2 billion+) are reserved for critical components
6. **User priority classes** should use values under 1 billion
7. **Priority affects scheduling**, not resource allocation after scheduling
8. **Priority is independent** of QoS class

---

## When to Use PriorityClass

### Use Cases

| Scenario | Priority Strategy |
|----------|------------------|
| **Critical Services** | High priority to ensure they always schedule |
| **Batch Jobs** | Low priority to avoid disrupting interactive workloads |
| **SLA Tiers** | Different priorities for different service levels |
| **Development vs Production** | Higher priority for production workloads |
| **Cost Optimization** | Low priority for interruptible workloads on spot instances |

### Best Practices

1. **Define clear priority tiers**: Create a few well-defined priority classes (e.g., critical, high, medium, low)
2. **Document priority usage**: Ensure teams understand when to use each class
3. **Set reasonable values**: Use values far apart (e.g., 100000, 500000, 1000000) to allow future insertions
4. **Avoid overuse of high priorities**: Too many high-priority pods defeats the purpose
5. **Test preemption behavior**: Understand what gets evicted before production use
6. **Combine with resource requests**: Always set resource requests for predictable behavior
7. **Monitor preemption events**: Track how often preemption occurs
8. **Use with PodDisruptionBudgets**: Protect critical low-priority pods from excessive disruption

---

## Troubleshooting

### Pod Not Preempting Lower Priority Pods

**Problem:** High-priority pod stays Pending despite lower-priority pods running

**Possible Causes:**
1. Node constraints (affinity, taints) prevent scheduling
2. Lower-priority pods protected by PodDisruptionBudget
3. Insufficient resources even after preemption
4. Preemption disabled in scheduler configuration

**Diagnosis:**
```bash
kubectl describe pod <pod-name>
```

Look for scheduling events explaining why preemption didn't occur.

### PriorityClass Not Found

**Problem:** Pod creation fails with "PriorityClass not found"

**Solution:**
```bash
# Verify PriorityClass exists
kubectl get priorityclass <priority-class-name>

# Check pod spec for typos
kubectl get pod <pod-name> -o yaml | grep priorityClassName
```

### Understanding Preemption Events

**View preemption events:**
```bash
kubectl get events --all-namespaces --sort-by=.metadata.creationTimestamp | grep -i preempt
```

**Event types:**
- `Preempted`: Pod was evicted to make room for higher priority pod
- `FailedScheduling`: Pod couldn't schedule even after attempting preemption

---

## Additional Commands Reference

```bash
# List all PriorityClasses
kubectl get priorityclasses
kubectl get pc  # Short alias

# Describe PriorityClass
kubectl describe priorityclass <name>

# View pod priorities
kubectl get pods -o custom-columns=NAME:.metadata.name,PRIORITY:.spec.priority

# Sort pods by priority
kubectl get pods -o custom-columns=NAME:.metadata.name,PRIORITY:.spec.priority --sort-by=.spec.priority

# View pod priority class
kubectl get pod <pod-name> -o jsonpath='{.spec.priorityClassName}'

# Watch for preemption events
kubectl get events -w | grep -i preempt

# Find pods with specific priority class
kubectl get pods -A -o json | jq '.items[] | select(.spec.priorityClassName=="high-priority") | .metadata.name'

# Check default priority class
kubectl get priorityclasses -o json | jq '.items[] | select(.globalDefault==true)'
```

---

## Advanced Concepts

### Preemption Policy

Starting Kubernetes 1.19, you can configure preemption policy:

```yaml
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: no-preemption
value: 1000000
preemptionPolicy: Never  # Pod will not preempt others
description: "High priority but won't preempt running pods"
```

**preemptionPolicy values:**
- `PreemptLowerPriority` (default): Can preempt lower priority pods
- `Never`: Will not preempt, even if it could

### Priority and Scheduling Queue

Kubernetes scheduler maintains queues:
1. **Active Queue**: Pods actively being scheduled
2. **Backoff Queue**: Pods that failed scheduling (retry with backoff)
3. **Unschedulable Queue**: Pods that couldn't schedule

High-priority pods:
- Move to front of Active Queue
- Retry more frequently from Backoff Queue
- Attempt preemption from Unschedulable Queue

---

## Real-World Examples

### Example 1: Multi-Tier Application

```yaml
# Critical database
apiVersion: v1
kind: Pod
metadata:
  name: database
spec:
  priorityClassName: critical-priority  # value: 10000000
  containers:
  - name: postgres
    image: postgres:14

---
# Important API service
apiVersion: v1
kind: Pod
metadata:
  name: api
spec:
  priorityClassName: high-priority  # value: 1000000
  containers:
  - name: api
    image: myapp:latest

---
# Background worker
apiVersion: v1
kind: Pod
metadata:
  name: worker
spec:
  priorityClassName: low-priority  # value: 100000
  containers:
  - name: worker
    image: worker:latest
```

### Example 2: Batch Processing

```yaml
# Interactive jobs
apiVersion: batch/v1
kind: Job
metadata:
  name: interactive-job
spec:
  template:
    spec:
      priorityClassName: high-priority
      containers:
      - name: processor
        image: data-processor:latest

---
# Batch jobs
apiVersion: batch/v1
kind: Job
metadata:
  name: batch-job
spec:
  template:
    spec:
      priorityClassName: low-priority
      containers:
      - name: batch
        image: batch-processor:latest
```

---

## Next Steps

Proceed to [Lab 20: Pod Scheduling with Taints and Tolerations](lab20-sched-taints-tolerations.md) to learn how to repel pods from nodes unless they have specific tolerations.

---

**Lab Created**: March 2026
**Compatible with**: Kubernetes 1.24+
