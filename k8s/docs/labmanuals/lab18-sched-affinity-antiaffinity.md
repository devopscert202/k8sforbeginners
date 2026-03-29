# Lab 18: Pod Scheduling with Node and Pod Affinity

## Overview
In this lab, you will learn advanced pod scheduling techniques using Node Affinity and Pod Affinity/Anti-Affinity. These features provide more expressive ways to control where pods run compared to NodeSelector, supporting complex scheduling rules and pod-to-pod relationships.

## Prerequisites
- A running Kubernetes cluster with multiple nodes
- `kubectl` CLI tool installed and configured
- Completion of Lab 09 (NodeSelector) recommended
- Basic understanding of Pods and labels

## Learning Objectives
By the end of this lab, you will be able to:
- Understand Node Affinity rules and scheduling preferences
- Use required and preferred Node Affinity constraints
- Implement Pod Affinity to co-locate related pods
- Use Pod Anti-Affinity to spread pods across nodes
- Understand topology keys and their role in affinity rules
- Troubleshoot affinity scheduling issues

---

## Understanding Affinity and Anti-Affinity

Kubernetes provides **three affinity mechanisms** that give you fine-grained control over Pod placement. Think of it like choosing seats at a conference:

| Mechanism | One-Liner | Real-World Analogy |
|-----------|-----------|-------------------|
| **Node Affinity** | "Run me on *this kind* of node" | "I want a seat in the VIP section" — choose by room characteristics |
| **Pod Affinity** | "Run me *next to* that Pod" | "Seat me next to my colleague" — co-locate with a specific person |
| **Pod Anti-Affinity** | "Keep me *away from* that Pod" | "Don't seat two managers at the same table" — spread across tables |

### What is Node Affinity?
**Node Affinity** matches against **node labels** (characteristics of the machine). It's NodeSelector's more expressive cousin:
- Six operators: `In`, `NotIn`, `Exists`, `DoesNotExist`, `Gt`, `Lt`
- Soft preferences (preferred) vs hard requirements (required)
- OR logic across terms, AND logic within a term
- **Use when:** you need GPU nodes, SSD storage, specific zones, or environment isolation

### What is Pod Affinity?
**Pod Affinity** matches against **labels of other Pods** already running in the cluster. It schedules your Pod on the same node (or topology domain) as matching Pods.
- **Use when:** you want low-latency access (cache next to app), data locality, or tightly coupled services
- Requires a **topologyKey** to define "same location" (hostname, zone, region)

### What is Pod Anti-Affinity?
**Pod Anti-Affinity** is the opposite of Pod Affinity — it prevents your Pod from landing on a node (or topology domain) that already has matching Pods.
- **Use when:** you need HA (spread database replicas), fault tolerance, or to prevent resource contention
- Requires a **topologyKey** to define "different location"

### Scheduling Types

| Type | Description | Behavior if Not Satisfied |
|------|-------------|---------------------------|
| **requiredDuringSchedulingIgnoredDuringExecution** | Hard requirement — must satisfy | Pod stays **Pending** indefinitely |
| **preferredDuringSchedulingIgnoredDuringExecution** | Soft preference — try but don't block | Pod schedules on best available node |

**Note:** "IgnoredDuringExecution" means if labels change after the Pod is running, the Pod is **not** evicted. Affinity rules only affect the initial scheduling decision.

### Topology Key Explained

The **topologyKey** defines the scope boundary for Pod Affinity / Anti-Affinity:

| Topology Key | Scope | Meaning |
|-------------|-------|---------|
| `kubernetes.io/hostname` | Per node | "Same node" or "different node" — most common |
| `topology.kubernetes.io/zone` | Per AZ | "Same zone" or "different zone" — for zone-level HA |
| `topology.kubernetes.io/region` | Per region | "Same region" or "different region" |

> **Interactive HTML**: See [Affinity and Anti-Affinity](../html/affinity-antiaffinity.html) for visual diagrams showing how each type works.

---

## Exercise 1: Node Affinity with Required Rules

### Step 1: Label Nodes for Environments

Label your nodes with environment tags:

```bash
kubectl label nodes <node-1> env=production
kubectl label nodes <node-2> env=staging
```

Example:
```bash
kubectl label nodes worker-1 env=production
kubectl label nodes worker-2 env=staging
```

Verify labels:
```bash
kubectl get nodes -L env
```

Expected output:
```
NAME           STATUS   ROLES           AGE   VERSION   ENV
control-plane  Ready    control-plane   5d    v1.28.0
worker-1       Ready    <none>          5d    v1.28.0   production
worker-2       Ready    <none>          5d    v1.28.0   staging
```

