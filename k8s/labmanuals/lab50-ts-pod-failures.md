# Lab 50: Troubleshooting Pod Failures

## Overview

This lab is a hands-on break-fix workshop. You will intentionally create Pods and Deployments in bad states, then practice the commands and mental model needed to diagnose and repair them.

You will work through common failure surfaces that show up in real clusters:

- **Pending** — scheduling cannot place the Pod (resources, selectors, affinity, volumes, and more).
- **ImagePullBackOff** — the kubelet cannot pull the container image (tag, registry auth, network).
- **CrashLoopBackOff** — the container starts, exits non-zero (or is killed), and Kubernetes restarts it in a loop.
- **OOMKilled** — the container exceeds its memory limit and the kernel terminates it.
- **CreateContainerConfigError** — configuration referenced by the Pod (Secrets, ConfigMaps, env) cannot be mounted or resolved before the container starts.
- **RunContainerError** — the container runtime failed to start the container after the image was pulled (less common; often volume mounts, binary paths, or runtime issues).

Each exercise follows the same rhythm: **break → observe → describe events → fix → verify**.

For a visual walkthrough, open the companion page: [ts-pod-failures.html](../html/ts-pod-failures.html).

## Prerequisites

- A running Kubernetes cluster and `kubectl` configured to use it (`kubectl cluster-info` should succeed).
- Basic familiarity with Pods and Deployments (Labs 01–03).
- Permission to label at least one Node (Exercise 2). If you are on a managed cluster where you cannot label nodes, read that exercise and use a local Kind/Minikube cluster for the hands-on portion.

## Learning Objectives

By the end of this lab, you will be able to:

- Read `kubectl get pods` output and map `STATUS` and `READY` columns to likely root causes.
- Use `kubectl describe pod` (or `kubectl describe deployment`) to interpret **Events** and scheduling messages.
- Use `kubectl logs` and `kubectl logs --previous` to distinguish configuration errors from application crashes.
- Adjust manifests (resources, selectors, image references, Secrets, and ConfigMaps) to return workloads to a healthy state.
- Apply a short diagnostic checklist when several Pods fail at once.

---

## Repository YAML Files

> Canonical manifests matching each exercise are in [`k8s/labs/troubleshooting/`](../labs/troubleshooting/). Create the lab namespace and set your context as shown in Exercise 1, then apply from the repository root, for example:
>
> `kubectl apply -f k8s/labs/troubleshooting/pending-cpu.yaml`
>
> | File | Exercise |
> |------|----------|
> | `pending-cpu.yaml`, `pending-cpu-fixed.yaml` | Exercise 1 |
> | `pending-nodeselector.yaml` | Exercise 2 |
> | `deploy-bad-image.yaml` | Exercise 3 |
> | `crash-cmd.yaml`, `crash-cmd-fixed.yaml` | Exercise 4 |
> | `missing-cm-pod.yaml` | Exercise 5 |
> | `oom-demo.yaml`, `oom-demo-fixed.yaml` | Exercise 6 |
> | `missing-secret-pod.yaml` | Exercise 7 |
> | `ts-quiz-all.yaml` | Exercise 8 |

---

## Exercise 1: Pod Stuck in Pending (Insufficient Resources)

**Goal:** See how an impossible CPU request prevents scheduling and how reducing the request fixes the Pod.

### Step 1: Create a dedicated namespace (recommended)

```bash
kubectl create namespace lab50-ts
kubectl config set-context --current --namespace=lab50-ts
```

### Step 2: Apply a Pod that requests 100 CPUs

Save the manifest below as `pending-cpu.yaml` (or paste inline with `kubectl apply -f -`).

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pending-huge-cpu
  labels:
    lab: "50"
    exercise: "pending-cpu"
spec:
  containers:
    - name: app
      image: nginx:1.25-alpine
      resources:
        requests:
          cpu: "100"
        limits:
          cpu: "100"
