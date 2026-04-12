# Lab 57: Network Policies — Pod and Application Traffic Control

## Overview

This lab is a set of hands-on exercises for controlling **pod-to-pod** traffic, **application-level** access, **ingress** and **egress** rules, and common **network segmentation** patterns in Kubernetes. You will start from permissive defaults, apply **default-deny** baselines, selectively allow DNS and application paths, compare **AND vs OR** selector logic, use **CIDR / ipBlock** rules, and finish with a **three-tier** isolation pattern.

Lab 13 covers **namespace isolation**; this lab adds **pod/app paths**, **ports**, **DNS egress**, and **CIDR** controls.

### Repository YAML Files

This lab references pre-built manifests in the `k8s/labs/security/` directory. You can apply these directly or use them as templates:

| File | Purpose |
|------|---------|
| [`deny-all-ingress.yaml`](../../labs/security/deny-all-ingress.yaml) | Deny all ingress to pods labeled `app: k8slearning` |
| [`allow-ingress.yaml`](../../labs/security/allow-ingress.yaml) | Allow ingress only from pods with matching `app: k8slearning` label |
| [`deny-from-other-namespaces.yaml`](../../labs/security/deny-from-other-namespaces.yaml) | Deny cross-namespace ingress in the `prod` namespace |

---

## Prerequisites

- A running Kubernetes cluster whose CNI **enforces** `NetworkPolicy` (for example **Calico**, **Cilium**, or **Weave**). Clusters that do not enforce policies will appear to “work” even when YAML is wrong.
- `kubectl` installed and configured to talk to your cluster.
- **Lab 13** ([`lab13-sec-network-policies.md`](lab13-sec-network-policies.md)) completed or understood—especially default-deny and namespace selectors.
- Basic familiarity with Pods, Services, labels, and `kubectl exec`.

### Quick setup: kind + Calico (optional)

If you need a local cluster where policies are enforced:

```bash
kind create cluster --name netpol-lab
# Install a CNI that enforces NetworkPolicy (follow Calico’s “kind” install docs for your Calico version).
# Verify enforcement: apply a default-deny and confirm traffic stops.
```

---

## Learning Objectives

- Implement **deny-all** ingress/egress baselines, then allow **DNS**, **pod/namespace** paths, and **ports**.
- Use **ipBlock** / **CIDR** / **`except`**; understand **AND vs OR** in **`from`/`to`** entries.
- Build **three-tier** isolation (**fe → be → db**, no lateral **fe → db**); **verify** with `kubectl` and exec probes.

---

## Exercise 1: Default Deny All (Baseline)

Create **`netpol-lab`**, run three nginx stacks, confirm traffic, then **default-deny** ingress and egress (egress breaks **DNS**).

### Step 1: Create namespace and workloads

Create **`netpol-lab`** with three nginx stacks named **`frontend`**, **`backend`**, and **`database`**, each with **`app`** label matching its role (standard `kubectl create deployment` / `expose`):

```bash
kubectl create ns netpol-lab
for APP in frontend backend database; do
  kubectl -n netpol-lab create deployment "$APP" --image=nginx:1.25-alpine
  kubectl -n netpol-lab expose deployment "$APP" --port=80 --target-port=80
done
kubectl -n netpol-lab rollout status deployment/frontend deployment/backend deployment/database
```

**Declarative equivalent:** three `Deployment` + `ClusterIP Service` pairs (selector `app: <name>`), same shape as Lab 13’s sample apps.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: frontend
  namespace: netpol-lab
spec:
  selector:
    app: frontend
  ports:
    - port: 80
      targetPort: 80
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  namespace: netpol-lab
spec:
  replicas: 1
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      containers:
        - name: nginx
          image: nginx:1.25-alpine
```

Repeat the **Service + Deployment** pair for **`backend`** and **`database`** (swap names and `app` label), or save all six resources in `lab57-ex1-apps.yaml`.

### Step 2: Baseline connectivity (no policies)

Wait until pods are ready, then run:

```bash
kubectl exec -n netpol-lab deploy/frontend -- wget -qO- --timeout=2 http://backend.netpol-lab.svc.cluster.local:80 | head -c 200
```

Expect HTML or a non-empty body (DNS + pod paths work).

### Step 3: Default deny ingress

The repository includes a ready-made deny-all ingress policy. Review it first:

```bash
cat k8s/labs/security/deny-all-ingress.yaml
```

That file targets pods labeled `app: k8slearning`. For this exercise we use a broader version that targets **all** pods in the namespace:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-ingress
  namespace: netpol-lab
spec:
  podSelector: {}
  policyTypes: [Ingress]
```

