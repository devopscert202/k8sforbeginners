# Lab 52: Network Troubleshooting

## Exercise index

| # | Topic |
|---|--------|
| 1 | [Service endpoint debugging (selector mismatch)](#ex1) |
| 2 | [DNS resolution testing (CoreDNS)](#ex2) |
| 3 | [Pod-to-pod connectivity (same and cross-namespace)](#ex3) |
| 4 | [NetworkPolicy blocking traffic](#ex4) |
| 5 | [Service port / targetPort mismatch](#ex5) |
| 6 | [NodePort accessibility](#ex6) |
| 7 | [Multi-failure diagnosis (intermediate)](#ex7) |

---

## Overview

Hands-on exercises for diagnosing and fixing Kubernetes networking issues: **Service** connectivity and endpoints, **DNS** resolution, **Pod-to-Pod** communication, **NetworkPolicy** blocking (including **DNS on port 53**), **Service port / targetPort** alignment, **NodePort** reachability, and **Ingress**-related mindset (debug Services before Ingress). Level: **beginner to intermediate**.

Use a **scratch directory** for manifests; do not commit intentionally broken YAML to this repository.

**Interactive companion:** [ts-networking.html](../html/ts-networking.html)

---

## Prerequisites

- Running cluster (Kind, Minikube, k3s, or cloud) and `kubectl` with rights for Namespaces, Workloads, Services, and NetworkPolicies
- CNI with **NetworkPolicy** support for Exercises 4 and 7 (otherwise behavior may not match)
- Familiarity with Services ([Lab 02: Creating Services](lab02-basics-creating-services.md)); optional DNS background ([Lab 45: DNS Configuration](lab45-net-dns-configuration.md))

---

## Learning Objectives

- Trace **selector → labels → Endpoints/EndpointSlices** with `kubectl get endpoints` and `kubectl describe svc`
- Validate **cluster DNS** from a debug Pod, read `resolv.conf`, and inspect **CoreDNS**
- Test **Pod IP** and **cross-namespace Service DNS**; spot **CNI** and **kube-proxy** (or equivalent) components
- Apply **default-deny** policies, interpret `kubectl describe networkpolicy`, and restore traffic with **allow** rules plus **UDP/TCP 53** to `kube-dns`
- Align **targetPort** with container listeners using `kubectl describe svc` and `ss -tlnp` inside Pods
- Troubleshoot **NodePort** (node IP, firewall, kube-proxy logs)
- Unwind **multiple** networking defects using a consistent inspection order

---

<a id="ex1"></a>

## Exercise 1: Service Endpoint Debugging

Create a Deployment labeled `app: web` and a Service whose selector uses `app: webapp` (intentional mismatch). Expect **no endpoints**, then fix the selector.

```bash
kubectl create namespace lab52-ex1
kubectl config set-context --current --namespace=lab52-ex1
```

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
  namespace: lab52-ex1
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
            - containerPort: 80
```

```bash
kubectl apply -f web-deployment.yaml
kubectl rollout status deployment/web
```

```yaml
apiVersion: v1
kind: Service
metadata:
  name: web-svc
  namespace: lab52-ex1
spec:
  selector:
    app: webapp
  ports:
    - port: 80
      targetPort: 80
```

```bash
kubectl apply -f web-svc-wrong.yaml
kubectl get endpoints web-svc
kubectl get endpointslices 2>/dev/null | grep web-svc || true
kubectl describe svc web-svc
kubectl get pods --show-labels
```

Fix: match Pod labels (`app=web`).

```bash
kubectl patch svc web-svc -p '{"spec":{"selector":{"app":"web"}}}'
kubectl get endpoints web-svc -o wide
kubectl run curl-test --rm -it --restart=Never --image=curlimages/curl -- curl -sS -m 5 http://web-svc.lab52-ex1.svc.cluster.local | head
```

**Takeaway:** Endpoints come only from Pods matching the Service **selector** (and ready, when probes apply).

---

<a id="ex2"></a>

## Exercise 2: DNS Resolution Testing

```bash
kubectl run debug --rm -it --restart=Never --image=busybox:1.36 -- sh
```

Inside the Pod:

```bash
nslookup kubernetes.default.svc.cluster.local
nslookup web-svc.lab52-ex1.svc.cluster.local
cat /etc/resolv.conf
```

Exit the shell, then on your workstation:

```bash
kubectl get pods -n kube-system -l k8s-app=kube-dns
kubectl logs -n kube-system -l k8s-app=kube-dns --tail=100
```

**Takeaway:** Resolver config is per-Pod; cluster DNS is served by **CoreDNS** (`k8s-app=kube-dns`). Failing lookups often show up in CoreDNS logs.

---

<a id="ex3"></a>

## Exercise 3: Pod-to-Pod Connectivity

Same Namespace: reach **Pod IP** directly. Different Namespace: use **FQDN** `<svc>.<namespace>.svc.cluster.local`.

```bash
kubectl create namespace lab52-ex3
kubectl create namespace lab52-ex3-client
kubectl config set-context --current --namespace=lab52-ex3
```

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod-b
  namespace: lab52-ex3
  labels:
    app: backend
spec:
  containers:
    - name: nginx
      image: nginx:1.25-alpine
      ports:
        - containerPort: 80
---
apiVersion: v1
kind: Pod
metadata:
  name: pod-a
  namespace: lab52-ex3
spec:
  containers:
    - name: shell
      image: busybox:1.36
      command: ["sleep", "3600"]
---
apiVersion: v1
kind: Service
metadata:
  name: backend-svc
  namespace: lab52-ex3
spec:
  selector:
    app: backend
  ports:
    - port: 80
      targetPort: 80
---
apiVersion: v1
kind: Pod
metadata:
  name: client
  namespace: lab52-ex3-client
spec:
  containers:
    - name: curl
      image: curlimages/curl
      command: ["sleep", "3600"]
```

```bash
kubectl apply -f lab52-ex3.yaml
kubectl wait --for=condition=Ready pod/pod-b pod/pod-a -n lab52-ex3 --timeout=120s
POD_B_IP=$(kubectl get pod pod-b -n lab52-ex3 -o jsonpath='{.status.podIP}')
kubectl exec -n lab52-ex3 pod-a -- wget -qO- "http://${POD_B_IP}:80" | head
kubectl wait --for=condition=Ready pod/client -n lab52-ex3-client --timeout=120s
kubectl exec -n lab52-ex3-client pod/client -- curl -sS -m 5 http://backend-svc.lab52-ex3.svc.cluster.local | head
kubectl get pods -n kube-system
kubectl get pods -n kube-system | grep kube-proxy || true
```

**Takeaway:** Pod IP tests the **CNI** path; Service DNS tests **kube-proxy** (or replacement) plus DNS. Some clusters omit `kube-proxy` Pods when using eBPF replacements.

---

<a id="ex4"></a>

## Exercise 4: NetworkPolicy Blocking Traffic

```bash
kubectl create namespace lab52-ex4
kubectl config set-context --current --namespace=lab52-ex4
```

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: backend
  namespace: lab52-ex4
  labels:
    role: backend
spec:
  containers:
    - name: nginx
      image: nginx:1.25-alpine
      ports:
        - containerPort: 80
---
apiVersion: v1
kind: Pod
metadata:
  name: frontend
  namespace: lab52-ex4
  labels:
    role: frontend
spec:
  containers:
    - name: busybox
      image: busybox:1.36
      command: ["sleep", "3600"]
---
apiVersion: v1
kind: Service
metadata:
  name: backend
  namespace: lab52-ex4
spec:
  selector:
    role: backend
  ports:
    - port: 80
      targetPort: 80
```

```bash
kubectl apply -f lab52-ex4-workloads.yaml
kubectl wait --for=condition=Ready pod/backend pod/frontend --timeout=120s
kubectl exec pod/frontend -- wget -qO- -T 3 http://backend.lab52-ex4.svc.cluster.local | head
```

**Default deny (ingress only):** frontend cannot reach backend.

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-ingress
  namespace: lab52-ex4
spec:
  podSelector: {}
  policyTypes:
    - Ingress
```

```bash
kubectl apply -f default-deny-ingress.yaml
kubectl exec pod/frontend -- wget -qO- -T 3 http://backend.lab52-ex4.svc.cluster.local
kubectl get networkpolicy
kubectl describe networkpolicy default-deny-ingress
```

**Fix — allow ingress to backend from frontend** (full YAML):

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-frontend-to-backend
  namespace: lab52-ex4
spec:
  podSelector:
    matchLabels:
      role: backend
  policyTypes:
    - Ingress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              role: frontend
      ports:
        - protocol: TCP
          port: 80
```

If you also restrict **egress** (common in hardened clusters), the frontend needs **egress to CoreDNS on 53/UDP and 53/TCP** (TCP is used for some DNS queries). Example **frontend egress** policy (full YAML):

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: frontend-egress
  namespace: lab52-ex4
spec:
  podSelector:
    matchLabels:
      role: frontend
  policyTypes:
    - Egress
  egress:
    - to:
        - podSelector:
            matchLabels:
              role: backend
      ports:
        - protocol: TCP
          port: 80
    - to:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: kube-system
          podSelector:
            matchLabels:
              k8s-app: kube-dns
      ports:
        - protocol: UDP
          port: 53
        - protocol: TCP
          port: 53
```

```bash
kubectl apply -f allow-frontend-to-backend.yaml
kubectl exec pod/frontend -- wget -qO- -T 3 http://backend.lab52-ex4.svc.cluster.local | head
```

**Tighten egress (so DNS must be allowed):** deny all **egress** from `frontend` only. HTTP still works on existing connections in some CNIs; new lookups break until DNS is allowed.

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: frontend-default-deny-egress
  namespace: lab52-ex4
spec:
  podSelector:
    matchLabels:
      role: frontend
  policyTypes:
    - Egress
```

```bash
kubectl apply -f frontend-default-deny-egress.yaml
kubectl exec pod/frontend -- nslookup backend.lab52-ex4.svc.cluster.local
```

Apply **`frontend-egress.yaml`** (full YAML above with **TCP 80** to `role: backend` and **UDP+TCP 53** to `k8s-app: kube-dns` in `kube-system`). Then:

```bash
kubectl apply -f frontend-egress.yaml
kubectl exec pod/frontend -- nslookup backend.lab52-ex4.svc.cluster.local
kubectl exec pod/frontend -- wget -qO- -T 3 http://backend.lab52-ex4.svc.cluster.local | head
```

If the `namespaceSelector` for `kube-system` does not match your cluster, ensure `kube-system` has label `kubernetes.io/metadata.name=kube-system` (Kubernetes sets this on newer releases) or adjust the rule per your admin guide.

**Takeaway:** With default deny, forgotten **DNS (53/UDP)** egress looks like random application failure.

---

<a id="ex5"></a>

## Exercise 5: Service Port Mismatch

Pod listens on **8080**; Service uses **targetPort 80** → connection refused or immediate failure.

```bash
kubectl create namespace lab52-ex5
kubectl config set-context --current --namespace=lab52-ex5
```

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app8080
  namespace: lab52-ex5
spec:
  replicas: 1
  selector:
    matchLabels:
      app: app8080
  template:
    metadata:
      labels:
        app: app8080
    spec:
      containers:
        - name: nginx
          image: nginx:1.25-alpine
          args:
            - /bin/sh
            - -c
            - sed -i 's/listen\s\+80;/listen 8080;/' /etc/nginx/conf.d/default.conf && nginx -g 'daemon off;'
          ports:
            - containerPort: 8080
---
apiVersion: v1
kind: Service
metadata:
  name: app-svc
  namespace: lab52-ex5
spec:
  selector:
    app: app8080
  ports:
    - port: 80
      targetPort: 80
```

```bash
kubectl apply -f lab52-ex5.yaml
kubectl rollout status deployment/app8080
kubectl run curl-fail --rm -it --restart=Never --image=curlimages/curl -- curl -v --max-time 5 http://app-svc.lab52-ex5.svc.cluster.local
kubectl describe svc app-svc
kubectl get endpoints app-svc -o yaml
APP_POD=$(kubectl get pod -l app=app8080 -o jsonpath='{.items[0].metadata.name}')
kubectl exec "$APP_POD" -- ss -tlnp
kubectl patch svc app-svc -p '{"spec":{"ports":[{"port":80,"targetPort":8080}]}}'
kubectl run curl-ok --rm -it --restart=Never --image=curlimages/curl -- curl -sS -m 5 http://app-svc.lab52-ex5.svc.cluster.local | head
```

**Takeaway:** **`port`** is the Service front door; **`targetPort`** must match a **listening** container port.

---

<a id="ex6"></a>

## Exercise 6: NodePort Accessibility

```bash
kubectl create namespace lab52-ex6
kubectl config set-context --current --namespace=lab52-ex6
```

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: echo
  namespace: lab52-ex6
spec:
  replicas: 2
  selector:
    matchLabels:
      app: echo
  template:
    metadata:
      labels:
        app: echo
    spec:
      containers:
        - name: echo
          image: hashicorp/http-echo:1.0.0
          args: ["-text=nodeport-ok"]
          ports:
            - containerPort: 5678
---
apiVersion: v1
kind: Service
metadata:
  name: echo-nodeport
  namespace: lab52-ex6
spec:
  type: NodePort
  selector:
    app: echo
  ports:
    - port: 80
      targetPort: 5678
```

```bash
kubectl apply -f lab52-ex6.yaml
kubectl get svc echo-nodeport
kubectl get nodes -o wide
NODE_IP=<node-ip>
NODEPORT=<nodeport-from-SERVICE>
curl -sS --max-time 5 "http://${NODE_IP}:${NODEPORT}"
```

If it fails: host/cloud **firewall** or **security group**, wrong **node IP** for your network path, or Kind/Docker needing **port maps**. Check dataplane:

```bash
kubectl get pods -n kube-system | grep kube-proxy || true
kubectl logs -n kube-system daemonset/kube-proxy --tail=80 2>/dev/null || true
```

**Takeaway:** NodePort exposes a high port on **each node**; reachability still depends on **routing** and **external** access to that node:port.

---

<a id="ex7"></a>

## Exercise 7: Multi-Failure Diagnosis (Intermediate)

Deploy **three** defects at once: wrong Service **selector**, wrong **targetPort**, and **default-deny-all** NetworkPolicy. Find and fix all three.

**Broken manifest — save as `lab52-broken.yaml`:**

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: lab52-capstone
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: capstone-web
  namespace: lab52-capstone
spec:
  replicas: 2
  selector:
    matchLabels:
      app: capstone
  template:
    metadata:
      labels:
        app: capstone
    spec:
      containers:
        - name: app
          image: hashicorp/http-echo:1.0.0
          args: ["-listen=:8080", "-text=capstone-fixed"]
          ports:
            - containerPort: 8080
---
apiVersion: v1
kind: Service
metadata:
  name: capstone-svc
  namespace: lab52-capstone
spec:
  selector:
    app: capstone-svc
  ports:
    - port: 80
      targetPort: 80
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: lab52-capstone
spec:
  podSelector: {}
  policyTypes:
    - Ingress
    - Egress
---
apiVersion: v1
kind: Pod
metadata:
  name: jumper
  namespace: lab52-capstone
  labels:
    role: jumper
spec:
  containers:
    - name: curl
      image: curlimages/curl
      command: ["sleep", "3600"]
```

```bash
kubectl apply -f lab52-broken.yaml
kubectl wait --for=condition=Available deployment/capstone-web -n lab52-capstone --timeout=120s
kubectl wait --for=condition=Ready pod/jumper -n lab52-capstone --timeout=120s
kubectl exec -n lab52-capstone pod/jumper -- curl -sS -m 5 http://capstone-svc.lab52-capstone.svc.cluster.local || true
```

Diagnose with:

```bash
kubectl get endpoints -n lab52-capstone capstone-svc
kubectl describe svc -n lab52-capstone capstone-svc
kubectl get networkpolicy -n lab52-capstone
```

### Solution (spoilers)

1. **Selector:** Pods are `app=capstone`; Service selects `app=capstone-svc` → empty endpoints until fixed.

```bash
kubectl patch svc capstone-svc -n lab52-capstone -p '{"spec":{"selector":{"app":"capstone"}}}'
```

2. **targetPort:** Container listens on **8080**; Service used **80**.

```bash
kubectl patch svc capstone-svc -n lab52-capstone -p '{"spec":{"ports":[{"port":80,"targetPort":8080}]}}'
```

3. **NetworkPolicy:** `default-deny-all` blocks ingress and egress. For this lab Namespace, delete it or replace with explicit allow rules (including DNS if you keep egress restrictions).

```bash
kubectl delete networkpolicy default-deny-all -n lab52-capstone
```

Verify:

```bash
kubectl get endpoints -n lab52-capstone capstone-svc
kubectl exec -n lab52-capstone pod/jumper -- curl -sS -m 5 http://capstone-svc.lab52-capstone.svc.cluster.local
```

Expected body: `capstone-fixed`.

---

## Key Takeaways

- **Endpoints** first: no addresses → labels, selectors, ports, readiness, or policy.
- **DNS** is a dependency for Service names; lockdown **egress** needs **53/UDP** (and often **53/TCP**) to `kube-dns`.
- **NetworkPolicy** errors look like **timeouts**; `kubectl describe networkpolicy` clarifies intent.
- **targetPort** must match listeners (`ss -tlnp` in the workload).
- **NodePort** failures are often **outside** the cluster (firewall, node IP, local Kind/Docker mapping).
- **Ingress:** confirm backend **Service** and **endpoints** before chasing Ingress controller rules ([Lab 35: Ingress and EndpointSlices](lab35-net-ingress-endpointslices.md)).

---

## Troubleshooting Tips

| Symptom | Checks |
|---------|--------|
| Service timeout / no route | `kubectl get endpoints`, `kubectl describe svc`, Pod labels |
| DNS failures | CoreDNS Pods, `kubectl logs -n kube-system -l k8s-app=kube-dns`, `cat /etc/resolv.conf` in client |
| Pod IP works, Service does not | kube-proxy / CNI dataplane implementation |
| Only one Namespace | `kubectl get netpol -n <ns>` |
| Ingress 502/503 | Endpoints, Service `port`, Ingress backend refs, controller logs |

---

## Cleanup

```bash
kubectl delete namespace lab52-ex1 lab52-ex3 lab52-ex3-client lab52-ex4 lab52-ex5 lab52-ex6 lab52-capstone --ignore-not-found
kubectl config set-context --current --namespace=default
```

---

## Next Steps

- [Lab 49: Cluster and Control Plane Troubleshooting](lab49-ts-cluster-control-plane.md)
- Lab **50** and **53** (troubleshooting series) when published (`lab50-ts-*.md`, `lab53-ts-*.md`)
- [Lab 45: DNS Configuration](lab45-net-dns-configuration.md)
- [Lab 13: Advanced Network Policies](lab13-sec-network-policies.md)
- [ts-networking.html](../html/ts-networking.html)
