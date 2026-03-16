# Google Kubernetes Engine (GKE) Beginner's Guide

## From Cluster Creation to WordPress Deployment


## 1. What is GKE?

**Google Kubernetes Engine (GKE)** is a managed Kubernetes service by Google Cloud Platform (GCP) that simplifies the deployment, management, and scaling of containerized applications using Kubernetes.

### Key Benefits of GKE:

* Managed Kubernetes control plane
* Easy auto-scaling of clusters and pods
* Integrated monitoring and logging
* Secure by default (Node Auto-Upgrade, VPC-native, IAM roles)

---

##  2. Prerequisites

Before you begin, ensure:

✅ You have a [Google Cloud account](https://console.cloud.google.com/).
✅ You’ve installed the [gcloud CLI](https://cloud.google.com/sdk/docs/install).
✅ You've created a project and set it as default:

```bash
gcloud config set project <your-project-id>
```

✅ You've enabled these APIs:

```bash
gcloud services enable container.googleapis.com
gcloud services enable compute.googleapis.com
```

(Optional but recommended) Use a dedicated VPC/Subnet:

```bash
gcloud compute networks create wf-vpc-dev --subnet-mode=custom
gcloud compute networks subnets create us-east4-sub \
  --network=wf-vpc-dev \
  --range=10.10.0.0/24 \
  --region=us-east4
```

---

## 3. Create a GKE Cluster

Run the following command to create a **regional GKE cluster** with 1 node in each zone of `us-east4`:

```bash
gcloud container clusters create regional-demo \
  --region=us-east4 \
  --num-nodes=1 \
  --machine-type=e2-standard-2 \
  --network=wf-vpc-dev \
  --subnetwork=us-east4-sub
```

> This creates a **high-availability** cluster (regional) with 3 nodes across 3 zones (1 per zone).

---

## 4. Connect to Your Cluster

After cluster creation, get cluster credentials:

```bash
gcloud container clusters get-credentials regional-demo --region=us-east4
```

You should now be able to run:

```bash
kubectl get nodes
```

---

## 5. Clone the GitHub Repository

The repo contains Kubernetes YAMLs to deploy WordPress + MySQL.

```bash
git clone https://github.com/devopscert202/k8sforbeginners.git
cd k8sforbeginners/k8s/labs/workloads/wordpress_aws
```

---

## 6. Understand the Files

This folder typically includes:

* `mysql-deployment.yaml`
* `mysql-service.yaml`
* `wordpress-deployment.yaml`
* `wordpress-service.yaml`

> These files define Deployments and Services for a WordPress app and its MySQL backend.

---

## 7. Apply the YAMLs

Apply the manifests in the following order:

```bash
kubectl apply -f mysql-deployment.yaml
kubectl apply -f mysql-service.yaml
kubectl apply -f wordpress-deployment.yaml
kubectl apply -f wordpress-service.yaml
```

Verify deployments and services:

```bash
kubectl get pods
kubectl get svc
```

---

## 8. Access WordPress

If your WordPress Service is of type `LoadBalancer`, it will get an external IP:

```bash
kubectl get svc wordpress
```

You’ll see output like:

```
NAME        TYPE           CLUSTER-IP     EXTERNAL-IP      PORT(S)        AGE
wordpress   LoadBalancer   10.0.171.254   34.120.XX.XX     80:32490/TCP   2m
```

Open the `EXTERNAL-IP` in a browser to access WordPress.

---

## 9. Cleanup Resources

To avoid incurring charges:

```bash
gcloud container clusters delete regional-demo --region=us-east4 --quiet
gcloud compute networks delete wf-vpc-dev --quiet
```

---

## 10. Summary

| Step | Action                                  |
| ---- | --------------------------------------- |
| 1    | Set up GCP project and enable APIs      |
| 2    | Create custom VPC & Subnet              |
| 3    | Create a regional GKE cluster           |
| 4    | Connect via `gcloud` & `kubectl`        |
| 5    | Clone and apply WordPress + MySQL YAMLs |
| 6    | Access the deployed WordPress           |
| 7    | Clean up your environment               |

---

## Extra Learning Resources

* [GKE Quickstart](https://cloud.google.com/kubernetes-engine/docs/quickstarts)
* [Kubernetes Basics](https://kubernetes.io/docs/tutorials/kubernetes-basics/)
* [Helm for Kubernetes Apps](https://helm.sh/docs/intro/)