```bash
kubectl apply -f lab57-ex1-deny-ingress.yaml
```

> **Tip:** Compare this with [`k8s/labs/security/deny-all-ingress.yaml`](../../labs/security/deny-all-ingress.yaml) — notice the difference: an empty `podSelector: {}` selects **all** pods, while `matchLabels: {app: k8slearning}` targets only matching pods. Choose the scope that fits your use case.

Ingress to pods in `netpol-lab` is denied unless another policy allows it; egress is still open, so DNS may work.

```bash
kubectl exec -n netpol-lab deploy/frontend -- wget -qO- --timeout=2 http://backend:80
```

Expect **failure** (backend cannot receive).

### Step 4: Default deny egress (separate policy)

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-egress
  namespace: netpol-lab
spec:
  podSelector: {}
  policyTypes: [Egress]
```

```bash
kubectl apply -f lab57-ex1-deny-egress.yaml
```

Egress is now restricted to explicit allows only.

### Step 5: Show that DNS breaks under deny-all egress

```bash
kubectl exec -n netpol-lab deploy/frontend -- wget -qO- --timeout=2 http://backend:80
kubectl exec -n netpol-lab deploy/frontend -- nslookup backend.netpol-lab.svc.cluster.local
```

Expect **both to fail**: deny-all egress blocks **UDP/TCP 53** to cluster DNS, so names stop resolving.

---

## Exercise 2: Allow DNS Egress (Critical Pattern)

Keep `default-deny-egress` in place. Add a policy that allows **only** DNS traffic to the cluster DNS pods in `kube-system`.

### Step 1: Confirm DNS pod labels (cluster-specific)

```bash
kubectl get pods -n kube-system --show-labels | grep -Ei 'dns|coredns'
```

Many clusters still label CoreDNS with `k8s-app=kube-dns`; some use `app.kubernetes.io/name=coredns`. **Match your cluster** in the policy below.

### Step 2: DNS allow policy

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-dns-egress
  namespace: netpol-lab
spec:
  podSelector: {}
  policyTypes: [Egress]
  egress:
    - to:
        - namespaceSelector: { matchLabels: { kubernetes.io/metadata.name: kube-system } }
          podSelector: { matchLabels: { k8s-app: kube-dns } }
      ports: [{ protocol: UDP, port: 53 }, { protocol: TCP, port: 53 }]
```

```bash
kubectl apply -f lab57-ex2-allow-dns.yaml
```

### Step 3: Verify DNS works again

```bash
kubectl exec -n netpol-lab deploy/frontend -- nslookup backend.netpol-lab.svc.cluster.local
```

**Expected:** A successful answer with a ClusterIP.

Once a pod is selected by a policy that includes **`Egress`** in `policyTypes`, **only listed egress** is permitted—so default-deny egress blocks DNS unless you add a resolver rule.

---

## Exercise 3: Pod-to-Pod Communication Control

Allow **frontend → backend** and **backend → database**; block **frontend → database**. Keep **default-deny** ingress/egress and **allow-dns-egress** from Exercise 2.

> **Reference:** The repository file [`k8s/labs/security/allow-ingress.yaml`](../../labs/security/allow-ingress.yaml) demonstrates the simplest allow pattern — permitting ingress only from pods sharing the same `app` label. The policies below extend this pattern with **directional, cross-app** rules (frontend → backend, backend → database).

### Step 1: Apply all path policies (single file)

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: frontend-to-backend-egress
  namespace: netpol-lab
spec:
  podSelector: { matchLabels: { app: frontend } }
  policyTypes: [Egress]
  egress:
    - to: [{ podSelector: { matchLabels: { app: backend } } }]
      ports: [{ protocol: TCP, port: 80 }]
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: backend-from-frontend-ingress
  namespace: netpol-lab
spec:
  podSelector: { matchLabels: { app: backend } }
  policyTypes: [Ingress]
  ingress:
    - from: [{ podSelector: { matchLabels: { app: frontend } } }]
      ports: [{ protocol: TCP, port: 80 }]
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: backend-to-database-egress
  namespace: netpol-lab