```

Apply it:

```bash
kubectl apply -f pending-cpu.yaml
```

### Step 3: Observe Pending

```bash
kubectl get pods -l exercise=pending-cpu
```

Expected: `STATUS` is `Pending` and `READY` is `0/1` (exact `AGE` varies).

### Step 4: Diagnose with `describe`

```bash
kubectl describe pod pending-huge-cpu
```

Scroll to **Events**. You should see messages similar to:

```text
Warning  FailedScheduling  ...  0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod.
```

That line tells you the scheduler could not find any Node with **100 CPUs** free for your request.

### Step 5: Fix — reduce the CPU request

Patch the Pod by replacing the manifest with realistic resources, or delete and recreate:

```bash
kubectl delete pod pending-huge-cpu --ignore-not-found
```

Use this corrected manifest:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pending-huge-cpu
  labels:
    lab: "50"
    exercise: "pending-cpu"
spec:
  containers:
    - name: app
      image: nginx:1.25-alpine
      resources:
        requests:
          cpu: "100m"
        limits:
          cpu: "500m"
```

```bash
kubectl apply -f pending-cpu-fixed.yaml
kubectl get pods -l exercise=pending-cpu -w
```

Press `Ctrl+C` when the Pod is `Running`.

### Step 6: Verify

```bash
kubectl get pod pending-huge-cpu
```

Expected: `Running` and `READY` `1/1`.

---

## Exercise 2: Pod Stuck in Pending (Node Selector Mismatch)

**Goal:** Practice **nodeSelector** failures: the Pod will not schedule until a Node carries the required label.

### Step 1: Apply a Pod that requires `disktype=nvme`

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pending-nodeselector
  labels:
    lab: "50"
    exercise: "pending-nodeselector"
spec:
  nodeSelector:
    disktype: nvme
  containers:
    - name: app
      image: nginx:1.25-alpine
```

```bash
kubectl apply -f pending-nodeselector.yaml
kubectl get pods -l exercise=pending-nodeselector
```

Expected: `Pending`, `0/1`.

### Step 2: Diagnose

```bash
kubectl describe pod pending-nodeselector
```

In **Events**, look for text similar to:

```text
0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.
```

### Step 3: Pick a Node and label it

List nodes:

```bash
kubectl get nodes
```

Choose a node name (example: `kind-worker`) and label it:

```bash
kubectl label node kind-worker disktype=nvme
```

> **Note:** Replace `kind-worker` with a real node from your cluster. On some cloud clusters you may not be allowed to label nodes; use Kind or Minikube for this step if needed.

### Step 4: Verify scheduling

```bash
kubectl get pods -l exercise=pending-nodeselector -w
```

When the Pod is `Running`, stop the watch with `Ctrl+C`.

### Step 5: Optional cleanup

```bash
kubectl delete pod pending-nodeselector
kubectl label node kind-worker disktype-
```

(Replace `kind-worker` with your node name.)

---

## Exercise 3: ImagePullBackOff

**Goal:** Recognize bad image tags and distinguish them from private-registry authentication problems.

### Step 1: Deploy with a non-existent tag

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: test
  labels:
    lab: "50"
    exercise: "imagepull"
spec:
  replicas: 1
  selector:
    matchLabels:
      app: test
  template:
    metadata:
      labels:
        app: test
        lab: "50"
    spec:
      containers:
        - name: nginx
          image: nginx:nonexistent-tag-xyz
          ports:
            - containerPort: 80
```

```bash
kubectl apply -f deploy-bad-image.yaml
kubectl get pods -l app=test -w
```

Expected: `ErrImagePull` then `ImagePullBackOff` on the ReplicaSet Pod (name suffixes vary). Press `Ctrl+C` when done watching.

### Step 2: Diagnose

```bash
kubectl describe pod -l app=test
```

Under **Events**, expect lines similar to:

```text
Failed to pull image "nginx:nonexistent-tag-xyz": rpc error: code = NotFound desc = failed to pull and unpack image ...
```

### Step 3: Fix with `kubectl set image`

```bash
kubectl set image deployment/test nginx=nginx:1.25
kubectl rollout status deployment/test
kubectl get pods -l app=test
```

Expected: new Pod `Running`, `1/1`.

### Step 4: Private registry scenario — `imagePullSecrets`

When the image exists but **pull fails with 401/403**, you usually need a Secret of type `kubernetes.io/dockerconfigjson` referenced by the Pod or ServiceAccount.

Example Pod fragment (illustrative — replace names and server):

```yaml
spec:
  imagePullSecrets:
    - name: regcred
  containers:
    - name: app
      image: private.example.com/myorg/myapp:1.2.3
```

