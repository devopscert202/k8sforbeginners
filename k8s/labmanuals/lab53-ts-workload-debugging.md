# Lab 53: Workload and Application Debugging

## Overview

Master the essential Kubernetes debugging tools used every day on real clusters: `kubectl logs`, `kubectl exec`, `kubectl port-forward`, ephemeral **debug** containers, and **event** analysis. This lab is aimed at **beginner to intermediate** operators who can create Pods and Services and now need a **repeatable, application-level troubleshooting workflow**—from “something is red” to a concrete fix.

You will practice **systematic** investigation: confirm what Kubernetes thinks is true (events, endpoints, probe status), then validate from **inside** the cluster (exec, port-forward) and from **outside** (curl through port-forward). The capstone exercise chains multiple realistic misconfigurations across a small three-tier app.

**Interactive companion:** [ts-application-debugging.html](../html/ts-application-debugging.html)

---

## Prerequisites

- A running Kubernetes cluster (Kind, Minikube, or a small dev cluster)
- `kubectl` installed and configured (`kubectl version --client`, `kubectl cluster-info`)
- Comfort creating Pods, Deployments, and Services (Labs [01](lab01-basics-creating-pods.md), [02](lab02-basics-creating-services.md), [03](lab03-basics-kubectl-essentials.md))
- Familiarity with ConfigMaps and Secrets is helpful ([Lab 25](lab25-workload-configmaps.md), [Lab 47](lab47-workload-secrets.md))
- For **Exercise 4**, cluster version **1.23+** recommended (`kubectl debug` / ephemeral containers). If your cluster has ephemeral containers disabled, use the fallback notes in that exercise.

---

## Learning Objectives

By the end of this lab, you will be able to:

- Stream, filter, and interpret container logs with `kubectl logs` (including multi-container and previous-instance logs)
- Open interactive and non-interactive shells with `kubectl exec` to inspect files, environment, and DNS
- Use `kubectl port-forward` to reach Pod, Service, and Deployment backends from your workstation
- Attach **ephemeral debug containers** to minimal images and use **copy** debugging when needed
- Build a timeline from `kubectl get events` and correlate it with `kubectl describe`
- Diagnose common application issues: missing configuration, wrong Service ports, and failing readiness probes
- Apply the same toolkit to a **multi-component** break-fix scenario end to end

---

## Exercise index