spec:
  podSelector: { matchLabels: { app: backend } }
  policyTypes: [Egress]
  egress:
    - to: [{ podSelector: { matchLabels: { app: database } } }]
      ports: [{ protocol: TCP, port: 80 }]
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: database-from-backend-ingress
  namespace: netpol-lab
spec:
  podSelector: { matchLabels: { app: database } }
  policyTypes: [Ingress]
  ingress:
    - from: [{ podSelector: { matchLabels: { app: backend } } }]
      ports: [{ protocol: TCP, port: 80 }]
```

```bash
kubectl apply -f lab57-ex3-paths.yaml
```

### Step 2: Tests

```bash
kubectl exec -n netpol-lab deploy/frontend -- wget -qO- --timeout=2 http://backend:80
kubectl exec -n netpol-lab deploy/frontend -- wget -qO- --timeout=2 http://database:80
kubectl exec -n netpol-lab deploy/backend -- wget -qO- --timeout=2 http://database:80
```

**Expected:** `frontend → backend` OK; `frontend → database` **blocked**; `backend → database` OK.

### Step 3: Label matching

`spec.podSelector` chooses which pods the policy applies to. **`ingress.from`** is who may send in; **`egress.to`** is where those pods may connect. Pod selectors match **Pods in the policy’s namespace** unless you add **`namespaceSelector`**. **Ports** must align with the traffic you test.

---

## Exercise 4: Port-Level Access Control

Deploy a **backend** that listens on **8080** (app) and **9090** (metrics). **frontend** may use **8080** only; **monitoring** may use **9090** only. Replace any Exercise 3 **backend** policies that conflict.

### Steps 1–3: ConfigMap, backend (dual port), monitoring

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: backend-dual-port
  namespace: netpol-lab
data:
  nginx.conf: |
    events {}
    http {
      server { listen 8080; default_type text/plain; return 200 "app-8080\n"; }
      server { listen 9090; default_type text/plain; return 200 "metrics-9090\n"; }
    }
---
apiVersion: v1
kind: Service
metadata:
  name: backend
  namespace: netpol-lab
spec:
  selector:
    app: backend
  ports:
    - name: app
      port: 8080
      targetPort: 8080
    - name: metrics
      port: 9090
      targetPort: 9090
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: netpol-lab
spec:
  replicas: 1
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
        - name: nginx
          image: nginx:1.25-alpine
          ports:
            - containerPort: 8080
            - containerPort: 9090
          volumeMounts:
            - name: cfg
              mountPath: /etc/nginx/nginx.conf
              subPath: nginx.conf
      volumes:
        - name: cfg
          configMap:
            name: backend-dual-port
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: monitoring
  namespace: netpol-lab
spec:
  replicas: 1
  selector:
    matchLabels:
      app: monitoring
  template:
    metadata:
      labels:
        app: monitoring
    spec:
      containers:
        - name: toolbox
          image: busybox:1.36
          command: ["sleep", "3600"]
```

```bash
kubectl apply -f lab57-ex4-backend-monitor.yaml
kubectl rollout status deployment/backend deployment/monitoring -n netpol-lab
```

### Step 4: Policies (narrow ports)

**Important:** Remove or adjust older **backend** policies from Exercise 3 if they conflict (same names/ports). For this exercise, ensure **default-deny** still applies, **DNS egress** still exists, then add:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: frontend-egress-backend-8080
  namespace: netpol-lab
spec:
  podSelector: { matchLabels: { app: frontend } }
  policyTypes: [Egress]
  egress:
    - to: [{ podSelector: { matchLabels: { app: backend } } }]
      ports: [{ protocol: TCP, port: 8080 }]
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: monitoring-egress-backend-9090
  namespace: netpol-lab
spec:
  podSelector: { matchLabels: { app: monitoring } }
  policyTypes: [Egress]
  egress:
    - to: [{ podSelector: { matchLabels: { app: backend } } }]
      ports: [{ protocol: TCP, port: 9090 }]
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: backend-ingress-split
  namespace: netpol-lab
spec:
  podSelector: { matchLabels: { app: backend } }
  policyTypes: [Ingress]
  ingress:
    - from: [{ podSelector: { matchLabels: { app: frontend } } }]
      ports: [{ protocol: TCP, port: 8080 }]
    - from: [{ podSelector: { matchLabels: { app: monitoring } } }]
      ports: [{ protocol: TCP, port: 9090 }]