### Step 2: Review Node Affinity Manifest

Navigate to the affinity labs directory:

```bash
cd k8s/labs/scheduling/affinity
```

Examine `node-affinity.yaml`:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: production-pod
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: env
            operator: In
            values:
            - production
  containers:
  - name: nginx
    image: nginx
```

**Understanding the manifest:**
- `requiredDuringSchedulingIgnoredDuringExecution` - Hard requirement (must match)
- `nodeSelectorTerms` - List of node selector requirements (OR logic between terms)
- `matchExpressions` - Matching rules (AND logic within a term)
- `operator: In` - Node label must have one of the specified values
- `values: [production]` - Acceptable values for the label

### Step 3: Deploy Production Pod

Apply the manifest:

```bash
kubectl apply -f node-affinity.yaml
```

Expected output:
```
pod/production-pod created
```

### Step 4: Verify Pod Placement

Check which node the pod was scheduled on:

```bash
kubectl get pod production-pod -o wide
```

Expected output:
```
NAME             READY   STATUS    RESTARTS   AGE   IP           NODE
production-pod   1/1     Running   0          15s   10.244.1.6   worker-1
```

The pod should be on the node labeled `env=production`.

Verify with describe:
```bash
kubectl describe pod production-pod | grep -A 3 "Node-Selectors"
```

---

## Exercise 2: Multiple Node Affinity Rules

### Step 1: Review Staging Pod Manifest

Examine `node-affinity_2.yaml`:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: staging-pod
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: env
            operator: In
            values:
            - staging
  containers:
  - name: nginx
    image: nginx
```

This is similar to the production pod but requires `env=staging`.

### Step 2: Deploy Staging Pod

Apply the manifest:

```bash
kubectl apply -f node-affinity_2.yaml
```

### Step 3: Verify Both Pods

List all pods and their node assignments:

```bash
kubectl get pods -o wide
```

Expected output:
```
NAME             READY   STATUS    RESTARTS   AGE   IP            NODE
production-pod   1/1     Running   0          2m    10.244.1.6    worker-1
staging-pod      1/1     Running   0          15s   10.244.2.3    worker-2
```

Both pods should be on different nodes based on their affinity rules.

---

## Exercise 3: Preferred Node Affinity (Soft Constraints)

### Step 1: Create a Preferred Affinity Pod

Create a manifest with preferred node affinity:

```bash
cat <<EOF > preferred-affinity.yaml
apiVersion: v1
kind: Pod
metadata:
  name: preferred-pod
spec:
  affinity:
    nodeAffinity:
      preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        preference:
          matchExpressions:
          - key: env
            operator: In
            values:
            - production
      - weight: 50
        preference:
          matchExpressions:
          - key: disktype
            operator: In
            values:
            - ssd
  containers:
  - name: nginx
    image: nginx
EOF
```

**Understanding the manifest:**
- `preferredDuringSchedulingIgnoredDuringExecution` - Soft preference
- `weight: 100` - Higher weight = stronger preference (1-100)
- Multiple preferences are evaluated, and the scheduler chooses the best match
- If no nodes match, pod still schedules on any available node

### Step 2: Deploy the Pod

Apply the manifest:

```bash
kubectl apply -f preferred-affinity.yaml
```

### Step 3: Observe Scheduling Behavior

Check where the pod was scheduled:

```bash
kubectl get pod preferred-pod -o wide
```

The scheduler will prefer nodes with `env=production` (weight 100) over nodes with `disktype=ssd` (weight 50). If neither matches, it will schedule on any available node.

---

## Exercise 4: Node Affinity with Multiple Operators

### Step 1: Create Advanced Node Affinity

Create a pod using multiple operators:

```bash
cat <<EOF > advanced-node-affinity.yaml
apiVersion: v1
kind: Pod
metadata:
  name: advanced-affinity-pod
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: env
            operator: In
            values:
            - production
            - staging
          - key: disktype
            operator: Exists
          - key: region
            operator: NotIn
            values:
            - us-east
  containers:
  - name: nginx
    image: nginx
EOF
```

**Understanding the operators:**
- `In` - Label value must be in the list
- `NotIn` - Label value must NOT be in the list
- `Exists` - Label key must exist (any value)
- `DoesNotExist` - Label key must not exist
- `Gt` - Label value greater than integer value
- `Lt` - Label value less than integer value

