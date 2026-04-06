# Kubernetes Lab Manuals

## Background

This collection of **61 comprehensive, hands-on lab manuals** has been created to provide a structured learning path for mastering Kubernetes from fundamentals to advanced production-ready concepts. Each lab has been carefully designed with step-by-step instructions, real-world examples, and practical exercises that build upon one another.

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

Filenames use **`labNN-{category}-{slug}.md`** where **`NN` is the global curriculum order (01–58)**.

| S. No | Category | Lab Name | Description | Link |
|-------|----------|----------|-------------|------|
| 1 | Basics | Creating Pods and Deployments | Learn to create Kubernetes Pods and Deployments using YAML manifests with Apache HTTP Server containers. | [lab01-basics-creating-pods.md](lab01-basics-creating-pods.md) |
| 2 | Basics | Creating Services | Expose Pods and Deployments using NodePort and LoadBalancer Services with service discovery. | [lab02-basics-creating-services.md](lab02-basics-creating-services.md) |
| 3 | Basics | Essential kubectl Commands | Master essential kubectl commands for day-to-day Kubernetes operations. | [lab03-basics-kubectl-essentials.md](lab03-basics-kubectl-essentials.md) |
| 4 | Basics | Docker Build and Run | Build Docker images, tag versions, run containers, and manage multi-version applications. | [lab04-basics-docker-build-run.md](lab04-basics-docker-build-run.md) |
| 5 | Install | Kind Local Kubernetes Cluster | Set up Kind for learning, create local single-node and multi-node clusters, and validate local development workflows. | [lab05-install-kind-local-kubernetes.md](lab05-install-kind-local-kubernetes.md) |
| 6 | Install | Kubernetes Installation (kubeadm) | Install a complete Kubernetes cluster from scratch on Ubuntu using kubeadm. | [lab06-install-kubernetes-kubeadm.md](lab06-install-kubernetes-kubeadm.md) |
| 7 | Cluster | etcd Backup and Restore | Backup and restore etcd, the distributed key-value store that serves as Kubernetes' brain. | [lab07-cluster-etcd-backup-restore.md](lab07-cluster-etcd-backup-restore.md) |
| 8 | Cluster | Cluster Administration | Essential cluster administration tasks using kubeadm and kubectl including certificate management. | [lab08-cluster-administration.md](lab08-cluster-administration.md) |
| 9 | Pod | Health Probes | Configure liveness, readiness, and startup probes for application health monitoring. | [lab09-pod-health-probes.md](lab09-pod-health-probes.md) |
| 10 | Pod | Init Containers | Use init containers for setup tasks before main application containers start. | [lab10-pod-init-containers.md](lab10-pod-init-containers.md) |
| 11 | Security | RBAC Security | Implement Role-Based Access Control with user certificates, roles, and permissions. | [lab11-sec-rbac-security.md](lab11-sec-rbac-security.md) |
| 12 | Security | Pod Security Context | Configure security contexts for Pods including user IDs, file permissions, and privilege escalation controls. | [lab12-sec-security-context.md](lab12-sec-security-context.md) |
| 13 | Security | Network Policies | Implement namespace isolation with NetworkPolicies to restrict cross-namespace traffic. | [lab13-sec-network-policies.md](lab13-sec-network-policies.md) |
| 14 | Security | OPA Gatekeeper | Use Open Policy Agent Gatekeeper to enforce security and compliance policies with admission control. | [lab14-sec-opa-gatekeeper.md](lab14-sec-opa-gatekeeper.md) |
| 15 | Security | Image Scanning with Trivy | Scan container images and Kubernetes resources for security vulnerabilities using Trivy. | [lab15-sec-image-scanning-trivy.md](lab15-sec-image-scanning-trivy.md) |
| 16 | Security | Pod Security Standards | Implement Pod Security Standards (PSS) and Pod Security Admission (PSA) for cluster-wide security policies (K8s 1.25+). | [lab16-sec-pod-security-standards.md](lab16-sec-pod-security-standards.md) |
| 17 | Scheduling | NodeSelector Scheduling | Control Pod placement using nodeSelector for node selection based on labels. | [lab17-sched-nodeselector.md](lab17-sched-nodeselector.md) |
| 18 | Scheduling | Affinity and Anti-Affinity | Use node and pod affinity rules for advanced scheduling requirements. | [lab18-sched-affinity-antiaffinity.md](lab18-sched-affinity-antiaffinity.md) |
| 19 | Scheduling | Priority Classes | Define priority levels for Pods to influence scheduling decisions. | [lab19-sched-priorityclass.md](lab19-sched-priorityclass.md) |
| 20 | Scheduling | Taints and Tolerations | Use taints and tolerations to control which Pods can run on which nodes. | [lab20-sched-taints-tolerations.md](lab20-sched-taints-tolerations.md) |
| 21 | Pod | Pod Lifecycle and Multi-Container | Understand Pod lifecycle hooks and multi-container patterns (sidecar, ambassador, adapter). | [lab21-pod-lifecycle-multi-container.md](lab21-pod-lifecycle-multi-container.md) |
| 22 | Deploy | Deployment Strategies | Deploy applications with rolling updates, rollbacks, and scaling strategies. | [lab22-deploy-deployment-strategies.md](lab22-deploy-deployment-strategies.md) |
| 23 | Deploy | Deployment Rollouts | Manage deployment rollouts with progressive delivery and canary deployments. | [lab23-deploy-deployment-rollouts.md](lab23-deploy-deployment-rollouts.md) |
| 24 | Deploy | Frontend Deployment | Deploy multi-tier frontend applications with proper service architecture. | [lab24-deploy-frontend-deployment.md](lab24-deploy-frontend-deployment.md) |
| 25 | Workloads | ConfigMaps | Use ConfigMaps to manage configuration data as environment variables and mounted files. | [lab25-workload-configmaps.md](lab25-workload-configmaps.md) |
| 26 | Workloads | DaemonSets | Run a copy of a Pod on every node using DaemonSets for cluster-wide services. | [lab26-workload-daemonsets.md](lab26-workload-daemonsets.md) |
| 27 | Workloads | Static Pods | Understand and configure static Pods that are managed directly by kubelet. | [lab27-workload-static-pods.md](lab27-workload-static-pods.md) |
| 28 | Workloads | Jobs and Batch Processing | Run one-time tasks and batch workloads with Kubernetes Jobs. | [lab28-workload-jobs-batch.md](lab28-workload-jobs-batch.md) |
| 29 | Workloads | CronJobs | Schedule recurring tasks with CronJobs for automated operations. | [lab29-workload-cronjobs.md](lab29-workload-cronjobs.md) |
| 30 | Workloads | Horizontal Pod Autoscaler | Automatically scale Pods based on CPU utilization and custom metrics. | [lab30-workload-hpa.md](lab30-workload-hpa.md) |
| 31 | Workloads | StatefulSets & Stateful Applications | Deploy and manage stateful applications using StatefulSets with volumeClaimTemplates for persistent data. | [lab31-workload-statefulsets.md](lab31-workload-statefulsets.md) |
| 32 | Workloads | Headlamp Kubernetes UI | Install Headlamp in-cluster with Helm, access it through port-forward, and validate Kubernetes UI workflows. | [lab32-workload-headlamp-kubernetes-ui.md](lab32-workload-headlamp-kubernetes-ui.md) |
| 33 | Workloads | Kubernetes Dashboard (Legacy) | Legacy reference for the deprecated Dashboard UI. Prefer Lab 32 (Headlamp) for a current in-cluster UI path. | [lab33-workload-kubernetes-dashboard-legacy.md](lab33-workload-kubernetes-dashboard-legacy.md) |
| 34 | Networking | Multi-Port Services | Create Services that expose multiple ports for applications with different endpoints. | [lab34-net-multi-port-services.md](lab34-net-multi-port-services.md) |
| 35 | Networking | Ingress Controllers | Configure Ingress controllers for HTTP/HTTPS routing with path-based, host-based, and TLS termination. | [lab35-net-ingress.md](lab35-net-ingress.md) |
| 36 | Observability | Metrics Server | Install and use Metrics Server for resource usage monitoring and metrics collection. | [lab36-observe-metrics-server.md](lab36-observe-metrics-server.md) |
| 37 | Resource Management | Resource Quotas and Limits | Set resource quotas and limits at namespace and Pod levels for resource governance. | [lab37-resmgmt-resource-quotas-limits.md](lab37-resmgmt-resource-quotas-limits.md) |
| 38 | Storage | Basic Storage Volumes | Work with emptyDir and hostPath volumes, sharing data between containers. | [lab38-storage-basic-volumes.md](lab38-storage-basic-volumes.md) |
| 39 | Storage | Persistent Storage | Learn PersistentVolumes (PV), PersistentVolumeClaims (PVC), NFS storage, and Secrets as volumes. | [lab39-storage-persistent-storage.md](lab39-storage-persistent-storage.md) |
| 40 | Upgrade | Cluster Upgrades with kubeadm | Upgrade a Kubernetes cluster from one version to another using kubeadm with zero-downtime strategies. | [lab40-upgrade-cluster-upgrades.md](lab40-upgrade-cluster-upgrades.md) |
| 41 | Advanced | WordPress on Kubernetes | Deploy a complete WordPress application with MySQL database on Kubernetes. | [lab41-adv-wordpress-on-kubernetes.md](lab41-adv-wordpress-on-kubernetes.md) |
| 42 | Advanced | High Availability Cluster (Optional) | Deploy a production-grade multi-master HA cluster with stacked etcd, load balancers, and failover capabilities. | [lab42-adv-ha-cluster-optional.md](lab42-adv-ha-cluster-optional.md) |
| 43 | Advanced | Custom Resource Definitions (Optional) | Extend the Kubernetes API with CRDs, create custom resources, and understand the operator pattern. | [lab43-adv-custom-resource-definitions.md](lab43-adv-custom-resource-definitions.md) |
| 44 | Networking | Gateway API (Next-Gen Ingress) | Configure Gateway API for advanced HTTP/HTTPS routing with domain workarounds for local development (K8s 1.26+). | [lab44-net-gateway-api.md](lab44-net-gateway-api.md) |
| 45 | Networking | DNS Configuration | Configure and customize DNS resolution in Kubernetes clusters. | [lab45-net-dns-configuration.md](lab45-net-dns-configuration.md) |
| 46 | Basics | YAML Manifests Deep Dive | Read, write, validate, and troubleshoot Kubernetes YAML (Pod, Deployment, Service, ConfigMap, Secrets); intentional break-and-fix exercises. | [lab46-basics-yaml-manifests.md](lab46-basics-yaml-manifests.md) |
| 47 | Workloads | Kubernetes Secrets | Create, consume, and secure Secrets (Opaque, TLS, docker-registry) as env vars and volume mounts. | [lab47-workload-secrets.md](lab47-workload-secrets.md) |
| 48 | Tools | Helm Charts | Install Helm, add repositories, deploy/upgrade/rollback releases, create your own chart, and master the essential command set. | [lab48-tools-helm-charts.md](lab48-tools-helm-charts.md) |
| 49 | Troubleshooting | Cluster and Control Plane | Diagnose and fix API Server, Scheduler, Controller Manager, and etcd issues. | [lab49-ts-cluster-control-plane.md](lab49-ts-cluster-control-plane.md) |
| 50 | Troubleshooting | Pod Failures | Troubleshoot Pending, ImagePullBackOff, CrashLoopBackOff, OOMKilled, and other pod failures. | [lab50-ts-pod-failures.md](lab50-ts-pod-failures.md) |
| 51 | Troubleshooting | Kubelet and Node | Fix Node NotReady, kubelet failures, container runtime issues, and resource pressure. | [lab51-ts-kubelet-node.md](lab51-ts-kubelet-node.md) |
| 52 | Troubleshooting | Networking | Debug Service connectivity, DNS resolution, NetworkPolicy, and Ingress routing issues. | [lab52-ts-networking.md](lab52-ts-networking.md) |
| 53 | Troubleshooting | Workload Debugging | Master kubectl logs, exec, port-forward, debug containers, and event analysis. | [lab53-ts-workload-debugging.md](lab53-ts-workload-debugging.md) |
| 54 | Troubleshooting | Commands Reference | Practice every essential troubleshooting command organized by category. | [lab54-ts-commands-reference.md](lab54-ts-commands-reference.md) |
| 55 | Troubleshooting | CKA Scenarios | CKA exam-style break-fix scenarios covering the 30% troubleshooting domain. | [lab55-ts-cka-scenarios.md](lab55-ts-cka-scenarios.md) |
| 56 | Networking | CoreDNS Deep Dive | CoreDNS architecture, Corefile, plugins, DNS records, ndots, customization, and troubleshooting. | [lab56-net-coredns.md](lab56-net-coredns.md) |
| 57 | Security | Network Policy Advanced | Pod-to-pod traffic control, ingress/egress rules, 3-tier isolation, CIDR blocks, AND vs OR logic. | [lab57-sec-network-policy-advanced.md](lab57-sec-network-policy-advanced.md) |
| 58 | Networking | EndpointSlices | Scalable endpoint management, custom EndpointSlices for external services, and topology-aware routing. | [lab58-net-endpointslices.md](lab58-net-endpointslices.md) |
| 59 | Basics | Container Runtime Interface — crictl | Install and use `crictl` for node-level pod, container, and image troubleshooting with CRI-compliant runtimes. | [lab59-basics-crictl.md](lab59-basics-crictl.md) |
| 60 | Basics | Kubernetes API Discovery | Explore `api-versions`, `api-resources`, `explain`, output formats (`-o wide/yaml/jsonpath`), and raw API endpoints. | [lab60-basics-k8s-apis.md](lab60-basics-k8s-apis.md) |
| 61 | Basics | Kubeconfig and Context Management | Create, switch, rename, and delete contexts; set default namespaces; merge kubeconfig files; RBAC context switching. | [lab61-basics-kubeconfig-contexts.md](lab61-basics-kubeconfig-contexts.md) |

