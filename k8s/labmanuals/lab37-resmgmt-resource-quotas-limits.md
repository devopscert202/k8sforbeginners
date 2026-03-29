# Lab 37: Resource Quotas and Limits

## Overview
In this lab, you will learn about Kubernetes Resource Quotas and Limits, essential tools for managing cluster resources and enforcing multi-tenancy. You'll create namespaces with resource quotas, deploy pods with resource requests and limits, and understand how Kubernetes enforces these constraints to prevent resource exhaustion.

## Prerequisites
- A running Kubernetes cluster (Minikube, Kind, or any K8s cluster)
- `kubectl` CLI tool installed and configured
- Basic understanding of Pods and Namespaces
- Administrative access to create namespaces and quotas

## Learning Objectives
By the end of this lab, you will be able to:
- Understand the importance of resource management in Kubernetes
- Create and configure ResourceQuota objects
- Define resource requests and limits for containers
- Deploy pods with resource specifications
- Troubleshoot quota enforcement issues
- Implement resource management best practices
- Monitor resource usage and quota consumption

---

## What are Resource Quotas and Limits?

### The Need for Resource Management

In a shared Kubernetes cluster, multiple applications compete for finite resources (CPU, memory, storage). Without proper controls:
- One application can consume all cluster resources
- Other applications may fail to schedule
- Cluster instability and performance degradation occur
- Cost management becomes difficult

**Resource Quotas** and **Resource Limits** provide governance and fairness across namespaces and workloads.

### Key Concepts

#### Resource Requests
- **Definition**: Minimum resources guaranteed to a container
- **Purpose**: Used by scheduler to find suitable nodes
- **Guarantee**: Kubernetes ensures these resources are available
- **Example**: "I need at least 256Mi memory to run"

#### Resource Limits
- **Definition**: Maximum resources a container can consume
- **Purpose**: Prevents resource hogging and protects other workloads
- **Enforcement**: Container is throttled (CPU) or killed (memory) if exceeded
- **Example**: "I should never use more than 512Mi memory"

#### Resource Quotas
- **Definition**: Aggregate resource limits at namespace level
- **Purpose**: Control total resource consumption per namespace
- **Scope**: Can limit CPU, memory, storage, and object counts
- **Example**: "This namespace can use max 4 CPU cores and 8Gi memory"

### Resource Types

| Resource | Unit | Description |
|----------|------|-------------|
| **CPU** | millicores (m) | 1000m = 1 CPU core |
| **Memory** | bytes | Mi (Mebibyte), Gi (Gibibyte) |
| **Storage** | bytes | Persistent volume claims |
| **Pods** | count | Number of Pods allowed |
| **Services** | count | Number of Services allowed |

### Common Use Cases

1. **Multi-Tenancy**: Isolate teams/projects with guaranteed resources
2. **Cost Control**: Limit spending per department/application
3. **Cluster Stability**: Prevent runaway applications
4. **Fair Resource Distribution**: Ensure no single app monopolizes cluster
5. **Development vs Production**: Different quotas for different environments

---

## Exercise 1: Create Namespace with Resource Quota

### Step 1: Create the Namespace

First, create a dedicated namespace for this lab:

```bash
kubectl create namespace quotaz
```

Expected output:
```
namespace/quotaz created
```

Verify the namespace:
```bash
kubectl get namespaces | grep quotaz
```

### Step 2: Review the ResourceQuota Manifest

Navigate to the workloads directory:
```bash
cd k8s/labs/workloads
```

Let's examine `resourcequota.yaml`:

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: mem-cpu-demo
  namespace: quotaz
spec:
  hard:
    requests.cpu: "1"
    requests.memory: 1Gi
    limits.cpu: "2"
    limits.memory: 2Gi