This pod requires:
1. Node has `env=production` OR `env=staging`
2. AND node has `disktype` label (any value)
3. AND node does NOT have `region=us-east`

### Step 2: Label Nodes for Testing

Add required labels:

```bash
kubectl label nodes worker-1 disktype=ssd
kubectl label nodes worker-2 disktype=hdd
```

### Step 3: Deploy and Test

Apply the manifest:

```bash
kubectl apply -f advanced-node-affinity.yaml
```

Check scheduling:

```bash
kubectl get pod advanced-affinity-pod -o wide
```

If no nodes satisfy all conditions, the pod will remain Pending.

---

## Exercise 5: Pod Anti-Affinity (Spread Pods)

### Step 1: Understanding Pod Anti-Affinity

Pod Anti-Affinity prevents pods from being scheduled on the same node (or topology domain) as other pods with specific labels.

**Common Use Cases:**
- High availability: Spread replicas across nodes
- Prevent resource contention between similar workloads
- Compliance: Separate different security zones

### Step 2: Review Pod Anti-Affinity Manifest

Examine `pod-anti-affinity.yaml`:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: anti-affinity-pod
spec:
  affinity:
    podAntiAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
      - labelSelector:
          matchExpressions:
          - key: "env"
            operator: In
            values:
            - production
        topologyKey: kubernetes.io/hostname
  containers:
  - name: nginx
    image: nginx
```

**Understanding the manifest:**
- `podAntiAffinity` - Defines pod anti-affinity rules
- `requiredDuringSchedulingIgnoredDuringExecution` - Hard requirement
- `labelSelector` - Selects pods to avoid
- `topologyKey: kubernetes.io/hostname` - Anti-affinity applies per node (hostname)

This pod will NOT schedule on any node that already has a pod with label `env=production`.

### Step 3: Deploy First Pod with Production Label

First, create a pod with the production label:

```bash
cat <<EOF > production-labeled-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: production-app
  labels:
    env: production
spec:
  containers:
  - name: nginx
    image: nginx
EOF
```

Apply it:

```bash
kubectl apply -f production-labeled-pod.yaml
```

Check which node it's on:

```bash
kubectl get pod production-app -o wide
```

### Step 4: Deploy Anti-Affinity Pod

Now deploy the anti-affinity pod:

```bash
kubectl apply -f pod-anti-affinity.yaml
```

### Step 5: Verify Pod Separation

Check pod placement:

```bash
kubectl get pods -o wide -l 'env in (production)' --show-labels
```

The `anti-affinity-pod` should be on a DIFFERENT node than `production-app`.

If you only have one node, the `anti-affinity-pod` will remain Pending:

```bash
kubectl get pod anti-affinity-pod
```

Check events:

```bash
kubectl describe pod anti-affinity-pod
```

You'll see events like:
```
Warning  FailedScheduling  0/1 nodes are available: 1 node(s) didn't match pod anti-affinity rules
```

---

## Exercise 6: Pod Anti-Affinity with Staging

### Step 1: Review Second Anti-Affinity Manifest

Examine `pod-anti-affinity-2.yaml`:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: anti-affinity-pod-2
spec:
  affinity:
    podAntiAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
      - labelSelector:
          matchExpressions:
          - key: "env"
            operator: In
            values:
            - staging
        topologyKey: kubernetes.io/hostname
  containers:
  - name: nginx
    image: nginx
```

This avoids nodes with pods labeled `env=staging`.

### Step 2: Deploy Staging Pod First

Create a staging pod:

```bash
cat <<EOF > staging-labeled-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: staging-app
  labels:
    env: staging
spec:
  containers:
  - name: nginx
    image: nginx
EOF
```

Apply it:

```bash
kubectl apply -f staging-labeled-pod.yaml
```

### Step 3: Deploy Second Anti-Affinity Pod

Apply the manifest:

```bash
kubectl apply -f pod-anti-affinity-2.yaml
```

### Step 4: Verify Separation

Check pod distribution:

```bash
kubectl get pods -o wide
```

The `anti-affinity-pod-2` should avoid nodes with `staging-app`.

---

## Exercise 7: Pod Affinity (Co-locate Pods)

### Step 1: Understanding Pod Affinity

Pod Affinity schedules pods on the same node (or topology domain) as other pods with specific labels.

**Use Cases:**
- Co-locate cache with application
- Place related microservices together for low latency
- Data locality requirements

### Step 2: Create Pod Affinity Example

Create a pod with pod affinity:

