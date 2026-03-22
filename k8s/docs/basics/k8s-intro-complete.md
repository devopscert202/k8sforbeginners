# Kubernetes Introduction for Beginners

Kubernetes (K8s) is an **open-source container orchestration platform** that automates the **deployment, scaling, and management** of containerized applications.

It helps teams manage containers (like Docker or containerd) at scale across clusters of servers — ensuring high availability, efficient resource utilization, and zero-downtime deployments.

📘 **Official Documentation:** [https://kubernetes.io/docs](https://kubernetes.io/docs)

---

## Containers and Docker – Quick Recap

### **Containers**

* **Definition:** Lightweight, portable units that package an application and all its dependencies together.
* **Isolation:** Provide process-level isolation without the heavy overhead of virtual machines.
* **Efficiency:** Containers share the host OS kernel, start up quickly, and use resources more efficiently than VMs.

### **Docker**

* **Definition:** A popular platform for building, packaging, and running containers.
* **Docker Images:** Immutable templates that define the contents of a container (app, libraries, dependencies).
* **Docker Engine:** The runtime responsible for running and managing containers.
* **Portability:** Containers run identically across environments — dev, test, or production.

### Container Image

A read-only template used to create containers.

### Containerized Application

An application packaged with its dependencies to ensure portability.

### Benefits of Containers

* Portability
* Scalability
* Consistency
* Isolation
* Speed

---

## Why Do We Need Kubernetes?

While **Docker** simplifies creating and running containers, it doesn't handle **container orchestration** — i.e., running containers at scale across multiple servers.

That's where **Kubernetes** comes in.

### **1. Automatic Scaling**

* **Challenge:** Manually scaling applications to handle variable loads is difficult.
* **Solution:** Kubernetes automatically adjusts the number of running containers (Pods) based on demand (via Horizontal Pod Autoscaler).

### **2. Service Discovery & Load Balancing**

* **Challenge:** How to route traffic to the right container?
* **Solution:** Kubernetes provides built-in DNS-based service discovery and load balancing.

### **3. Self-Healing**

* **Challenge:** Handling crashed or unhealthy containers manually.
* **Solution:** Kubernetes automatically restarts, replaces, or reschedules failed Pods.

### **4. Automated Rollouts & Rollbacks**

* **Challenge:** Deploying new versions without downtime.
* **Solution:** Kubernetes supports rolling updates and allows rollback to stable versions.

### **5. Resource Management**

* **Challenge:** Optimizing CPU, memory, and storage usage across clusters.
* **Solution:** Kubernetes schedules containers based on resource requests/limits for maximum efficiency.

### **6. Persistent Storage Management**

* **Challenge:** Containers are ephemeral; how to persist data?
* **Solution:** Kubernetes supports Persistent Volumes (PVs) and Persistent Volume Claims (PVCs) to manage stateful apps.

### **7. Batch Execution**

* Kubernetes can run batch jobs, cron jobs, and scheduled tasks.

### **8. Secret & Config Management**

* Manage sensitive data and configurations securely.

### **9. Storage Orchestration**

* Automatically mount storage systems (local, cloud, etc.).

---

## Kubernetes Architecture Overview

A **Kubernetes cluster** consists of:

* A **Control Plane (Master components)** – manages the cluster.
* One or more **Worker Nodes** – run your applications (Pods).

Here's a conceptual diagram:

```
               +--------------------------------------+
               |           Control Plane              |
               |--------------------------------------|
               |  kube-apiserver   etcd               |
               |  kube-scheduler   kube-controller-mgr|
               |  cloud-controller-manager (optional) |
               +--------------------------------------+
                             |
                 Cluster Communication (API)
                             |
       +---------------------------------------------------+
       |                   Worker Nodes                    |
       |---------------------------------------------------|
       |  kubelet | kube-proxy | container runtime (e.g.,  |
       |  containerd) | Pods (App Containers)               |
       +---------------------------------------------------+
```

### Overview

Kubernetes architecture follows a **master–worker** model (Control Plane and Nodes).

#### Core Components

1. **Control Plane (Master)** – Manages the cluster state and decisions.
2. **Worker Nodes** – Run the actual application workloads (Pods).
3. **etcd** – Distributed key-value store for cluster state.
4. **Controller Manager & Scheduler** – Manage lifecycle and placement of workloads.

---

## Kubernetes Components Explained

### **Control Plane Components (Master)**

| Component                    | Description                                                                                                                                  |
| ---------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| **kube-apiserver**           | The central management point — exposes the Kubernetes API. All communication (kubectl, UI, controllers) passes through it.                   |
| **etcd**                     | A distributed key-value store that stores all cluster data (state, config, secrets, etc.). Acts as Kubernetes' "brain."                      |
| **kube-scheduler**           | Assigns Pods to nodes based on resource requirements, constraints, and policies.                                                             |
| **kube-controller-manager**  | Runs various controllers that manage different aspects of the cluster (e.g., node controller, replication controller, endpoints controller). |
| **cloud-controller-manager** | Integrates Kubernetes with underlying cloud provider APIs (for load balancers, storage, etc.).                                               |

**kube-apiserver**
* Exposes the Kubernetes API (REST interface).
* Validates and configures cluster data for objects like Pods, Services, etc.

**etcd**
* Stores all cluster state data.
* Distributed and consistent.
* Example:
  ```bash
  etcdctl get /registry/pods/default/nginx
  ETCDCTL_API=3 etcdctl get /registry/nodes/worker-1
  ```

**kube-scheduler**
* Assigns Pods to Nodes based on resource needs and policies.
* Scheduling Process:
  1. Filtering
  2. Scoring
  3. Binding
* Example filters: CPU, Memory, Labels
* Example scoring: Least requested node wins.

**kube-controller-manager**
* Runs controllers that manage replicas, endpoints, and nodes.

**cloud-controller-manager**
* Integrates Kubernetes with cloud platforms (AWS, GCP, Azure).
* Bridges Kubernetes with cloud providers (e.g., creates LoadBalancers, storage volumes).

---

### **Node (Worker) Components**

| Component             | Description                                                                                                                       |
| --------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| **kubelet**           | The agent running on each node. It communicates with the control plane and ensures containers are running as defined in PodSpecs. |
| **kube-proxy**        | Manages network routing and load balancing for Pods within the node. It maintains network rules for cluster IPs and services.     |
| **Container Runtime** | The software responsible for running containers (e.g., containerd, CRI-O, Docker in older versions).                              |

Each Node runs:

* **kubelet** – Communicates with API server and manages Pods.
  - Manages containers on a node.
  - Watches the API server for Pod specs.
  - Reports node and Pod status.
  - Example manifest:
    ```bash
    cat /etc/kubernetes/manifests/kube-apiserver.yaml
    ```

* **kube-proxy** – Handles networking, routing, load balancing.
  - Handles Pod-to-Pod and external network routing.
  - Operation Modes:
    * iptables mode
    * IPVS mode

* **Container Runtime** – Runs containers (containerd, CRI-O).

---

### **Additional Core Concepts**

| Concept                                                    | Description                                                                                      |
| ---------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| **Pod**                                                    | The smallest deployable unit in Kubernetes — one or more containers sharing network and storage. |
| **ReplicaSet**                                             | Ensures a specified number of Pod replicas are running at all times.                             |
| **Deployment**                                             | Manages stateless applications — handles rolling updates, rollbacks, and scaling.                |
| **Service**                                                | Provides stable networking and load balancing for Pods.                                          |
| **Ingress**                                                | Manages external HTTP/HTTPS access to Services within the cluster.                               |
| **ConfigMap / Secret**                                     | Store configuration data and sensitive information separately from the application code.         |
| **Persistent Volume (PV) / Persistent Volume Claim (PVC)** | Manage storage independently from Pods.                                                          |
| **Namespace**                                              | Logical partitions for organizing cluster resources (like environments or teams).                |

---

## Container Runtime

**Container Runtime Interface (CRI):**

* Connects Kubernetes to underlying container runtime.

Common runtimes:

* containerd
* CRI-O
* Docker (deprecated since v1.24)

### Transition from Docker to Containerd

Kubernetes **removed Docker support** in v1.24, adopting **containerd** directly.

**Why?**

* Docker is built atop containerd.
* Removing Docker simplifies runtime integration.

**Example:**

```bash
# Check container runtime
kubectl get node -o wide
# or
crictl ps
```

### Containerd CLI and crictl

**crictl** – CLI for CRI-compatible runtimes.

```bash
crictl ps        # List containers
crictl images    # List images
crictl inspect   # Inspect container
```

---

## Controllers in Kubernetes

Controllers continuously monitor cluster state and take actions to reach the **desired state**.

### Types:

* **ReplicationController**
* **DeploymentController**
* **NodeController**
* **JobController**
* **DaemonSetController**

---

## Node Affinity / Anti-Affinity

Used to **control which nodes Pods are placed on.**

Example:

```yaml
affinity:
  nodeAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      nodeSelectorTerms:
        - matchExpressions:
            - key: kubernetes.io/hostname
              operator: In
              values: ["node1"]
```

---

## Kubernetes API

* The **Kubernetes API** exposes resources such as `Pods`, `Services`, `Deployments`, etc.
* Use `kubectl` to interact:

  ```bash
  kubectl get pods
  kubectl describe node worker-1
  ```

---

## Kubernetes Objects

Objects represent the **desired state** in the cluster (e.g., how many replicas, what image, etc.)

### Object Fields

* `apiVersion`
* `kind`
* `metadata`
* `spec`
* `status`

Example Pod YAML:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx-pod
spec:
  containers:
    - name: nginx
      image: nginx:1.27
      ports:
        - containerPort: 80
```

---

## Pods – The Smallest Deployable Unit

### Multi-container Pod Example:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: multi-container
spec:
  containers:
    - name: app
      image: nginx
    - name: sidecar
      image: busybox
      command: ["sh", "-c", "echo sidecar running; sleep 3600"]
```

---

## ReplicaSets and Deployments

### ReplicaSet

Maintains a stable set of replica Pods.

```yaml
apiVersion: apps/v1
kind: ReplicaSet
metadata:
  name: nginx-rs
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
        - name: nginx
          image: nginx
```

### Deployment

Manages ReplicaSets and updates.

---

## Deployment Operations

```bash
kubectl rollout status deployment/nginx-deploy
kubectl rollout undo deployment/nginx-deploy
kubectl scale deployment/nginx-deploy --replicas=5
```

---

## Networking in Kubernetes

### Key Concepts

* Every Pod gets a unique IP.
* Services expose Pods internally/externally.
* CNI Plugins (Calico, Flannel, Weave Net).

---

## Cluster Administration

* **Planning a cluster** – choose topology, storage, network.
* **Node management** – adding/removing nodes.
* **Kubelet authz/authn** – TLS, certificates, RBAC.
* **Kubeadm** – bootstrap and manage clusters.

Example:

```bash
kubeadm init --pod-network-cidr=10.244.0.0/16
kubeadm join <control-plane>:6443 --token <token>
```

---

## Kubernetes Dashboard

Note: Kubernetes Dashboard should now be treated as a legacy UI reference. The upstream repository is archived and no longer maintained. For the current UI path in this repo, use [Headlamp UI overview](../workloads/k8s-headlamp-ui.md) or [Headlamp HTML guide](../html/k8s-ui-headlamp.html).

Web-based UI to monitor, deploy, and manage workloads.

---

## Kubelet Authentication & Authorization

* **Authentication:** x509 certificates, bearer tokens.
* **Authorization:** RBAC, ABAC, Node authorizer.

---

## Advantages of Kubernetes

* ✅ **Scalability** – Automatically scale up/down based on demand
* ✅ **Self-healing** – Automatically restarts/replaces failed Pods
* ✅ **Rolling updates** – Zero downtime deployments
* ✅ **Portability** – Works across on-premises and cloud environments
* ✅ **Resource efficiency** – Optimizes hardware utilization
* ✅ **Declarative management** – "Desired state" maintained automatically
* ✅ **Automation and declarative management**
* ✅ **Cloud agnostic**
* ✅ **Efficient resource utilization**
* ✅ **Faster deployment cycles**
* ✅ **Cost efficiency**
* ✅ **Scalability and fault tolerance**

---

## Disadvantages of Kubernetes

* ❗ **Complexity:** Steep learning curve for beginners
* ❗ **Operational overhead:** Control plane components consume resources
* ❗ **Setup challenges:** Requires proper configuration for networking, security, and storage
* ❗ **Debugging difficulty:** Troubleshooting distributed systems can be challenging

---

## Business Benefits of Kubernetes

* 🚀 **Faster deployment cycles**
* 💰 **Cost efficiency**
* 🧱 **Scalability and fault tolerance**
* ⚙️ **Automation and declarative management**
* 🌍 **Cloud agnostic**
* 🧠 **Efficient resource utilization**

---

## Organizations Using Kubernetes

* Google (GKE)
* AWS (EKS)
* Microsoft (AKS)
* Spotify
* Airbnb
* Shopify
* Netflix

---

## Helpful References

* 📘 [Kubernetes Documentation](https://kubernetes.io/docs)
* 📦 [Kubernetes Architecture Explained (Official)](https://kubernetes.io/docs/concepts/overview/components/)
* 🧰 [Kubernetes Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)
* 🧩 [Interactive Playground – Katacoda (Archived)](https://www.katacoda.com/courses/kubernetes)
* ☸️ [Play with Kubernetes](https://labs.play-with-k8s.com/)

---

## Summary

Kubernetes is a **complete ecosystem** for automating containerized workloads, with:

* Declarative configuration
* Self-healing
* Scalability
* Extensibility via CRDs & Operators
* Multi-cloud support