```

### Step 5: Tests

```bash
kubectl exec -n netpol-lab deploy/frontend -- wget -qO- --timeout=2 http://backend:8080
kubectl exec -n netpol-lab deploy/frontend -- wget -qO- --timeout=2 http://backend:9090
kubectl exec -n netpol-lab deploy/monitoring -- wget -qO- --timeout=2 http://backend:9090
kubectl exec -n netpol-lab deploy/monitoring -- wget -qO- --timeout=2 http://backend:8080
```

**Expected:** frontend hits **8080** only; monitoring hits **9090** only.

---

## Exercise 5: Namespace-to-Namespace Communication

Create **`team-a`** and **`team-b`**, deploy simple apps, apply **default deny** in both, then allow **team-a → team-b** for a **specific** backend using combined selectors.

> **Reference:** The repository file [`k8s/labs/security/deny-from-other-namespaces.yaml`](../../labs/security/deny-from-other-namespaces.yaml) shows the classic namespace isolation pattern — allowing only same-namespace ingress in the `prod` namespace via an empty `podSelector: {}` under `from`. Try applying it directly:
> ```bash
> kubectl apply -f k8s/labs/security/deny-from-other-namespaces.yaml
> ```
> The exercises below build on this pattern with **cross-namespace selective allows** using `namespaceSelector` and `podSelector` together.

### Step 1: Namespaces and apps

```bash
kubectl create ns team-a
kubectl create ns team-b
```

**Workloads** (`team-b` API + `team-a` client):

```yaml
apiVersion: v1
kind: Service
metadata:
  name: api
  namespace: team-b
spec:
  selector:
    app: api
  ports:
    - port: 80
      targetPort: 80
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
  namespace: team-b
spec:
  replicas: 1
  selector:
    matchLabels:
      app: api
  template:
    metadata:
      labels:
        app: api
    spec:
      containers:
        - name: nginx
          image: nginx:1.25-alpine
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: client
  namespace: team-a
spec:
  replicas: 1
  selector:
    matchLabels:
      app: client
  template:
    metadata:
      labels:
        app: client
    spec:
      containers:
        - name: toolbox
          image: busybox:1.36
          command: ["sleep", "3600"]
```

```bash
kubectl apply -f lab57-ex5-workloads.yaml
kubectl rollout status deployment/api -n team-b
kubectl rollout status deployment/client -n team-a
```

### Step 2: Default deny in both namespaces

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: team-a
spec:
  podSelector: {}
  policyTypes: [Ingress, Egress]
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: team-b
spec:
  podSelector: {}
  policyTypes: [Ingress, Egress]
```

Add **DNS egress** in **both** namespaces (copy Exercise 2 `allow-dns-egress`, set `metadata.namespace` to `team-a` and `team-b`).

### Step 3: AND pattern — single `from` entry with both selectors

One `from` item with **both** `namespaceSelector` and `podSelector` ⇒ the peer must match **both** (AND).

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-from-team-a-clients
  namespace: team-b
spec:
  podSelector: { matchLabels: { app: api } }
  policyTypes: [Ingress]
  ingress:
    - from:
        - namespaceSelector: { matchLabels: { kubernetes.io/metadata.name: team-a } }
          podSelector: { matchLabels: { app: client } }
      ports: [{ protocol: TCP, port: 80 }]
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: client-egress-to-team-b-api
  namespace: team-a
spec:
  podSelector: { matchLabels: { app: client } }
  policyTypes: [Egress]
  egress:
    - to:
        - namespaceSelector: { matchLabels: { kubernetes.io/metadata.name: team-b } }
          podSelector: { matchLabels: { app: api } }
      ports: [{ protocol: TCP, port: 80 }]
```

```bash
kubectl apply -f lab57-ex5-and-policies.yaml
```

Test:

```bash
kubectl exec -n team-a deploy/client -- wget -qO- --timeout=2 http://api.team-b.svc.cluster.local:80 | head -c 120
```

### Step 4: OR pattern — two separate `from` entries

If **any** `from` list element matches, traffic is allowed (OR). Each element can still use **AND** between `namespaceSelector` and `podSelector`.

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-ingress-or-demo
  namespace: team-b
spec:
  podSelector: { matchLabels: { app: api } }
  policyTypes: [Ingress]
  ingress:
    - from:
        - namespaceSelector: { matchLabels: { kubernetes.io/metadata.name: team-a } }
          podSelector: { matchLabels: { app: client } }
        - namespaceSelector: { matchLabels: { kubernetes.io/metadata.name: kube-system } }
      ports: [{ protocol: TCP, port: 80 }]
```

