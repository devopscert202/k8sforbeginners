# Kubernetes Architecture Overview

## 🏗️ Introduction

Kubernetes is a powerful container orchestration platform that automates the deployment, scaling, and management of containerized applications. Understanding its architecture is fundamental to working effectively with Kubernetes clusters.

The Kubernetes architecture follows a **master-worker** (control plane and worker nodes) pattern, where:

- **Control Plane (Master Node)**: Manages the cluster, makes scheduling decisions, and responds to cluster events
- **Worker Nodes**: Run the actual application workloads in containers

## 📐 Key Components

### Control Plane Components

1. **API Server (kube-apiserver)** - The front-end for the Kubernetes control plane. All communication goes through this central hub.
2. **etcd** - Distributed key-value store that holds all cluster data. The single source of truth.
3. **Scheduler (kube-scheduler)** - Watches for newly created pods and assigns them to nodes based on resource requirements.
4. **Controller Manager (kube-controller-manager)** - Runs controller processes that regulate the state of the cluster.
5. **Cloud Controller Manager** - Integrates with cloud provider APIs for cloud-specific control logic.

### Worker Node Components

1. **Kubelet** - An agent that runs on each worker node, ensuring containers are running in pods.
2. **Container Runtime** - Software responsible for running containers (containerd, CRI-O, Docker).
3. **kube-proxy** - Network proxy that maintains network rules and enables service communication.
4. **CNI Plugin** - Handles pod networking and IP address management (Calico, Flannel, Weave).

## 🌐 How It All Works Together

1. Users interact with the cluster via **kubectl** CLI, sending commands to the API Server
2. The **API Server** validates and processes requests, storing state in **etcd**
3. The **Scheduler** watches for unscheduled pods and assigns them to suitable nodes
4. The **Kubelet** on each node receives instructions and manages pod lifecycle
5. The **Container Runtime** actually starts and stops containers
6. **kube-proxy** manages networking rules for service discovery and load balancing
7. **Controllers** continuously monitor cluster state and make corrections to match desired state

## 🎯 Real-World Analogy: Container Harbor

Think of Kubernetes as a modern shipping harbor:

- **Ship Captain (User)** brings cargo requests via kubectl
- **Harbor Master (API Server)** coordinates all operations
- **Crane Operator (Scheduler)** decides where to place containers
- **Dock Supervisor (Kubelet)** manages dock workers
- **Forklift Crew (Container Runtime)** moves physical containers
- **Storage Yard (Pods)** holds the containers
- **Traffic Control (kube-proxy)** routes vehicles efficiently
- **Road System (CNI)** connects everything together

---

## 🎨 Interactive Architecture Diagram

For a comprehensive visual understanding of Kubernetes architecture with interactive components, animations, and detailed explanations:

### **[📊 View Interactive Kubernetes Architecture Diagram →](./interactive-k8s-architecture.html)**

**What you'll see:**
- ✨ Animated flow diagrams showing component interactions
- 🖱️ Hover tooltips with detailed component descriptions
- 🎯 Visual representation of control plane and worker nodes
- 🔄 Real-time data flow animations
- 🚢 Complete harbor analogy with storytelling flow
- 📦 Pod lifecycle and networking visualization

**Recommended for:**
- Understanding component relationships
- Visual learning and teaching
- Certification preparation (CKA/CKAD)
- Architectural presentations

---

## 📚 Further Reading

- [Official Kubernetes Architecture Documentation](https://kubernetes.io/docs/concepts/architecture/)
- [Kubernetes Components](https://kubernetes.io/docs/concepts/overview/components/)
- [Cluster Architecture](https://kubernetes.io/docs/concepts/architecture/nodes/)

---

## 🎓 Learning Path

After understanding the architecture:

1. **Basics** → [Pods](../workloads/pods.md), [Namespaces](../common/k8s-namespaces.md)
2. **Workloads** → [Deployments](../workloads/deployments.md), [Services](../networking/services.md)
3. **Networking** → [Ingress](../networking/ingress.md), [Network Policies](../networking/networkpolicies.md)
4. **Security** → [RBAC](../security/rbac.md), [Pod Security Standards](../security/pod-security-standards.md)
5. **Storage** → [Volumes](../storage/volumes.md), [Persistent Volumes](../storage/persistentvolumes.md)

---

**💡 Pro Tip**: Open the interactive diagram in a separate tab and refer to it while working through the labs for better understanding of how components interact!
