# Lab 55: CKA Troubleshooting Practice Scenarios

## Overview

This lab is a **CKA-style troubleshooting drill set**. Each exercise presents a broken cluster or workload state; you investigate, narrow the root cause, and apply the smallest fix that restores expected behavior. Together, the scenarios map to the **CKA troubleshooting domain** (about 30% of the exam): control plane and node components, networking, storage, workload rollout, node conditions, scheduling, and RBAC.

Work through scenarios in order or jump using the index. Treat each scenario like an exam question: set a timer, avoid peeking at the solution until you have a written plan (commands you would run and what you expect to see).

**Interactive companion:** [CKA Troubleshooting Scenarios](../html/ts-cka-scenarios.html) — same ten scenarios in a toggle UI for quick review.

## Prerequisites

- Running Kubernetes cluster (**kubeadm-based** preferred so you can use static pod paths, `kubeadm certs`, and node SSH patterns shown here)
- `kubectl` configured; **SSH** to control plane and worker nodes (sudo where noted)
- Solid comfort with pods, Deployments, Services, Namespaces, and `kubectl describe` / events
- Completed the troubleshooting fundamentals track: [Lab 49: Cluster and Control Plane](lab49-ts-cluster-control-plane.md), [Lab 50: Pod Failures](lab50-ts-pod-failures.md), [Lab 51: Kubelet and Node](lab51-ts-kubelet-node.md), and companion labs **52–54** in your curriculum (networking, storage, workloads/security as your course defines them)

> **Safety:** Several scenarios intentionally describe destructive or disruptive states. Use a **lab cluster** only. Do not run certificate renewals or manifest surgery on production without change control.

---

## Repository YAML Files

> Sample policies and objects referenced by **kubectl apply -f** in this lab are in [`k8s/labs/troubleshooting/`](../labs/troubleshooting/):

| File | Scenario |
|------|----------|
| [`allow-frontend-backend.yaml`](../labs/troubleshooting/allow-frontend-backend.yaml) | Scenario 5 (NetworkPolicy allow; namespace `app`) |
| [`storageclass-fast.yaml`](../labs/troubleshooting/storageclass-fast.yaml) | Scenario 6 (illustrative `StorageClass`; adjust provisioner for your cluster) |
| [`role-pod-reader.yaml`](../labs/troubleshooting/role-pod-reader.yaml) | Scenario 10 (`Role` in namespace `dev`) |

---

## Learning Objectives

- Practice a repeatable troubleshooting loop: symptoms → `kubectl get` / `describe` → events → logs → node-level checks
- Map common symptoms to components: kubelet, static pods, API server TLS, CoreDNS, NetworkPolicy, PVC/PV, Deployment rollout, disk pressure, scheduler, RBAC
- Choose **minimal fixes** (one command or one manifest) that match CKA answer style
- Use `kubectl auth can-i`, `openssl`, `kubeadm certs`, and CNI-aware NetworkPolicy reasoning under time pressure

## Exercise index