```

**Understanding the manifest:**

- `kind: ResourceQuota` - Defines a quota object
- `metadata.name: mem-cpu-demo` - Name of the quota
- `metadata.namespace: quotaz` - Applied to 'quotaz' namespace
- `spec.hard` - Hard limits that cannot be exceeded
  - `requests.cpu: "1"` - Total CPU requests cannot exceed 1 core
  - `requests.memory: 1Gi` - Total memory requests cannot exceed 1 GiB
  - `limits.cpu: "2"` - Total CPU limits cannot exceed 2 cores
  - `limits.memory: 2Gi` - Total memory limits cannot exceed 2 GiB

**Important Relationship:**
- Total requests must not exceed quota requests
- Total limits must not exceed quota limits
- Typically: limits >= requests

### Step 3: Create the ResourceQuota

Apply the quota manifest:

```bash
kubectl apply -f resourcequota.yaml
```

Expected output:
```
resourcequota/mem-cpu-demo created
```

### Step 4: Verify the ResourceQuota

View the quota:

```bash
kubectl get resourcequota -n quotaz
```

Expected output:
```
NAME           AGE   REQUEST                                   LIMIT
mem-cpu-demo   10s   requests.cpu: 0/1, requests.memory: 0/1Gi   limits.cpu: 0/2, limits.memory: 0/2Gi
```

**Understanding the output:**
- `requests.cpu: 0/1` - Using 0 out of 1 CPU core quota
- `requests.memory: 0/1Gi` - Using 0 out of 1 GiB memory quota
- `limits.cpu: 0/2` - Using 0 out of 2 CPU cores limit quota
- `limits.memory: 0/2Gi` - Using 0 out of 2 GiB memory limit quota

Get detailed information:

```bash
kubectl describe resourcequota mem-cpu-demo -n quotaz
```

Expected output:
```
Name:            mem-cpu-demo
Namespace:       quotaz
Resource         Used  Hard
--------         ----  ----
limits.cpu       0     2
limits.memory    0     2Gi
requests.cpu     0     1
requests.memory  0     1Gi
```

---

## Exercise 2: Deploy Pod Within Quota

### Step 1: Review the First Pod Manifest

Let's examine `resourcequota_pod1.yaml`:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: quota-mem-cpu-demo
  namespace: quotaz
spec:
  containers:
  - name: quota-mem-cpu-demo-ctr
    image: nginx
    resources:
      limits:
        memory: "800Mi"
        cpu: "800m"
      requests:
        memory: "600Mi"
        cpu: "400m"
```

**Understanding the manifest:**

- `metadata.namespace: quotaz` - Deployed in namespace with quota
- `resources.requests`:
  - `memory: "600Mi"` - Requests 600 MiB (0.6 GiB)
  - `cpu: "400m"` - Requests 400 millicores (0.4 CPU)
- `resources.limits`:
  - `memory: "800Mi"` - Max 800 MiB (0.8 GiB)
  - `cpu: "800m"` - Max 800 millicores (0.8 CPU)

**Quota Check:**
- Requests: 600Mi + 400m (within 1Gi + 1 CPU quota) ✓
- Limits: 800Mi + 800m (within 2Gi + 2 CPU quota) ✓

This pod should deploy successfully!

### Step 2: Deploy the First Pod

Apply the manifest:

```bash
kubectl apply -f resourcequota_pod1.yaml
```

Expected output:
```
pod/quota-mem-cpu-demo created
```

### Step 3: Verify Pod Creation

Check pod status:

```bash
kubectl get pods -n quotaz
```

Expected output:
```
NAME                 READY   STATUS    RESTARTS   AGE
quota-mem-cpu-demo   1/1     Running   0          15s
```

View pod details:

```bash
kubectl describe pod quota-mem-cpu-demo -n quotaz
```

Look for the resources section:
```
    Limits:
      cpu:     800m
      memory:  800Mi
    Requests:
      cpu:        400m
      memory:     600Mi
```

### Step 4: Check Updated Quota Usage

View quota consumption:

```bash
kubectl get resourcequota mem-cpu-demo -n quotaz
```

