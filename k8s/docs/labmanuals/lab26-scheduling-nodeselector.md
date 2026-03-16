# Lab 26: Pod Scheduling with NodeSelector

## Overview
In this lab, you will learn how to control pod scheduling using NodeSelector, the simplest way to constrain pods to run on specific nodes. You'll label nodes and use NodeSelector to direct pods to appropriate nodes based on their labels.

## Prerequisites
- A running Kubernetes cluster with multiple nodes (or Minikube)
- `kubectl` CLI tool installed and configured
- Basic understanding of Pods and labels
- Completion of Lab 01 (recommended)

## Learning Objectives
By the end of this lab, you will be able to:
- Understand how Kubernetes schedules pods
- Add labels to nodes
- Use NodeSelector to schedule pods on specific nodes
- Troubleshoot scheduling issues with NodeSelector
- Understand the limitations of NodeSelector

---

## Understanding NodeSelector

### What is NodeSelector?
**NodeSelector** is the simplest form of node selection constraint in Kubernetes. It allows you to specify a set of key-value labels that a node must have for the pod to be scheduled on it.

### How It Works
1. **Label nodes** with key-value pairs (e.g., `env=staging`)
2. **Specify nodeSelector** in pod specification
3. **Scheduler matches** the nodeSelector requirements with node labels
4. **Pod scheduled** only on nodes that match ALL specified labels

### When to Use NodeSelector
- Simple node selection based on environment (dev, staging, production)
- Hardware requirements (GPU nodes, high-memory nodes)
- Geographic location (datacenter, region)
- Dedicated workloads on specific nodes

### Limitations
- Only supports equality-based matching
- Cannot express complex logic (OR conditions)
- For advanced scenarios, use Node Affinity

---

## Exercise 1: View Current Nodes and Labels

### Step 1: List All Nodes

View all nodes in your cluster:

```bash
kubectl get nodes
```

Expected output:
```
NAME           STATUS   ROLES           AGE   VERSION
control-plane  Ready    control-plane   5d    v1.28.0
worker-1       Ready    <none>          5d    v1.28.0
worker-2       Ready    <none>          5d    v1.28.0
```

### Step 2: View Node Labels

Check existing labels on nodes:

```bash
kubectl get nodes --show-labels
```

This displays all default labels that Kubernetes assigns to nodes, such as:
- `kubernetes.io/hostname`
- `kubernetes.io/os`
- `kubernetes.io/arch`
- `node.kubernetes.io/instance-type`

View labels for a specific node:

```bash
kubectl describe node <node-name> | grep -A 10 Labels
```

---

## Exercise 2: Label Nodes for Environments

### Step 1: Add Staging Environment Label

Label a node as a staging environment:

```bash
kubectl label nodes <node-name> env=staging
```

Replace `<node-name>` with your actual node name. For example:
```bash
kubectl label nodes worker-1 env=staging
```

Expected output:
```
node/worker-1 labeled
```

### Step 2: Add Production Environment Label

If you have multiple nodes, label another as production:

```bash
kubectl label nodes <another-node-name> env=production
```

Example:
```bash
kubectl label nodes worker-2 env=production
```

### Step 3: Verify Node Labels

Check that labels were applied:

```bash
kubectl get nodes -L env
```

Expected output:
```
NAME           STATUS   ROLES           AGE   VERSION   ENV
control-plane  Ready    control-plane   5d    v1.28.0
worker-1       Ready    <none>          5d    v1.28.0   staging
worker-2       Ready    <none>          5d    v1.28.0   production
```

The `-L env` flag adds the `env` label as a column.

---

## Exercise 3: Deploy Pod with NodeSelector

### Step 1: Review the NodeSelector Pod Manifest

Navigate to the scheduling labs directory:

```bash
cd k8s/labs/scheduling/nodeselector
```

Examine the `nodeselector.yaml` file:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx-node-staging
  labels:
    env: test
spec:
  containers:
  - name: nginx
    image: nginx
    imagePullPolicy: IfNotPresent
  nodeSelector:
    env: staging