| # | Topic |
|---|--------|
| 1 | [kubectl logs mastery](#exercise-1-kubectl-logs-mastery) |
| 2 | [kubectl exec for live investigation](#exercise-2-kubectl-exec-for-live-investigation) |
| 3 | [Port forwarding](#exercise-3-port-forwarding) |
| 4 | [Ephemeral debug containers](#exercise-4-ephemeral-debug-containers) |
| 5 | [Events timeline analysis](#exercise-5-events-timeline-analysis) |
| 6 | [Common application issues (break-fix)](#exercise-6-common-application-issues-break-fix) |
| 7 | [End-to-end debugging challenge](#exercise-7-end-to-end-debugging-challenge-intermediate) |

---

## Exercise 1: kubectl logs Mastery

### Step 1: Create a dedicated namespace (recommended)

```bash
kubectl create namespace lab53-ts
kubectl config set-context --current --namespace=lab53-ts
```

### Step 2: Deploy a quiet Pod (nginx) and a chatty Pod

**Nginx (low log volume by default):**

```bash
kubectl run web-nginx --image=nginx:1.25 --labels='app=web,tier=frontend'
```

**Chatty logger (continuous stdout):**

```bash
kubectl run web-logger --image=busybox:1.36 --labels='app=web,tier=support' \
  -- sh -c 'i=0; while true; do i=$((i+1)); echo "tick $$i $$(date -Iseconds)"; sleep 2; done'
```

Wait until both are `Running`:

```bash
kubectl get pods -l app=web -o wide
```

### Step 3: Basic logs

Replace `<pod>` with your Pod name (e.g. `web-logger-...`):

```bash
kubectl logs web-logger
```

### Step 4: Last N lines

```bash
kubectl logs web-logger --tail=20
```

### Step 5: Time window

```bash
kubectl logs web-logger --since=5m
```

### Step 6: Follow live (stop with Ctrl+C)

```bash
kubectl logs web-logger -f
```

### Step 7: Timestamps

```bash
kubectl logs web-logger --timestamps
```

### Step 8: Multi-container Pod — logs per container

Create a Pod with two containers sharing the `app=web` label:

```bash
cat <<'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: web-twoctr
  labels:
    app: web
    demo: multict
spec:
  containers:
  - name: nginx
    image: nginx:1.25
  - name: sidecar
    image: busybox:1.36
    args: [/bin/sh, -c, 'while true; do echo sidecar-heartbeat; sleep 5; done']
EOF
```

Stream logs from a **specific** container:

```bash
kubectl logs web-twoctr -c nginx
kubectl logs web-twoctr -c sidecar --tail=5
```

### Step 9: Previous container instance (`--previous`)

**When it matters:** after a **restart**, the currently running container’s filesystem and stdout might not explain the *last* crash. `--previous` asks the kubelet for the **terminated** instance’s logs (if retained).

To practice safely, force a restart:

```bash
kubectl delete pod web-logger --force --grace-period=0
kubectl run web-logger --image=busybox:1.36 --labels='app=web,tier=support' \
  -- sh -c 'echo starting; sleep 3; echo crashing; exit 1'
```

After a couple of restarts:

```bash
kubectl logs web-logger --previous
```

You should see output from the **last crashed** attempt. (If you see “previous terminated container not found,” wait for a restart cycle or check `kubectl describe pod web-logger`.)

### Step 10: All Pods matching a label (all containers)

```bash
kubectl logs -l app=web --all-containers --prefix=true --tail=20
```

**Note:** `--prefix=true` prepends pod/container names so interleaved streams are readable.

**Takeaway:** pair logs with **events** and **describe**; use label selectors during incidents.

---

## Exercise 2: kubectl exec for Live Investigation

### Step 1: Exec into nginx

Ensure `web-nginx` is running (from Exercise 1) or create it again.

Interactive shell (Alpine/Busybox images often use `sh`; Debian-based nginx supports `bash` if installed—`sh` is the portable choice):

```bash
kubectl exec -it web-nginx -- /bin/sh
```

**Inside the container**, run:

```bash
env | sort | head
cat /etc/nginx/nginx.conf | head -n 40
ls -la /usr/share/nginx/html/
exit
```

### Step 2: Single-shot remote command (non-interactive)

```bash
kubectl exec web-nginx -- cat /etc/resolv.conf
```

### Step 3: Validate in-cluster DNS (throwaway Pod)

Nginx may not include `curl`. Use Busybox once:

```bash
kubectl run netcheck --rm -it --restart=Never --image=busybox:1.36 -- wget -qO- http://kubernetes.default.svc.cluster.local
```

**Failure to resolve** `kubernetes.default` is the signal you are hunting (CoreDNS or `resolv.conf`).

### Step 4: Multi-container exec (`-c`)

```bash
kubectl exec -it web-twoctr -c sidecar -- /bin/sh -c 'echo hello-from-sidecar && hostname && exit'
```

**Takeaway:** `exec` proves what the container **actually** sees versus what YAML *intended*.

---

## Exercise 3: Port Forwarding

### Step 1: Forward to a Pod

```bash
kubectl port-forward pod/web-nginx 8080:80
```

In **another terminal**:

```bash
curl -sS -I http://localhost:8080
```

You should see `HTTP/1.1 200` headers from nginx.

Stop port-forward with **Ctrl+C** in the first terminal.

### Step 2: Forward to a Service

Expose the Pod with a ClusterIP Service:

```bash
kubectl expose pod web-nginx --name=web-svc --port=80 --target-port=80
kubectl port-forward svc/web-svc 8080:80
```

Test:

```bash
curl -sS -I http://localhost:8080
```

### Step 3: Forward to a Deployment (works even if Pod names change)

```bash
kubectl create deployment pf-demo --image=nginx:1.25
kubectl rollout status deployment/pf-demo
kubectl expose deployment pf-demo --name=pf-demo-svc --port=80 --target-port=80
kubectl port-forward deployment/pf-demo 8080:80
```

`kubectl port-forward deployment/...` selects a **ready** Pod from the Deployment’s ReplicaSet—handy when pods churn.

### When to use port-forward vs a real Service

| Approach | Good for | Caveats |
|----------|----------|---------|
| **port-forward** | Local debugging, quick UI/API checks, restricted clusters | Runs on your laptop; breaks if your machine sleeps; not multi-user |
| **ClusterIP / NodePort / LB** | Real consumers, other Pods, CI, production paths | Requires correct selectors, ports, and network policies |

---

## Exercise 4: Ephemeral Debug Containers

### Context

**Distroless** and other minimal runtime images often ship **without** `/bin/sh`. The same workflow applies: you attach a **debug** container with tools.

### Step 1: Run a minimal Pod (pause = no shell, always reliable)

We use Kubernetes’ **pause** image so the exercise works on every cluster; real **gcr.io/distroless/static\*** images behave the same for `exec` (no shell) once your app container is running.

```bash
cat <<'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: minimal-app
spec:
  containers:
  - name: app
    image: registry.k8s.io/pause:3.9
EOF
```

```bash
kubectl wait --for=condition=Ready pod/minimal-app --timeout=120s
```

### Step 2: Confirm `exec` has no shell

```bash
kubectl exec -it minimal-app -- /bin/sh
```

Expect an error (binary not found). **Optional:** repeat with `gcr.io/distroless/static-debian12:nonroot` and a long-lived `command`/`args` from your own app image once you have one.

### Step 3: Ephemeral debug container (`--target`)

```bash
kubectl debug minimal-app -it --image=busybox:1.36 --target=app
```

Inside the debug shell, inspect the workload (paths vary by Kubernetes version):

```bash
ps
ls -la /proc/1/root 2>/dev/null || ls -la /
```

Exit with **Ctrl+D** or `exit`.

### Step 4: Copy debugging (`--copy-to`)

Clones the Pod spec into a **new** Pod with your debug image:

```bash
kubectl debug minimal-app -it --copy-to=minimal-app-debug --image=busybox:1.36 -- sleep 3600
kubectl delete pod minimal-app-debug --ignore-not-found
```

### Step 5: Node debugging (advanced, cluster-admin often required)

**Warning:** Node debugging is powerful—treat it like **root on the node**.

```bash
kubectl get nodes
```

Pick a node name, then:

```bash
kubectl debug node/<NODE_NAME> -it --image=ubuntu:22.04 -- chroot /host
```

Inside, `/host` is typically the node root filesystem mount—inspect kubelet config, container logs paths, or networking **only** on clusters where you are authorized.

### Fallback if `kubectl debug` is unavailable

Use a short-lived toolbox Pod, or a **debug** variant of your image (e.g. distroless `*:debug` tags) **only** in non-production namespaces.

---

## Exercise 5: Events Timeline Analysis

### Step 1: Deploy an intentionally broken Deployment

```bash
kubectl create deployment broken-img --image=this-registry-does-not-exist.example/bad:tag
```

### Step 2: Chronological events

```bash
kubectl get events --sort-by='.lastTimestamp' | tail -n 30
```

### Step 3: Warnings only

```bash
kubectl get events --field-selector type=Warning --sort-by='.lastTimestamp'
```

### Step 4: Pod-scoped events

```bash
kubectl get events --field-selector involvedObject.kind=Pod --sort-by='.lastTimestamp'
```

### Step 5: Describe the Deployment (Events section)

```bash
kubectl describe deployment broken-img
```

Scroll to **Events**. You should see **image pull** failures, **back-off**, and scheduling messages.

### Event literacy

- **Type `Normal`**: expected transitions (Scheduled, Pulled, Started, ScalingReplicaSet…)
- **Type `Warning`**: likely user action or system stress (FailedMount, FailedCreate, Unhealthy, BackOff…)
- **Reason** codes are your compact index—grep them in docs or search engines when unfamiliar.

### Cleanup this exercise

```bash
kubectl delete deployment broken-img --ignore-not-found
```

---

## Exercise 6: Common Application Issues (Break-Fix)

Use **scratch manifests** (here-documents) so broken YAML never lands in git.

### Scenario A — Missing environment variable (crash loop)

**Broken Pod** (expects `DATABASE_URL`):

```bash
cat <<'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: need-db-url
spec:
  restartPolicy: Always
  containers:
  - name: app
    image: busybox:1.36
    command: ["/bin/sh", "-c"]
    args:
    - |
      if [ -z "$DATABASE_URL" ]; then echo "FATAL: DATABASE_URL missing"; exit 1; fi
      echo "OK connected to $DATABASE_URL"
      sleep 3600
EOF
```

**Diagnose:**

```bash
kubectl logs need-db-url --tail=20
kubectl describe pod need-db-url
```

**Fix:**

```bash
kubectl create configmap lab53-db --from-literal=DATABASE_URL='postgres://demo:demo@db:5432/app'
kubectl delete pod need-db-url --ignore-not-found
cat <<'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: need-db-url
spec:
  containers:
  - name: app
    image: busybox:1.36
    command: ["/bin/sh", "-c"]
    args:
    - |
      if [ -z "$DATABASE_URL" ]; then echo "FATAL: DATABASE_URL missing"; exit 1; fi
      echo "OK connected to $DATABASE_URL"
      sleep 3600
    envFrom:
    - configMapRef:
        name: lab53-db
EOF
kubectl logs need-db-url --tail=5
kubectl exec need-db-url -- printenv DATABASE_URL
```

### Scenario B — App listens on 3000, Service targets 8080

```bash
kubectl run api --image=node:20-alpine --labels='app=api' \
  --command -- sh -c 'npx -y http-server -p 3000 -a 0.0.0.0 /tmp'
kubectl expose pod api --name=api-svc-bad --port=80 --target-port=8080
```

From a client Pod, `curl` to `http://api-svc-bad/` should **fail**. Confirm listen port: `kubectl exec api -- sh -c 'ss -tlnp || netstat -tln'`. **Fix:** `kubectl delete svc api-svc-bad && kubectl expose pod api --name=api-svc-good --port=80 --target-port=3000` and retest.

### Scenario C — Readiness probe wrong HTTP path

**Broken Pod:**

```bash
cat <<'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: probe-demo
  labels:
    app: probe-demo
spec:
  containers:
  - name: app
    image: nginx:1.25
    readinessProbe:
      httpGet:
        path: /this-does-not-exist
        port: 80
      initialDelaySeconds: 2
      periodSeconds: 3
EOF
kubectl get pod probe-demo
kubectl describe pod probe-demo | sed -n '/Events/,$p'
```

**Fix:** delete and re-apply with `readinessProbe.httpGet.path: /`, then wait for Ready:

```bash
kubectl delete pod probe-demo --ignore-not-found
cat <<'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: probe-demo
  labels:
    app: probe-demo
spec:
  containers:
  - name: app
    image: nginx:1.25
    readinessProbe:
      httpGet:
        path: /
        port: 80
      initialDelaySeconds: 2
      periodSeconds: 3
EOF
kubectl wait --for=condition=Ready pod/probe-demo --timeout=60s
```

### Scenario cleanup

```bash
kubectl delete pod need-db-url probe-demo --ignore-not-found
kubectl delete pod api --ignore-not-found
kubectl delete svc api-svc-bad api-svc-good --ignore-not-found
kubectl delete configmap lab53-db --ignore-not-found
```

---

## Exercise 7: End-to-End Debugging Challenge (Intermediate)

You will deploy a **three-tier** demo: `frontend` → `backend` → `database`. Each tier has **one deliberate defect**. Use only the techniques from this lab (logs, exec, port-forward, events, describe) before peeking at the solution.

### Step 1: Deploy the broken stack

```bash
cat <<'EOF' | kubectl apply -f -
apiVersion: v1
kind: Secret
metadata:
  name: backend-token
stringData:
  API_TOKEN: "supersecret"
---
apiVersion: v1
kind: Pod
metadata:
  name: db
  labels:
    app: db
    tier: data
spec:
  containers:
  - name: mariadb
    image: mariadb:11
    env:
    - name: MARIADB_ROOT_PASSWORD
      value: "lab53"
    - name: MARIADB_DATABASE
      value: "app"
    ports:
    - containerPort: 3306
---
apiVersion: v1
kind: Service
metadata:
  name: db
spec:
  selector:
    app: db
  ports:
  - name: mysql
    port: 3306
    targetPort: 9999
---
apiVersion: v1
kind: Pod
metadata:
  name: backend
  labels:
    app: backend
    tier: app
spec:
  containers:
  - name: api
    image: busybox:1.36
    command: ["/bin/sh", "-c"]
    args:
    - |
      echo "backend starting..."
      if [ -z "$API_TOKEN" ]; then echo "MISSING API_TOKEN"; exit 1; fi
      while true; do
        echo "ok $$(date -Iseconds)" | nc -l -p 8080
      done
---
apiVersion: v1
kind: Service
metadata:
  name: backend
spec:
  selector:
    app: not-backend
  ports:
  - port: 8080
    targetPort: 8080
---
apiVersion: v1
kind: Pod
metadata:
  name: frontend
  labels:
    app: frontend
    tier: web
spec:
  containers:
  - name: web
    image: busybox:1.36
    command: ["/bin/sh", "-c"]
    args:
    - |
      echo "frontend starting..."
      while true; do
        echo -e "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nCalling backend..." | nc -l -p 80
      done
EOF
```

### Step 2: Observe symptoms (no spoilers)

```bash
kubectl get pods,svc,endpoints -o wide
kubectl get events --sort-by='.lastTimestamp' | tail -n 40
```

Form **three hypotheses** (one per tier) before opening the solution.

---

### Solution walkthrough (read only after attempting)

| Tier | Symptom | Tooling | Fix |
|------|---------|---------|-----|
| Backend | Crash loop, `MISSING API_TOKEN` in logs | `kubectl logs backend` | Add `env.valueFrom.secretKeyRef` for `API_TOKEN` from Secret `backend-token` |
| Frontend → backend | Service exists but **no Endpoints** | `kubectl get endpoints backend`, `describe svc` | Selector was `app=not-backend`; patch to `app=backend` (`kubectl patch svc backend -p '{"spec":{"selector":{"app":"backend","tier":"app"}}}'`) |
| Database | Service port OK but **wrong targetPort** | `kubectl describe svc db`, `nc -zv db 3306` from a throwaway Pod | Patch Service `targetPort` from `9999` to `3306` |

**Sanity check:** `kubectl get pods,svc,endpoints`, then `kubectl port-forward pod/frontend 9080:80` and `curl -sS http://localhost:9080/` (plain-text response from the Busybox “HTTP” loop).

### Challenge cleanup

```bash
kubectl delete pod frontend backend db --ignore-not-found
kubectl delete svc backend db --ignore-not-found
kubectl delete secret backend-token --ignore-not-found
```

---

## Key Takeaways

- **Logs** tell you what a container *said*; **events** tell you what Kubernetes *did*; **exec** shows what the container *sees*.
- **`kubectl port-forward`** is the fastest safe bridge from laptop to cluster IPs for HTTP/TCP debugging.
- **Debug containers** are the standard answer to “I cannot exec because there is no shell.”
- Most “mystery” outages are boring: **wrong labels/selectors**, **wrong ports**, **missing Secrets/ConfigMaps**, and **bad probes**.
- Label your exercises (`app=...`) and use namespaces (`lab53-ts`) so cleanup is one command.

---

## Troubleshooting Tips

- **`kubectl logs` empty:** container may still be starting, logging to a file instead of stdout, or crashed before writing—use `describe` and `logs --previous`.
- **`exec` fails with `container not found`:** check `-c` name; for Pods not yet created, look at `Init` containers.
- **`port-forward` hangs or resets:** Pod not Ready, process not listening on container port, or local port already in use.
- **`kubectl debug` permission errors:** your user may lack `pods/ephemeralcontainers` subresource rights—ask cluster admins on shared environments.
- **Events disappeared:** the Kubernetes event store is **short-lived**; pair with cluster logging if you need months of history.

---

## Cleanup

If you used the recommended namespace:

```bash
kubectl delete namespace lab53-ts
kubectl config set-context --current --namespace=default
```

Otherwise delete individual objects created during exercises (Deployments, Services, Pods, Secrets, ConfigMaps) with `kubectl delete ...`.

---

## Next Steps

- Deepen **Pod-level** failure modes in [Lab 50: Troubleshooting Pod Failures](lab50-ts-pod-failures.md).
- Extend into **networking and Services** with [Lab 52: Network Troubleshooting](lab52-ts-networking.md) and the companion page [ts-networking.html](../html/ts-networking.html).
- Practice exam-style scenarios in [Lab 55: CKA Troubleshooting Practice Scenarios](lab55-ts-cka-scenarios.md) and [ts-cka-scenarios.html](../html/ts-cka-scenarios.html).
- Reinforce probes and health checks in [Lab 09: Health Probes](lab09-pod-health-probes.md) and cluster-wide signals in [Lab 36: Metrics Server](lab36-observe-metrics-server.md).
- Interactive recap: [ts-application-debugging.html](../html/ts-application-debugging.html).

---

**End of Lab 53**