---

## Learning Paths

Choose a learning path based on your goals and experience (numbers refer to **global Lab 01–60**):

### Path 1: Complete Beginner
Start here if you're new to Kubernetes:
```
Lab 04 (Docker) → Lab 01 (Pods) → Lab 46 (YAML deep dive, optional but recommended) → Lab 02 (Services) → Lab 03 (kubectl) →
Lab 60 (K8s API Discovery) → Lab 59 (crictl) → Lab 25 (ConfigMaps) → Lab 22 (Deployment Strategies)
```

### Path 2: Security Focus
Master Kubernetes security:
```
Lab 01 (basics) → Lab 11 (RBAC) → Lab 12 (Security Context) →
Lab 13 (Network Policies) → Lab 14 (OPA) → Lab 15 (Image Scanning) → Lab 16 (PSS)
```

### Path 3: Storage Mastery
Deep dive into storage:
```
Lab 01 (basics) → Lab 38 (Basic Volumes) → Lab 39 (Persistent Storage) →
Lab 25 (ConfigMaps) → Lab 41 (WordPress practical)
```

### Path 4: Workload Patterns
Learn workload controllers:
```
Lab 01 (basics) → Lab 22 (Deployments) → Lab 26 (DaemonSets) → Lab 27 (Static Pods) →
Lab 28 (Jobs) → Lab 29 (CronJobs) → Lab 30 (HPA) → Lab 31 (StatefulSets)
```