Expected output:
```
NAME           AGE   REQUEST                                        LIMIT
mem-cpu-demo   5m    requests.cpu: 400m/1, requests.memory: 600Mi/1Gi   limits.cpu: 800m/2, limits.memory: 800Mi/2Gi
```

Notice the quota is now partially consumed!

Get detailed view:

```bash
kubectl describe resourcequota mem-cpu-demo -n quotaz
```

Output:
```
Resource         Used   Hard
--------         ----   ----
limits.cpu       800m   2
limits.memory    800Mi  2Gi
requests.cpu     400m   1
requests.memory  600Mi  1Gi
```

**Analysis:**
- Used 40% of CPU request quota (400m of 1 CPU)
- Used 60% of memory request quota (600Mi of 1Gi)
- Used 40% of CPU limit quota (800m of 2 CPU)
- Used 40% of memory limit quota (800Mi of 2Gi)

---

## Exercise 3: Test Quota Enforcement

### Step 1: Review the Second Pod Manifest

Let's examine `resourcequota_pod2.yaml`:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: quota-mem-cpu-demo-2
  namespace: quotaz
spec:
  containers:
  - name: quota-mem-cpu-demo-ctr
    image: nginx
    resources:
      limits:
        memory: "800Mi"   # 0.8 GiB
        cpu: "800m"       # 0.8 CPU
      requests:
        memory: "600Mi"   # 0.6 GiB
        cpu: "400m"       # 0.4 CPU
```

**Quota Math:**
- Current usage: 600Mi memory requests, 400m CPU requests
- Pod 2 requests: 600Mi memory, 400m CPU
- Total would be: 1200Mi memory (exceeds 1Gi quota!), 800m CPU (within quota)

This pod should **FAIL** to deploy due to quota limits!

### Step 2: Attempt to Deploy Second Pod

Try to apply the manifest:

```bash
kubectl apply -f resourcequota_pod2.yaml
```

Expected output:
```
Error from server (Forbidden): error when creating "resourcequota_pod2.yaml": pods "quota-mem-cpu-demo-2" is forbidden: exceeded quota: mem-cpu-demo, requested: requests.memory=600Mi, used: requests.memory=600Mi, limited: requests.memory=1Gi
```

**Understanding the error:**
- `exceeded quota: mem-cpu-demo` - Quota name that was exceeded
- `requested: requests.memory=600Mi` - What the new pod requested
- `used: requests.memory=600Mi` - What's currently used
- `limited: requests.memory=1Gi` - The quota limit
- Total would be 1200Mi (1.17 GiB), which exceeds the 1Gi quota

### Step 3: Verify Pod Did Not Create

Check pods in namespace:

```bash
kubectl get pods -n quotaz
```

Output (only first pod exists):
```
NAME                 READY   STATUS    RESTARTS   AGE
quota-mem-cpu-demo   1/1     Running   0          5m
```

### Step 4: Check Quota Status

Verify quota is still at previous levels:

```bash
kubectl describe resourcequota mem-cpu-demo -n quotaz
```

Output shows no change:
```
Resource         Used   Hard
--------         ----   ----
limits.cpu       800m   2
limits.memory    800Mi  2Gi
requests.cpu     400m   1
requests.memory  600Mi  1Gi
```

---

## Exercise 4: Deploy Pod After Resource Adjustment

### Step 1: Scale Down First Pod's Resources

To fit the second pod, we need to free up quota. Let's delete the first pod and redeploy with lower resources.

Delete the first pod:

```bash
kubectl delete pod quota-mem-cpu-demo -n quotaz
```

Expected output:
```
pod "quota-mem-cpu-demo" deleted
```

### Step 2: Create Modified Pod Manifest

Create a new manifest with reduced resources:

```bash
cat <<EOF > quota-pod-reduced.yaml
apiVersion: v1
kind: Pod
metadata:
  name: quota-mem-cpu-demo
  namespace: quotaz
