### Horizontal Pod Autoscaler (HPA): Background, Use Cases, and Benefits

**Background**  
Horizontal Pod Autoscaler (HPA) adjusts the number of Pods in a workload (commonly a **Deployment**, **ReplicaSet**, or **StatefulSet**) based on observed metrics such as CPU or memory, or on custom metrics when a metrics pipeline supports them. The controller periodically compares current utilization to targets and changes the workload’s **desired replica** count.

**Use Cases**
1. **Dynamic load**: Add replicas during traffic spikes to protect latency.
2. **Cost and efficiency**: Remove replicas when demand drops (subject to stabilization rules).
3. **Availability**: Maintain headroom during rolling updates or node disruption when combined with sensible `minReplicas`.
4. **Event-driven or bursty workloads**: Campaigns, batch ingress, or APIs with uneven traffic.

**Benefits**
- Aligns capacity with demand without manual resizing.
- Uses the same declarative model as other Kubernetes workloads.
- Works with the **Metrics API** when **Metrics Server** (or equivalent) supplies resource metrics.

---

### What HPA needs

- **Metrics source**: For CPU/memory, the cluster needs metrics available through the Metrics API (typically **Metrics Server**).
- **Resource requests**: For CPU-based scaling, Pods should define **CPU requests** so utilization can be computed relative to requested CPU.
- **Scale target**: An API object with a `scale` subresource (Deployment, ReplicaSet, StatefulSet, etc.).

---

### Illustrative example manifests

**Workload with CPU requests** (abbreviated; image registry may vary by cluster):

```yaml
apiVersion: v1
kind: Service
metadata:
  name: php-apache
spec:
  ports:
  - port: 80
    protocol: TCP
    targetPort: 80
  selector:
    run: php-apache
---
apiVersion: apps/v1
kind: Deployment
metadata:
  labels:
    run: php-apache
  name: php-apache
spec:
  replicas: 1
  selector:
    matchLabels:
      run: php-apache
  template:
    metadata:
      labels:
        run: php-apache
    spec:
      containers:
      - image: registry.k8s.io/hpa-example
        name: php-apache
        ports:
        - containerPort: 80
        resources:
          requests:
            cpu: 200m
```

**HPA targeting that Deployment** (`autoscaling/v2` is preferred on current clusters; `autoscaling/v1` with `targetCPUUtilizationPercentage` still illustrates the idea):

```yaml
apiVersion: autoscaling/v1
kind: HorizontalPodAutoscaler
metadata:
  name: php-apache
spec:
  maxReplicas: 10
  minReplicas: 1
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: php-apache
  targetCPUUtilizationPercentage: 50
```

---

### Scaling down

HPA **does scale down** when average utilization stays below the target, subject to:

1. **Stabilization windows** — especially for scale-down, to avoid flapping when load is noisy.
2. **`minReplicas`** — the controller will not go below this floor.
3. **Controller-manager settings** — global defaults for HPA behavior can be tuned by cluster administrators.

When load drops after a spike, expect a **gradual** decrease in replicas rather than an immediate snap back to one Pod.

---

### Summary

HPA automates horizontal scaling from observed metrics. It depends on **meaningful resource requests**, a working **metrics pipeline**, and sensible **min/max** bounds. Load generation, `kubectl get hpa`, and verification steps belong in hands-on labs rather than in this reference page.

---

## Hands-On Labs

Practice these concepts with guided lab exercises:

| Lab | Description |
|-----|-------------|
| [Lab 30: Horizontal Pod Autoscaler](../../labmanuals/lab30-workload-hpa.md) | Install prerequisites, configure HPA, generate load, and observe scale-up and scale-down. |