**AND vs OR:** one `from` item with **both** selectors ⇒ peer must match **both**. **Two** `from` items ⇒ peer may match **either** item.

---

## Exercise 6: External Traffic with ipBlock/CIDR

Use **`ipBlock`** to allow **ingress** or **egress** to **IP ranges**, optionally carving out subnets with **`except`**.

### Step 1: Egress allowlist by CIDR

Restrict **frontend** egress to **10.0.0.0/8:443** (add **DNS** egress separately, same as Exercise 2).

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: egress-corporate-only
  namespace: netpol-lab
spec:
  podSelector: { matchLabels: { app: frontend } }
  policyTypes: [Egress]
  egress:
    - to: [{ ipBlock: { cidr: 10.0.0.0/8 } }]
      ports: [{ protocol: TCP, port: 443 }]
```

### Step 2: Ingress only from a CIDR, excluding a subnet

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: ingress-from-cidr-with-except
  namespace: netpol-lab
spec:
  podSelector: { matchLabels: { app: frontend } }
  policyTypes: [Ingress]
  ingress:
    - from:
        - ipBlock:
            cidr: 10.0.0.0/8
            except: [10.0.1.0/24]
      ports: [{ protocol: TCP, port: 80 }]
```

**Meaning:** allow `10.0.0.0/8` **except** `10.0.1.0/24` to **frontend:80** (node/NAT paths depend on CNI). **Use cases:** hybrid ranges, external APIs/databases, and **`except`** for untrusted subnets.

---

## Exercise 7: Complete 3-Tier Application Isolation

Deploy **fe** (nginx **:80**), **be** (nginx **:8080**), **db** (PostgreSQL **:5432**) with labels **`tier=frontend|backend|database`**.

### Step 1: Manifests (`fe` / `be` / `db`)

Create **Services + Deployments** with labels **`tier=frontend`**, **`tier=backend`**, **`tier=database`**. **fe** and **be** are nginx on **80** and **8080**; **db** is PostgreSQL on **5432**.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: fe
  namespace: netpol-lab
spec:
  selector:
    tier: frontend
  ports:
    - port: 80
      targetPort: 80
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fe
  namespace: netpol-lab
spec:
  replicas: 1
  selector:
    matchLabels:
      tier: frontend
  template:
    metadata:
      labels:
        tier: frontend
    spec:
      containers:
        - name: nginx
          image: nginx:1.25-alpine
---
apiVersion: v1
kind: Service
metadata:
  name: be
  namespace: netpol-lab
spec:
  selector:
    tier: backend
  ports:
    - port: 8080
      targetPort: 8080
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: be
  namespace: netpol-lab
spec:
  replicas: 1
  selector:
    matchLabels:
      tier: backend
  template:
    metadata:
      labels:
        tier: backend
    spec:
      containers:
        - name: api
          image: nginx:1.25-alpine
        - name: probe
          image: busybox:1.36
          command: ['sleep', '3600']
---
apiVersion: v1
kind: Service
metadata:
  name: db
  namespace: netpol-lab
spec:
  selector:
    tier: database
  ports:
    - port: 5432
      targetPort: 5432
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: db
  namespace: netpol-lab
spec:
  replicas: 1
  selector:
    matchLabels:
      tier: database
  template:
    metadata:
      labels:
        tier: database
    spec:
      containers:
        - name: postgres
          image: postgres:15-alpine
          env:
            - name: POSTGRES_PASSWORD
              value: labpass