spec:
  containers:
  - name: quota-mem-cpu-demo-ctr
    image: nginx
    resources:
      limits:
        memory: "400Mi"
        cpu: "400m"
      requests:
        memory: "300Mi"
        cpu: "200m"
EOF
```

Apply the reduced pod:

```bash
kubectl apply -f quota-pod-reduced.yaml
```

### Step 3: Verify Quota Usage

Check current quota usage:

```bash
kubectl describe resourcequota mem-cpu-demo -n quotaz
```

Output:
```
Resource         Used   Hard
--------         ----   ----
limits.cpu       400m   2
limits.memory    400Mi  2Gi
requests.cpu     200m   1
requests.memory  300Mi  1Gi
```

Now we have room!
- Available request memory: 1Gi - 300Mi = 724Mi
- Available request CPU: 1 - 200m = 800m

### Step 4: Deploy Second Pod Successfully

Modify the second pod to fit:

```bash
cat <<EOF > quota-pod2-reduced.yaml
apiVersion: v1
kind: Pod
metadata:
  name: quota-mem-cpu-demo-2
  namespace: quotaz
spec:
  containers:
  - name: quota-mem-cpu-demo-ctr
    image: nginx
    resources:
      limits:
        memory: "500Mi"
        cpu: "600m"
      requests:
        memory: "400Mi"
        cpu: "300m"
EOF
```

Apply it:

```bash
kubectl apply -f quota-pod2-reduced.yaml
```

Expected output:
```
pod/quota-mem-cpu-demo-2 created
```

### Step 5: Verify Both Pods Running

Check all pods:

```bash
kubectl get pods -n quotaz
```

Expected output:
```
NAME                   READY   STATUS    RESTARTS   AGE
quota-mem-cpu-demo     1/1     Running   0          2m
quota-mem-cpu-demo-2   1/1     Running   0          30s
```

Check final quota usage:

```bash
kubectl describe resourcequota mem-cpu-demo -n quotaz
```

Output:
```
Resource         Used   Hard
--------         ----   ----
limits.cpu       1      2
limits.memory    900Mi  2Gi
requests.cpu     500m   1
requests.memory  700Mi  1Gi
```

Both pods are now running within the quota limits!

---

## Exercise 5: Understanding Quota Enforcement Without Requests/Limits

### What Happens Without Resource Specifications?

When a ResourceQuota for compute resources exists in a namespace, all pods **MUST** specify requests and limits. Otherwise, they will be rejected.

### Step 1: Try Creating Pod Without Resources

Create a pod without resource specifications:

```bash
cat <<EOF > quota-pod-no-resources.yaml
apiVersion: v1
kind: Pod
metadata:
  name: quota-mem-cpu-demo-3
  namespace: quotaz
spec:
  containers:
  - name: nginx-ctr
    image: nginx
EOF
```

Apply it:

```bash
kubectl apply -f quota-pod-no-resources.yaml
```

Expected error:
```
Error from server (Forbidden): error when creating "quota-pod-no-resources.yaml": pods "quota-mem-cpu-demo-3" is forbidden: failed quota: mem-cpu-demo: must specify limits.cpu for: nginx-ctr; limits.memory for: nginx-ctr; requests.cpu for: nginx-ctr; requests.memory for: nginx-ctr
```

**Understanding the error:**
- Namespace has compute resource quota
- Pod must specify both requests AND limits for CPU and memory
- Prevents unlimited resource consumption

### Step 2: Solution - LimitRange

To provide default values, use a LimitRange:

```bash
cat <<EOF > limitrange.yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: default-limits
  namespace: quotaz
spec:
  limits:
  - default:
      memory: 256Mi
      cpu: 200m
    defaultRequest:
      memory: 128Mi
      cpu: 100m
    type: Container
