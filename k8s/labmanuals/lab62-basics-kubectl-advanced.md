# Lab 62: Advanced kubectl Patterns

## Overview

Lab 03 covers day-to-day kubectl essentials — create, inspect, expose, scale, delete. This lab picks up where Lab 03 leaves off and focuses on the **advanced output, filtering, patching, and debugging** capabilities that make kubectl a power tool for cluster operators and CKA exam candidates.

**Based on:** [kubectl Command Reference](../docs/basics/kubectl-reference.md)

## Prerequisites

- A running Kubernetes cluster (Kind, kubeadm, or managed)
- `kubectl` CLI configured and pointing to the cluster
- Completion of Lab 03 (recommended)
- A test namespace: `kubectl create namespace lab62`

## Learning Objectives

By the end of this lab, you will be able to:

- Extract specific fields from resources using JSONPath
- Build custom tabular views with `custom-columns`
- Patch resources using strategic merge, JSON merge, and JSON patch
- Filter resources using `--field-selector`
- Compare live state against manifests with `kubectl diff`
- Debug running pods with `kubectl debug`
- Check API permissions with `kubectl auth can-i`
- Set up kubectl aliases and bash/zsh completion
- Use resource shortnames for speed
- Generate YAML manifests using imperative dry-run
- Use `-o wide`, `--show-labels`, and `-w` effectively

---

## Exercise 1: JSONPath Output

JSONPath lets you extract specific fields from Kubernetes resources — critical for scripting, automation, and CKA exam answers.

### Step 1: Create test resources

```bash
kubectl -n lab62 create deployment web --image=nginx:1.25 --replicas=3
kubectl -n lab62 expose deployment web --port=80 --type=ClusterIP
kubectl -n lab62 wait --for=condition=available deployment/web --timeout=60s
```

### Step 2: Extract a single field

```bash
kubectl -n lab62 get svc web -o jsonpath='{.spec.clusterIP}'
```

### Step 3: Extract multiple fields with formatting

```bash
kubectl -n lab62 get pods -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.podIP}{"\t"}{.spec.nodeName}{"\n"}{end}'
```

### Step 4: Get all container images in the namespace

```bash
kubectl -n lab62 get pods -o jsonpath='{.items[*].spec.containers[*].image}'
```

### Step 5: Extract with conditions (filter in JSONPath)

```bash
kubectl get nodes -o jsonpath='{.items[?(@.status.conditions[-1].type=="Ready")].metadata.name}'
```

### Verify

- Each command should return clean, parseable output without YAML/JSON wrapping.

---

## Exercise 2: Custom Columns

Custom columns let you build your own tabular views — useful when `-o wide` doesn't show the fields you need.

### Step 1: Pod name, IP, and node

```bash
kubectl -n lab62 get pods -o custom-columns=\
NAME:.metadata.name,\
IP:.status.podIP,\
NODE:.spec.nodeName,\
STATUS:.status.phase
```

### Step 2: Deployments with image and replicas

```bash
kubectl -n lab62 get deployments -o custom-columns=\
NAME:.metadata.name,\
IMAGE:.spec.template.spec.containers[0].image,\
DESIRED:.spec.replicas,\
READY:.status.readyReplicas
```

### Step 3: Nodes with capacity and allocatable

```bash
kubectl get nodes -o custom-columns=\
NODE:.metadata.name,\
CPU_CAP:.status.capacity.cpu,\
MEM_CAP:.status.capacity.memory,\
CPU_ALLOC:.status.allocatable.cpu,\
MEM_ALLOC:.status.allocatable.memory
```

### Verify

- Output should be a clean table with your chosen column headers.

---

## Exercise 3: Patching Resources

Kubernetes supports three patch strategies. Understanding when to use each is essential.

### Step 1: Strategic merge patch (default for kubectl patch)

Add a label to the deployment:

```bash
kubectl -n lab62 patch deployment web -p '{"metadata":{"labels":{"tier":"frontend"}}}'
kubectl -n lab62 get deployment web --show-labels
```

### Step 2: JSON merge patch

Change the image:

```bash
kubectl -n lab62 patch deployment web --type=merge \
  -p '{"spec":{"template":{"spec":{"containers":[{"name":"nginx","image":"nginx:1.26"}]}}}}'
kubectl -n lab62 rollout status deployment/web
```

### Step 3: JSON patch (RFC 6902)

Add an annotation using JSON patch operations:

```bash
kubectl -n lab62 patch deployment web --type=json \
  -p '[{"op":"add","path":"/metadata/annotations/patched-by","value":"lab62"}]'
kubectl -n lab62 get deployment web -o jsonpath='{.metadata.annotations.patched-by}'
```

