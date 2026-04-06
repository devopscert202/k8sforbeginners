### **Azure Kubernetes Service (AKS) — Part 2: Kubernetes resources**

---

### **1. Introduction**

On AKS you use the same Kubernetes APIs as anywhere else: **Namespaces**, **Deployments**, **Services**, and cloud-backed **LoadBalancer** Services. The difference is **how** `type: LoadBalancer` is implemented: Azure’s cloud controller provisions an **Azure Load Balancer** and wires health probes and backends to your nodes/pods.

---

### **2. Illustrative manifests**

Below YAML is for **understanding shape and fields**, not a copy-paste lab sequence.

**Namespace**

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: apache-namespace
```

**Deployment (example: httpd)**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: apache-server
  namespace: apache-namespace
spec:
  replicas: 3
  selector:
    matchLabels:
      app: apache-server
  template:
    metadata:
      labels:
        app: apache-server
    spec:
      containers:
      - name: apache-server
        image: httpd:latest
        ports:
        - containerPort: 80
```

**Public LoadBalancer Service**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: apache-service
  namespace: apache-namespace
spec:
  selector:
    app: apache-server
  ports:
    - protocol: TCP
      port: 80
      targetPort: 80
  type: LoadBalancer
```

**Internal load balancer (annotation)**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: apache-service-ilb
  namespace: apache-namespace
  annotations:
    service.beta.kubernetes.io/azure-load-balancer-internal: "true"
spec:
  selector:
    app: apache-server
  ports:
    - protocol: TCP
      port: 80
      targetPort: 80
  type: LoadBalancer
```

---

### **3. How AKS implements LoadBalancer Services**

The **cloud controller manager** creates and updates Azure load balancing resources to match Service objects: frontend IP, backend pool tied to nodes, probes, and rules. **Internal** load balancers use annotations so the frontend stays on a private subnet.

---

### **4. Service types (comparison)**

| Service type     | Behavior | Typical use |
|------------------|----------|-------------|
| **ClusterIP**    | Virtual IP inside the cluster only | East-west traffic between Pods |
| **NodePort**     | Host port on each node | Simple external access, dev clusters |
| **LoadBalancer** | External LB (Azure-managed on AKS) | Internet-facing or private LB with annotations |
| **ExternalName** | CNAME to external DNS | Pointing to services outside the cluster |

---

### **5. Rolling updates**

Changing the container **image** (or other pod template fields) on a Deployment triggers a **rolling update**: new ReplicaSet scales up, old one scales down according to strategy defaults or `maxSurge` / `maxUnavailable`. Status is visible via `kubectl rollout status` and ReplicaSet history.

---

### **6. AKS-specific notes**

- **Cloud controller** manages LB lifecycle; failures often show up as Events on the Service or controller logs.
- **Managed identity** is commonly used for AKS to Azure resource access without long-lived secrets in cluster.
- **Network policies** (with a supporting CNI) add pod-level firewall rules.
- **Scaling** applies at the Deployment replica count and at the node pool level for capacity.

---

## Hands-On Labs

Practice these concepts with guided lab exercises:

| Lab | Description |
|-----|-------------|
| [Lab 01: Creating Pods and Deployments](../../labmanuals/lab01-basics-creating-pods.md) | Deployments, labels, and rolling updates |
| [Lab 02: Creating Kubernetes Services](../../labmanuals/lab02-basics-creating-services.md) | ClusterIP, NodePort, and LoadBalancer patterns |
