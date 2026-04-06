## Kubernetes Labelling Guide

### Introduction
Labels in Kubernetes are key-value pairs assigned to Kubernetes objects such as Pods, Deployments, Nodes, and Services. They are fundamental for organizing, categorizing, and managing workloads in Kubernetes clusters. Labels are critical for scheduling decisions, resource allocation, monitoring, and security policies.

### Why Labeling is Useful
1. **Organization and Management:** Labels allow administrators to categorize resources based on purpose, environment, or owner.
2. **Selection & Filtering:** Tools like kubectl and controllers can filter resources based on labels, enhancing operational efficiency.
3. **Affinities and Taints/Tolerations:** Labels help define pod scheduling rules, making sure workloads are deployed on appropriate nodes.
4. **Metrics and Monitoring:** Labels provide a mechanism to group resources for logging and monitoring tools.
5. **Security & Policies:** Network policies and role-based access can be enhanced using labels.

### Common Labels
- **env:** Identifies the environment like `production`, `staging`, or `development`.
- **department:** Specifies the owning department such as `engineering`, `finance`, etc.
- **appowner:** Defines the owner of the application.
- **business_critical:** Indicates whether a workload is critical (`yes` or `no`).

### Example setup

Consider a cluster with a control plane node (**master.example.com**) and workers (**worker-node-1.example.com**, **worker-node-2.example.com**). You can attach labels to **Nodes**, **Pods**, **Deployments**, and other objects—either in the manifest (`metadata.labels`) or imperatively with `kubectl label`. Use **`kubectl get … --show-labels`** (or `-l` selectors) to inspect and filter what you have in the cluster.

### Exposing Services Based on Labels
Labels are also used to group Pods for service exposure.

#### Service Example
```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-app-service
spec:
  selector:
    app: my-app
    env: production
  ports:
    - protocol: TCP
      port: 80
      targetPort: 80
```
In this example, the service selects all Pods with labels `app=my-app` and `env=production` and exposes them on port 80.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app-deployment
  labels:
    app: my-app
    env: production
    department: engineering
    appowner: john_doe
    business_critical: "yes"
spec:
  replicas: 2
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
        env: production
        department: engineering
        appowner: john_doe
        business_critical: "yes"
    spec:
      containers:
      - name: my-app
        image: nginx:latest
```

### Using Labels in Node and Pod Affinity
Labels can be used to influence pod scheduling using Node Affinity and Pod Affinity rules.

#### Node Affinity Example
```yaml
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: business_critical
            operator: In
            values:
            - "yes"
```
This configuration ensures that the pod only schedules on nodes marked as `business_critical=yes`.

#### Pod Affinity Example
```yaml
spec:
  affinity:
    podAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
      - labelSelector:
          matchLabels:
            env: production
        topologyKey: "kubernetes.io/hostname"
```
This ensures that pods with the `env=production` label will be scheduled on the same node.

### Conclusion
Kubernetes labeling is a simple yet powerful feature that provides granular control over managing resources. It enhances the Kubernetes environment’s flexibility and scalability through mechanisms like affinity, node selection, and monitoring. Properly defining and applying labels to resources in your cluster ensures better organization, resource allocation, and workload placement. When building production-grade environments, thoughtful labeling should be part of your Kubernetes best practices.

---

## Hands-On Labs

Practice these concepts with guided lab exercises:

| Lab | Description |
|-----|-------------|
| [Lab 46: YAML manifests](../../labmanuals/lab46-basics-yaml-manifests.md) | Author and fix manifests where `metadata.labels` and selectors must stay in sync. |