### Step 4: Patch a service

```bash
kubectl -n lab62 patch svc web -p '{"spec":{"type":"NodePort"}}'
kubectl -n lab62 get svc web
```

### Verify

- Deployment label `tier=frontend` is present.
- Image is now `nginx:1.26`.
- Annotation `patched-by=lab62` exists.
- Service type changed to NodePort.

---

## Exercise 4: Field Selectors and Sorting

Field selectors filter resources by their spec/status fields — different from label selectors.

### Step 1: Find running pods

```bash
kubectl get pods -A --field-selector=status.phase=Running | head -20
```

### Step 2: Find pods on a specific node

```bash
NODE=$(kubectl get nodes -o jsonpath='{.items[0].metadata.name}')
kubectl get pods -A --field-selector spec.nodeName=$NODE
```

### Step 3: Combine field-selector with label-selector

```bash
kubectl -n lab62 get pods --field-selector=status.phase=Running -l app=web
```

### Step 4: Sort by creation timestamp

```bash
kubectl -n lab62 get pods --sort-by=.metadata.creationTimestamp
```

### Step 5: Sort nodes by CPU capacity

```bash
kubectl get nodes --sort-by=.status.capacity.cpu
```

### Verify

- Field selectors return a filtered subset; label selectors can be combined on the same command.

---

## Exercise 5: kubectl diff, dry-run, and server-side apply

These commands let you preview changes safely before applying them.

### Step 1: Create a manifest file

```bash
cat <<'EOF' > /tmp/lab62-web.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
  namespace: lab62
spec:
  replicas: 5
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
        image: nginx:1.27
        resources:
          requests:
            cpu: 50m
            memory: 64Mi
          limits:
            cpu: 200m
            memory: 128Mi
EOF
```

### Step 2: Preview with diff

```bash
kubectl diff -f /tmp/lab62-web.yaml
```

The output shows what would change (replicas, image, resources) without applying anything.

### Step 3: Validate with dry-run

```bash
kubectl apply -f /tmp/lab62-web.yaml --dry-run=server
```

Server-side dry-run validates against admission controllers and quotas.

### Step 4: Apply with server-side apply

```bash
kubectl apply -f /tmp/lab62-web.yaml --server-side
kubectl -n lab62 rollout status deployment/web
```

### Verify

- `kubectl diff` shows a human-readable diff.
- `--dry-run=server` returns the object without persisting.
- After apply, deployment has 5 replicas running `nginx:1.27`.

---

## Exercise 6: kubectl debug and auth can-i

### Step 1: Debug a running pod with an ephemeral container

```bash
POD=$(kubectl -n lab62 get pods -l app=web -o jsonpath='{.items[0].metadata.name}')
kubectl -n lab62 debug $POD -it --image=busybox:1.36 --target=nginx -- sh
```

Inside the ephemeral container:

```bash
wget -qO- http://localhost:80
exit
```

### Step 2: Debug by copying a pod

```bash
kubectl -n lab62 debug $POD -it --copy-to=debug-copy --image=busybox:1.36 -- sh
```

```bash
ls /
exit
```

Clean up the copy:

```bash
kubectl -n lab62 delete pod debug-copy
```

### Step 3: Check your permissions

```bash
kubectl auth can-i create deployments -n lab62
kubectl auth can-i delete nodes
kubectl auth can-i '*' '*' --all-namespaces
```

### Step 4: Check permissions as another user

```bash
kubectl auth can-i get pods -n lab62 --as=system:serviceaccount:lab62:default
kubectl auth can-i create deployments -n lab62 --as=system:serviceaccount:lab62:default
```

### Verify

- Ephemeral container attaches and can reach the nginx process.
- `auth can-i` returns `yes` or `no` for each permission check.

---

## Exercise 7: Productivity Setup and Tips

Muscle memory with aliases, completion, and shortcuts saves significant time during daily work and CKA exams.

### Step 1: Enable bash completion

```bash
source <(kubectl completion bash)
```

Verify it works — type `kubectl get p` and press Tab. It should complete to `pods`.

### Step 2: Set up the kubectl alias

```bash
alias k=kubectl
complete -o default -F __start_kubectl k
```

Now test:

```bash
k get pods -n lab62
k get nodes -o wide
```

### Step 3: Try resource shortnames

```bash
k get po -A               # pods in all namespaces
k get svc -n kube-system   # services
k get deploy -n lab62      # deployments
k get no                   # nodes
k get cm -n lab62          # configmaps
k get ns                   # namespaces
k get ep -n lab62          # endpoints
```

To see all shortnames available on your cluster:

```bash
kubectl api-resources --sort-by=name | head -30
```