### Path 5: Pod Scheduling
Master pod placement:
```
Lab 01 (basics) → Lab 17 (NodeSelector) → Lab 18 (Affinity) →
Lab 19 (PriorityClass) → Lab 20 (Taints/Tolerations)
```

### Path 6: Networking Deep Dive
Understand Kubernetes networking:
```
Lab 02 (Services) → Lab 34 (Multi-Port) → Lab 13 (Network Policies) →
Lab 35 (Ingress) → Lab 58 (EndpointSlices) → Lab 45 (DNS) → Lab 44 (Gateway API) → Lab 46 (YAML recap, optional)
```

### Path 7: Production Readiness
Build production-grade deployments:
```
Labs 01–08 (Basics → Kind → Cluster admin) → Lab 09 (Probes) → Lab 36 (Metrics) →
Lab 30 (HPA) → Lab 37 (Quotas) → Lab 23 (Rollouts) → Lab 41 (WordPress)
```

### Path 8: Troubleshooting and CKA Prep
Master Kubernetes troubleshooting (CKA 30% domain):
```
Lab 54 (Commands Reference) → Lab 49 (Control Plane) → Lab 50 (Pod Failures) →
Lab 51 (Kubelet/Node) → Lab 52 (Networking) → Lab 53 (Workload Debugging) →
Lab 55 (CKA Scenarios)
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
├── basics/              # Labs 01-02 (see also docs for 03-04)
├── yaml-lab/            # Lab 46 (YAML manifests practice)
├── administration/      # Cluster/etcd assets aligned with Labs 07-08
├── security/            # Labs 11-16
├── storage/             # Labs 38-39
├── config/              # Lab 25 (ConfigMaps)
├── workloads/           # Labs 22-31, 33
├── scheduling/          # Labs 17-20
│   ├── nodeselector/
│   ├── affinity/
│   ├── priorityclass/
│   └── tolerations/
├── troubleshooting/     # Labs 49-55
└── networking/          # Labs 34-35, 44-45, 56, 58
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
- **[YAML 101 for Kubernetes Labs](../docs/basics/yaml-basics.md)** (repo) — start here before editing lab manifests; interactive HTML: [Part 1](../html/yaml-k8s-part1-syntax.html), [Part 2](../html/yaml-k8s-part2-objects-editing.html), [Part 3](../html/yaml-k8s-part3-tools-troubleshooting.html); hands-on: [Lab 46: YAML Manifests](lab46-basics-yaml-manifests.md)
- [YAML language spec](https://yaml.org/) (reference)
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

- **58 comprehensive labs** covering Kubernetes from basics to advanced topics
- **Logical categories** (see index): Basics, Install, Cluster, Pod, Security, Scheduling, Deploy, Workloads, Networking, Observability, Resource Management, Storage, Upgrade, Advanced, Tools, Troubleshooting
- **8 curated learning paths** for different goals and experience levels
- **Complete cross-references** between related labs
- **Production-ready skills** with real-world examples
- **Modern K8s features**: Includes K8s 1.25-1.28+ features (PSS/PSA, Gateway API, CronJob timezones, native sidecar spec, CEL validation)
- **Advanced optional labs**: Custom Resource Definitions (CRDs), High Availability clusters
- **Open for contributions** via Pull Requests

---

**Happy Learning!**

*Last Updated: March 29, 2026*
*Total Labs: 58*
*Kubernetes Compatibility: 1.24+ (with K8s 1.25-1.28+ advanced features)*

For questions, issues, or contributions, please submit a Pull Request or open an issue in the repository.
