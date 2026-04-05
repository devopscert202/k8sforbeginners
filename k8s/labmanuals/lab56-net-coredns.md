# Lab 56: CoreDNS — Kubernetes DNS Deep Dive

## Exercise index

| # | Topic |
|---|--------|
| 1 | [CoreDNS architecture exploration](#ex1) |
| 2 | [Understanding the Corefile](#ex2) |
| 3 | [DNS record types — Services](#ex3) |
| 4 | [Pod DNS records and ndots](#ex4) |
| 5 | [Custom Corefile modifications](#ex5) |
| 6 | [Per-Pod DNS configuration](#ex6) |
| 7 | [DNS troubleshooting workshop](#ex7) |

---

## Overview

This lab is a hands-on tour of **CoreDNS** in Kubernetes: how cluster DNS is wired, how the **Corefile** maps queries to plugins, which **record types** you get for Services and Pods, and how **resolver options** (search list, **ndots**) change what actually gets queried. You will practice **safe customization** (hosts, stub forwarding) and a **repeatable troubleshooting** path when lookups fail. **Beginner to intermediate**; use a **scratch directory** for manifests and do not commit experimental YAML to this repository.

**Interactive companion (optional):** [coredns-deep-dive.html](../html/coredns-deep-dive.html)

## Prerequisites

- Running Kubernetes cluster (Kind, Minikube, or kubeadm) and `kubectl` configured
- Permission to read `kube-system` objects and edit the `coredns` ConfigMap (Exercise 5 — cluster admin on learning clusters only)
- [Lab 45: DNS Configuration](lab45-net-dns-configuration.md) recommended but not required
- Basic comfort with `kubectl`, Services, and Pods

## Learning Objectives

- Understand CoreDNS architecture and how it integrates with Kubernetes
- Inspect and interpret the CoreDNS **Corefile** ConfigMap and in-Pod mounts
- Verify DNS records for **ClusterIP**, **Headless**, and **ExternalName** Services (including SRV where applicable)
- Explain **ndots**, **search domains**, and how short names expand into FQDNs
- Customize DNS with **hosts** entries, **stub / conditional forwarding**, and upstream resolution
- Troubleshoot DNS failures in a systematic order (data plane, resolver config, CoreDNS, policy)

---

<a id="ex1"></a>

## Exercise 1: CoreDNS Architecture Exploration

### Step 1: Locate CoreDNS workloads and the cluster DNS Service

CoreDNS runs as a **Deployment** in `kube-system`. Pods are commonly labeled `k8s-app=kube-dns` for historical compatibility with kube-dns.

```bash
kubectl get pods -n kube-system -l k8s-app=kube-dns
kubectl get deployment coredns -n kube-system
kubectl get svc kube-dns -n kube-system -o wide
```

Expected pattern: **two Running** CoreDNS Pods; `kube-dns` is **ClusterIP** on **53/UDP** and **53/TCP** (often **9153/TCP** for metrics). ClusterIP is cluster-specific — many kubeadm/Kind clusters use `10.96.0.10`, but confirm with `kubectl get svc`.

**What to notice:** The Service front-ends CoreDNS on **53/UDP** and **53/TCP** (and often **9153/TCP** for metrics). Pods use this **ClusterIP** as their resolver.

### Step 2: Confirm the Service has Endpoints

```bash
kubectl get endpoints kube-dns -n kube-system
kubectl get endpointslices -n kube-system -l kubernetes.io/service-name=kube-dns
```

You should see **addresses** pointing to CoreDNS Pod IPs. Empty endpoints here would break cluster DNS for everyone.

### Step 3: Inspect resolver settings from a short-lived debug Pod

```bash
kubectl run dns-debug --image=busybox:1.36 --rm -it --restart=Never -- sh
```

Inside the Pod:

```bash
cat /etc/resolv.conf
```

Typical output:

```text
search default.svc.cluster.local svc.cluster.local cluster.local
nameserver 10.96.0.10
options ndots:5
```

**Read it like an operator:**

| Field | Meaning |
|--------|---------|
| `nameserver` | IP of the **kube-dns** Service (CoreDNS). The kubelet sets this from **`--cluster-dns`** (or the equivalent config in newer kubelet configs). |
| `search` | Ordered suffix list. Short names may be expanded by appending these domains. |
| `options ndots:5` | If the query has **fewer than 5 dots**, the resolver tries **search-domain expansion** before treating the name as “fully qualified.” |

**Cluster domain:** The suffix `cluster.local` is the default **cluster domain** (kubelet **`--cluster-domain`**). Your cluster may use a different domain if explicitly configured.

### Step 4: Relate kubelet flags to Pod resolv.conf

On a **Node** (SSH or cloud node access), you can often see kubelet arguments or config referencing:

- **`--cluster-dns=<Service ClusterIP>`** — must match `kube-dns` ClusterIP (or the DNS Service you use).
- **`--cluster-domain=cluster.local`** — must match the DNS zone CoreDNS’s **kubernetes** plugin is authoritative for.

If `nameserver` in Pods does not match the live `kube-dns` ClusterIP, lookups will fail or hit the wrong resolver.

Exit the debug shell when finished (the Pod is removed because of `--rm`).

---

<a id="ex2"></a>

## Exercise 2: Understanding the Corefile

### Step 1: Dump the live CoreDNS ConfigMap

```bash
kubectl get configmap coredns -n kube-system -o yaml
```

The important key is usually `Corefile` (multi-line text). You are looking for a server block listening on **.:53** plus optional extra blocks (stub zones, custom plugins).

### Step 2: Map plugins to responsibilities

Below is a **reference table** for directives commonly seen in Kubernetes CoreDNS templates. Your exact Corefile may omit or reorder some plugins.

| Plugin / block | Typical purpose in Kubernetes |
|----------------|--------------------------------|
| `errors` | Logs errors to stdout/stderr for observability. |
| `health` | Exposes a health HTTP endpoint for liveness probes. |
| `ready` | Exposes readiness so Kubernetes waits until CoreDNS is prepared to serve. |
| `kubernetes` | Answers names under the cluster domain (`*.svc.cluster.local`, Pod DNS, etc.). |
| `prometheus` | Exposes CoreDNS metrics (often on `:9153`). |
| `forward` (or `proxy` in very old files) | Sends **non-cluster** queries upstream (node resolv.conf, fixed IPs, or DoH upstreams depending on distro). |
| `cache` | Caches responses to reduce upstream load and latency. |
| `loop` | Detects forwarding loops that would wedge CoreDNS; **can cause CrashLoopBackOff** if misconfigured. |
| `reload` | Watches ConfigMap changes and reloads Corefile (subject to timing; many operators still restart). |
| `loadbalance` | Randomizes answers when multiple A/AAAA records exist. |

### Step 3: See where the Corefile is mounted inside a CoreDNS Pod

```bash
COREDNS_POD=$(kubectl get pod -n kube-system -l k8s-app=kube-dns -o jsonpath='{.items[0].metadata.name}')
kubectl exec -n kube-system "$COREDNS_POD" -- ls -la /etc/coredns
kubectl exec -n kube-system "$COREDNS_POD" -- cat /etc/coredns/Corefile
```

**Takeaway:** The **ConfigMap** is projected into the Pod filesystem; editing the ConfigMap changes the file CoreDNS reads (often after **reload** or a **rollout restart**).

---

<a id="ex3"></a>

## Exercise 3: DNS Record Types — Services

Create an isolated Namespace for this exercise.

```bash
kubectl create namespace lab56-dns
kubectl config set-context --current --namespace=lab56-dns
```

### Step 1: ClusterIP Service — A/AAAA via the kubernetes plugin

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
  namespace: lab56-dns
spec:
  replicas: 2
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
        - name: nginx
          image: nginx:1.25-alpine
          ports:
            - name: http
              containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: my-svc
  namespace: lab56-dns
spec:
  selector:
    app: web
  ports:
    - name: http
      port: 80
      targetPort: 80
      protocol: TCP
```

```bash
kubectl apply -f lab56-clusterip.yaml
kubectl rollout status deployment/web -n lab56-dns --timeout=120s
```

From a debug Pod (run from **default** or **lab56-dns**; adjust FQDN if needed):

```bash
kubectl run dns-client --rm -it --restart=Never --image=busybox:1.36 -n lab56-dns -- sh
```

Inside:

```bash
nslookup my-svc
nslookup my-svc.lab56-dns
nslookup my-svc.lab56-dns.svc.cluster.local
```

Expected pattern:

```text
Name:   my-svc.lab56-dns.svc.cluster.local
Address: 10.96.xxx.xxx
```

**FQDN form:**

```text
<svc>.<namespace>.svc.<cluster-domain>
```

Example: `my-svc.lab56-dns.svc.cluster.local`

### Step 2: Headless Service — A records per ready Pod

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-headless
  namespace: lab56-dns
spec:
  clusterIP: None
  selector:
    app: web
  ports:
    - name: http
      port: 80
      targetPort: 80
      protocol: TCP
```

```bash
kubectl apply -f lab56-headless.yaml
kubectl get endpoints my-headless -n lab56-dns
```

Inside `dns-client`:

```bash
nslookup my-headless.lab56-dns.svc.cluster.local
```

Expected: **multiple addresses** (one per ready Pod) or round-robin style listing depending on resolver output.

### Step 3: ExternalName Service — CNAME chain

```yaml
apiVersion: v1
kind: Service
metadata:
  name: ext-example
  namespace: lab56-dns
spec:
  type: ExternalName
  externalName: example.com
```

```bash
kubectl apply -f lab56-externalname.yaml
```

Test:

```bash
nslookup ext-example.lab56-dns.svc.cluster.local
```

Expected pattern:

```text
ext-example.lab56-dns.svc.cluster.local canonical name = example.com.
```

### Step 4: SRV records for named ports

For `my-svc` with port **name** `http` and protocol **TCP**, Kubernetes publishes an SRV name of the form:

```text
_http._tcp.my-svc.lab56-dns.svc.cluster.local
```

```bash
nslookup -type=SRV _http._tcp.my-svc.lab56-dns.svc.cluster.local
```

If your `busybox` build lacks SRV support, use an image with `dig`:

```bash
kubectl run dig-client --rm -it --restart=Never --image=nicolaka/netshoot -n lab56-dns -- bash -lc 'dig +short SRV _http._tcp.my-svc.lab56-dns.svc.cluster.local'
```

---

<a id="ex4"></a>

## Exercise 4: Pod DNS Records and ndots

### Step 1: Create a Pod and capture its IP

```bash
kubectl run pod-dns-demo --image=nginx:1.25-alpine -n lab56-dns --restart=Never
kubectl wait --for=condition=Ready pod/pod-dns-demo -n lab56-dns --timeout=120s
kubectl get pod pod-dns-demo -n lab56-dns -o wide
```

Suppose the Pod IP is `10.244.1.17`. Convert dots to dashes:

```text
10.244.1.17  ->  10-244-1-17
```

### Step 2: Resolve the Pod’s DNS name

```bash
kubectl run ndots-client --rm -it --restart=Never --image=busybox:1.36 -n lab56-dns -- sh
```

Inside (replace the dashed IP with yours):

```bash
nslookup 10-244-1-17.lab56-dns.pod.cluster.local
```

Expected: an answer pointing back to the Pod IP.

**FQDN form:**

```text
<pod-ip-dashes>.<namespace>.pod.<cluster-domain>
```

> Note: Pod DNS records may be disabled or restricted in some clusters (kubelet/CoreDNS settings). If this fails on your distro, compare with `kubectl exec` into CoreDNS logs while querying.

### Step 3: Observe ndots and search expansion

Still inside a Pod in Namespace `lab56-dns`, compare:

```bash
nslookup -debug my-svc 2>&1 | head -n 40
nslookup -debug google.com 2>&1 | head -n 60
```

**Conceptual model (resolver behavior):**

- **`my-svc`** has **0 dots** → fewer than `ndots:5` → the resolver tries appending **search domains** (e.g. `my-svc.lab56-dns.svc.cluster.local`) before giving up.
- **`google.com`** has **1 dot** → still `< 5` → many resolvers will still try **search list** first, which can add **latency** and sometimes **surprising NXDOMAIN** patterns depending on NXDOMAIN optimization.

### Step 4: Use an absolute name to skip search expansion

Trailing dot means “this is already absolute”:

```bash
nslookup google.com.
```

**Ways to reduce surprises:**

- Prefer **FQDNs** for cross-namespace Services (`svc.ns.svc.cluster.local.`)
- Tune **`dnsConfig.options`** to lower **ndots** for microservices that talk to many external hosts (Exercise 6)
- Keep critical internal dependencies on **short names within the same Namespace** where the first search suffix succeeds quickly

---

<a id="ex5"></a>

## Exercise 5: Custom Corefile Modifications

> **Warning:** This exercise changes **cluster-wide** DNS. Do it only on **disposable learning clusters**. Take a backup before editing.

### Step 1: Backup the current ConfigMap

```bash
kubectl get configmap coredns -n kube-system -o yaml > /tmp/coredns-configmap-backup.yaml
```

### Step 2: Plan a minimal, reversible change

**A) Static hosts for lab-only names**

Add a `hosts` stanza **inside** the main `.:53` server block, typically **before** `kubernetes` (exact placement depends on your upstream template). Example snippet:

```text
hosts {
    10.0.0.1 mydb.internal
    fallthrough
}
```

- **`fallthrough`** allows queries that do not match to continue to later plugins (like `kubernetes`).

**B) Stub / delegated zone to corporate DNS (illustrative)**

If you must forward `corp.example.com` to `203.0.113.53`, a common pattern is a **separate server block**:

```text
corp.example.com:53 {
    errors
    cache 30
    forward . 203.0.113.53
}
```

Your organization’s **real** resolver IPs, ACLs, and split-horizon rules belong here — never guess in production.

### Step 3: Edit and apply

```bash
kubectl edit configmap coredns -n kube-system
```

Save and exit the editor.

### Step 4: Wait for reload or restart safely

With the **`reload`** plugin, CoreDNS may pick up ConfigMap changes within about **two minutes** — or immediately after a restart. To avoid guessing:

```bash
kubectl rollout restart deployment/coredns -n kube-system
kubectl rollout status deployment/coredns -n kube-system --timeout=120s
```

### Step 5: Verify

```bash
kubectl run hosts-test --rm -it --restart=Never --image=busybox:1.36 -- sh
```

Inside:

```bash
nslookup mydb.internal
```

If you added stub forwarding, test a name you truly know exists in that zone (replace accordingly):

```bash
nslookup host01.corp.example.com
```

### Step 6: Restore if anything breaks cluster DNS

```bash
kubectl apply -f /tmp/coredns-configmap-backup.yaml
kubectl rollout restart deployment/coredns -n kube-system
```

---

<a id="ex6"></a>

## Exercise 6: Per-Pod DNS Configuration

### Step 1: Baseline — `ClusterFirst` (default)

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: dns-clusterfirst
  namespace: lab56-dns
spec:
  dnsPolicy: ClusterFirst
  containers:
    - name: app
      image: busybox:1.36
      command: ["sleep", "3600"]
```

```bash
kubectl apply -f lab56-clusterfirst.yaml
kubectl exec -n lab56-dns dns-clusterfirst -- cat /etc/resolv.conf
```

You should see the **cluster** nameserver and default searches.

### Step 2: Fully custom — `dnsPolicy: None`

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: dns-none-custom
  namespace: lab56-dns
spec:
  dnsPolicy: "None"
  dnsConfig:
    nameservers:
      - "8.8.8.8"
    searches:
      - "custom.local"
    options:
      - name: ndots
        value: "2"
  containers:
    - name: app
      image: busybox:1.36
      command: ["sleep", "3600"]
```

```bash
kubectl apply -f lab56-dns-none.yaml
kubectl exec -n lab56-dns dns-none-custom -- cat /etc/resolv.conf
```

Expected highlights:

```text
nameserver 8.8.8.8
search custom.local
options ndots:2
```

**Caution:** This Pod **will not** use cluster DNS unless you explicitly set the **kube-dns ClusterIP** as a nameserver. Use for learning **isolated** workloads or special cases only.

### Step 3: Node resolver — `dnsPolicy: Default`

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: dns-default-node
  namespace: lab56-dns
spec:
  dnsPolicy: Default
  containers:
    - name: app
      image: busybox:1.36
      command: ["sleep", "3600"]
```

```bash
kubectl apply -f lab56-dns-default.yaml
kubectl exec -n lab56-dns dns-default-node -- cat /etc/resolv.conf
```

Compare with the node’s `/etc/resolv.conf` patterns (not identical in all CNIs, but often similar).

### Step 4: When to use which policy

| Policy | Typical use |
|--------|-------------|
| **ClusterFirst** | Default for Pods that should resolve **Kubernetes Services** and still reach external names via CoreDNS forwarding. |
| **ClusterFirstWithHostNet** | Pods with `hostNetwork: true` that still need cluster DNS semantics. |
| **Default** | Legacy apps that must match **node** resolver behavior exactly. |
| **None** | Custom resolvers, **split DNS**, **lower ndots**, or **additional searches** — you own the entire resolver config. |

---

<a id="ex7"></a>

## Exercise 7: DNS Troubleshooting Workshop

This exercise trains a **fixed checklist**. You may simulate breakage using a scratch Namespace and deliberate misconfigurations (wrong nameserver, NetworkPolicy, or invalid forward target).

### Step 1: Symptom — a client Pod “cannot resolve DNS”

Example broken client (intentionally points away from cluster DNS):

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: dns-broken-client
  namespace: lab56-dns
spec:
  dnsPolicy: "None"
  dnsConfig:
    nameservers:
      - "203.0.113.255"
  containers:
    - name: app
      image: busybox:1.36
      command: ["sleep", "3600"]
```

```bash
kubectl apply -f lab56-broken-client.yaml
kubectl exec -n lab56-dns dns-broken-client -- nslookup kubernetes.default.svc.cluster.local
```

Expect **timeout** or **failure**.

### Step 2: Systematic diagnosis (the workshop checklist)

**1) CoreDNS Pods healthy**

```bash
kubectl get pods -n kube-system -l k8s-app=kube-dns
kubectl logs -n kube-system -l k8s-app=kube-dns --tail=100
```

**2) kube-dns Service and Endpoints**

```bash
kubectl get svc kube-dns -n kube-system
kubectl get endpoints kube-dns -n kube-system
```

**3) Client resolv.conf**

```bash
kubectl exec -n lab56-dns dns-broken-client -- cat /etc/resolv.conf
```

**4) Tests from a known-good Pod**

```bash
kubectl run dns-good --rm -it --restart=Never --image=busybox:1.36 -n lab56-dns -- sh -c 'nslookup kubernetes.default.svc.cluster.local && wget -qO- --timeout=3 http://my-svc.lab56-dns.svc.cluster.local | head'
```

If **good** works but **broken** does not, the defect is **per-Pod DNS config** or **policy**, not CoreDNS.

**5) CoreDNS logs while reproducing**