### Step 4: Practice -o wide, --show-labels, and -w

```bash
# -o wide adds Node, IP, and other columns
k get pods -n lab62 -o wide

# --show-labels adds a LABELS column
k get pods -n lab62 --show-labels

# -w (watch) streams updates in real-time — open in a separate terminal
k get pods -n lab62 -w
```

In another terminal, scale the deployment and watch the first terminal update:

```bash
k -n lab62 scale deploy web --replicas=1
k -n lab62 scale deploy web --replicas=3
```

Press Ctrl+C to stop watching.

### Step 5: Generate YAML templates without creating resources

```bash
k run test-pod --image=nginx --dry-run=client -o yaml
k create deployment test-deploy --image=nginx --replicas=2 --dry-run=client -o yaml
k create service clusterip test-svc --tcp=80:80 --dry-run=client -o yaml
k create configmap test-cm --from-literal=env=dev --dry-run=client -o yaml
```

Redirect to files for editing:

```bash
k run test-pod --image=nginx --dry-run=client -o yaml > /tmp/test-pod.yaml
cat /tmp/test-pod.yaml
rm /tmp/test-pod.yaml
```

### Step 6: kubectl wait and kubectl cp

```bash
# Wait for deployment to be available
k -n lab62 wait --for=condition=available deployment/web --timeout=60s

# Copy a file into a pod
POD=$(k -n lab62 get pods -l app=web -o jsonpath='{.items[0].metadata.name}')
echo "hello from lab62" > /tmp/lab62-test.txt
k cp /tmp/lab62-test.txt lab62/$POD:/tmp/lab62-test.txt

# Copy it back
k cp lab62/$POD:/tmp/lab62-test.txt /tmp/lab62-retrieved.txt
cat /tmp/lab62-retrieved.txt

# Cleanup
rm /tmp/lab62-test.txt /tmp/lab62-retrieved.txt
```

### Verify

- Tab completion works with both `kubectl` and `k`.
- Shortnames resolve correctly.
- `-o wide` shows Node and IP columns.
- `--show-labels` appends a LABELS column.
- `-w` streams live updates.
- `--dry-run=client -o yaml` generates manifests without creating resources.
- `kubectl cp` successfully copies files in both directions.

---

## Cleanup

```bash
kubectl delete namespace lab62
rm -f /tmp/lab62-web.yaml
```

---

## Command Reference

| Pattern | Command | When to use |
|---------|---------|-------------|
| JSONPath | `-o jsonpath='{...}'` | Extract specific fields for scripting |
| Custom columns | `-o custom-columns=COL:path` | Build tailored tabular views |
| Strategic merge patch | `kubectl patch ... -p '{...}'` | Add/update fields, arrays merge intelligently |
| JSON merge patch | `kubectl patch --type=merge ...` | Replace entire subtrees |
| JSON patch | `kubectl patch --type=json ...` | Surgical add/remove/replace operations |
| Field selector | `--field-selector=key=value` | Filter by spec/status fields |
| Diff | `kubectl diff -f file.yaml` | Preview changes before applying |
| Dry run | `--dry-run=server` | Validate against server without persisting |
| Debug | `kubectl debug pod -it --image=...` | Attach ephemeral container to running pod |
| Auth check | `kubectl auth can-i verb resource` | Verify RBAC permissions |
| Resource shortnames | `k get po`, `k get svc`, `k get deploy` | Save typing with abbreviated resource names |
| `-o wide` | `kubectl get pods -o wide` | Show extra columns (node, IP, ports) |
| `--show-labels` | `kubectl get pods --show-labels` | Display all labels as a column |
| `-w` (watch) | `kubectl get pods -w` | Stream resource changes in real-time |
| `-A` (all namespaces) | `kubectl get pods -A` | Cross-namespace view |
| Imperative generator | `kubectl run ... --dry-run=client -o yaml` | Generate YAML without creating |
| Wait | `kubectl wait --for=condition=... ...` | Block until condition is met |
| Copy | `kubectl cp local pod:remote` | Transfer files to/from pods |

---

## What's Next?

| Lab | Focus |
|-----|-------|
| [Lab 03: kubectl essentials](./lab03-basics-kubectl-essentials.md) | Day-to-day create, inspect, expose, scale, delete |
| [Lab 54: Troubleshooting commands reference](./lab54-ts-commands-reference.md) | Command-oriented troubleshooting drills |
| [Lab 60: Kubernetes API discovery](./lab60-basics-k8s-apis.md) | api-resources, api-versions, kubectl explain |
| [Lab 61: Kubeconfig and contexts](./lab61-basics-kubeconfig-contexts.md) | Multi-cluster context switching |
