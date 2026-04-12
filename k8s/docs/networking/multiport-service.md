# Multi-Port Services in Kubernetes

Applications often expose **more than one port**—for example HTTP on one port and metrics or gRPC on another. Kubernetes models this by declaring **multiple `containerPort` entries** on the Pod (or workload) and **multiple `ports` entries** on the Service, optionally with **names** for stable references in probes and Ingress backends.

---

## Why multiple ports?

- **Protocols or roles**: Separate admin, metrics, or secondary APIs from user-facing HTTP.
- **Contract with clients**: Different Service `port` values can map to different `targetPort` values on the same Pods.
- **Named ports**: Using `name` on Service ports aligns with `targetPort: <name>` and makes manifests easier to refactor than raw numbers alone.

---

## Pod with multiple container ports

Each listening process in the container should have a corresponding `containerPort` (and name, when you want stable references).

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: multi-port-pod
  labels:
    app: multi-port-app
spec:
  containers:
  - name: multi-port-container
    image: hashicorp/http-echo
    args:
    - "-text=Hello, Multi-Port Service!"
    ports:
    - containerPort: 8080
      name: http
    - containerPort: 9090
      name: custom
```

---

## Service exposing multiple ports

A **NodePort**, **ClusterIP**, or **LoadBalancer** Service can list several port mappings. The `selector` must match the Pod labels; each `port`/`targetPort` pair defines one forwarded path.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: multi-port-service
spec:
  selector:
    app: multi-port-app
  type: NodePort
  ports:
  - protocol: TCP
    port: 8080
    targetPort: http
    nodePort: 30080
    name: http
  - protocol: TCP
    port: 9090
    targetPort: custom
    nodePort: 30090
    name: custom
```

**Notes:**

- **`nodePort`** must be in the allowed NodePort range if you set it explicitly; omit it to auto-assign.
- **`port`** is what clients use against the Service ClusterIP; **`targetPort`** is the container port (number or name).
- For **LoadBalancer** Services, cloud controllers publish each port according to provider behavior.

---

## Summary

| **Resource** | **Role** |
|--------------|----------|
| **Pod / workload** | Declares every port the container listens on. |
| **Service** | Load-balances each declared Service port to the matching `targetPort` on selected Pods. |
| **Named ports** | Reduce coupling to numeric ports and align Services, probes, and Ingress. |

---

## Hands-On Labs

Practice these concepts with guided lab exercises:

| Lab | Description |
|-----|-------------|
| [Lab 34: Multi-Port Services in Kubernetes](../../labmanuals/lab34-net-multi-port-services.md) | Build multi-port Pods and Services, verify NodePort access, and explore naming conventions. |