Create a generic docker-registry secret (example):

```bash
kubectl create secret docker-registry regcred \
  --docker-server=private.example.com \
  --docker-username=myuser \
  --docker-password=mypassword \
  --docker-email=myuser@example.com
```

Then reference `regcred` in `imagePullSecrets` as shown above.

---

## Exercise 4: CrashLoopBackOff (Bad Command)

**Goal:** Use logs and restart history to see a container that always exits with an error.

### Step 1: Deploy a container that exits immediately

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: crash-cmd
  labels:
    lab: "50"
    exercise: "crash-cmd"
spec:
  replicas: 1
  selector:
    matchLabels:
      app: crash-cmd
  template:
    metadata:
      labels:
        app: crash-cmd
    spec:
      containers:
        - name: app
          image: busybox:1.36
          command: ["/bin/sh", "-c", "exit 1"]
```

```bash
kubectl apply -f crash-cmd.yaml
kubectl get pods -l app=crash-cmd
```

Expected: `CrashLoopBackOff` or `Error` with restarts increasing.

### Step 2: Read logs from the current and previous instance

```bash
POD=$(kubectl get pods -l app=crash-cmd -o jsonpath='{.items[0].metadata.name}')
kubectl logs "$POD"
kubectl logs "$POD" --previous
```

BusyBox may produce little output; the signal is the exit code and rapid restarts.

### Step 3: Inspect `describe` for termination details

```bash
kubectl describe pod "$POD"
```

Look for:

- **Restart Count** increasing
- **Last State: Terminated** with **Reason: Error** (or **Completed** if the process exited 0 — here it is non-zero)

### Step 4: Fix the command

Delete the broken Deployment and apply a healthy one:

```bash
kubectl delete deployment crash-cmd
```

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: crash-cmd
spec:
  replicas: 1
  selector:
    matchLabels:
      app: crash-cmd
  template:
    metadata:
      labels:
        app: crash-cmd
    spec:
      containers:
        - name: app
          image: busybox:1.36
          command: ["/bin/sh", "-c", "echo ok && sleep 3600"]
```

```bash
kubectl apply -f crash-cmd-fixed.yaml
kubectl get pods -l app=crash-cmd
```

Expected: `Running`, `1/1`.

---

## Exercise 5: CrashLoopBackOff (Missing ConfigMap)

**Goal:** See how **missing ConfigMaps** referenced through `envFrom` block Pod startup.

### Step 1: Create a Pod that references a ConfigMap that does not exist

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: missing-cm-pod
  labels:
    lab: "50"
    exercise: "missing-cm"
spec:
  containers:
    - name: app
      image: busybox:1.36
      command: ["/bin/sh", "-c", "env | sort && sleep 3600"]
      envFrom:
        - configMapRef:
            name: app-config-that-does-not-exist
```

```bash
kubectl apply -f missing-cm-pod.yaml
kubectl get pods -l exercise=missing-cm
```

You may see `CreateContainerConfigError` first, then `CrashLoopBackOff` depending on timing and kubelet behavior. Both are acceptable signals for this exercise.

### Step 2: Diagnose

```bash
kubectl describe pod missing-cm-pod
```

Look for Events mentioning the missing object, for example:

```text
Error: configmap "app-config-that-does-not-exist" not found
```

### Step 3: Create the ConfigMap

```bash
kubectl create configmap app-config-that-does-not-exist \
  --from-literal=FEATURE_FLAG=on \
  --from-literal=LOG_LEVEL=info
```

### Step 4: Verify the Pod recovers

```bash
kubectl delete pod missing-cm-pod --ignore-not-found
kubectl apply -f missing-cm-pod.yaml
kubectl wait --for=condition=Ready pod/missing-cm-pod --timeout=120s
kubectl logs missing-cm-pod | head
```

You should see `FEATURE_FLAG` and `LOG_LEVEL` in the log output from `env | sort`.

---

## Exercise 6: OOMKilled (Memory Limit Too Low)

**Goal:** Correlate **OOMKilled** with memory limits using `describe` and structured status fields.

### Step 1: Run a container that exceeds a 10Mi limit

The snippet below uses a continuous read on `/dev/zero` so the process accumulates work until the cgroup memory limit is hit. Your cluster must allow the `busybox:1.36` image.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: oom-demo
  labels:
    lab: "50"
    exercise: "oom"
spec:
  containers:
    - name: hog
      image: busybox:1.36
      resources:
        limits:
          memory: "10Mi"
        requests:
          memory: "10Mi"
      command: ["/bin/sh", "-c", "tail -f /dev/zero"]
```

