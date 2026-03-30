### **Understanding Resource Quota in Kubernetes**

#### **What is Resource Quota?**
Resource Quota is a Kubernetes feature that limits the total amount of resources (like CPU, memory, storage, etc.) that can be consumed by all pods, containers, or other resources in a namespace. It helps ensure fair usage among users or teams sharing the same cluster, prevents resource overuse, and enforces governance.

---

### **How Resource Quota Works**

When a Resource Quota is applied to a namespace:
1. Every pod (or other resource) that is created in the namespace is measured against the limits specified in the Resource Quota.
2. If adding a new pod causes the total resource usage in the namespace to exceed the quota, the pod deployment fails.

---

### **Example Resource Quota**

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: mem-cpu-demo
  namespace: quotaz
spec:
  hard:
    requests.cpu: "1"        # Total allowed CPU requests: 1 CPU
    requests.memory: 1Gi     # Total allowed memory requests: 1 GiB
    limits.cpu: "2"          # Total allowed CPU limits: 2 CPUs
    limits.memory: 2Gi       # Total allowed memory limits: 2 GiB
```

- **`requests.cpu` and `requests.memory`**: Define the guaranteed minimum resources a pod can consume.
- **`limits.cpu` and `limits.memory`**: Define the maximum resources a pod can use.

---

### **Scenario: Deploying Pods Under Resource Quota**

#### **First Pod Deployment**

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
        memory: "800Mi"   # 0.8 GiB
        cpu: "800m"       # 0.8 CPU
      requests:
        memory: "600Mi"   # 0.6 GiB
        cpu: "400m"       # 0.4 CPU
```

#### **Resource Usage After First Pod**

- The first pod's requests and limits:
  - Requests: 0.4 CPU, 600Mi memory.
  - Limits: 0.8 CPU, 800Mi memory.

- Resource Quota remaining after deploying the first pod:
  - **Requests:**
    - `requests.cpu`: `1 - 0.4 = 0.6 CPU`
    - `requests.memory`: `1Gi - 600Mi = 400Mi`
  - **Limits:**
    - `limits.cpu`: `2 - 0.8 = 1.2 CPU`
    - `limits.memory`: `2Gi - 800Mi = 1.2Gi`

Since the first pod's resources fit within the Resource Quota, **it is deployed successfully**.

---

#### **Second Pod Deployment**

You now try to deploy a second pod with identical resource requirements:

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

#### **Resource Check**

The second pod requests:
- **Requests:**
  - `requests.cpu`: 0.4 CPU
  - `requests.memory`: 600Mi
- **Limits:**
  - `limits.cpu`: 0.8 CPU
  - `limits.memory`: 800Mi

After deploying the first pod, the remaining quota is:
- **Requests:**
  - `requests.cpu`: 0.6 CPU (sufficient for the second pod).
  - `requests.memory`: 400Mi (**insufficient**, as the second pod needs 600Mi).
- **Limits:**
  - `limits.cpu`: 1.2 CPU (sufficient for the second pod).
  - `limits.memory`: 1.2Gi (sufficient for the second pod).

Since the second pod's **`requests.memory` (600Mi)** exceeds the available quota (400Mi), **it cannot be deployed**.

---

### **Key Takeaways**
1. **Requests vs. Limits**:
   - Requests are the guaranteed minimum resources a pod gets.
   - Limits are the maximum resources a pod can use.

2. **Why the Second Pod Fails**:
   The second pod's resource requests exceed the available `requests.memory` in the namespace.

3. **Managing Resource Quota**:
   - **Increase the quota**: If more resources are needed, update the `ResourceQuota`:
     ```yaml
     spec:
       hard:
         requests.memory: 2Gi
     ```
   - **Reduce pod requests**: Adjust the second pod’s resource requests to fit within the available quota:
     ```yaml
     resources:
       requests:
         memory: "400Mi"
         cpu: "400m"
     ```
   - **Delete unused pods**: Free up resources by deleting pods that are no longer needed.

---

### **Simplified Visual Example**

| **Quota Type**   | **Total (Quota)** | **Used (After 1st Pod)** | **Remaining** | **2nd Pod Requirement** | **Can Deploy?** |
|-------------------|-------------------|--------------------------|---------------|--------------------------|-----------------|
| `requests.cpu`    | 1 CPU            | 0.4 CPU                 | 0.6 CPU       | 0.4 CPU                 | ✅ Yes          |
| `requests.memory` | 1 Gi             | 600 Mi                  | 400 Mi        | 600 Mi                  | ❌ No           |
| `limits.cpu`      | 2 CPUs           | 0.8 CPU                 | 1.2 CPU       | 0.8 CPU                 | ✅ Yes          |
| `limits.memory`   | 2 Gi             | 800 Mi                  | 1.2 Gi        | 800 Mi                  | ✅ Yes          |

By understanding how the Resource Quota calculates usage and availability, you can effectively manage resource constraints in Kubernetes clusters.