```

**Understanding the manifest:**
- `nodeSelector.env: staging` - Pod will ONLY schedule on nodes with label `env=staging`
- `metadata.labels.env: test` - This is a pod label (different from node label)
- `imagePullPolicy: IfNotPresent` - Use cached image if available

### Step 2: Deploy the Pod

Apply the manifest:

```bash
kubectl apply -f nodeselector.yaml
```

Expected output:
```
pod/nginx-node-staging created
```

### Step 3: Verify Pod Scheduling

Check which node the pod was scheduled on:

```bash
kubectl get pod nginx-node-staging -o wide
```

Expected output:
```
NAME                 READY   STATUS    RESTARTS   AGE   IP           NODE
nginx-node-staging   1/1     Running   0          10s   10.244.1.5   worker-1
```

The pod should be running on the node labeled with `env=staging`.

### Step 4: Detailed Pod Information

View detailed scheduling information:

```bash
kubectl describe pod nginx-node-staging
```

Look for these sections:
- **Node:** Shows which node the pod is running on
- **Events:** Shows scheduling decisions

Example events:
```
Events:
  Type    Reason     Age   From               Message
  ----    ------     ----  ----               -------
  Normal  Scheduled  30s   default-scheduler  Successfully assigned default/nginx-node-staging to worker-1
  Normal  Pulled     29s   kubelet            Container image "nginx" already present on machine
  Normal  Created    29s   kubelet            Created container nginx
  Normal  Started    29s   kubelet            Started container nginx
```

---

## Exercise 4: Test NodeSelector Constraints

### Step 1: Create a Pod with Non-Existent Label

Let's see what happens when a pod requires a label that no node has.

Create a test manifest:

```bash
cat <<EOF > test-nodeselector.yaml
apiVersion: v1
kind: Pod
metadata:
  name: test-impossible-pod
spec:
  containers:
  - name: nginx
    image: nginx
  nodeSelector:
    env: development
    region: us-east
EOF
```

Apply it:

```bash
kubectl apply -f test-nodeselector.yaml
```

### Step 2: Observe Scheduling Failure

Check pod status:

```bash
kubectl get pod test-impossible-pod
```

Expected output:
```
NAME                  READY   STATUS    RESTARTS   AGE
test-impossible-pod   0/1     Pending   0          30s
```

The pod remains in **Pending** state because no node matches the nodeSelector criteria.

### Step 3: View Scheduling Events

Check why the pod isn't scheduling:

```bash
kubectl describe pod test-impossible-pod
```

Look for events:
```
Events:
  Type     Reason            Age   From               Message
  ----     ------            ----  ----               -------
  Warning  FailedScheduling  45s   default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector
```

This tells us the scheduler cannot find any node matching the required labels.

### Step 4: Clean Up Test Pod

Delete the test pod:

```bash
kubectl delete pod test-impossible-pod
```

---

## Exercise 5: Advanced NodeSelector with Preferred Scheduling

### Step 1: Review the NotIn Operator Example

Examine the `notin-nodeselector.yaml` file:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: webserver-node-affinity
spec:
  affinity:
    nodeAffinity:
      preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 1
        preference:
          matchExpressions:
          - key: env
            operator: NotIn
            values:
            - staging
  containers:
  - name: httpd
    image: docker.io/httpd
```

**Note:** This example actually uses **Node Affinity**, not NodeSelector. NodeSelector only supports equality matching. This demonstrates the limitation of NodeSelector and shows when you need to use Node Affinity instead.

**Understanding the manifest:**
- `preferredDuringSchedulingIgnoredDuringExecution` - Soft preference (not required)
- `matchExpressions` - Allows complex matching
- `operator: NotIn` - Excludes nodes with `env=staging`
- `weight: 1` - Preference weight (1-100)

### Step 2: Deploy the Pod

Apply the manifest:

```bash
kubectl apply -f notin-nodeselector.yaml
```

Expected output:
```
pod/webserver-node-affinity created
```

### Step 3: Verify Scheduling

Check which node the pod was scheduled on:

```bash
kubectl get pod webserver-node-affinity -o wide
```

The pod should prefer nodes that are NOT labeled `env=staging`. However, if no other nodes are available, it can still be scheduled on staging nodes because it's a preference, not a requirement.

---

## Exercise 6: Multiple NodeSelector Labels

### Step 1: Add Multiple Labels to a Node

Add additional labels to a node:

```bash
kubectl label nodes <node-name> disktype=ssd
kubectl label nodes <node-name> region=us-west
```

Example:
```bash
kubectl label nodes worker-1 disktype=ssd
kubectl label nodes worker-1 region=us-west
```

### Step 2: Create Pod with Multiple Selectors

Create a pod requiring multiple node labels:

```bash
cat <<EOF > multi-selector.yaml
apiVersion: v1
kind: Pod
metadata:
  name: multi-selector-pod
spec:
  containers:
  - name: nginx
    image: nginx
  nodeSelector:
    env: staging
    disktype: ssd
    region: us-west
EOF
```

Apply it:

```bash
kubectl apply -f multi-selector.yaml
```

### Step 3: Verify Pod Placement

Check pod status:

```bash
kubectl get pod multi-selector-pod -o wide
```