```bash
cat <<EOF > pod-affinity.yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod-affinity-example
spec:
  affinity:
    podAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
      - labelSelector:
          matchExpressions:
          - key: env
            operator: In
            values:
            - production
        topologyKey: kubernetes.io/hostname
  containers:
  - name: nginx
    image: nginx
EOF
```

This pod MUST be scheduled on a node that already has a pod with `env=production`.

### Step 3: Deploy and Verify

Apply the manifest:

```bash
kubectl apply -f pod-affinity.yaml
```

Check placement:

```bash
kubectl get pod pod-affinity-example -o wide
```

This pod should be on the SAME node as the `production-app` pod.

Verify:

```bash
kubectl get pods -o custom-columns=NAME:.metadata.name,NODE:.spec.nodeName,LABELS:.metadata.labels
```

---

## Exercise 8: Combining Node and Pod Affinity

### Step 1: Create Combined Affinity Rules

Create a pod with both node and pod affinity:

```bash
cat <<EOF > combined-affinity.yaml
apiVersion: v1
kind: Pod
metadata:
  name: combined-affinity-pod
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: env
            operator: In
            values:
            - production
    podAffinity:
      preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        podAffinityTerm:
          labelSelector:
            matchExpressions:
            - key: app
              operator: In
              values:
              - cache
          topologyKey: kubernetes.io/hostname
  containers:
  - name: nginx
    image: nginx
EOF
```

**This pod:**
1. MUST be on a node with `env=production` (required node affinity)
2. PREFERS to be with pods labeled `app=cache` (preferred pod affinity)

### Step 2: Deploy and Test

Apply the manifest:

```bash
kubectl apply -f combined-affinity.yaml
```

Check where it was scheduled:

```bash
kubectl get pod combined-affinity-pod -o wide
```

---

## Exercise 9: Topology Keys and Zones

### Step 1: Understanding Topology Keys

**Topology Key** defines the scope of the affinity/anti-affinity rule:
- `kubernetes.io/hostname` - Node level (each node is a separate domain)
- `topology.kubernetes.io/zone` - Zone level (e.g., availability zone)
- `topology.kubernetes.io/region` - Region level

### Step 2: Zone-Level Anti-Affinity

Create zone-level anti-affinity:

```bash
cat <<EOF > zone-anti-affinity.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: zone-spread-deployment
spec:
  replicas: 3
  selector:
    matchLabels:
      app: zone-spread
  template:
    metadata:
      labels:
        app: zone-spread
    spec:
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - zone-spread
              topologyKey: topology.kubernetes.io/zone
      containers:
      - name: nginx
        image: nginx
EOF
```

This deployment tries to spread replicas across different availability zones.

### Step 3: Deploy and Observe

Apply the deployment:

```bash
kubectl apply -f zone-anti-affinity.yaml
```

Check replica distribution:

```bash
kubectl get pods -l app=zone-spread -o wide
```

View node zones:

```bash
kubectl get nodes -L topology.kubernetes.io/zone
```

---

## Lab Cleanup

Remove all resources created in this lab:

```bash
# Delete all pods
kubectl delete pod production-pod staging-pod preferred-pod advanced-affinity-pod --ignore-not-found
kubectl delete pod anti-affinity-pod anti-affinity-pod-2 --ignore-not-found
kubectl delete pod production-app staging-app --ignore-not-found
kubectl delete pod pod-affinity-example combined-affinity-pod --ignore-not-found

# Delete deployments
kubectl delete deployment zone-spread-deployment --ignore-not-found

# Remove custom labels (optional)
kubectl label nodes <node-name> env-
kubectl label nodes <node-name> disktype-
kubectl label nodes <node-name> region-
```

Verify cleanup:

```bash
kubectl get pods
```

---

## Key Takeaways

1. **Node Affinity** is more expressive than NodeSelector
2. **Required rules** must be satisfied; pods stay Pending if not
3. **Preferred rules** are soft constraints; scheduler tries but doesn't guarantee
4. **Pod Anti-Affinity** spreads pods for high availability
5. **Pod Affinity** co-locates pods for performance
6. **Topology keys** define the scope (node, zone, region)
7. **Weights** (1-100) prioritize multiple preferences
8. Affinity rules are evaluated at scheduling time, not during execution

---

## Comparison: NodeSelector vs Node Affinity

| Feature | NodeSelector | Node Affinity |
|---------|-------------|---------------|
| **Complexity** | Simple | Advanced |
| **Operators** | Equality only | In, NotIn, Exists, DoesNotExist, Gt, Lt |
| **Soft Constraints** | No | Yes (preferred rules) |
| **Multiple Rules** | AND only | AND and OR logic |
| **Best For** | Simple cases | Complex scheduling requirements |

