# Google Kubernetes Engine (GKE) beginner's guide

## What is GKE?

**Google Kubernetes Engine (GKE)** is Google Cloud’s managed Kubernetes service. Google operates the **control plane**; you configure **node pools**, networking, release channel, and workload APIs.

### Key benefits

* Managed control plane and automated upgrades (by channel and maintenance windows)
* Cluster and node **autoscaling** options
* Integrated **logging and monitoring** (Cloud Logging / Cloud Monitoring)
* **VPC-native** clusters (alias IP ranges) for Pod IPs integrated with GCP networking
* **IAM** integration for human and workload identity

---

## Prerequisites (conceptual)

* A **GCP project** with billing enabled where appropriate
* **gcloud CLI** installed and authenticated
* **APIs enabled:** e.g. `container.googleapis.com`, `compute.googleapis.com`
* Optional: a **custom VPC and subnet** for predictable IP planning (recommended for non-trivial deployments)

Example (illustrative only):

```bash
gcloud config set project YOUR_PROJECT_ID
gcloud services enable container.googleapis.com compute.googleapis.com
```

---

## Creating a cluster (what to decide)

* **Regional vs zonal:** Regional spreads control plane and nodes across zones in a region for higher availability.
* **Node pools:** Machine type, disk size, autoscaling, and labels/taints.
* **Networking:** VPC-native (default in modern flows) with secondary ranges for Pods and Services if using alias IP.
* **Release channel:** Rapid, regular, or stable balances feature velocity vs patch cadence.

The exact `gcloud container clusters create` flags depend on those choices; see the [GKE quickstart](https://cloud.google.com/kubernetes-engine/docs/quickstarts) for current syntax.

---

## Connecting with kubectl

After the cluster exists:

```bash
gcloud container clusters get-credentials CLUSTER_NAME --region REGION
kubectl get nodes
```

---

## Running workloads

Use standard Kubernetes objects (Deployments, Services, Ingress, etc.). Sample application manifests in this repo (for example under `k8s/labs/`) can be applied once your kubeconfig points at GKE—see the lab manuals for ordered exercises rather than duplicating apply steps here.

---

## Cleanup

Deleting the cluster and unused networks avoids ongoing **compute and load balancer** charges. Use `gcloud container clusters delete` and remove associated network resources when labs are complete.

---

## Summary

| Topic | Takeaway |
| ----- | -------- |
| Control plane | Managed by Google; you focus on nodes and workloads |
| Networking | Plan VPC, subnet, and IP ranges for Pods/Services |
| Access | `gcloud` credentials + `kubectl` |
| Workloads | Standard Kubernetes APIs |
| Learning path | Use Hands-On Labs below for concrete exercises |

---

## Hands-On Labs

Practice these concepts with guided lab exercises:

| Lab | Description |
|-----|-------------|
| [Lab 01: Creating Pods and Deployments](../../labmanuals/lab01-basics-creating-pods.md) | Core workloads on Kubernetes (run against your GKE cluster) |
| [Lab 02: Creating Kubernetes Services](../../labmanuals/lab02-basics-creating-services.md) | Service types and connectivity |

---

## Extra learning resources

* [GKE Quickstart](https://cloud.google.com/kubernetes-engine/docs/quickstarts)
* [Kubernetes Basics](https://kubernetes.io/docs/tutorials/kubernetes-basics/)
* [Helm](https://helm.sh/docs/intro/)
