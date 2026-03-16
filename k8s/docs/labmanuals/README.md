# Kubernetes Lab Manuals

## Background

This collection of **43 comprehensive, hands-on lab manuals** has been created to provide a structured learning path for mastering Kubernetes from fundamentals to advanced production-ready concepts. Each lab has been carefully designed with step-by-step instructions, real-world examples, and practical exercises that build upon one another.

### What We're Trying to Achieve

These lab manuals aim to:
- **Progressive Learning**: Start from basic concepts and gradually advance to complex topics
- **Hands-On Practice**: Learn by doing with complete, working YAML examples
- **Production Readiness**: Cover not just theory, but practical skills needed in real-world environments
- **Comprehensive Coverage**: Address all key areas - basics, security, storage, networking, scheduling, observability, and more
- **Self-Paced**: Allow learners to follow their own path based on goals and experience level
- **Reference Material**: Serve as a quick reference guide for common Kubernetes operations

The labs are based on real Kubernetes manifests from the `k8s/labs/` directory and are enhanced with detailed explanations, troubleshooting guides, and best practices drawn from production experience.

---

## How to Use These Lab Manuals

### Getting Started

1. **Prerequisites Setup**: Ensure you have a Kubernetes cluster (Minikube, Kind, or cloud-based) and `kubectl` installed
2. **Choose Your Path**: Select a learning path based on your experience level (see [Learning Paths](#learning-paths) below)
3. **Navigate to Lab Directory**: All YAML files referenced in labs are located in `k8s/labs/` subdirectories
4. **Follow Step-by-Step**: Each lab includes:
   - Overview of concepts
   - Prerequisites
   - Detailed exercises with commands
   - Expected outputs
   - Troubleshooting tips
   - Cleanup instructions
5. **Practice and Experiment**: Don't just copy-paste - understand what each YAML field does and try variations

### Lab Structure

Every lab follows a consistent format:
- **Overview**: What you'll learn in this lab
- **Prerequisites**: Required setup and prior labs
- **Learning Objectives**: Specific skills you'll gain
- **Exercises**: Step-by-step hands-on activities
- **Key Takeaways**: Summary of important concepts
- **Troubleshooting**: Common issues and solutions
- **Cleanup**: How to remove resources
- **Next Steps**: Recommended labs to continue

---

## Complete Lab Index

| S. No | Category | Lab Name | Description | Link |
|-------|----------|----------|-------------|------|
| 1 | Foundation | Creating Pods and Deployments | Learn to create Kubernetes Pods and Deployments using YAML manifests with Apache HTTP Server containers. | [lab01-creating-pods.md](lab01-creating-pods.md) |
| 2 | Foundation | Creating Services | Expose Pods and Deployments using NodePort and LoadBalancer Services with service discovery. | [lab02-creating-services.md](lab02-creating-services.md) |
| 3 | Foundation | ETCD Backup and Restore | Backup and restore etcd, the distributed key-value store that serves as Kubernetes' brain. | [lab03-etcd-backup-restore.md](lab03-etcd-backup-restore.md) |
| 4 | Foundation | Essential kubectl Commands | Master essential kubectl commands for day-to-day Kubernetes operations. | [lab04-kubectl-essentials.md](lab04-kubectl-essentials.md) |
| 5 | Foundation | Cluster Administration | Essential cluster administration tasks using kubeadm and kubectl including certificate management. | [lab05-cluster-administration.md](lab05-cluster-administration.md) |
| 6 | Foundation | Kubernetes Installation | Install a complete Kubernetes cluster from scratch on Ubuntu using kubeadm. | [lab06-kubernetes-installation.md](lab06-kubernetes-installation.md) |
| 7 | Foundation | RBAC Security | Implement Role-Based Access Control with user certificates, roles, and permissions. | [lab07-rbac-security.md](lab07-rbac-security.md) |
| 8 | Foundation | Docker Build and Run | Build Docker images, tag versions, run containers, and manage multi-version applications. | [lab08-docker-build-run.md](lab08-docker-build-run.md) |
| 9 | Security | Pod Security Context | Configure security contexts for Pods including user IDs, file permissions, and privilege escalation controls. | [lab09-security-context.md](lab09-security-context.md) |
| 10 | Security | Advanced Network Policies | Implement namespace isolation with NetworkPolicies to restrict cross-namespace traffic. | [lab10-advanced-network-policies.md](lab10-advanced-network-policies.md) |
| 11 | Security | OPA Gatekeeper | Use Open Policy Agent Gatekeeper to enforce security and compliance policies with admission control. | [lab11-opa-gatekeeper.md](lab11-opa-gatekeeper.md) |
| 12 | Security | Image Scanning with Trivy | Scan container images and Kubernetes resources for security vulnerabilities using Trivy. | [lab12-image-scanning.md](lab12-image-scanning.md) |
| 13 | Storage | Basic Storage Volumes | Work with emptyDir and hostPath volumes, sharing data between containers. | [lab13-basic-storage-volumes.md](lab13-basic-storage-volumes.md) |
| 14 | Storage | Persistent Storage | Learn PersistentVolumes (PV), PersistentVolumeClaims (PVC), NFS storage, and Secrets as volumes. | [lab14-persistent-storage.md](lab14-persistent-storage.md) |
| 15 | Workloads | ConfigMaps | Use ConfigMaps to manage configuration data as environment variables and mounted files. | [lab15-configmap.md](lab15-configmap.md) |
| 16 | Workloads | Deployment Strategies | Deploy applications with rolling updates, rollbacks, and scaling strategies. | [lab16-deployment-strategies.md](lab16-deployment-strategies.md) |
| 17 | Workloads | DaemonSets | Run a copy of a Pod on every node using DaemonSets for cluster-wide services. | [lab17-daemonset.md](lab17-daemonset.md) |
| 18 | Workloads | Jobs and Batch Processing | Run one-time tasks and batch workloads with Kubernetes Jobs. | [lab18-jobs-batch.md](lab18-jobs-batch.md) |
| 19 | Workloads | CronJobs | Schedule recurring tasks with CronJobs for automated operations. | [lab19-cronjob.md](lab19-cronjob.md) |
| 20 | Workloads | Horizontal Pod Autoscaler | Automatically scale Pods based on CPU utilization and custom metrics. | [lab20-hpa.md](lab20-hpa.md) |
| 21 | Workloads | Init Containers | Use init containers for setup tasks before main application containers start. | [lab21-init-containers.md](lab21-init-containers.md) |
| 22 | Workloads | Pod Lifecycle and Multi-Container | Understand Pod lifecycle hooks and multi-container patterns (sidecar, ambassador, adapter). | [lab22-pod-lifecycle-multi-container.md](lab22-pod-lifecycle-multi-container.md) |
| 23 | Networking | Multi-Port Services | Create Services that expose multiple ports for applications with different endpoints. | [lab23-multi-port-services.md](lab23-multi-port-services.md) |
| 24 | Networking | Ingress and EndpointSlices | Configure Ingress controllers for HTTP/HTTPS routing and understand EndpointSlices. | [lab24-ingress-endpointslices.md](lab24-ingress-endpointslices.md) |
| 25 | Networking | DNS Configuration | Configure and customize DNS resolution in Kubernetes clusters. | [lab25-dns-configuration.md](lab25-dns-configuration.md) |
| 26 | Scheduling | NodeSelector Scheduling | Control Pod placement using nodeSelector for node selection based on labels. | [lab26-scheduling-nodeselector.md](lab26-scheduling-nodeselector.md) |
| 27 | Scheduling | Affinity and Anti-Affinity | Use node and pod affinity rules for advanced scheduling requirements. | [lab27-scheduling-affinity.md](lab27-scheduling-affinity.md) |
| 28 | Scheduling | Priority Classes | Define priority levels for Pods to influence scheduling decisions. | [lab28-scheduling-priorityclass.md](lab28-scheduling-priorityclass.md) |
| 29 | Scheduling | Taints and Tolerations | Use taints and tolerations to control which Pods can run on which nodes. | [lab29-scheduling-tolerations.md](lab29-scheduling-tolerations.md) |
| 30 | Observability | Health Probes | Configure liveness, readiness, and startup probes for application health monitoring. | [lab30-probes.md](lab30-probes.md) |
| 31 | Observability | Metrics Server | Install and use Metrics Server for resource usage monitoring and metrics collection. | [lab31-metrics-server.md](lab31-metrics-server.md) |
| 32 | Resource Management | Resource Quotas and Limits | Set resource quotas and limits at namespace and Pod levels for resource governance. | [lab32-resource-quotas-limits.md](lab32-resource-quotas-limits.md) |
| 33 | Resource Management | Deployment Rollouts | Manage deployment rollouts with progressive delivery and canary deployments. | [lab33-deployment-rollouts.md](lab33-deployment-rollouts.md) |
| 34 | Resource Management | Kubernetes Dashboard | Install and use the Kubernetes Dashboard for cluster visualization and management. | [lab34-kubernetes-dashboard.md](lab34-kubernetes-dashboard.md) |
| 35 | Advanced Topics | Static Pods | Understand and configure static Pods that are managed directly by kubelet. | [lab35-static-pods.md](lab35-static-pods.md) |
| 36 | Advanced Topics | WordPress on Kubernetes | Deploy a complete WordPress application with MySQL database on Kubernetes. | [lab36-wordpress-on-k8s.md](lab36-wordpress-on-k8s.md) |
| 37 | Advanced Topics | Frontend Deployment | Deploy multi-tier frontend applications with proper service architecture. | [lab37-frontend-deployment.md](lab37-frontend-deployment.md) |
| 38 | Security | Pod Security Standards | Implement Pod Security Standards (PSS) and Pod Security Admission (PSA) for cluster-wide security policies (K8s 1.25+). | [lab38-pod-security-standards.md](lab38-pod-security-standards.md) |
| 39 | Workloads | StatefulSets & Stateful Applications | Deploy and manage stateful applications like databases using StatefulSets with volumeClaimTemplates for persistent data. | [lab39-statefulsets.md](lab39-statefulsets.md) |
| 40 | Advanced Topics | Cluster Upgrades with kubeadm | Upgrade a Kubernetes cluster from one version to another using kubeadm with zero-downtime strategies. | [lab40-cluster-upgrades.md](lab40-cluster-upgrades.md) |
| 41 | Networking | Gateway API (Next-Gen Ingress) | Configure Gateway API for advanced HTTP/HTTPS routing with domain workarounds for local development (K8s 1.26+). | [lab41-gateway-api.md](lab41-gateway-api.md) |
| 42 | Advanced Topics | High Availability Cluster (Optional) | Deploy a production-grade multi-master HA cluster with stacked etcd, load balancers, and failover capabilities. | [lab42-ha-cluster-optional.md](lab42-ha-cluster-optional.md) |
| 43 | Advanced Topics | Custom Resource Definitions (Optional) | Extend the Kubernetes API with Custom Resource Definitions (CRDs), create custom resources, and understand the operator pattern. | [lab43-custom-resource-definitions.md](lab43-custom-resource-definitions.md) |

---

## Learning Paths

Choose a learning path based on your goals and experience:

### Path 1: Complete Beginner
Start here if you're new to Kubernetes:
```
Lab 08 (Docker) → Lab 01 (Pods) → Lab 02 (Services) → Lab 04 (kubectl) →
Lab 15 (ConfigMaps) → Lab 16 (Deployments)
```

### Path 2: Security Focus
Master Kubernetes security:
```
Lab 01 (basics) → Lab 07 (RBAC) → Lab 09 (Security Context) →
Lab 10 (Network Policies) → Lab 11 (OPA) → Lab 12 (Image Scanning)
```

### Path 3: Storage Mastery
Deep dive into storage:
```
Lab 01 (basics) → Lab 13 (Basic Volumes) → Lab 14 (Persistent Storage) →
Lab 15 (ConfigMaps) → Lab 36 (WordPress practical)
```

### Path 4: Workload Patterns
Learn all workload controllers:
```
Lab 01 (basics) → Lab 16 (Deployments) → Lab 17 (DaemonSets) →
Lab 18 (Jobs) → Lab 19 (CronJobs) → Lab 20 (HPA) → Lab 21-22 (Advanced Patterns)
```

### Path 5: Pod Scheduling
Master pod placement:
```
Lab 01 (basics) → Lab 26 (NodeSelector) → Lab 27 (Affinity) →
Lab 28 (Priority) → Lab 29 (Taints/Tolerations)
```

### Path 6: Networking Deep Dive
Understand Kubernetes networking:
```
Lab 02 (Services) → Lab 23 (Multi-Port) → Lab 25 (DNS) →
Lab 10 (Network Policies) → Lab 24 (Ingress)
```

### Path 7: Production Readiness
Build production-grade deployments:
```
Labs 01-08 (Foundation) → Lab 30 (Probes) → Lab 31 (Metrics) →
Lab 20 (HPA) → Lab 32 (Quotas) → Lab 33 (Rollouts) → Lab 36 (Real App)
```

---

## Prerequisites

Before starting, ensure you have:

### Required Tools
- **Kubernetes cluster**: Minikube, Kind, Docker Desktop, or cloud-based (GKE/EKS/AKS)
- **kubectl**: Kubernetes CLI installed and configured
- **docker**: For building and running containers
- **Terminal**: Bash, PowerShell, or similar
- **Text editor**: VS Code, vim, nano, etc.

### Required Knowledge
- Basic command-line operations
- Understanding of containers and Docker
- YAML syntax basics
- Basic networking concepts

### Quick Verification
```bash
# Check kubectl
kubectl version --client

# Verify cluster connection
kubectl cluster-info

# Check nodes
kubectl get nodes
```

---

## Lab Files Location

All YAML files referenced in the labs are organized in subdirectories:

```
k8s/labs/
├── basics/              # Labs 01-02
├── administration/      # Labs 03-05
├── security/            # Labs 07, 09-12
├── storage/             # Labs 13-14
├── config/              # Lab 15
├── workloads/           # Labs 17-22, 30, 36
├── scheduling/          # Labs 26-29
│   ├── nodeselector/
│   ├── affinity/
│   ├── priorityclass/
│   └── tolerations/
└── networking/          # Labs 23-25
```

---

## Tips for Success

1. **Follow sequentially** - Early labs build foundational knowledge
2. **Don't skip cleanup** - Remove resources after each lab to avoid conflicts
3. **Read error messages** - They provide valuable debugging information
4. **Use `kubectl describe` and `kubectl logs`** - Your best debugging tools
5. **Experiment** - Modify YAML files to understand how changes affect behavior
6. **Take notes** - Document your learnings and issues encountered
7. **Practice regularly** - Consistent hands-on practice is key to mastery

---

## Contributing & Reporting Issues

### Found a Bug or Have Suggestions?

We welcome contributions from the community! Here's how you can help:

#### Reporting Bugs
If you find errors, typos, or issues in the lab manuals:
1. Check if the issue already exists in the repository
2. Create a detailed bug report including:
   - Lab number and section
   - Description of the issue
   - Expected vs actual behavior
   - Your environment (Kubernetes version, cluster type)
   - Steps to reproduce

#### Suggesting Improvements
Have ideas for improvements or new labs?
1. Open an issue describing your suggestion
2. Provide clear examples and use cases
3. Explain how it would benefit learners

#### Submitting Pull Requests
To contribute directly:
1. **Fork the repository** to your GitHub account
2. **Create a feature branch**: `git checkout -b fix/lab05-typo` or `git checkout -b feature/new-lab`
3. **Make your changes** with clear, descriptive commits
4. **Test thoroughly** - Ensure commands work as expected
5. **Update related documentation** if needed
6. **Submit a Pull Request (PR)** to the upstream repository with:
   - Clear title describing the change
   - Detailed description of what was changed and why
   - Reference any related issues
   - Screenshots or outputs if applicable

#### PR Guidelines
- Keep changes focused and atomic (one issue/feature per PR)
- Follow existing lab manual formatting and structure
- Ensure all commands are tested and work
- Use consistent terminology aligned with official Kubernetes documentation
- Update the lab index table if adding/removing labs

**Repository Owner**: All contributions will be reviewed by the upstream maintainer before merging.

---

## Additional Resources

- [Kubernetes Official Documentation](https://kubernetes.io/docs/)
- [kubectl Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)
- [YAML Syntax Guide](https://yaml.org/)
- [Docker Documentation](https://docs.docker.com/)
- [Kubernetes Patterns Book](https://kubernetes.io/docs/concepts/cluster-administration/manage-deployment/)

### Certification Alignment
These labs align with:
- **CKA** (Certified Kubernetes Administrator)
- **CKAD** (Certified Kubernetes Application Developer)
- **CKS** (Certified Kubernetes Security Specialist)

---

## Troubleshooting Common Issues

### kubectl not found
```bash
# Install kubectl following the official guide
# https://kubernetes.io/docs/tasks/tools/
```

### Can't connect to cluster
```bash
# Check cluster status
kubectl cluster-info

# For Minikube
minikube status

# For Kind
kind get clusters
```

### Image pull errors
```bash
# Check Docker daemon
docker ps

# For Minikube, use Minikube's Docker daemon
eval $(minikube docker-env)
```

### Resources from previous labs interfering
```bash
# List all resources
kubectl get all

# Clean up
kubectl delete deployment,service,pod --all

# Or delete namespace (if not default)
kubectl delete namespace <namespace-name>
```

---

## Summary

- **43 comprehensive labs** covering Kubernetes from basics to advanced topics
- **9 logical categories**: Foundation, Security, Storage, Workloads, Networking, Scheduling, Observability, Resource Management, Advanced
- **7 curated learning paths** for different goals and experience levels
- **Complete cross-references** between related labs
- **Production-ready skills** with real-world examples
- **Modern K8s features**: Includes K8s 1.25-1.28+ features (PSS/PSA, Gateway API, CronJob timezones, native sidecar spec, CEL validation)
- **Advanced optional labs**: Custom Resource Definitions (CRDs), High Availability clusters
- **Open for contributions** via Pull Requests

---

**Happy Learning! 🚀**

*Last Updated: March 16, 2026*
*Total Labs: 43*
*Kubernetes Compatibility: 1.24+ (with K8s 1.25-1.28+ advanced features)*

For questions, issues, or contributions, please submit a Pull Request or open an issue in the repository.