---

## Troubleshooting

### Pod Stuck in Pending with Affinity Rules

**Diagnosis:**
```bash
kubectl describe pod <pod-name>
```

Look for:
```
Warning  FailedScheduling  0/3 nodes are available: 3 node(s) didn't match pod affinity rules
```

**Solutions:**
1. Check if nodes have required labels
2. Verify pod labels for pod affinity/anti-affinity
3. Check if topology key exists on nodes
4. Consider using preferred instead of required rules
5. Ensure enough nodes exist for anti-affinity rules

### Anti-Affinity Not Working

**Problem:** Pods scheduling on the same node despite anti-affinity

**Check:**
1. Label selectors match correctly
2. Topology key is valid and exists on nodes
3. Using `requiredDuringScheduling` (not preferred)
4. Pods have the labels being selected against

**Verify:**
```bash
# Check pod labels
kubectl get pods --show-labels

# Check topology key on nodes
kubectl get nodes --show-labels | grep <topology-key>
```

### Preferred Rules Not Being Honored

**Remember:** Preferred rules are NOT guaranteed. The scheduler considers them but may ignore if:
- Resource constraints exist
- Higher priority rules conflict
- No nodes match the preference

---

## Additional Commands Reference

```bash
# View affinity rules in pod spec
kubectl get pod <pod-name> -o yaml | grep -A 20 affinity

# Check pod's node assignment
kubectl get pod <pod-name> -o jsonpath='{.spec.nodeName}'

# List pods by node
kubectl get pods -o wide --sort-by=.spec.nodeName

# View pod distribution across nodes
kubectl get pods -o wide | awk '{print $7}' | sort | uniq -c

# Check node labels
kubectl get nodes --show-labels

# View events for scheduling decisions
kubectl get events --sort-by=.metadata.creationTimestamp | grep -i schedule
```

---

## Best Practices

1. **Start simple**: Use NodeSelector for basic needs, graduate to affinity when needed
2. **Use preferred for flexibility**: Hard requirements can cause scheduling failures
3. **Plan for scale**: Anti-affinity requires enough nodes to satisfy rules
4. **Test scheduling rules**: Deploy test pods before production rollout
5. **Document affinity rules**: Complex rules need clear documentation
6. **Monitor scheduling**: Watch for pods stuck in Pending state
7. **Combine with Deployments**: Use affinity with Deployments for production workloads
8. **Consider costs**: Affinity requirements may prevent efficient node utilization

---

## Real-World Use Cases

### Use Case 1: High Availability Database
```yaml
# Spread database replicas across nodes
podAntiAffinity:
  requiredDuringSchedulingIgnoredDuringExecution:
  - labelSelector:
      matchLabels:
        app: database
    topologyKey: kubernetes.io/hostname
```

### Use Case 2: Co-locate Cache with Application
```yaml
# Place cache pods on same nodes as app pods
podAffinity:
  preferredDuringSchedulingIgnoredDuringExecution:
  - weight: 100
    podAffinityTerm:
      labelSelector:
        matchLabels:
          app: myapp
      topologyKey: kubernetes.io/hostname
```

### Use Case 3: GPU Workloads
```yaml
# Require nodes with GPU
nodeAffinity:
  requiredDuringSchedulingIgnoredDuringExecution:
    nodeSelectorTerms:
    - matchExpressions:
      - key: hardware
        operator: In
        values:
        - gpu
```

### Use Case 4: Zone Redundancy
```yaml
# Spread across availability zones
podAntiAffinity:
  preferredDuringSchedulingIgnoredDuringExecution:
  - weight: 100
    podAffinityTerm:
      labelSelector:
        matchLabels:
          app: myapp
      topologyKey: topology.kubernetes.io/zone
```

---

## Next Steps

- **Lab 19: PriorityClass** — [Pod Scheduling with PriorityClass](lab19-sched-priorityclass.md) — learn how to prioritize pod scheduling during resource contention
- **Lab 20: Taints and Tolerations** — [Taints and Tolerations](lab20-sched-taints-tolerations.md) — the complementary mechanism that repels Pods from nodes
- **Interactive HTML**: [Affinity and Anti-Affinity](../html/affinity-antiaffinity.html) — visual diagrams, operator reference, and comparison tables

---

**Lab Created**: March 2026
**Compatible with**: Kubernetes 1.24+