The pod will only schedule on nodes that have ALL three labels:
- `env=staging`
- `disktype=ssd`
- `region=us-west`

---

## Lab Cleanup

Remove all resources created in this lab:

```bash
# Delete pods
kubectl delete pod nginx-node-staging
kubectl delete pod webserver-node-affinity
kubectl delete pod multi-selector-pod --ignore-not-found

# Remove custom labels from nodes (optional)
kubectl label nodes <node-name> env-
kubectl label nodes <node-name> disktype-
kubectl label nodes <node-name> region-
```

Example:
```bash
kubectl label nodes worker-1 env-
kubectl label nodes worker-1 disktype-
kubectl label nodes worker-1 region-
kubectl label nodes worker-2 env-
```

**Note:** The `-` suffix removes the label.

Verify labels are removed:
```bash
kubectl get nodes -L env,disktype,region
```

---

## Key Takeaways

1. **NodeSelector** is the simplest way to constrain pods to specific nodes
2. **Nodes must be labeled** before NodeSelector can match them
3. **All labels must match** - NodeSelector uses AND logic
4. **Pending pods** indicate no nodes match the selector
5. **NodeSelector limitations**:
   - Only equality-based matching
   - Cannot use OR logic
   - Cannot express "not equal" or "greater than"
6. For complex requirements, use **Node Affinity** (see Lab 10)

---

## Troubleshooting

### Pod Stuck in Pending State

**Problem:** Pod remains Pending indefinitely

**Diagnosis:**
```bash
kubectl describe pod <pod-name>
```

Look for events mentioning "didn't match Pod's node affinity/selector"

**Solutions:**
1. Verify node labels: `kubectl get nodes --show-labels`
2. Check if any nodes have the required labels
3. Add missing labels to nodes
4. Modify pod's nodeSelector to match existing labels

### Pod Scheduled on Wrong Node

**Problem:** Pod runs on unexpected node

**Possible Causes:**
1. Multiple nodes have matching labels
2. No nodeSelector specified in pod manifest
3. Typo in node labels or nodeSelector

**Verification:**
```bash
# Check pod's nodeSelector
kubectl get pod <pod-name> -o yaml | grep -A 5 nodeSelector

# Check node labels
kubectl get nodes -L <label-key>
```

### Label Not Applied to Node

**Problem:** Label command succeeds but label doesn't appear

**Verification:**
```bash
kubectl describe node <node-name> | grep <label-key>
```

**Solution:**
Ensure correct syntax:
```bash
kubectl label nodes <node-name> key=value
```

---

## Additional Commands Reference

```bash
# View all labels on a node
kubectl get node <node-name> --show-labels

# Filter nodes by label
kubectl get nodes -l env=staging

# View multiple label columns
kubectl get nodes -L env,region,disktype

# Update existing label
kubectl label nodes <node-name> env=production --overwrite

# Remove a label
kubectl label nodes <node-name> env-

# Get pod's node assignment
kubectl get pod <pod-name> -o jsonpath='{.spec.nodeName}'

# View node selector in pod spec
kubectl get pod <pod-name> -o jsonpath='{.spec.nodeSelector}'
```

---

## Best Practices

1. **Use meaningful label names**: `env`, `tier`, `region`, `hardware-type`
2. **Document your labeling scheme**: Maintain consistency across the cluster
3. **Avoid overusing NodeSelector**: Use Deployments with nodeSelector for production
4. **Plan for failure**: Ensure multiple nodes can satisfy critical nodeSelectors
5. **Use Node Affinity for complex cases**: When NodeSelector isn't expressive enough
6. **Label nodes during provisioning**: Automate node labeling in your infrastructure code

---

## Real-World Use Cases

### Use Case 1: Environment Separation
```yaml
# Development pods on dev nodes
nodeSelector:
  env: development

# Production pods on production nodes
nodeSelector:
  env: production
```

### Use Case 2: Hardware Requirements
```yaml
# GPU workloads
nodeSelector:
  hardware: gpu

# High-memory workloads
nodeSelector:
  node.kubernetes.io/instance-type: m5.xlarge
```

### Use Case 3: Geographic Distribution
```yaml
# EU data residency
nodeSelector:
  region: eu-west-1
  compliance: gdpr
```

### Use Case 4: Cost Optimization
```yaml
# Spot instances for batch jobs
nodeSelector:
  node-lifecycle: spot
```

---

## Next Steps

Proceed to [Lab 27: Pod Scheduling with Node and Pod Affinity](lab27-scheduling-affinity.md) to learn about more advanced scheduling constraints.

---

**Lab Created**: March 2026
**Compatible with**: Kubernetes 1.24+