```bash
kubectl apply -f oom-demo.yaml
sleep 5
kubectl get pods -l exercise=oom
```

Expected: `OOMKilled` or rapid restarts leading to `CrashLoopBackOff` depending on timing.

### Step 2: Inspect termination state

```bash
kubectl describe pod oom-demo
```

Under the container status, look for **Last State: Terminated** with **Reason: OOMKilled**.

Structured view (optional `| jq .` if installed):

```bash
kubectl get pod oom-demo -o jsonpath='{.status.containerStatuses[0].lastState}' ; echo
```

Look for `"reason":"OOMKilled"` and often `exitCode` **137** (128 + 9, SIGKILL).

### Step 3: Fix — raise the memory limit

```bash
kubectl delete pod oom-demo
```

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: oom-demo
  labels:
    lab: "50"
    exercise: "oom"
spec:
  containers:
    - name: hog
      image: busybox:1.36
      resources:
        limits:
          memory: "256Mi"
        requests:
          memory: "64Mi"
      command: ["/bin/sh", "-c", "tail -f /dev/zero"]
```

```bash
kubectl apply -f oom-demo-fixed.yaml
kubectl get pods -l exercise=oom
```

> **Lab safety:** Delete this Pod when finished — it intentionally consumes memory on the Node up to its limit.

---

## Exercise 7: CreateContainerConfigError (Missing Secret)

**Goal:** Differentiate **Secret-not-found** style errors from image pull and crash loops.

### Step 1: Pod referencing a Secret that does not exist

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: missing-secret-pod
  labels:
    lab: "50"
    exercise: "missing-secret"
spec:
  containers:
    - name: app
      image: busybox:1.36
      command: ["/bin/sh", "-c", "echo API_KEY=$API_KEY && sleep 3600"]
      env:
        - name: API_KEY
          valueFrom:
            secretKeyRef:
              name: app-secret
              key: api_key
```

```bash
kubectl apply -f missing-secret-pod.yaml
kubectl get pods -l exercise=missing-secret
```

Expected: `CreateContainerConfigError`, `0/1`.

### Step 2: Diagnose

```bash
kubectl describe pod missing-secret-pod
```

Events typically include:

```text
Error: secret "app-secret" not found
```

### Step 3: Create the Secret

```bash
kubectl create secret generic app-secret --from-literal=api_key=supersecretvalue
```

### Step 4: Verify

```bash
kubectl delete pod missing-secret-pod
kubectl apply -f missing-secret-pod.yaml
kubectl wait --for=condition=Ready pod/missing-secret-pod --timeout=120s
kubectl logs missing-secret-pod
```

Expected log line: `API_KEY=supersecretvalue`.

---

## Exercise 8: Quick Diagnosis Practice (Three Broken Pods)

**Goal:** Strengthen pattern matching using only **`kubectl get pods`**, **`kubectl describe`**, and **`kubectl logs`**.

### Step 1: Apply all three manifests at once

Save as `ts-quiz-all.yaml` — **Pod A** = impossible CPU (Pending), **Pod B** = bad image tag, **Pod C** = crashing command:

```yaml
---
apiVersion: v1
kind: Pod
metadata:
  name: ts-quiz-a-pending
  labels:
    lab: "50"
    quiz: "true"
    case: "A"
spec:
  containers:
    - name: app
      image: nginx:1.25-alpine
      resources:
        requests:
          cpu: "500"
        limits:
          cpu: "500"
---
apiVersion: v1
kind: Pod
metadata:
  name: ts-quiz-b-image
  labels:
    lab: "50"
    quiz: "true"
    case: "B"
spec:
  containers:
    - name: app
      image: nginx:definitely-not-a-real-tag
---
apiVersion: v1
kind: Pod
metadata:
  name: ts-quiz-c-crash
  labels:
    lab: "50"
    quiz: "true"
    case: "C"
spec:
  containers:
    - name: app
      image: busybox:1.36
      command: ["/bin/sh", "-c", "echo failing && exit 42"]
```

