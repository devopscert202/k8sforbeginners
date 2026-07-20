# Multi-Port Services in Kubernetes

## Objective (conceptual)

Many workloads expose **more than one network interface** on the same Pod — for example user-facing HTTP and a separate Prometheus metrics endpoint. Kubernetes models this with multiple `containerPort` entries on the Pod and multiple named `ports` on the Service. When a Service defines more than one port, **each port must have a unique `name`**.

The mental model: one Pod, multiple listeners; one Service, multiple stable front doors (`port`) each mapped to the correct container listener (`targetPort`).

**Interactive reference:** [Multi-Port Services](../../html/multi-port-services.html)

---

## Pod: HTTP + metrics sidecar

This repository uses the common **nginx + nginx-prometheus-exporter** pattern from production tutorials:

- **nginx** serves HTTP on port `80` (`name: http`)
- **metrics** scrapes `stub_status` on localhost and exposes Prometheus format on `9113` (`name: metrics`)

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: multi-port-pod
  labels:
    app: multi-port-app
spec:
  containers:
  - name: nginx
    image: nginx:1.25-alpine
    ports:
    - containerPort: 80
      name: http
  - name: metrics
    image: nginx/nginx-prometheus-exporter:1.1.0
    args:
    - -nginx.scrape-uri=http://127.0.0.1/stub_status
    ports:
    - containerPort: 9113
      name: metrics
```

---

## Service: named ports and targetPort by name

Per [Kubernetes multi-port Services](https://kubernetes.io/docs/concepts/services-networking/service/#multi-port-services), reference Pod port **names** in `targetPort` so Service definitions stay stable if container port numbers change.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: multi-port-service
spec:
  type: NodePort
  selector:
    app: multi-port-app
  ports:
  - name: http
    port: 80
    targetPort: http
    nodePort: 30080
  - name: metrics
    port: 9113
    targetPort: metrics
    nodePort: 30113
```

| Field | Meaning |
|-------|---------|
| `port` | Port clients use on the Service ClusterIP / DNS name |
| `targetPort` | Container port number **or name** on selected Pods |
| `name` | Required when the Service exposes multiple ports |
| `nodePort` | Optional fixed NodePort (omit to auto-assign) |

---

## Verify endpoints

```bash
kubectl get svc multi-port-service
kubectl get endpoints multi-port-service
kubectl describe svc multi-port-service
```

Both `80` and `9113` should appear on the same Pod IP in Endpoints.

---

## Operational commands (reference)

```bash
kubectl apply -f k8s/labs/networking/multi-port-configmap.yaml
kubectl apply -f k8s/labs/networking/multi-port-pod.yaml
kubectl apply -f k8s/labs/networking/multi-port-service.yaml

kubectl port-forward service/multi-port-service 8080:80
kubectl port-forward service/multi-port-service 9113:9113
```

---

## Hands-On Labs

Practice these concepts with guided lab exercises:

| Lab | Description |
|-----|-------------|
| [Lab 34: Multi-Port Services in Kubernetes](../../labmanuals/lab34-net-multi-port-services.md) | Deploy nginx + metrics sidecar, apply a multi-port NodePort Service, and test HTTP and `/metrics` separately. |
