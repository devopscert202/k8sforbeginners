# Kubernetes Dashboard

## Deprecation Note

The **Kubernetes Dashboard** project is no longer the recommended UI path for new Kubernetes learning content.

The Kubernetes Dashboard project was officially retired and archived on **January 21, 2026**. The official GitHub repository states that the project is no longer maintained. That same repository recommends that users consider **Headlamp** instead.

For the current UI path in this repository, use:

- Markdown overview: [k8s-headlamp-ui.md](./k8s-headlamp-ui.md)
- HTML walkthrough: [../../html/k8s-ui-headlamp.html](../../html/k8s-ui-headlamp.html)

---

## Background

Kubernetes Dashboard was historically the best-known open-source web UI for Kubernetes clusters. It gave users a browser-based way to:

- inspect workloads
- view cluster resources
- access logs and metrics
- perform some management tasks visually

That historical context is still useful when reading older tutorials or maintaining legacy environments, but it should now be treated as a **legacy UI path** rather than the default recommendation.

---

## What Kubernetes Dashboard Was Used For

Kubernetes Dashboard was commonly used to:

- view Pods, Deployments, Services, ConfigMaps, and Secrets
- inspect cluster resource health
- troubleshoot workloads visually
- create resources from forms or YAML
- access a browser-based management view without relying only on `kubectl`

### Benefits it provided

- **Visibility**: A graphical view of cluster objects and application state
- **Simplicity**: Easier entry point for users new to Kubernetes
- **Troubleshooting help**: Fast access to logs, status, and object details
- **Demonstration value**: Useful for showing workloads and namespace structure during live sessions

---

## Why It Is No Longer the Recommended UI Here

The project status has changed:

- the upstream repository is archived
- it is no longer maintained
- the official repository points users to **Headlamp**

Because of that, new documentation in this repository should prefer **Headlamp** instead of expanding Kubernetes Dashboard usage.

---

## Legacy Installation Reference

If you still need to understand how older labs referenced Kubernetes Dashboard, the common flow was:

1. install the dashboard into the `kubernetes-dashboard` namespace
2. create a ServiceAccount for login
3. create or retrieve a token
4. use port-forward or ingress to access the UI

Example legacy commands:

```bash
helm repo add kubernetes-dashboard https://kubernetes.github.io/dashboard/
helm upgrade --install kubernetes-dashboard kubernetes-dashboard/kubernetes-dashboard --create-namespace --namespace kubernetes-dashboard

kubectl -n kubernetes-dashboard create token admin-user
kubectl -n kubernetes-dashboard port-forward svc/kubernetes-dashboard-kong-proxy 8444:443
```

This is retained only as historical context for older material.

---

## Recommended Replacement

Use **Headlamp** instead for current UI-based Kubernetes learning and labs.

### Why Headlamp is the better current path

- active and current project direction
- official in-cluster deployment documentation
- plugin support
- modern extensibility
- cleaner fit for future OIDC-based access patterns

### Headlamp references in this repo

- Markdown overview: [k8s-headlamp-ui.md](./k8s-headlamp-ui.md)
- Lab manual: [../../labmanuals/lab32-workload-headlamp-kubernetes-ui.md](../../labmanuals/lab32-workload-headlamp-kubernetes-ui.md)
- HTML reference: [../../html/k8s-ui-headlamp.html](../../html/k8s-ui-headlamp.html)

---

## Summary

Kubernetes Dashboard remains part of Kubernetes platform history, but it should now be treated as a legacy reference in this repository. For current web UI setup and installation, the recommended direction is **Headlamp**.

---

## Sources

- Archived Kubernetes Dashboard repository note: https://github.com/kubernetes/dashboard
- Headlamp overview: https://headlamp.dev/docs/latest/
- Headlamp in-cluster install: https://headlamp.dev/docs/latest/installation/in-cluster/