| # | Scenario | Level |
|---|----------|--------|
| 1 | [Worker node NotReady (kubelet)](#ex1) | Beginner |
| 2 | [Static pod not running](#ex2) | Beginner |
| 3 | [API server certificate expired](#ex3) | Intermediate |
| 4 | [CoreDNS not resolving](#ex4) | Beginner |
| 5 | [NetworkPolicy blocking traffic](#ex5) | Intermediate |
| 6 | [PVC not binding](#ex6) | Beginner |
| 7 | [Deployment rollout stuck](#ex7) | Intermediate |
| 8 | [Node disk pressure evictions](#ex8) | Intermediate |
| 9 | [Scheduler not running](#ex9) | Intermediate |
| 10 | [RBAC permission denied](#ex10) | Beginner |

---

<a id="ex1"></a>

## Scenario 1: Worker Node NotReady (Beginner)

**Aligns with HTML:** *1. Broken kubelet*

### Setup

You are told that workloads no longer schedule onto **worker-2** (or a named worker). The control plane is healthy. Other workers remain `Ready`.

### Task

Restore the worker to **Ready** so new pods can be placed on it again.

### Investigation

Confirm the symptom from the control plane:

```bash
kubectl get nodes
```

```bash
kubectl describe node worker-2
```

In **Conditions**, expect `Ready` = `False` with a message about the kubelet or node heartbeat. Note **Taints** if any were added automatically.

SSH to the worker (replace with your hostname or IP):

```bash
ssh worker-2
```

On the node, check kubelet:

```bash
sudo systemctl status kubelet
```

If the service is inactive, also scan recent logs:

```bash
sudo journalctl -u kubelet -n 50 --no-pager
```

### Root cause

The **kubelet** service is **stopped** or **failed** (not running), so the node cannot report status or run pods.

### Fix

Start kubelet and enable it at boot:

```bash
sudo systemctl start kubelet
sudo systemctl enable kubelet
```

If `status` showed a failed unit due to config, fix the reported error (for example bad kubelet config) before `start` succeeds.

### Verification

From your admin machine:

```bash
kubectl get node worker-2
```

Expect `STATUS` **Ready**. Optional:

```bash
kubectl describe node worker-2 | sed -n '/Conditions/,/Addresses/p'
```

---

<a id="ex2"></a>

## Scenario 2: Static Pod Not Running (Beginner)

**Aligns with HTML:** *2. Static pod not running*

### Setup

A **monitoring agent** is deployed as a **static pod** and should appear on **every** node. On **worker-2**, the mirror pod never shows up in the API (or it appears and immediately fails). Other nodes look fine.

### Task

Make the static pod run on worker-2 without changing cluster-level objects (fix the node-local definition).

### Investigation

On **worker-2**, list the static manifest directory (kubeadm default):

```bash
ls -la /etc/kubernetes/manifests/
```

Confirm kubelet’s static path if your cluster uses a non-default location:

```bash
sudo grep -R staticPodPath /var/lib/kubelet/config.yaml /etc/kubernetes/kubelet.conf 2>/dev/null
```

Read the monitoring manifest and validate indentation and keys. Check kubelet for parse errors:

```bash
sudo journalctl -u kubelet -n 80 --no-pager | tail -40
```

### Root cause

The static pod **YAML on disk** has a **syntax error** (for example a missing `:` after a key, wrong indentation, or invalid field), so kubelet **refuses** to create the pod.

### Fix

Edit the broken file (name is illustrative):

```bash
sudo nano /etc/kubernetes/manifests/monitoring-agent.yaml
```

Correct the YAML so it is valid for a minimal Pod (e.g. `apiVersion`, `kind`, `metadata`, `spec` with `containers`).

You usually do **not** need to restart kubelet; the directory is watched. If the file was partially written, a restart can help after the file is valid:

```bash
sudo systemctl restart kubelet
```

### Verification

```bash
kubectl get pods -A | grep -i monitoring
```

You should see a mirror pod name like `monitoring-agent-<worker-2-hostname>` in namespace `kube-system` (or the configured mirror namespace) with `Running`.

---

<a id="ex3"></a>

## Scenario 3: API Server Certificate Expired (Intermediate)

**Aligns with HTML:** *3. API server certificate expired*

### Setup

Every `kubectl` command fails with TLS errors similar to:

```text
Unable to connect to the server: x509: certificate has expired or is not yet valid
```

### Task

Restore **kubectl** and API access by fixing **API server** certificate expiry.

### Investigation

On a **control plane** node, inspect the API server certificate dates:

```bash
sudo openssl x509 -in /etc/kubernetes/pki/apiserver.crt -noout -dates
```

Use kubeadm’s summary:

```bash
sudo kubeadm certs check-expiration
```

Compare `notAfter` with the current time. If the apiserver cert is expired, that matches the client error.

### Root cause

The **kube-apiserver serving certificate** has **expired**, so clients validating the server cert reject the connection.

### Fix

Renew the API server certificate:

```bash
sudo kubeadm certs renew apiserver
```

Restart the API server so it loads the new material. On kubeadm **static pod** installs, a common pattern is to bounce the manifest:

```bash
sudo mv /etc/kubernetes/manifests/kube-apiserver.yaml /tmp/
sleep 3
sudo mv /tmp/kube-apiserver.yaml /etc/kubernetes/manifests/
```

Your environment may use a different restart method; follow local runbooks if systemd manages the API server.

> **Note:** After rotation, some clusters also need **admin kubeconfig** or **front-proxy** trust updates depending on what was renewed. If `kubectl` still fails, re-check `kubeadm certs check-expiration` and admin `kubeconfig` server CA alignment (covered in depth in Lab 49).

### Verification

```bash
kubectl cluster-info
kubectl get nodes
```

Both should succeed without x509 expiry errors.

---

<a id="ex4"></a>

## Scenario 4: CoreDNS Not Resolving (Beginner)

**Aligns with HTML:** *4. DNS not resolving*

### Setup

Pods can curl **external IPs** (egress works), but **cluster DNS** fails—for example `nslookup kubernetes.default` inside a pod times out or returns SERVFAIL.

### Task

Restore **in-cluster DNS** so Service names resolve again.

### Investigation

List DNS-related pods (selectors vary by install):

```bash
kubectl get pods -n kube-system -l k8s-app=kube-dns
```

```bash
kubectl get pods -n kube-system -l app.kubernetes.io/name=coredns
```

Check CoreDNS logs:

```bash
kubectl logs -n kube-system deploy/coredns --tail=80
```

If pods are crashing:

```bash
kubectl describe pod -n kube-system -l k8s-app=kube-dns
```

Fetch the Corefile:

```bash
kubectl get configmap coredns -n kube-system -o yaml
```

### Root cause

**CoreDNS** pods are in **CrashLoopBackOff** because the **Corefile** is invalid for your topology—here, a **`loop` plugin** (or bad forward/upstream config) creates a **forwarding loop** and CoreDNS exits.

### Fix

Edit the ConfigMap:

```bash
kubectl edit configmap coredns -n kube-system
```

In the `Corefile` data, **remove** the problematic `loop` line or **fix** upstream forwarders so CoreDNS does not forward to itself. Save and exit.

Roll the CoreDNS pods:

```bash
kubectl delete pods -n kube-system -l k8s-app=kube-dns
```

(Use the label set that matches your CoreDNS Deployment.)

### Verification

Run a disposable debug pod (adjust image if needed):

```bash
kubectl run dns-check --rm -it --restart=Never --image=busybox:1.36 -- nslookup kubernetes.default
```

Expect a successful answer for `kubernetes.default.svc.cluster.local`.

---

<a id="ex5"></a>

## Scenario 5: NetworkPolicy Blocking Traffic (Intermediate)

**Aligns with HTML:** *5. NetworkPolicy blocking traffic*

### Setup

In namespace `app`, a **frontend** Deployment could reach **backend** before someone applied NetworkPolicies. After the change, `curl` from frontend to the backend Service fails (timeout or connection refused at the network layer), while Endpoints still exist.

### Task

Restore **frontend → backend** connectivity **without** removing all security—add an explicit allow that matches your intent.

### Investigation

```bash
kubectl get networkpolicy -n app
```

```bash
kubectl describe networkpolicy deny-all-ingress -n app
```

Test from a frontend pod (adjust deployment name and URL):

```bash
kubectl exec -n app deploy/frontend -- curl -sS -m 2 http://backend.app.svc.cluster.local:8080
```

Remember: once a pod is selected by an ingress **NetworkPolicy**, many CNIs enforce **default deny** for that pod’s ingress unless another policy **allows** the traffic.

### Root cause

A **default-deny** (or overly narrow) **ingress** policy selects the **backend** pods, but **no rule** allows traffic from **frontend** pods (by label and port).

### Fix

Apply an allow policy—for example:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-frontend-to-backend
  namespace: app
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
    - Ingress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: frontend
      ports:
        - protocol: TCP
          port: 8080
```

Save as `allow-frontend-backend.yaml` and apply:

```bash
kubectl apply -f allow-frontend-backend.yaml
```

If the client lives in another namespace, add a `namespaceSelector` (and possibly labels on the namespace).

### Verification

```bash
kubectl exec -n app deploy/frontend -- curl -sS -m 2 http://backend.app.svc.cluster.local:8080
```

Expect HTTP success (or your app’s health response). Confirm you did not attach a blanket `podSelector: {}` allow unless the question explicitly asked for it.

---

<a id="ex6"></a>

## Scenario 6: PVC Not Binding (Beginner)

**Aligns with HTML:** *6. PVC not binding*

### Setup

A workload pod stays **Pending**. Events mention the **PersistentVolumeClaim** cannot bind.

### Task

Fix **storage** so the PVC binds and the pod can schedule.

### Investigation

```bash
kubectl get pvc -A
```

```bash
kubectl get pv
```

```bash
kubectl get storageclass
```

Describe the claim (name/namespace illustrative):

```bash
kubectl describe pvc data-vol -n dev
```

Read events for messages like **no storage class**, **provisioner not found**, or **waiting for a volume to be created**.

### Root cause

The PVC specifies `storageClassName: fast`, but **no** StorageClass named **`fast`** exists (and no default StorageClass satisfies the claim).

### Fix

**Option A — create** the missing class (provisioner must match your environment; example is illustrative only):

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast
provisioner: kubernetes.io/no-provisioner
volumeBindingMode: WaitForFirstConsumer
```

For cloud or dynamic provisioning, set the correct `provisioner` and parameters for your platform, then:

```bash
kubectl apply -f storageclass-fast.yaml
```

**Option B — repoint** the PVC to an existing class:

```bash
kubectl patch pvc data-vol -n dev -p '{"spec":{"storageClassName":"standard"}}'
```

### Verification

```bash
kubectl get pvc data-vol -n dev
```

`STATUS` should be **Bound**. Then:

```bash
kubectl get pods -n dev
```

The pod should leave `Pending` (assuming no other constraints).

---

<a id="ex7"></a>

## Scenario 7: Deployment Rollout Stuck (Intermediate)

**Aligns with HTML:** *7. Deployment not rolling out*

### Setup

```bash
kubectl rollout status deployment/web
```

hangs. Of three desired replicas, only one becomes **Ready**; others fail.

### Task

Unblock the **rollout** so all replicas run the intended good revision.

### Investigation

```bash
kubectl get pods -l app=web -o wide
```

```bash
kubectl describe deployment web
```

```bash
kubectl get rs -l app=web
```

Pick the **new** ReplicaSet and describe it:

```bash
kubectl describe rs web-7d9c8f4b5c
```

Read pod events for **ImagePullBackOff**, **ErrImagePull**, **CrashLoopBackOff**, or failed probes.

### Root cause

The **new** ReplicaSet uses a **bad image tag** (or wrong registry path), causing **ImagePullBackOff** / failed containers, so the Deployment never reaches availability.

### Fix

**Fast exam-style recovery — undo** the bad rollout:

```bash
kubectl rollout undo deployment/web
kubectl rollout status deployment/web
```

**Or** set a known-good image:

```bash
kubectl set image deployment/web web=nginx:1.25
kubectl rollout status deployment/web
```

### Verification

```bash
kubectl get pods -l app=web
kubectl get deployment web
```

All pods **Running** and `READY` matches `desired` replicas.

---

<a id="ex8"></a>

## Scenario 8: Node Disk Pressure Evictions (Intermediate)

**Aligns with HTML:** *8. Node disk pressure evictions*

### Setup

Pods on **worker-3** are **evicted** or disappear. Events cite **low on resource: ephemeral-storage**.

### Task

Clear **DiskPressure** and stop unnecessary evictions.

### Investigation

```bash
kubectl describe node worker-3
```

In **Conditions**, find:

```text
DiskPressure   True
```

SSH to the node:

```bash
ssh worker-3
```

```bash
df -h
```

Inspect container runtime storage (paths vary; containerd example):

```bash
sudo du -sh /var/lib/containerd/* 2>/dev/null | sort -h | tail
```

### Root cause

**Ephemeral disk** (images, writable layers, logs) exceeded kubelet/eviction thresholds, so the kubelet **evicts** pods to protect the node.

### Fix

Prune unused images (containerd/CRI):

```bash
sudo crictl rmi --prune
```

Configure **log rotation** for the container runtime and kubelet per your distribution docs (long-term fix).

Add **ephemeral-storage** requests/limits on noisy pods to cap usage:

```yaml
resources:
  requests:
    ephemeral-storage: "256Mi"
  limits:
    ephemeral-storage: "512Mi"
```

### Verification

```bash
kubectl describe node worker-3 | sed -n '/Conditions/,/Addresses/p'
```

`DiskPressure` should return to **False** after free space crosses the threshold. Recreate evicted workloads if needed.

---

<a id="ex9"></a>

## Scenario 9: Scheduler Not Running (Intermediate)

**Aligns with HTML:** *9. Scheduler not running*

### Setup

New pods stay **Pending**. Events suggest **no nodes available to schedule pods** even though nodes are **Ready** and capacity exists.

### Task

Restore **scheduling** cluster-wide.

### Investigation

```bash
kubectl get pods -n kube-system | grep -E 'scheduler|kube-scheduler'
```

If missing, on the **control plane** node:

```bash
ls -la /etc/kubernetes/manifests/
```

Confirm whether `kube-scheduler.yaml` is absent or empty.

### Root cause

The **kube-scheduler** static pod manifest was **deleted or corrupted**, so no scheduler assigns pods to nodes.

### Fix

Restore `kube-scheduler.yaml` from **backup** or from the **kubeadm** reference manifest for your **exact** Kubernetes minor version (flags and images must match).

Example copy-from-backup flow:

```bash
sudo cp /root/backup/kube-scheduler.yaml /etc/kubernetes/manifests/kube-scheduler.yaml
sudo chmod 600 /etc/kubernetes/manifests/kube-scheduler.yaml
```

Kubelet will recreate the static pod automatically.

### Verification

```bash
kubectl get pods -n kube-system -l component=kube-scheduler
```

```bash
kubectl get pods -A --field-selector=status.phase=Pending
```

Pending pods that are otherwise schedulable should transition to **Running**.

---

<a id="ex10"></a>

## Scenario 10: RBAC Permission Denied (Beginner)

**Aligns with HTML:** *10. RBAC permission denied*

### Setup

User **dev-user** receives API errors when listing pods in namespace **dev**:

```text
User "dev-user" cannot list resource "pods" in API group "" in the namespace "dev"
```

### Task

Fix **RBAC** so the developer can list (and optionally watch) pods in **dev**.

### Investigation

Impersonate the user:

```bash
kubectl auth can-i list pods -n dev --as=dev-user
```

List bindings:

```bash
kubectl get rolebindings,clusterrolebindings -n dev
```

Describe the relevant RoleBinding:

```bash
kubectl describe rolebinding dev-readonly -n dev
```

Check whether the referenced Role exists:

```bash
kubectl get role -n dev
```

### Root cause

A **RoleBinding** references a **Role** name that **does not exist** in the namespace (or the Role exists but lacks `list` on `pods`).

### Fix

Create the missing Role:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: dev
  name: pod-reader
rules:
  - apiGroups: [""]
    resources: ["pods"]
    verbs: ["get", "list", "watch"]
```

```bash
kubectl apply -f role-pod-reader.yaml
```

If the RoleBinding pointed at the wrong name, either **rename** the Role to match `roleRef` or **patch** the RoleBinding’s `roleRef.name` to `pod-reader`.

### Verification

```bash
kubectl auth can-i list pods -n dev --as=dev-user
```

Expect **yes**.

---

## Exam tips (troubleshooting items)

### Time management

- Read the question once; note **namespace**, **object names**, and the **symptom** (Pending, CrashLoop, NotReady, RBAC, DNS).
- Spend the first **1–2 minutes** on `kubectl get` + `kubectl describe` on the failing object; avoid random log diving until events narrow the area.
- If stuck after **5 minutes**, apply the **smallest** fix that matches the evidence (one manifest, one `kubectl` patch, one systemd start)—partial credit in practice clusters still rewards correct direction.

### Always start here

```bash
kubectl get pods -A
kubectl get events -A --sort-by='.lastTimestamp' | tail -30
```

Then **namespace-local**:

```bash
kubectl describe pod <name> -n <ns>
kubectl describe deployment <name> -n <ns>
kubectl describe node <name>
```

### Events first, then logs

- **Events** explain *why* the kubelet, scheduler, or control plane rejected an action.
- **Logs** explain *why* the application or agent inside the container exited.

```bash
kubectl logs <pod> -n <ns> --previous
```

### Patterns worth memorizing

| Symptom | Likely layer |
|--------|----------------|
| Node `NotReady` | kubelet, network to API, PIDs/disk pressure |
| Static pod missing | manifest path, YAML on disk, kubelet logs |
| x509 / TLS | certs, time skew, wrong CA in kubeconfig |
| DNS fails in-cluster only | CoreDNS pods, Corefile, Service `kube-dns` |
| Was working until policy | NetworkPolicy + pod selectors + ports |
| PVC `Pending` | StorageClass, provisioner, binding mode |
| Rollout stuck | new RS, image pull, probes, quota |
| Many evictions | DiskPressure/MemoryPressure, limits |
| All pods Pending, nodes Ready | scheduler, binding, webhook timeouts |
| `cannot list` / RBAC | Role/ClusterRole + Binding + `roleRef` |

---

## Key takeaways

- **Troubleshooting is layered:** cluster → node → control plane → workload → app. Walk the stack instead of guessing.
- **kubelet** ties node health, static pods, and eviction behavior together; start with `systemctl` and `journalctl` on the node when the API says `NotReady`.
- **Certificates** are a common CKA theme: `openssl` dates and `kubeadm certs check-expiration` are fast confirmations.
- **DNS** is a service like any other: pods, logs, ConfigMap.
- **NetworkPolicy** is additive allow inside a selected pod’s ingress/egress world—deny is often implicit once policies select the pod.
- **Storage** issues surface in **PVC events**; always check **StorageClass** existence and **PV** binding mode.
- **Rollouts** are debugged via **ReplicaSets** and **pod events**; `rollout undo` is a valid fix path.
- **RBAC** mistakes are often **missing Role** or wrong **`roleRef`**; `kubectl auth can-i --as=` is the fastest proof.

---

## Troubleshooting tips

- **Wrong node?** Replace `worker-1`, `worker-2`, etc. with names from `kubectl get nodes`.
- **No SSH?** Use your lab’s console or `kubectl debug node/<name> -it --image=busybox` (Kubernetes version dependent) for read-only inspection where allowed.
- **CNI differences:** Some NetworkPolicy behaviors differ slightly by CNI; always test with a pod that matches the **same labels** the policy uses.
- **Certificate renewals:** Renew only what the scenario states; rotating the front-proxy or etcd certs without care can widen outages—follow Lab 49 guidance.
- **Static pod paths:** Not every distro uses `/etc/kubernetes/manifests/`; confirm with `staticPodPath`.

---

## Cleanup

Remove scratch files you created on your laptop (examples):

```bash
rm -f allow-frontend-backend.yaml role-pod-reader.yaml storageclass-fast.yaml
```

If you applied sample policies or PVCs in a dedicated lab namespace:

```bash
kubectl delete namespace lab55-cka-scenarios
```

(Only if you used that namespace for experiments.)

On nodes, **do not** leave broken manifests in `/etc/kubernetes/manifests/`; restore from backup after drills.

---

## Next steps

- Revisit the fundamentals in order: [Lab 49](lab49-ts-cluster-control-plane.md) → [Lab 50](lab50-ts-pod-failures.md) → [Lab 51](lab51-ts-kubelet-node.md); continue with Labs **52–54** from your troubleshooting track (for example networking and storage deep-dives when those manuals exist in this repo).
- Drill the same ten scenarios in the browser: [ts-cka-scenarios.html](../html/ts-cka-scenarios.html).
- Related topic labs already in this repository: [Lab 13: Network Policies](lab13-sec-network-policies.md), [Lab 27: Static Pods](lab27-workload-static-pods.md), [Lab 39: Persistent Storage](lab39-storage-persistent-storage.md), [Lab 11: RBAC](lab11-sec-rbac-security.md), [Lab 45: DNS](lab45-net-dns-configuration.md).
- Timed practice: pick **three** scenarios at random, **15 minutes** total, and write only the commands you would run before checking answers.
