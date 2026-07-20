# Lab 34: Multi-Port Services in Kubernetes

## Overview

In this lab you deploy a **realistic multi-port Pod** (nginx HTTP + Prometheus metrics sidecar) and expose both interfaces through a single **NodePort Service** with **named ports**. The manifests follow the [Kubernetes multi-port Service documentation](https://kubernetes.io/docs/concepts/services-networking/service/#multi-port-services).

## Prerequisites

- A running Kubernetes cluster (Minikube, Kind, or any K8s cluster)
- `kubectl` configured
- Completion of [Lab 02: Creating Services](lab02-basics-creating-services.md)

## Learning Objectives

By the end of this lab, you will be able to:

- Declare multiple named `containerPort` entries on a Pod
- Configure a Service with multiple named `ports`
- Use `targetPort` by **port name** (not only by number)
- Verify Endpoints for each Service port
- Access HTTP and metrics traffic independently

---

## Repository YAML Files

Under `k8s/labs/networking/`:

| File | Description |
|------|-------------|
| [`multi-port-configmap.yaml`](../labs/networking/multi-port-configmap.yaml) | nginx config with `/` response and `/stub_status` for the exporter |
| [`multi-port-pod.yaml`](../labs/networking/multi-port-pod.yaml) | Pod with **nginx** (`http:80`) and **nginx-prometheus-exporter** (`metrics:9113`) |
| [`multi-port-service.yaml`](../labs/networking/multi-port-service.yaml) | NodePort Service mapping `http` → 30080 and `metrics` → 30113 |

**Pattern:** application traffic and observability traffic share one Pod but use **separate Service ports** — the same model used with Prometheus `ServiceMonitor` and NetworkPolicy rules in production.

---

## Exercise 1: Review the Manifests

### Step 1: Navigate to the lab directory

```bash
cd k8s/labs/networking
```

### Step 2: Review the ConfigMap

`multi-port-configmap.yaml` enables `stub_status` on localhost so the metrics sidecar can scrape nginx without exposing admin data on the Service:

```yaml
location /stub_status {
    stub_status;
    allow 127.0.0.1;
    deny all;
}
```

### Step 3: Review the Pod

`multi-port-pod.yaml` defines **two containers** in one Pod:

| Container | Image | Port name | Port |
|-----------|-------|-----------|------|
| `nginx` | `nginx:1.25-alpine` | `http` | 80 |
| `metrics` | `nginx/nginx-prometheus-exporter:1.1.0` | `metrics` | 9113 |

Both containers share the Pod network namespace, so the exporter reaches nginx at `http://127.0.0.1/stub_status`.

### Step 4: Review the Service

`multi-port-service.yaml` exposes both container ports through one Service:

```yaml
ports:
- name: http
  port: 80
  targetPort: http      # resolves to containerPort name on the Pod
  nodePort: 30080
- name: metrics
  port: 9113
  targetPort: metrics
  nodePort: 30113
```

**Rule:** When a Service lists more than one port, **every port must have a unique `name`**.

---

## Exercise 2: Deploy the Stack

### Step 1: Apply all manifests

```bash
kubectl apply -f multi-port-configmap.yaml
kubectl apply -f multi-port-pod.yaml
kubectl apply -f multi-port-service.yaml
```

Expected output:

```
configmap/multi-port-nginx-config created
pod/multi-port-pod created
service/multi-port-service created
```

### Step 2: Verify Pod readiness

```bash
kubectl get pod multi-port-pod
```

Expected:

```
NAME             READY   STATUS    RESTARTS   AGE
multi-port-pod   2/2     Running   0          30s
```

`2/2` means both containers are running.

### Step 3: Verify the Service

```bash
kubectl get svc multi-port-service
```

Expected (NodePorts may vary if 30080/30113 are taken):

```
NAME                 TYPE       CLUSTER-IP      EXTERNAL-IP   PORT(S)                       AGE
multi-port-service   NodePort   10.96.x.x       <none>        80:30080/TCP,9113:30113/TCP   1m
```

### Step 4: Inspect Endpoints

```bash
kubectl get endpoints multi-port-service -o wide
```

Both `80` and `9113` should point to the **same Pod IP**:

```
NAME                 ENDPOINTS                         AGE
multi-port-service   10.244.x.x:80,10.244.x.x:9113     2m
```

If either endpoint is missing, run `kubectl describe pod multi-port-pod` and check container logs.

---

## Exercise 3: Test Each Port

### Step 1: Test HTTP from a debug Pod

```bash
kubectl run curl-test --image=curlimages/curl:8.5.0 --rm -it --restart=Never -- \
  curl -s http://multi-port-service:80
```

Expected: `Hello from nginx on port 80`

### Step 2: Test metrics from the same debug Pod

```bash
kubectl run curl-metrics --image=curlimages/curl:8.5.0 --rm -it --restart=Never -- \
  curl -s http://multi-port-service:9113/metrics | head
```

Expected: Prometheus text lines starting with `# HELP nginx_` or similar.

### Step 3: Port-forward each Service port

HTTP:

```bash
kubectl port-forward service/multi-port-service 8080:80
```

In another terminal:

```bash
curl http://localhost:8080
```

Metrics (stop the previous forward first):

```bash
kubectl port-forward service/multi-port-service 9113:9113
curl http://localhost:9113/metrics | head
```

### Step 4: NodePort access (Minikube)

```bash
minikube ip
curl http://$(minikube ip):30080
curl http://$(minikube ip):30113/metrics | head
```

---

## Exercise 4: Named Port Mapping

### Why names matter

`targetPort: http` tells Kubernetes to forward Service port `80` to whichever container port is named `http` on the Pod. You can change `containerPort: 80` to another number later and only update the Pod — the Service keeps using the name.

### Step 1: Describe the Service

```bash
kubectl describe svc multi-port-service
```

Confirm two port blocks:

```
Port:                     http  80/TCP
TargetPort:               http/TCP
NodePort:                 http  30080/TCP

Port:                     metrics  9113/TCP
TargetPort:               metrics/TCP
NodePort:                 metrics  30113/TCP
```

### Step 2: Compare with a single-port Service

| Aspect | Single-port Service | Multi-port Service |
|--------|---------------------|--------------------|
| `ports` entries | One | Two or more |
| Port `name` | Optional | **Required** |
| Typical use | Simple web API | HTTP + metrics, HTTP + gRPC, etc. |
| Endpoints | One port per Pod IP | Multiple ports per Pod IP |

---

## Exercise 5: Optional — Separate Services per Port

Some teams expose **public HTTP** via a LoadBalancer and keep **metrics** on an internal ClusterIP Service only.

Create a metrics-only Service (same selector, one port):

```bash
cat <<'EOF' | kubectl apply -f -
apiVersion: v1
kind: Service
metadata:
  name: multi-port-metrics-internal
spec:
  type: ClusterIP
  selector:
    app: multi-port-app
  ports:
  - name: metrics
    port: 9113
    targetPort: metrics
EOF
```

Verify both Services select the same Pod:

```bash
kubectl get endpoints multi-port-service multi-port-metrics-internal
```

Cleanup this optional Service when done:

```bash
kubectl delete service multi-port-metrics-internal --ignore-not-found
```

---

## Troubleshooting

### One port works, the other does not

```bash
kubectl logs multi-port-pod -c nginx
kubectl logs multi-port-pod -c metrics
kubectl describe pod multi-port-pod
kubectl get endpoints multi-port-service -o yaml
```

Common causes:

- ConfigMap not mounted — exporter cannot reach `/stub_status`
- `targetPort` name typo — Endpoints missing for that port
- Hitting the wrong Service `port` (Service port vs container port)

### Service validation error: port name required

```
Service "my-svc" is invalid: spec.ports[1].name: Required value
```

Add a unique `name` to every port when `ports` has more than one entry.

---

## Lab Cleanup

```bash
kubectl delete -f multi-port-service.yaml --ignore-not-found
kubectl delete -f multi-port-pod.yaml --ignore-not-found
kubectl delete -f multi-port-configmap.yaml --ignore-not-found
kubectl delete service multi-port-metrics-internal --ignore-not-found

kubectl get pods,svc,configmap | grep multi-port || echo "Cleanup complete"
```

---

## Key Takeaways

1. Multi-port Services map **several Service ports** to **several container ports** on the same Pod set.
2. Each Service port **must be named** when there is more than one.
3. Use **`targetPort: <name>`** to reference Pod `containerPort` names.
4. **HTTP + metrics** is a common production pattern (sidecar or second container).
5. Endpoints list **every `(Pod IP, port)` pair** the Service forwards to — verify both appear.
6. You can use **one multi-port Service** or **multiple single-port Services** with the same selector.

---

## Next Steps

1. **[Lab 35: Ingress](lab35-net-ingress.md)** — HTTP routing at L7 (typically the `http` port only)
2. **[Lab 58: EndpointSlices](lab58-net-endpointslices.md)** — how large clusters track Service backends
3. **Concept doc:** [Multi-Port Services](../docs/networking/multiport-service.md)
4. **Interactive guide:** [Multi-Port Services HTML](../html/multi-port-services.html)

---

## Additional Reading

- [Kubernetes Services — multi-port Services](https://kubernetes.io/docs/concepts/services-networking/service/#multi-port-services)
- [nginx-prometheus-exporter](https://github.com/nginxinc/nginx-prometheus-exporter)
- [Service port and targetPort](https://kubernetes.io/docs/concepts/services-networking/service/#defining-a-service)

---

**Lab updated:** July 2026  
**Compatible with:** Kubernetes 1.24+  
**Tested on:** Minikube, Kind
