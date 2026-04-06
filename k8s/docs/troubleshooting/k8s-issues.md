# Kubernetes Troubleshooting Guide

## Introduction

Kubernetes failures range from application misconfiguration to cluster-wide outages. A structured path—**symptoms → cluster health → nodes → workloads → networking and storage → applications**—narrows root cause faster than random `kubectl` commands.

This guide is **reference material**: what to check, why it matters, and diagnostic signals. Managed clusters (**AWS EKS**, **Azure AKS**, **Google GKE**) add provider control planes, IAM, and cloud networking; use provider docs when symptoms point outside the data plane you manage.

**Cloud troubleshooting (official):**

- [AWS EKS troubleshooting](https://docs.aws.amazon.com/eks/latest/userguide/troubleshooting.html)
- [Azure AKS troubleshooting](https://learn.microsoft.com/en-us/azure/aks/troubleshooting)
- [Google GKE troubleshooting](https://cloud.google.com/kubernetes-engine/docs/troubleshooting)

For guided exercises, use **Hands-On Labs** at the end (Labs 49–55).

---

## Diagnosis approach

Start broad, then narrow:

| Goal | Command |
|------|---------|
| Node status | `kubectl get nodes` |
| Workloads everywhere | `kubectl get pods -A` |
| Recent cluster events | `kubectl get events -A` (add `--sort-by='.lastTimestamp'` as needed) |
| API reachability | `kubectl cluster-info` · `kubectl get --raw /healthz` |
| Legacy component view | `kubectl get componentstatus` (deprecated; prefer `kube-system` pod health) |

**Things to check:** Are nodes `Ready`? Any `CrashLoopBackOff` or long `Pending`? Do events mention scheduling, image pull, or volume attach?

> **Q:** How do I tell if the problem is control plane vs worker nodes?  
> **A:** Control plane: API errors, `kubectl` timeouts, unhealthy `kube-apiserver` / `etcd` / scheduler / controller-manager (logs on control plane nodes, or `kube-system` pods). Workers: `NotReady` nodes, kubelet/CNI/runtime errors—use `kubectl describe node <name>` and `journalctl -u kubelet` on the node.

> **Q:** Why do Kubernetes events matter?  
> **A:** They record state changes and failures (scheduling, pulls, probes, evictions). Use `kubectl describe pod|node|deployment …` and `kubectl get events` to see *why* something failed, not only *that* it failed.

> **Q:** A deployment’s pods never schedule—where do I look?  
> **A:** `kubectl describe pod <pod>` for `FailedScheduling` messages; check resource requests vs `kubectl describe nodes`; taints/tolerations and affinity; PVC binding if volumes are required.

> **Q:** How do I chase an intermittent cluster issue?  
> **A:** Enable or raise log verbosity on affected components, correlate with metrics (Prometheus, metrics-server), and compare timestamps across kubelet, API, and app logs.

---

## Cluster

**Typical scenarios:** unresponsive API, upgrade stuck halfway, etcd or scheduler issues, cluster-wide `Pending`, frequent evictions.

### Command reference

| Goal | Command |
|------|---------|
| Node status | `kubectl get nodes` |
| Cluster endpoints | `kubectl cluster-info` |
| Broad diagnostics | `kubectl cluster-info dump` (optional: `-n <namespace>`) |
| API health | `kubectl get --raw /healthz` |
| Control-plane load (if metrics-server) | `kubectl top pod -n kube-system` |
| etcd (where you have access) | `etcdctl endpoint health` · `etcdctl endpoint status` |

**Things to check:** Node `Ready` state, API latency, etcd quorum and disk, events for control-plane or CNI failures.

> **Q:** The cluster feels hung—how do I verify the control plane?  
> **A:** `kubectl get --raw /healthz`; inspect API server logs (`journalctl -u kube-apiserver` on self-managed nodes); verify etcd connectivity and health; ensure `kube-system` control-plane pods are running.

> **Q:** API server is unavailable—common causes?  
> **A:** OOM, network partition, bad certs, or etcd failure. Check API server logs, etcd health, and resource pressure in `kube-system`.

> **Q:** `kubeadm init` failed—what next?  
> **A:** Re-read `kubeadm` output; check `/var/log/kubelet.log` and container logs; verify network, DNS, swap disabled, and CNI ready to install.

> **Q:** etcd lost quorum—recovery outline?  
> **A:** Identify surviving members (`etcdctl member list`); restore from snapshot if needed (`etcdctl snapshot restore`); re-form quorum and restart control plane components per your install guide.

> **Q:** etcd shows split-brain or inconsistent members?  
> **A:** `etcdctl member list` and logs (`journalctl -u etcd`); remove failed members with `etcdctl member remove <id>`; add/replace members with `etcdctl member add` only following your runbook so quorum is preserved.

> **Q:** Control plane node disk full?  
> **A:** `df -h`; large paths often include `/var/lib/etcd`, container logs, and image store; free space, rotate logs, `etcdctl defrag` if appropriate, then resize disk.

> **Q:** kube-apiserver slow or pods cannot reach the API?  
> **A:** From the pod network, verify routes to the API VIP/IP; check kube-proxy and any corporate proxy; API server logs and certificates in `/etc/kubernetes/pki`.

> **Q:** Kubernetes Dashboard unreachable?  
> **A:** `kubectl get svc -n kubernetes-dashboard`; pod logs; RBAC for the logged-in identity; expose via supported pattern (Ingress, port-forward)—avoid insecure defaults in production.

> **Q:** All pods are `Pending` cluster-wide?  
> **A:** `kubectl get events`; confirm nodes are `Ready` and schedulable; verify CNI pods are healthy; check for total resource starvation.

> **Q:** API server is slow—what to inspect?  
> **A:** API server logs for slow requests; `etcdctl endpoint status` for latency; watch etcd disk I/O; metrics for API/etcd CPU and memory.

> **Q:** Upgrade failed mid-way?  
> **A:** Check component versions and installer logs (`kubeadm` or cloud upgrade history); validate API and etcd health; roll back using vendor procedure and backups.

> **Q:** Pods are evicted often?  
> **A:** `kubectl describe pod` for eviction reason; `kubectl describe node` for `DiskPressure` / `MemoryPressure`; tune requests/limits and kubelet eviction thresholds.

### Component failure signals

Kubernetes tolerates some skew between components, but repeated restarts, etcd quorum loss, or sustained API latency are high risk. Watch `kubectl get events -A`, `kube-system` pod restarts, and node conditions.

> **Q:** kube-scheduler is not scheduling—how to debug?  
> **A:** `kubectl describe pod` for events; `kubectl get nodes`; scheduler logs (`kubectl logs -n kube-system` for static-pod setups, or `journalctl -u kube-scheduler`); check taints, requests, and PriorityClass.

> **Q:** kube-controller-manager looks stuck?  
> **A:** Controller-manager logs; API connectivity; `kubectl top pod -n kube-system` if metrics available; watch reconciliation delays in metrics.

> **Q:** etcd using too much memory?  
> **A:** `etcdctl endpoint status`; consider `etcdctl defrag`; reduce write churn; scale or resize etcd per guidance.

> **Q:** Cluster autoscaler not adding nodes?  
> **A:** `kubectl logs -n kube-system` for the autoscaler deployment; pending pods and unschedulable reasons; cloud quotas, IAM, and node pool limits.

> **Q:** kube-proxy appears broken on a node?  
> **A:** `kubectl get pods -n kube-system -o wide | grep kube-proxy` and that node’s kube-proxy logs; validate CNI and dataplane (iptables, IPVS, or eBPF) for the cluster; ensure no local firewall rules block Service CIDR traffic.

> **Q:** Namespace deletion is stuck?  
> **A:** `kubectl get namespace <ns> -o yaml` for `status.phase` and finalizers; remove blocking finalizers only when you understand the consequences: `kubectl patch namespace <ns> -p '{"spec":{"finalizers":[]}}' --type=merge`.

> **Q:** PVs left behind after namespace delete?  
> **A:** Check `persistentVolumeReclaimPolicy` on PVs (`Retain` vs `Delete`); `kubectl get pv`; clean up orphaned volumes per storage and compliance policy.

---

## Nodes

**Concept:** A node is `Ready` when kubelet reports healthy, the runtime is up, and the network plugin succeeds. Loss of API connectivity or kubelet failure usually flips `NotReady`.

### Logs and on-node tools

**Control plane:** API server, scheduler, controller-manager, etcd—often under `/var/log/pods/…` or `journalctl` for systemd-managed services.

**Workers:** `journalctl -u kubelet` for registration, CNI, image pull, and PLEG messages. Pod log files also appear under `/var/log/pods/`.

**`crictl`:** On the node, `crictl ps -a`, `crictl logs <container-id>` (with `--tail`) help when the API is unreliable.

| Symptom | On-node checks |
|---------|----------------|
| NotReady | `systemctl status kubelet` · `journalctl -u kubelet` · CNI pods |
| Disk pressure | `df -h` · kubelet eviction messages · image and log growth |
| Join failures | kubelet logs · API server logs for TLS/bootstrap · `kubeadm` logs |

> **Q:** Which logs for node connectivity problems?  
> **A:** `journalctl -u kubelet`; CNI plugin logs (Calico, Cilium, etc.); host network (`dmesg`, `/var/log/syslog` or journal) for interface errors.

> **Q:** Node won’t join the cluster?  
> **A:** Kubelet logs on the new node; API server logs for certificate or auth errors; `kubeadm join` output if used.

> **Q:** NotReady due to networking?  
> **A:** From the node, verify reachability to the API server; check CNI and kube-proxy; firewall routes between node and control plane.

> **Q:** NotReady due to memory pressure?  
> **A:** `kubectl top node`; evict or reschedule workloads; add capacity or reduce limits.

> **Q:** NotReady—missing CNI?  
> **A:** Reinstall or fix CNI manifests; confirm configs under `/etc/cni/net.d/`.

> **Q:** kubelet keeps crashing?  
> **A:** `journalctl -u kubelet`; validate `/var/lib/kubelet/config.yaml`; check disk and memory; `systemctl restart kubelet` after fixing root cause.

> **Q:** `kubectl drain` fails?  
> **A:** `kubectl describe node` for blocking pods; DaemonSets without tolerations; use `--ignore-daemonsets` and only `--force` when eviction policy allows.

---

## Logging

**Concept:** Applications should log to **stdout/stderr**. The runtime captures streams; node agents or DaemonSets may forward to centralized systems (Loki, ELK, cloud logging).

**`kubectl logs`:** Pod- and container-scoped; `--tail`, `--since`, `--previous` (after crash), `--all-containers` for multi-container pods.

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

**Architecture checklist:** node-level collection → agent health → aggregation path (network, auth, buffering) → retention and rotation.

> **Q:** How do I confirm a node logging agent (e.g. Fluentd) is healthy?  
> **A:** `kubectl get pods -n kube-system` (or agent namespace); read agent pod logs; validate config maps for namespace filters.

> **Q:** One app’s logs never reach the central system?  
> **A:** Agent filters/labels for that namespace; verify `kubectl logs` works for the pod (proves the container emits logs).

> **Q:** Log pipeline is slow?  
> **A:** CPU/memory on forwarders; network RTT to the sink; batch sizes and buffering.

> **Q:** Truncated or missing container logs?  
> **A:** Runtime log driver opts (`max-size`, `max-file`); kubelet rotation settings; disk space on the node.

> **Q:** Best practices for long-term logs?  
> **A:** Central store with retention policy; rotation on nodes; object storage for archives where appropriate.

**Filtering component logs (example):**

```bash
kubectl logs -l k8s-app=kube-proxy -n kube-system
```

**Rotation (node / runtime):** kubelet flags such as `--container-log-max-size` and `--container-log-max-backups` (names vary by version) cap per-container log files. For Docker’s `json-file` driver, analogous settings live in `daemon.json`:

```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

---

## Pods

**Representative deployment (labels and image wiring):**

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

**Taints:** `NoSchedule` blocks scheduling unless the pod tolerates the taint—remove taint or add toleration deliberately.

**Images:** `ImagePullBackOff` / `ErrImagePull`—wrong image, tag, registry auth, or missing `imagePullSecrets`. Details appear in `kubectl describe pod`.

| Status | Common causes | Where to look |
|--------|----------------|---------------|
| `CrashLoopBackOff` | Bad command, app panic, failing probes | `kubectl logs`, `describe`, `logs --previous` |
| `Pending` | Resources, taints, affinity, unbound PVC | Events in `describe`, `kubectl get nodes`, quotas |
| `Terminating` | Finalizers, stuck volume detach | `kubectl get pod -o yaml` (finalizers) |
| `ContainerCreating` | Image pull, mount, CNI | `describe` events |

> **Q:** Pod in `CrashLoopBackOff`?  
> **A:** `kubectl describe pod`; `kubectl logs <pod> --previous`; verify env, command, dependencies, and probes.

> **Q:** Pod stuck `Pending`?  
> **A:** `kubectl describe pod` for `FailedScheduling`; match requests to node capacity; check taints, affinity, PVCs, and ResourceQuota.

> **Q:** Multi-container pod logs?  
> **A:** `kubectl logs <pod> -c <container>` per container; correlate timestamps.

> **Q:** Job stuck `Active` or too many pods?  
> **A:** Inspect Job `parallelism`, `completions`, `backoffLimit`; pod logs; resource availability.

> **Q:** Init container failing?  
> **A:** `kubectl logs <pod> -c <init-container-name>`; resources and command correctness.

> **Q:** Pod stuck `Terminating`?  
> **A:** Finalizers in pod YAML; stuck volume detach; patch finalizers only when safe.

> **Q:** What are Kubernetes *events* on a pod?  
> **A:** Short-lived records of scheduling, pulls, mounts, kills. `kubectl describe pod <pod> -n <ns>` shows them at the bottom; cluster-wide: `kubectl get events -A`.

> **Q:** Frequent `Evicted` events?  
> **A:** Node pressure—`kubectl describe node`; align pod requests/limits with real usage.

> **Q:** DaemonSet missing on some nodes?  
> **A:** `nodeSelector` / affinity vs node labels; taints without tolerations; `describe` events on the DaemonSet pods.

**Advanced tools:** `kubectl debug` (ephemeral debug containers), **netshoot** image for network probes from a pod, **Lens** or similar UIs for visualization—use what your environment permits.

---

## Networking

**Services and endpoints:** Selectors must match pod labels, and endpoints only include **Ready** pods. A typo in labels yields empty Endpoints and connection failures.

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

| Goal | Command |
|------|---------|
| Services | `kubectl get svc` |
| Endpoints | `kubectl get endpoints <service>` · `kubectl describe endpoints <service>` |
| Labels | `kubectl get pods --show-labels` |
| NetworkPolicy | `kubectl describe networkpolicy <name> -n <ns>` |
| DNS / CoreDNS | `kubectl get pods -n kube-system -l k8s-app=kube-dns` (or your DNS label set) |

**Pod-exec connectivity checks** (image must include the tool):

| Goal | Example |
|------|---------|
| DNS | `kubectl exec -it <pod> -- nslookup <service>` · `dig <service>.<ns>.svc.cluster.local` |
| HTTP / TCP | `kubectl exec -it <pod> -- wget -qO- http://<host>:<port>` |
| Latency path | `kubectl exec -it <pod> -- ping <ip>` · `traceroute <ip>` (if installed) |
| Same-namespace Service | `kubectl get endpoints <svc> -n <ns>` then test pod IP or Service DNS |

From a debug pod (with needed tools): `curl`/`wget` to ClusterIP or DNS name; `nslookup` / `dig` for DNS.

> **Q:** DNS resolution fails inside the cluster?  
> **A:** CoreDNS pods running and healthy; `kubectl logs` on CoreDNS; from a test pod: `nslookup kubernetes.default` or `dig <service>.<ns>.svc.cluster.local`.

> **Q:** Service unreachable inside the cluster?  
> **A:** `kubectl get svc` and `kubectl describe endpoints <svc>`; NetworkPolicies; kube-proxy / dataplane health; test from a peer pod with `curl`.

> **Q:** Ingress misroutes traffic?  
> **A:** `kubectl describe ingress`; ingress controller logs; DNS to the right front-end IP; verify backend Service and port.

> **Q:** LoadBalancer has no external access?  
> **A:** `kubectl get svc` for `EXTERNAL-IP`; cloud provider events for LB provisioning; security groups / firewall; backend endpoints Ready.

> **Q:** NetworkPolicy blocks expected traffic?  
> **A:** `kubectl describe networkpolicy`; confirm pod labels and namespaces match rules; temporarily relax in non-production to confirm.

> **Q:** Calico (example CNI) pod-to-pod issues?  
> **A:** Calico pod logs; `calicoctl get policy` (if installed) for conflicting rules.

> **Q:** Multi-port Service—only one port works?  
> **A:** `kubectl describe svc` lists every `Port`; confirm container `ports` and `targetPort` for each; test the secondary port with `curl`/`nc` to the pod IP.

> **Q:** NodePort works on one node but not from a pod on another node?  
> **A:** NodePort should be reachable on every node via kube-proxy; check `kube-system` kube-proxy pods and logs; verify host firewall and cloud security groups for the NodePort range.

> **Q:** `hostNetwork: true` pod not reachable on the expected address?  
> **A:** `kubectl describe pod` for the host IP and ports; port conflicts on the node; host firewall rules.

> **Q:** `connection refused` in app logs?  
> **A:** Service port vs container port; endpoints empty; target pod not listening; NetworkPolicy or upstream dependency down.

**External dependencies:** From the pod, test `curl`/`nc` to the dependency; verify egress allowed (NetworkPolicy, firewall, cloud NAT); validate credentials and URLs.

---

## Applications

**Approach:** Confirm scheduling (`get`/`describe` pod), then logs and `exec` (if the image has tools), then readiness/liveness probes, then Service alignment.

**Common themes:** wrong image or env; readiness failing so endpoints stay empty; dependencies unreachable; `OOMKilled` from tight memory limits.

**Tools:** `kubectl logs -f`, `kubectl exec`, `kubectl port-forward` for local testing without exposing Services.

> **Q:** Application not responding?  
> **A:** `kubectl get pods -n <ns>`; `kubectl logs`; probe configuration in the manifest; from the pod: `curl` to localhost or the Service.

> **Q:** Deployment failing on bad image?  
> **A:** `kubectl describe deployment` / pod events; verify image name, tag, registry auth, and `imagePullSecrets`.

> **Q:** Readiness probe always failing?  
> **A:** `kubectl describe pod`; `kubectl exec` to run the same check as the probe (path, port, command).

> **Q:** No application logs?  
> **A:** Confirm process runs (`kubectl exec … ps`); ensure the app writes to stdout/stderr; check for logging sidecars misconfigured.

> **Q:** HPA not scaling?  
> **A:** `kubectl describe hpa`; metrics-server or custom metrics availability; requests/limits set so CPU metrics are meaningful.

> **Q:** Liveness probe causes restart loops?  
> **A:** Loosen timeouts/period, or fix the check so it matches real startup time; read restart counts and `describe` events.

> **Q:** Rolling update causes downtime?  
> **A:** `kubectl rollout status`; maxUnavailable / maxSurge; readiness must pass before old pods terminate—`kubectl rollout pause` while fixing the app.

> **Q:** Helm install fails?  
> **A:** `helm install --dry-run --debug`; fix values and chart requirements; correlate with `kubectl get events`.

**Monitoring (typical stack):** Prometheus for scrape storage, Grafana for dashboards, Loki for logs, kube-state-metrics for Kubernetes object metrics—use these to correlate spikes with logs and events.

**Example:** install a common observability bundle with Helm (adjust repo/chart versions for your environment):

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install kube-prometheus-stack prometheus-community/kube-prometheus-stack
```

> **Q:** Prometheus not scraping node or pod targets?  
> **A:** Prometheus targets UI or config; ServiceMonitors/PodMonitors; network from Prometheus to exporters; RBAC for `discovery`.

> **Q:** Grafana shows gaps in graphs?  
> **A:** Prometheus retention and disk; datasource URL; clock skew between components.

> **Q:** HPA scales too fast and causes flapping?  
> **A:** `kubectl describe hpa`; tune `behavior.scaleUp` / `scaleDown` stabilization windows and policies in the HPA spec.

> **Q:** `kubectl apply` fails with a server error?  
> **A:** `kubectl apply --dry-run=client -f <file>` for schema issues; API server logs for admission or conversion webhooks.

> **Q:** Cluster-wide ConfigMap change broke apps—how to roll back?  
> **A:** Re-apply the last known good manifest from version control; restart or roll workloads that cache ConfigMap data in memory.

---

## Quick FAQ (cross-cutting scenarios)

Concise answers for patterns that span multiple layers:

> **Q:** StatefulSet won’t scale or attach volumes?  
> **A:** PVC binding per ordinal; events on new pods; headless Service for stable network identity; storage class and provisioner health.

> **Q:** PVC stuck `Pending`?  
> **A:** Matching PV or dynamic provisioner; StorageClass `volumeBindingMode`; provisioner logs.

> **Q:** PV stuck `Released`?  
> **A:** Reclaim policy and claimRef; may need manual cleanup or recycle per policy.

> **Q:** `hostPath` volume—pod cannot see files?  
> **A:** Path exists on the *scheduled* node; permissions; `hostPath` is node-local and not portable.

> **Q:** Volume snapshot fails?  
> **A:** `VolumeSnapshot` / `VolumeSnapshotClass` correctness; CSI driver logs; backend support for snapshots.

> **Q:** NFS PVC latency is high?  
> **A:** NFS server health and network path; `iperf` or similar between node and server; compare storage class IOPS if applicable.

> **Q:** Data not persisting after pod restart?  
> **A:** Confirm volume type (`emptyDir` vs PVC); PVC still bound; app writing to the mounted path.

> **Q:** High restart count?  
> **A:** `kubectl describe pod` for back-off; logs for OOM or probe failures; fix app or limits.

> **Q:** Webhook or admission errors after upgrade?  
> **A:** API server logs; webhook service reachability and TLS; update webhook for new API versions.

> **Q:** CSI volume fails to mount?  
> **A:** CSI driver pod logs; `describe pod` events; storage class and secret alignment.

> **Q:** Custom operator not reconciling?  
> **A:** Operator pod logs; CRD and RBAC; reconcile errors in metrics or logs.

> **Q:** Service mesh breaks pod traffic?  
> **A:** Sidecar logs (e.g. Envoy); mesh policy; compare with direct cluster IP tests.

> **Q:** Cluster-wide performance degradation?  
> **A:** `kubectl top node`; etcd and API latency; noisy neighbors; control plane sizing.

> **Q:** Intermittent HTTP 503 from an Ingress or Service?  
> **A:** Backend pod logs and restarts; readiness failures; empty endpoints; Ingress controller logs.

> **Q:** Container runtime upgrade broke nodes?  
> **A:** `journalctl -u containerd` or `docker`; validate `/etc/containerd/config.toml` / Docker daemon config; roll back runtime if needed.

> **Q:** Projected volume pod won’t start?  
> **A:** Each projected source (Secret, ConfigMap, downwardAPI) must exist and be readable; check pod events.

> **Q:** Suspected memory leak in an app?  
> **A:** Heap or language profilers (e.g. Go `pprof`); correlate with container memory metrics and OOM events.

> **Q:** Suspected DDoS or abusive traffic to a public Service?  
> **A:** Identify sources via cloud flow logs or LB metrics; tighten NetworkPolicy and ingress rules; use cloud WAF or DDoS protection where available.

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

## Additional reading

- [Kubernetes documentation](https://kubernetes.io/docs/home/)
- [Kubernetes documentation — debug cluster](https://kubernetes.io/docs/tasks/debug/debug-cluster/)
- [Kubernetes networking concepts](https://kubernetes.io/docs/concepts/services-networking/)
- [CKA certification](https://www.cncf.io/certification/certified-kubernetes-administrator/)

---

## Why this skill matters

Narrowing failures from symptoms to root cause is a core platform skill. The CKA exam stresses cluster, workload, and networking recovery. Repeated practice on real clusters (see the labs above) builds fluency with `describe`, events, logs, and node-level tools under pressure.
