### **Azure Kubernetes Service (AKS) — Part 1: Concepts and setup overview**

---

### **1. Introduction to AKS**

**Azure Kubernetes Service (AKS)** is Microsoft’s managed Kubernetes offering. Azure operates the **control plane** (API server, scheduler, controllers, etcd); you manage **node pools**, workloads, and integrations.

#### **Features of AKS**

1. **Managed control plane:** Upgrades, patching, and scaling of control plane components are handled by the platform.
2. **Azure integrations:** Azure Monitor, Microsoft Entra ID (formerly Azure AD), Azure Policy, Key Vault, and ACR are common pairing points.
3. **Networking:** **Kubenet** is simpler (overlay); **Azure CNI** assigns pod IPs from VNet space and suits enterprise IP and peering requirements.
4. **Scaling:** Manual node pool scaling, cluster autoscaler, and workload-level HPA.
5. **Availability:** Zone-redundant options for higher resilience.

---

### **2. Comparison: AKS vs other cloud Kubernetes offerings**

| Feature                  | **Azure AKS**                   | **Amazon EKS**                  | **Google GKE**                  |
|--------------------------|----------------------------------|----------------------------------|----------------------------------|
| **Control plane cost**   | No separate control-plane charge for the standard model (pay for nodes and associated resources) | Control plane fee (varies by region) | Varies by mode (Standard vs Autopilot, etc.) |
| **Networking**           | Azure CNI, Kubenet              | VPC CNI (default on EKS)         | VPC-native / alias IP patterns   |
| **Autoscaling**          | Supported                       | Supported                        | Supported                        |
| **Integrated monitoring**| Azure Monitor                   | CloudWatch                       | Cloud Logging / Monitoring       |
| **Hybrid / attach**      | Azure Arc                       | EKS Anywhere / Outposts patterns | Anthos-related options           |
| **Multi-zone**           | Supported                       | Supported                        | Supported                        |

**Why choose AKS:** Strong fit when workloads already live in Azure; identity and policy integration; operational focus on apps rather than control plane VMs.

---

### **3. Creating a cluster (conceptual)**

A typical **custom-network** AKS flow uses Azure CLI or ARM/Bicep/Terraform:

- **Resource group** — scope for the cluster and related resources.
- **Virtual network and subnet** — address space for nodes (and, with Azure CNI, plan for pod IP consumption).
- **`az aks create`** — parameters include node count, `network-plugin` (`azure` or `kubenet`), subnet ID, service CIDR/DNS IP for Kubernetes services, identity (often managed identity), and SSH keys or key management for node access.

Exact names, subscription IDs, and CIDRs are environment-specific; avoid copying hard-coded subscription or resource IDs from tutorials into production templates.

---

### **4. Connecting to the cluster**

- **`az login`** establishes Azure identity (Cloud Shell is already authenticated).
- **`az account set --subscription <id>`** selects the subscription when you have more than one.
- **`az aks get-credentials --resource-group <rg> --name <cluster>`** merges the cluster kubeconfig for `kubectl`.

**What you see in `kubectl get nodes`:** Only **agent** (worker) nodes appear. The AKS **control plane** is not listed; it is managed by Azure and not accessed as SSH-able master VMs.

---

### **5. Cost and cleanup**

Delete or scale down lab clusters when finished (`az aks delete` in the appropriate resource group) to avoid ongoing node and networking charges.

---

## Hands-On Labs

Practice these concepts with guided lab exercises:

| Lab | Description |
|-----|-------------|
| [Lab 01: Creating Pods and Deployments](../../labmanuals/lab01-basics-creating-pods.md) | Core workload objects on a Kubernetes cluster (use with your AKS kubeconfig) |
| [Lab 02: Creating Kubernetes Services](../../labmanuals/lab02-basics-creating-services.md) | Services and in-cluster networking patterns on AKS or any cluster |