EOF
```

Apply it:

```bash
kubectl apply -f limitrange.yaml
```

Now the pod without explicit resources will use these defaults!

---

## Exercise 6: Additional Quota Types

### Object Count Quotas

ResourceQuotas can limit the number of Kubernetes objects:

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: object-counts
  namespace: quotaz
spec:
  hard:
    pods: "10"
    services: "5"
    configmaps: "10"
    persistentvolumeclaims: "4"
    replicationcontrollers: "5"
    secrets: "10"
    services.nodeports: "2"
```

Apply and test:

```bash
kubectl apply -f - <<EOF
apiVersion: v1
kind: ResourceQuota
metadata:
  name: object-counts
  namespace: quotaz
spec:
  hard:
    pods: "10"
    services: "5"
    configmaps: "10"
EOF
```

Check quota:

```bash
kubectl describe resourcequota object-counts -n quotaz
```

### Storage Quotas

Limit storage resources:

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: storage-quota
  namespace: quotaz
spec:
  hard:
    requests.storage: 10Gi
    persistentvolumeclaims: "5"
```

---

## Lab Cleanup

Remove all resources created in this lab:

```bash
# Delete all pods in the namespace
kubectl delete pods --all -n quotaz

# Delete resource quotas
kubectl delete resourcequota --all -n quotaz

# Delete limit ranges
kubectl delete limitrange --all -n quotaz

# Delete the namespace (removes everything)
kubectl delete namespace quotaz

# Verify cleanup
kubectl get namespace quotaz
```

Expected output:
```
Error from server (NotFound): namespaces "quotaz" not found
```

---

## Key Takeaways

1. **Resource Quotas** enforce aggregate limits at namespace level
2. **Resource Requests** guarantee minimum resources to containers
3. **Resource Limits** cap maximum resource consumption
4. **Quota Enforcement** prevents pod creation when limits are exceeded
5. **Namespaces with Quotas** require all pods to specify requests/limits
6. **LimitRanges** provide default resource values
7. **Multi-Tenancy** depends on proper quota configuration
8. **Monitoring** quota usage is essential for capacity planning

---

## Best Practices

### 1. Always Set Requests and Limits

```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

**Guidelines:**
- Requests: Based on minimum needs
- Limits: Based on maximum tolerable usage
- Limits should be >= Requests

### 2. Use LimitRanges for Defaults

```yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: mem-limit-range
  namespace: production
spec:
  limits:
  - default:
      memory: 512Mi
      cpu: 500m
    defaultRequest:
      memory: 256Mi
      cpu: 250m
    max:
      memory: 1Gi
      cpu: 1
    min:
      memory: 128Mi
      cpu: 100m
    type: Container
```

### 3. Set Appropriate Quota Per Environment

```yaml
# Development namespace - smaller quota
apiVersion: v1
kind: ResourceQuota
metadata:
  name: dev-quota
  namespace: development
spec:
  hard:
    requests.cpu: "10"
    requests.memory: 20Gi
    limits.cpu: "20"
    limits.memory: 40Gi
    pods: "50"

---
# Production namespace - larger quota
apiVersion: v1
kind: ResourceQuota
metadata:
  name: prod-quota
  namespace: production
spec:
  hard:
    requests.cpu: "50"
    requests.memory: 100Gi
    limits.cpu: "100"
    limits.memory: 200Gi
    pods: "200"
```

### 4. Monitor Quota Usage

```bash
# View all quotas
kubectl get resourcequota --all-namespaces

# Watch quota in specific namespace
watch kubectl describe resourcequota -n production

# Get quota as percentage
kubectl get resourcequota mem-cpu-demo -n quotaz -o json | jq '.status'
```

### 5. Document Quota Decisions

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: team-a-quota
  namespace: team-a
  annotations:
    description: "Team A - 5 developers, 3 microservices"
    last-review: "2026-03-01"
    owner: "team-a-lead@company.com"
spec:
  hard:
    requests.cpu: "20"
    requests.memory: 40Gi
```

---

## Additional Commands Reference

```bash
# Create namespace
kubectl create namespace <namespace-name>

