# Kubernetes Troubleshooting Guide

## Introduction

Kubernetes can present challenges from application misconfiguration to cluster-level failures. A structured approach—cluster health, node and kubelet state, workload events, networking, and storage—helps you narrow root cause quickly. This guide is **conceptual reference material**: it explains what to check, why it matters, and which diagnostic signals to use. For guided exercises, use the **Hands-On Labs** at the end.

You will find coverage of:

- Cluster and control-plane health
- Logging paths (`kubectl` logs, node filesystem, `journalctl`, `crictl`)
- Node readiness and kubelet behavior
- Common pod and container failure modes
- Application-level debugging patterns
- Service discovery, selectors, and connectivity

---

## Kubernetes troubleshooting areas

### Section 1: Troubleshooting the Kubernetes cluster

**Areas to troubleshoot:** cluster health, node status, namespaces, and component availability.

**Typical scenarios:** unresponsive API, nodes not `Ready`, or namespace-scoped resource issues.

**Diagnostic commands (reference):**

| Goal | Command |
|------|---------|
| Node status | `kubectl get nodes` |
| Cluster endpoints | `kubectl cluster-info` |
| Broad diagnostics | `kubectl cluster-info dump` (optional: `-n <namespace>`) |
| Legacy component view | `kubectl get componentstatus` (deprecated; prefer checking `kube-system` pods) |

**Things to check:** Are nodes `Ready`? Can you reach the API? Do events show control-plane or etcd problems?

---

### Section 2: Kubernetes logging architecture

**Concept:** Application logs are typically the container’s `stdout`/`stderr`, collected by the container runtime. Cluster-level logging may forward these to an agent (e.g. node-level DaemonSet) and then to a central store (Loki, ELK, cloud logging).

**`kubectl logs`:** Targets a pod (and optionally a container). Supports `--tail`, `--since`, `--previous` (after crash), and `--all-containers` for multi-container pods.

**Illustrative pod (continuous log output):**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: counter
spec:
  containers:
  - name: count
    image: busybox:1.28
    args: [/bin/sh, -c, 'i=0; while true; do echo "$i: $(date)"; i=$((i+1)); sleep 1; done']
```

**Things to check:** Is the pod running? Are you using the correct container name? For crashes, use `--previous` to read the last terminated instance’s logs.

---

### Section 3: Cluster and node logs

**Control plane (static pods / systemd):** API server, scheduler, controller-manager, and etcd logs are usually on control plane nodes under `/var/log/pods/...` (path includes pod UID) or via `journalctl` for systemd-managed services.

**Workers:** `journalctl -u kubelet` is the primary tool for registration, CNI, and runtime errors. Pod logs under `/var/log/pods/` mirror what the kubelet exposes.

**Things to check:** Certificate and etcd errors in API server logs; leader election and watch errors in controller-manager; scheduling failures in scheduler logs; PLEG, CNI, and image pull messages in kubelet logs.

---

### Section 4: Node readiness

**Concept:** A node is `Ready` when kubelet is healthy, runtime is up, and network plugins report success. Stopping kubelet or losing connectivity to the API server typically flips the node to `NotReady`.

**Diagnosis:** `kubectl describe node <name>` shows conditions and recent events. On the node, verify kubelet status and logs.

**Things to check:** Kubelet service state, disk/memory pressure conditions, CNI pods, and API reachability from the node.

---

### Section 5: Container logs via crictl

On the node, **`crictl`** talks to the container runtime API. `crictl ps -a` lists containers; `crictl logs <container-id>` shows logs; `--tail` limits output. Use this when debugging at the node without API access to pod objects.

---

### Section 6: Pod logs and common pod issues

**Representative deployment (for understanding image and label wiring):**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx
  labels:
    app: nginx
spec:
  replicas: 1
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx
```

**Taints and scheduling:** A `NoSchedule` taint prevents scheduling unless the pod has a matching toleration. Either remove the taint or add tolerations intentionally.

**Incorrect images:** `ImagePullBackOff` / `ErrImagePull` usually mean wrong name/tag, registry auth, or missing image. `kubectl describe pod` surfaces pull errors.