Tail logs while running failing lookups from the bad client.

**6) NetworkPolicy — port 53**

If you use **default-deny egress**, ensure **UDP/TCP 53** to `kube-dns` is allowed. See [Lab 13: Network Policies](lab13-sec-network-policies.md) and [Lab 52: Network Troubleshooting](lab52-ts-networking.md).

**7) Corefile sanity**

```bash
kubectl get configmap coredns -n kube-system -o yaml
```

Look for recent edits, invalid `forward` targets, or `loop` plugin crashes after changes.

### Step 3: Fix the broken client

```bash
kubectl delete pod dns-broken-client -n lab56-dns --ignore-not-found
```

Recreate with **ClusterFirst** or add the **kube-dns ClusterIP** to `dnsConfig.nameservers` if you must keep `dnsPolicy: None`.

---

## Key Takeaways

- **kube-dns Service → CoreDNS Pods → kubernetes plugin** is the default path for `*.svc.cluster.local` names; kubelet stamps **`/etc/resolv.conf`** using **cluster DNS IP** and **cluster domain**.
- The **Corefile** is a plugin pipeline: **kubernetes** answers in-cluster names; **forward** handles upstream; **cache**, **health**, **ready**, and **prometheus** make it operable.
- **Headless** Services return **Pod A records**; **ExternalName** yields **CNAME**; **SRV** exists for **named ports** on Services.
- **ndots** and **search** drive how short names expand — this affects **latency** and sometimes **surprising query order**.
- **Cluster-wide Corefile edits** are powerful and risky: **backup**, **validate**, then **rollout restart** if unsure.
- **dnsPolicy** and **dnsConfig** override resolver behavior per Pod — mistakes here look like “CoreDNS is broken” but are often **local config**.