# View all resource quotas
kubectl get resourcequota --all-namespaces

# View quota in specific namespace
kubectl get resourcequota -n <namespace>

# Describe quota (detailed view)
kubectl describe resourcequota <quota-name> -n <namespace>

# Delete quota
kubectl delete resourcequota <quota-name> -n <namespace>

# View limit ranges
kubectl get limitrange -n <namespace>

# Describe limit range
kubectl describe limitrange <name> -n <namespace>

# View pod resource usage
kubectl top pods -n <namespace>

# Get quota in YAML
kubectl get resourcequota <name> -n <namespace> -o yaml

# Edit quota
kubectl edit resourcequota <name> -n <namespace>

# View all resources in namespace
kubectl api-resources --verbs=list --namespaced -o name | xargs -n 1 kubectl get --show-kind --ignore-not-found -n <namespace>
```

---

## Troubleshooting

**Issue**: Pod fails with "exceeded quota" error

```bash
# Check quota limits
kubectl describe resourcequota -n <namespace>

# Check current usage
kubectl get resourcequota -n <namespace>

# List all pods and their resources
kubectl get pods -n <namespace> -o custom-columns=NAME:.metadata.name,CPU-REQUEST:.spec.containers[*].resources.requests.cpu,MEM-REQUEST:.spec.containers[*].resources.requests.memory

# Solution: Either reduce pod resources or increase quota
kubectl edit resourcequota <name> -n <namespace>
```

**Issue**: Pod rejected for missing resource specifications

```bash
# Error: "must specify limits.cpu, limits.memory, requests.cpu, requests.memory"

# Solution 1: Add resources to pod spec
# Solution 2: Create LimitRange to provide defaults
kubectl apply -f limitrange.yaml
```

**Issue**: Quota appears to have available space but pod still fails

```bash
# Check for multiple quotas
kubectl get resourcequota -n <namespace>

# Each quota is enforced independently
# Pod must satisfy ALL quotas

# Describe each quota
kubectl describe resourcequota -n <namespace>
```

---

## Real-World Example: Multi-Tenant Cluster

```yaml
# Namespace for Team A
apiVersion: v1
kind: Namespace
metadata:
  name: team-a
  labels:
    team: team-a
    environment: production

---
# Team A Resource Quota
apiVersion: v1
kind: ResourceQuota
metadata:
  name: team-a-quota
  namespace: team-a
spec:
  hard:
    requests.cpu: "30"
    requests.memory: 60Gi
    limits.cpu: "60"
    limits.memory: 120Gi
    pods: "100"
    services: "20"
    persistentvolumeclaims: "20"
    requests.storage: 100Gi

---
# Team A LimitRange
apiVersion: v1
kind: LimitRange
metadata:
  name: team-a-limits
  namespace: team-a
spec:
  limits:
  - max:
      memory: 4Gi
      cpu: 2
    min:
      memory: 64Mi
      cpu: 50m
    default:
      memory: 512Mi
      cpu: 500m
    defaultRequest:
      memory: 256Mi
      cpu: 250m
    type: Container
```

---

## Next Steps

Now that you understand Resource Quotas and Limits, proceed to:
- [Lab 23: Deployment Strategies and Rollouts](lab23-deploy-deployment-rollouts.md) - Learn about rolling updates and rollbacks
- Explore Vertical Pod Autoscaling (VPA) for automatic resource tuning
- Learn about Cluster Resource Management and Node Resources

## Further Reading

- [Kubernetes Resource Quotas Documentation](https://kubernetes.io/docs/concepts/policy/resource-quotas/)
- [Configure Memory and CPU Quotas](https://kubernetes.io/docs/tasks/administer-cluster/manage-resources/quota-memory-cpu-namespace/)
- [LimitRange Documentation](https://kubernetes.io/docs/concepts/policy/limit-range/)
- [Resource Management for Pods and Containers](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/)

---

**Lab Created**: March 2026
**Compatible with**: Kubernetes 1.24+
