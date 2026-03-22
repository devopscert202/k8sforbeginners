# Lab 33: Kubernetes Dashboard (Legacy)

## Status Note

This lab is kept as a **legacy reference**.

The Kubernetes Dashboard project was officially retired and archived on **January 21, 2026**. The official Kubernetes Dashboard GitHub repository says the project is no longer maintained. That same repository recommends that users consider **Headlamp** instead.

For the current UI learning path in this repository, use:

- [Headlamp overview](../workloads/k8s-headlamp-ui.md)
- [Lab 32: Headlamp Kubernetes UI](./lab32-workload-headlamp-kubernetes-ui.md)
- [Headlamp HTML reference](../html/k8s-ui-headlamp.html)

---

## Overview

This lab explains the older Kubernetes Dashboard access model so existing material still makes sense, but it should not be treated as the default UI path for new cluster setups.

## What this lab still helps with

- understanding older dashboard-based tutorials
- recognizing the `kubernetes-dashboard` namespace and related resources
- understanding token-based UI access patterns
- comparing legacy Dashboard workflows with the newer Headlamp-based approach

---

## Historical Summary

Kubernetes Dashboard was a general-purpose web UI for Kubernetes clusters. The older workflow was typically:

1. install Dashboard
2. create a ServiceAccount
3. bind permissions
4. generate a token
5. access the UI through port-forward or ingress

Example legacy commands:

```bash
helm repo add kubernetes-dashboard https://kubernetes.github.io/dashboard/
helm upgrade --install kubernetes-dashboard kubernetes-dashboard/kubernetes-dashboard --create-namespace --namespace kubernetes-dashboard

kubectl apply -f k8s-dashboard.yaml
kubectl create token admin-user -n kubernetes-dashboard
kubectl port-forward -n kubernetes-dashboard service/kubernetes-dashboard 8443:443
```

---

## Why the Recommended Path Changed

The project status changed upstream:

- the repository is archived
- it is no longer maintained
- the repository itself points users to **Headlamp**

Because of that, new UI labs in this repository now use **Headlamp** for in-cluster installation and browser access.

---

## Recommended Replacement Lab

Use this lab instead for current practice:

- [Lab 32: Headlamp Kubernetes UI](./lab32-workload-headlamp-kubernetes-ui.md)

That lab covers:

- in-cluster Headlamp installation with Helm
- ServiceAccount-based lab login
- port-forward access
- workload and namespace validation
- a cleaner upgrade path to ingress and OIDC

---

## Migration Guidance

If you have older notes that say:

- `k8s-dashboard.yaml`
- `kubernetes-dashboard` namespace
- Dashboard token login
- Dashboard ingress

map them to the Headlamp content in this repo:

- [Headlamp overview](../workloads/k8s-headlamp-ui.md)
- [Lab 32: Headlamp lab manual](./lab32-workload-headlamp-kubernetes-ui.md)
- [Headlamp HTML walkthrough](../html/k8s-ui-headlamp.html)

---

## Further Reading

- Archived Kubernetes Dashboard repository note: https://github.com/kubernetes/dashboard
- Headlamp overview: https://headlamp.dev/docs/latest/
- Headlamp in-cluster install: https://headlamp.dev/docs/latest/installation/in-cluster/

---

**Lab Status**: Legacy reference  
**Preferred replacement**: Lab 32 Headlamp Kubernetes UI
