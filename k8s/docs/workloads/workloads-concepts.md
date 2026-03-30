# Kubernetes Training Material: Workloads and POD Concepts

---

## **Section 1: Workloads in Kubernetes**

### **What are Workloads?**
In Kubernetes, workloads are abstractions that represent applications running on the cluster. They are designed to manage and scale your applications efficiently by deploying containers as a set of pods.

### **Types of Workloads**
1. **Pod**: The smallest deployable unit that can run in Kubernetes.
2. **ReplicaSet**: Ensures a specified number of pod replicas are running at all times.
3. **Deployment**: Manages stateless applications by handling rolling updates and scaling.
4. **StatefulSet**: Used for stateful applications, ensuring stable identifiers and storage.
5. **DaemonSet**: Ensures a pod is running on all (or selected) nodes.
6. **Job**: Runs a single task to completion.
7. **CronJob**: Manages periodic tasks based on a schedule.

### **When to Use What?**
| Workload       | Use Case                                              |
|----------------|------------------------------------------------------|
| Pod            | Basic unit of deployment for single container apps. |
| ReplicaSet     | Maintain desired pod count for high availability.   |
| Deployment     | Stateless apps, rolling updates, easy scaling.      |
| StatefulSet    | Databases or apps needing persistent storage.       |
| DaemonSet      | Cluster-wide services like logging agents.          |
| Job            | One-time batch processes.                           |
| CronJob        | Scheduled tasks like backups.                       |

---

## **Section 2: Pods in Kubernetes**

### **What are Pods?**
A pod is the smallest, most basic deployable object in Kubernetes. It encapsulates one or more containers, shared storage, network, and specifications for how to run them.

### **Pod Characteristics**
- **Shared Network Namespace**: All containers in a pod share the same IP address and port space.
- **Shared Storage Volumes**: Containers within the pod can mount shared volumes.
- **Tightly Coupled Containers**: Containers within a pod are co-scheduled and run together on the same node.

### **Pod Lifecycle**
Pods go through several phases during their lifecycle:
1. **Pending**: Pod has been accepted but is waiting for resource assignment.
2. **Running**: Containers in the pod are executing.
3. **Succeeded**: All containers have exited successfully.
4. **Failed**: Containers have exited with an error.
5. **Unknown**: Pod state cannot be determined.

#### Example Pod YAML
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: simple-pod
spec:
  containers:
  - name: nginx
    image: nginx:latest
    ports:
    - containerPort: 80
```

---

## **Section 3: Multi-Container Pods**

### **What are Multi-Container Pods?**
Pods can host multiple containers that work together. These containers share the same network and storage resources.

### **Use Cases for Multi-Container Pods**
1. **Sidecar Pattern**: Additional functionality like logging or caching.
2. **Adapter Pattern**: Translating requests from one interface to another.
3. **Ambassador Pattern**: Proxying requests to an external service.

#### Example Multi-Container Pod YAML
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: multi-container-pod
spec:
  containers:
  - name: app-container
    image: myapp:latest
  - name: sidecar-container
    image: logging-agent:latest
```

---

## **Section 4: Init Containers**

### **What are Init Containers?**
Init containers run before application containers and are used to perform initialization tasks, such as setting up prerequisites or performing configuration steps.

### **Use Cases for Init Containers**
1. Fetch configuration files before the main container starts.
2. Check for service dependencies.
3. Set up the environment for the application container.

#### Example Init Container YAML
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: init-container-pod
spec:
  initContainers:
  - name: init-container
    image: busybox
    command: ['sh', '-c', 'echo Initializing...; sleep 5;']
  containers:
  - name: app-container
    image: nginx:latest
```

---

## **Section 5: Health Monitoring of Kubernetes Pods**

### **Why Health Monitoring?**
Health monitoring ensures that pods are running correctly and restarts unhealthy containers automatically.

### **Liveness and Readiness Probes**
1. **Liveness Probe**: Checks if the container is running. If it fails, Kubernetes restarts the container.
2. **Readiness Probe**: Checks if the container is ready to accept traffic.

#### Example Health Check YAML
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: health-check-pod
spec:
  containers:
  - name: nginx
    image: nginx:latest
    livenessProbe:
      httpGet:
        path: /
        port: 80
      initialDelaySeconds: 5
      periodSeconds: 10
    readinessProbe:
      httpGet:
        path: /
        port: 80
      initialDelaySeconds: 5
      periodSeconds: 10
```

---

## **Section 6: Resource Quotas**

### **What are Resource Quotas?**
Resource quotas enforce resource constraints at the namespace level to ensure fair resource allocation among users.

### **Resource Types That Can Be Limited**
1. **CPU**
2. **Memory**
3. **Persistent Volume Claims**

#### Example Resource Quota YAML
```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: compute-resources
  namespace: my-namespace
spec:
  hard:
    requests.cpu: "2"
    requests.memory: "1Gi"
    limits.cpu: "4"
    limits.memory: "2Gi"
```

---

## **Section 7: Summary and Use Cases**

| **Concept**        | **Description**                           | **Use Case**                                  | **Example**                              |
|--------------------|-------------------------------------------|-----------------------------------------------|------------------------------------------|
| **Pods**           | Smallest deployable unit in Kubernetes.   | Basic unit of deployment.                    | Deploying an Nginx pod.                  |
| **Multi-Container Pods** | Pods with multiple containers working together. | Sidecar or logging services.                | App with a logging agent.               |
| **Init Containers**| Runs initialization tasks.                | Fetching configs or setting up dependencies. | Database initialization script.          |
| **Health Probes**  | Liveness and readiness checks.            | Ensures containers are running and ready.    | Nginx liveness probe.                   |
| **Resource Quotas**| Limits resource usage in a namespace.     | Avoid resource over-allocation.              | CPU and memory quotas for a namespace.   |

---

By understanding these concepts, Kubernetes administrators can deploy and manage workloads effectively, ensuring high availability, scalability, and optimized resource usage. Each concept plays a vital role in the Kubernetes ecosystem, and selecting the right one depends on the specific use case and application requirements.

