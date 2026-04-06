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

## Legacy installation (historical)

Older material often installed Dashboard into a dedicated namespace (for example `kubernetes-dashboard`), created a **ServiceAccount** and **token** (or kubeconfig) for sign-in, and reached the UI through **port-forward** or **Ingress**. Exact Helm chart names and Service names varied by release. Treat any legacy install docs as **historical context** only; do not extend them for new learning paths.

For the current UI direction in this repository, see [k8s-headlamp-ui.md](./k8s-headlamp-ui.md) and [k8s-ui-alternatives.md](./k8s-ui-alternatives.md).

---

## Recommended replacement

Use **Headlamp** for current UI-based Kubernetes learning: active documentation, in-cluster and desktop options, plugins, and RBAC-aligned access patterns. Headlamp is **not** a substitute for `kubectl` automation but complements it for discovery and triage.

---

## Summary

Kubernetes Dashboard remains part of Kubernetes platform history, but it should now be treated as a **legacy** reference in this repository. For current web UI setup, prefer **Headlamp**.

---

## Hands-On Labs

Practice these concepts with guided lab exercises:

| Lab | Description |
|-----|-------------|
| [Lab 33: Kubernetes Dashboard (legacy)](../../labmanuals/lab33-workload-kubernetes-dashboard-legacy.md) | Historical Dashboard-oriented exercises where still needed for comparison or maintenance of older environments. |
| [Lab 32: Headlamp Kubernetes UI](../../labmanuals/lab32-workload-headlamp-kubernetes-ui.md) | Recommended path: deploy Headlamp, authenticate, and explore workloads in the browser. |

---

## Sources

- Archived Kubernetes Dashboard repository note: https://github.com/kubernetes/dashboard
- Headlamp overview: https://headlamp.dev/docs/latest/
- Headlamp in-cluster install: https://headlamp.dev/docs/latest/installation/in-cluster/