```bash
kubectl apply -f ts-quiz-all.yaml
kubectl get pods -l quiz=true
```

### Step 2: Diagnose without peeking below

For each Pod, write down:

1. Observed `STATUS` from `kubectl get pods`.
2. The **one or two Event lines** that prove your theory.
3. The **single minimal fix** you would apply.

Commands you may use:

```bash
kubectl get pods -l quiz=true
kubectl describe pod ts-quiz-a-pending
kubectl describe pod ts-quiz-b-image
kubectl describe pod ts-quiz-c-crash
kubectl logs ts-quiz-c-crash
kubectl logs ts-quiz-c-crash --previous
```

### Solution (read after you attempt the quiz)

| Pod | Symptom | Root cause | Minimal fix |
|-----|---------|------------|-------------|
| `ts-quiz-a-pending` | `Pending`, `0/1` | CPU request far larger than any Node (`Insufficient cpu` in Events) | Reduce `resources.requests.cpu` to a realistic value (for example `100m`) |
| `ts-quiz-b-image` | `ImagePullBackOff` / `ErrImagePull` | Image tag does not exist in the registry | Change `image` to a valid tag (for example `nginx:1.25-alpine`) |
| `ts-quiz-c-crash` | `CrashLoopBackOff`, restarts increasing | Container exits with code 42 | Replace `command` with a stable process (for example `sleep 3600`) or fix application code |

Example fixes: delete each quiz Pod, edit the same fields in `ts-quiz-all.yaml` (CPU `100m`, valid `image`, stable `command`), then `kubectl apply -f ts-quiz-all.yaml` again — or patch with `kubectl edit pod/...` if your cluster allows it.

---

## Key Takeaways

- **`Pending`:** scheduler could not place the Pod — read `FailedScheduling` Events (CPU/memory, selectors, taints, volumes).
- **`ImagePullBackOff`:** bad tag, registry down, or missing `imagePullSecrets` for private images.
- **`CrashLoopBackOff`:** process exits — use `kubectl logs` / `--previous` plus **Restart Count** and **Last State** in `describe`.
- **`OOMKilled`:** exceeded memory **limits** (or node pressure) — right-size memory; exit code **137** is common.
- **`CreateContainerConfigError`:** Secret/ConfigMap/env wiring wrong **before** the app starts.
- **`RunContainerError`:** runtime could not start the container (mounts, binary path, policy) — compare Events to node/runtime logs if you have access.

---

## Troubleshooting Tips

- Read **Events from the bottom** of `kubectl describe` first — newest lines are usually at the end.
- Correlate **`READY`** with **`STATUS`** (`0/1 Running` vs `Pending` vs `CrashLoopBackOff` mean different things).
- For flaky crashes, always run **`kubectl logs pod --previous`**; for Deployments, **`kubectl get pods -l app=...`** narrows noise.

---

## Cleanup

Remove the lab namespace (deletes all objects created in these exercises if you used `lab50-ts`):

```bash
kubectl delete namespace lab50-ts
```

If you created resources in `default` or another namespace, delete them explicitly:

```bash
kubectl delete deployment test crash-cmd --ignore-not-found
kubectl delete pod pending-huge-cpu pending-nodeselector missing-cm-pod oom-demo missing-secret-pod --ignore-not-found
kubectl delete pod ts-quiz-a-pending ts-quiz-b-image ts-quiz-c-crash --ignore-not-found
kubectl delete configmap app-config-that-does-not-exist --ignore-not-found
kubectl delete secret app-secret --ignore-not-found
```

Reset your context namespace if you changed it:

```bash
kubectl config set-context --current --namespace=default
```

---

## Next Steps

- Continue with [Lab 51: Kubelet and Node Troubleshooting](lab51-ts-kubelet-node.md) and [Lab 52: Network Troubleshooting](lab52-ts-networking.md) (Services, DNS, and paths through the cluster network). Add **Lab 53** to this sequence when your course materials publish that module.
- Revisit scheduling fundamentals in [Lab 17: Node Selector](lab17-sched-nodeselector.md) and resource governance in [Lab 37: Resource Quotas and Limits](lab37-resmgmt-resource-quotas-limits.md).
- Open the interactive companion: [ts-pod-failures.html](../html/ts-pod-failures.html).