---

## Troubleshooting Tips

| Symptom | Likely causes | Fast checks |
|---------|---------------|-------------|
| `nslookup: can't resolve` from all Pods | CoreDNS down, kube-dns endpoints empty, CNI/kube-proxy dataplane | `kubectl get pods -n kube-system -l k8s-app=kube-dns`, `kubectl get endpoints kube-dns -n kube-system` |
| Only certain Pods fail | `dnsPolicy: None` without kube-dns IP, typos in searches, wrong ndots | `kubectl exec ... cat /etc/resolv.conf` |
| External names fail but Services work | Broken upstream forward, node resolver, corporate firewall | CoreDNS logs; `forward` plugin target |
| After Corefile edit, DNS unstable | Syntax error, reload not picked up, `loop` detection | `kubectl logs` for CoreDNS; restore backup ConfigMap |
| Timeouts under NetworkPolicy | Missing allow to **kube-dns** on **53/UDP** and **53/TCP** | `kubectl describe networkpolicy` |

---

## Cleanup

```bash
kubectl delete namespace lab56-dns --ignore-not-found
kubectl config set-context --current --namespace=default
```

---

## Next Steps

- [Lab 45: DNS Configuration](lab45-net-dns-configuration.md) — Pod DNS policies and fundamentals
- [Lab 52: Network Troubleshooting](lab52-ts-networking.md) — includes DNS checks alongside Service and NetworkPolicy paths
- [Lab 13: Advanced Network Policies](lab13-sec-network-policies.md) — default-deny and allowing DNS explicitly
- [coredns-deep-dive.html](../html/coredns-deep-dive.html) — interactive companion (if present in your tree)