```

```bash
kubectl apply -f lab57-ex7-3tier.yaml
kubectl rollout status deployment/fe deployment/be deployment/db -n netpol-lab
```

### Step 2: Policies (full stack)

Use a **clean** `netpol-lab` (drop stray policies or recreate the namespace and re-apply Step 1). Apply **default deny** + **DNS** (Exercise 2 file) + the tier rules below: **fe** accepts **:80** from anywhere; **fe → be:8080**; **be** from **fe** only and **be → db:5432**; **db** from **be** only.

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: tier-default-deny
  namespace: netpol-lab
spec:
  podSelector: {}
  policyTypes: [Ingress, Egress]
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: fe-ingress-any
  namespace: netpol-lab
spec:
  podSelector: { matchLabels: { tier: frontend } }
  policyTypes: [Ingress]
  ingress:
    - ports: [{ protocol: TCP, port: 80 }]
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: fe-egress-to-be
  namespace: netpol-lab
spec:
  podSelector: { matchLabels: { tier: frontend } }
  policyTypes: [Egress]
  egress:
    - to: [{ podSelector: { matchLabels: { tier: backend } } }]
      ports: [{ protocol: TCP, port: 8080 }]
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: be-ingress-from-fe
  namespace: netpol-lab
spec:
  podSelector: { matchLabels: { tier: backend } }
  policyTypes: [Ingress]
  ingress:
    - from: [{ podSelector: { matchLabels: { tier: frontend } } }]
      ports: [{ protocol: TCP, port: 8080 }]
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: be-egress-to-db
  namespace: netpol-lab
spec:
  podSelector: { matchLabels: { tier: backend } }
  policyTypes: [Egress]
  egress:
    - to: [{ podSelector: { matchLabels: { tier: database } } }]
      ports: [{ protocol: TCP, port: 5432 }]
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: db-ingress-from-be
  namespace: netpol-lab
spec:
  podSelector: { matchLabels: { tier: database } }
  policyTypes: [Ingress]
  ingress:
    - from: [{ podSelector: { matchLabels: { tier: backend } } }]
      ports: [{ protocol: TCP, port: 5432 }]
```

```bash
kubectl apply -f lab57-ex2-allow-dns.yaml
kubectl apply -f lab57-ex7-policies.yaml
```

### Step 3: Test the chain and lateral movement

```bash
kubectl exec -n netpol-lab deploy/fe -- wget -qO- --timeout=2 http://be:8080 | head -c 80
kubectl exec -n netpol-lab deploy/be -c probe -- nc -zvw2 db 5432
kubectl exec -n netpol-lab deploy/fe -- wget -qO- --timeout=2 http://db:5432
```

**Expected:** `fe → be` OK; `be → db` (TCP **5432**) OK; `fe → db` **blocked**.

---

## Exercise 8: Verification and Debugging

### Step 1: List and inspect policies

```bash
kubectl get networkpolicy -n netpol-lab
kubectl get networkpolicy -n team-a
kubectl get networkpolicy -n team-b
kubectl describe networkpolicy allow-dns-egress -n netpol-lab
```

Confirm `Spec`: which pods are selected, `policyTypes`, each `Ingress`/`Egress` peer and port.

### Step 2: Systematic connectivity checks

Build a small matrix (source pod × destination Service × port) with `kubectl exec` and `wget`/`nc`. Re-run the same commands after each policy change so failures are attributable to a single diff.

### Step 3: When traffic is still wrong

Check **CNI enforcement**, **pod and namespace labels** vs selectors, that **`policyTypes`** matches what you intended, **DNS egress** when using names, **wrong namespace** for the policy object, **AND vs OR** in `from`/`to` lists, and **port alignment** (container vs Service vs rule).

**Common mistakes:** no DNS allow with deny-all egress; selector confusion; policies applied outside the workload namespace.

---

## Key Takeaways

- Start from **default deny** (ingress and/or egress), then add the smallest set of allows.  
- **Deny-all egress** requires an explicit **DNS (53/udp+tcp)** path to `kube-system` resolvers or name-based tests will lie.  
- Pair **identity** (`podSelector` / `namespaceSelector`) with **ports** for least privilege.  
- **AND:** one `from`/`to` entry with both namespace and pod selectors. **OR:** multiple entries in the same list.  
- **`ipBlock`** + **`except`** model external and hybrid IP ranges.  
- **Three-tier** designs use per-tier ingress/egress; **block lateral** hops (e.g. frontend → database).  
- **Verify** with `kubectl get/describe networkpolicy` plus repeatable exec probes.

---

## Troubleshooting Tips

- All traffic still allowed ⇒ CNI may not enforce policies (or `hostNetwork` / special paths).  
- Names fail but IPs work ⇒ **DNS** egress or **CoreDNS labels** in the policy.  
- Change one policy at a time; use `kubectl get endpoints` to confirm Services target the pods you think they do.

---

## Cleanup

Remove the lab namespaces when finished:

```bash
kubectl delete ns netpol-lab team-a team-b --ignore-not-found
```

---

## Next Steps

- **Lab 13** ([`lab13-sec-network-policies.md`](lab13-sec-network-policies.md)), **Lab 52** ([`lab52-ts-networking.md`](lab52-ts-networking.md)), interactive [`../html/network-policy.html`](../html/network-policy.html).
