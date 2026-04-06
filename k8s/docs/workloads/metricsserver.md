# Metrics Server and Use Cases

**Metrics Server** is an in-cluster component that **aggregates resource usage** (CPU and memory) from kubelets and exposes it through the **Metrics API**. That API backs **`kubectl top`** and supports **Horizontal Pod Autoscaler (HPA)** when scaling on CPU or memory.

---

## Use cases

- **Real-time utilization**: View current CPU/memory for nodes and Pods (`kubectl top` style workflows).
- **Autoscaling**: Supply resource metrics to HPA so replica counts can track demand.
- **Troubleshooting**: Spot hot nodes or mis-sized containers when requests/limits and actual usage diverge.
- **Capacity planning**: Reason about headroom and sizing using recent utilization (note: Metrics Server retains only short-term data; long-term planning usually needs Prometheus or cloud monitoring).

---

## How it fits architecturally

1. **Kubelet** (`/stats/summary` and related endpoints) reports container and node metrics.
2. **Metrics Server** scrapes those summaries, normalizes them, and serves the **Metrics API**.
3. **API consumers** (HPA controller, `kubectl top`) query that API.

On many clusters, Metrics Server ships as a **Deployment** in `kube-system` (or similar) plus **Service**, **APIService** registration, and RBAC. **TLS** between Metrics Server and kubelets must be trusted; lab clusters sometimes need extra flags or patches depending on how the kubelet presents its serving certificate.

---

## Relationship to other observability tools

Metrics Server answers **“what is usage right now?”** for scheduling and autoscaling. It is **not** a full monitoring platform: limited retention, no rich query language, no long-term alerting by itself.

| **Tool** | **Role** | **Compared to Metrics Server** |
|----------|----------|--------------------------------|
| **Prometheus** | Scrapes metrics, rules, alerting | Historical TSDB and PromQL; often paired with Grafana |
| **Grafana Agent / Alloy** | Collect and forward metrics | Heavier or lighter paths to a backend |
| **OpenTelemetry** | Metrics, traces, logs | Vendor-neutral instrumentation and pipelines |
| **cAdvisor** | Container metrics | Often scraped by Prometheus |
| **Cloud vendor monitoring** | Managed metrics for AKS/EKS/GKE | Integrated dashboards and alarms |

Commercial platforms (Datadog, Sysdig, and others) also ingest Kubernetes metrics and add APM, security, or fleet features.

---

## Summary

Metrics Server is the **default building block** for resource metrics in Kubernetes. It enables **`kubectl top`** and **CPU/memory-driven HPA**. For dashboards, SLOs, and long history, plan additional observability on top. Installation, verification, and common lab-cluster fixes are covered in the linked lab rather than in this reference page.

---

## Hands-On Labs

Practice these concepts with guided lab exercises:

| Lab | Description |
|-----|-------------|
| [Lab 36: Metrics Server](../../labmanuals/lab36-observe-metrics-server.md) | Deploy or verify Metrics Server, use `kubectl top`, and relate metrics to HPA behavior. |