**Typical statuses:**

| Status | Common causes | Where to look |
|--------|----------------|---------------|
| `CrashLoopBackOff` | App exit, bad command, probes | `kubectl logs`, `describe`, `--previous` |
| `Pending` | Resources, taints, affinity, PVC | `describe` events, `kubectl get nodes` |
| `Terminating` | Finalizers, stuck volumes | `get pod -o yaml`, finalizers |
| `ContainerCreating` | Image pull, volume mount, CNI | `describe` events |

---

### Section 7: Application troubleshooting

**Approach:** Confirm the workload is scheduled (`get`/`describe` pod), then logs and exec (if the image has a shell), then probes and Service/Endpoints alignment.

**Common themes:** wrong image or env, failing readiness so endpoints stay empty, dependency not reachable, resource limits causing OOMKilled.

**Tools:** `kubectl logs -f`, `kubectl exec`, `kubectl port-forward` for local testing without exposing Services.

---

### Section 8: Component health and failure thresholds

**Concept:** Kubernetes tolerates some component lag (see version skew policy), but repeated restarts, etcd quorum loss, or API latency indicate systemic risk.

**Signals:** Node conditions, `kubectl get events -A`, control-plane pod restarts in `kube-system`, and etcd health (`etcdctl endpoint health` where applicable).

---

### Section 9: Networking issues

**Service selectors and endpoints:** A Service must select pod labels that match **and** pods must be **Ready** for endpoints to populate. A selector typo produces an empty Endpoints object and failed connections.

**Illustrative Pod + Service (labels must match selector):**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: httpd-pod
  labels:
    app: httpd-demo
spec:
  containers:
  - name: web
    image: httpd
    ports:
    - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: httpd-service
spec:
  selector:
    app: httpd-demo
  ports:
  - port: 80
    targetPort: 80
```

**Checks:** `kubectl get svc`, `kubectl get endpoints <service>`, `kubectl get pods --show-labels`, and from a debug pod: `curl`/`wget` to ClusterIP or DNS name.

---

## Hands-On Labs

Practice these concepts with guided lab exercises:

| Lab | Description |
|-----|-------------|
| [Lab 49: Cluster and Control Plane Troubleshooting](../../labmanuals/lab49-ts-cluster-control-plane.md) | API server, etcd, scheduler, and control-plane debugging |
| [Lab 50: Troubleshooting Pod Failures](../../labmanuals/lab50-ts-pod-failures.md) | Image pull, crash loops, and pod lifecycle issues |
| [Lab 51: Kubelet and Node Troubleshooting](../../labmanuals/lab51-ts-kubelet-node.md) | Node readiness, kubelet, and runtime on workers |
| [Lab 52: Network Troubleshooting](../../labmanuals/lab52-ts-networking.md) | Services, DNS, and cluster networking |
| [Lab 53: Workload and Application Debugging](../../labmanuals/lab53-ts-workload-debugging.md) | Deployments, probes, and application-level diagnosis |
| [Lab 54: Troubleshooting Commands Practice](../../labmanuals/lab54-ts-commands-reference.md) | `kubectl` debugging command drills |
| [Lab 55: CKA Troubleshooting Practice Scenarios](../../labmanuals/lab55-ts-cka-scenarios.md) | Exam-style troubleshooting scenarios |

---

## Additional Reading

- [Kubernetes Documentation - Troubleshooting](https://kubernetes.io/docs/tasks/debug/debug-cluster/)
- [Kubernetes Networking Concepts](https://kubernetes.io/docs/concepts/services-networking/)
- [CKA Exam Preparation](https://www.cncf.io/certification/certified-kubernetes-administrator/)

---

## Importance of troubleshooting skills

In interviews and on the job, the ability to narrow a failure from symptoms to root cause is a core platform skill. The CKA exam explicitly tests cluster, workload, and networking recovery. Regular practice with real clusters (see the labs above) builds the muscle memory to use `describe`, events, logs, and node-level tools under pressure.
