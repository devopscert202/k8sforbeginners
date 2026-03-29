# Lab 46: YAML Manifests — Read, Write, Break, and Fix

## Overview

This hands-on lab is a **single, end-to-end YAML practice module** aligned with the interactive HTML guides and the markdown primer in this repository. You will walk through the same **core examples** used in those materials (minimal Pod, Deployment with template, Service selectors, multi-document files, ConfigMap multiline blocks), then **deliberately introduce faults**, interpret `kubectl` and parser errors, and correct them.

**Companion material (read alongside or afterward):**

- Markdown: [YAML 101 for Kubernetes Labs](../basics/yaml-basics.md)
- HTML (visual walkthrough): [Part 1 — Syntax](../html/yaml-k8s-part1-syntax.html), [Part 2 — Objects & editing](../html/yaml-k8s-part2-objects-editing.html), [Part 3 — Tools & troubleshooting](../html/yaml-k8s-part3-tools-troubleshooting.html)

**Scope:** **Lab 46** is dedicated entirely to **YAML for Kubernetes**—syntax, object structure, applying safe manifests, validating with `kubectl`, and deliberate break-and-fix practice. Use it **before** complex labs if you want a solid base, **alongside** early Pod and Deployment work, or **any time** you need to untangle manifest errors without redoing a whole topic lab.

## Prerequisites

- A running Kubernetes cluster and working `kubectl` configuration
- Completion of [Lab 01: Creating Pods](lab01-basics-creating-pods.md) is helpful but not strictly required
- A text editor (VS Code recommended)

## Learning Objectives

By the end of this lab, you will be able to:

- Explain the roles of `apiVersion`, `kind`, `metadata`, and `spec` in a manifest
- Use **2-space indentation**, lists (`-`), and mappings without introducing tabs or broken nesting
- Apply and update manifests under a dedicated namespace (`yaml-lab`)
- Use `kubectl explain`, client/server dry-run, and `kubectl diff` to validate changes
- Recognize common YAML and schema errors from error messages and fix them systematically

---

## Exercise index (all 12)

Use this list to jump to any section. Exercises **5–10** are the **break-and-fix** drills (after you have applied the known-good manifests in 3–4).

| # | Topic | Jump |
|---|--------|------|
| 1 | YAML building blocks (scalars, lists, comments) | [→](#ex1) |
| 2 | Kubernetes object shape (`apiVersion` … `spec`) | [→](#ex2) |
| 3 | Namespace + minimal Pod (`01-pod-minimal.yaml`) | [→](#ex3) |
| 4 | Multi-doc Service + Deployment (`---`) | [→](#ex4) |
| 5 | Dry-run (client/server) and `kubectl diff` | [→](#ex5) |
| 6 | ConfigMap multiline (`03-configmap-multiline.yaml`) | [→](#ex6) |
| 7 | **Break:** tab characters | [→](#ex7) |
| 8 | **Break:** broken list indentation | [→](#ex8) |
| 9 | **Break:** `containers` under wrong parent (Deployment) | [→](#ex9) |
| 10 | **Break:** Service selector ≠ Pod labels | [→](#ex10) |
| 11 | Optional: `stringData` Secret | [→](#ex11) |
| 12 | VS Code + online validators | [→](#ex12) |

**Parts:** **1–2** = read/learn · **3–6** = apply known-good YAML · **7–10** = intentional mistakes on scratch files · **11–12** = optional extensions.

---

## Working directory

All **known-good** manifests for this lab live in:

```text
k8s/labs/yaml-lab/
```

| File | Purpose |
|------|---------|
| `namespace.yaml` | Creates namespace `yaml-lab` |
| `01-pod-minimal.yaml` | Single Pod (teaches object shape + lists) |
| `02-deployment-and-service.yaml` | `---` multi-doc: Service + Deployment |
| `03-configmap-multiline.yaml` | ConfigMap with `\|` multiline string |

For **broken** examples, you will create **scratch files yourself** (for example `scratch-broken.yaml`) so you never accidentally apply bad YAML from a shared folder.

---

<a id="ex1"></a>

## Exercise 1 — YAML building blocks (read and type)

**Goal:** Connect syntax to Kubernetes manifests before you apply anything.

### 1.1 Scalars and mappings

Scalars are single values. Mappings are nested keys (indent children deeper than the parent).

```yaml
name: nginx
replicas: 3
metadata:
  name: demo
  namespace: yaml-lab
```

**Walkthrough:** `metadata:` is a key whose value is a mapping; `name` and `namespace` are **children** of `metadata`, so they are indented **one level** more than `metadata`.

### 1.2 Lists (sequences)

List entries start with `-`. Container and port arrays are where beginners most often break indentation.

```yaml
spec:
  containers:
    - name: web
      image: nginx:1.25-alpine
      ports:
        - containerPort: 80
```

**Walkthrough:**

- `containers:` is a **list**; each element starts with `-`.
- `name`, `image`, and `ports` belong to **that list item**, so they line up with each other **after** the `-`.
- `ports` is itself a list of port objects.

**Try it:** In a scratch file, intentionally mis-indent `image:` to align with `containers:` and note how a linter or `kubectl apply` would complain later.

### 1.3 Comments and multiline text

```yaml
# whole-line comment
image: nginx:1.25-alpine  # inline comment
```

Multiline literal block (preserves line breaks)—common in ConfigMaps:

```yaml
script.sh: |
  #!/bin/sh
  echo hello
```

**Takeaway:** Kubernetes accepts comments in manifest files; they are ignored by the API.

---

<a id="ex2"></a>

## Exercise 2 — The Kubernetes object shape (four top-level keys)

Every object you `kubectl apply` typically has:

| Key | Role |
|-----|------|
| `apiVersion` | Which API group/version serves this resource |
| `kind` | Resource type (`Pod`, `Service`, `Deployment`, …) |
| `metadata` | Name, namespace, labels, annotations |
| `spec` | Desired state (shape depends on `kind`) |

**Walkthrough question (answer mentally or in notes):** For a `Pod`, where do **container definitions** live—under `metadata` or under `spec`? (Answer: `spec.containers`.)

**Command discovery:**

```bash
kubectl explain pod
kubectl explain pod.metadata
kubectl explain pod.spec
kubectl explain pod.spec.containers
```

---

<a id="ex3"></a>

## Exercise 3 — Create the lab namespace and a minimal Pod

**Goal:** Apply a valid Pod manifest line-by-line and verify the cluster state.

### Step 1: Create the namespace

```bash
cd k8s/labs/yaml-lab
kubectl apply -f namespace.yaml
```

Expected:

```text
namespace/yaml-lab created
```

### Step 2: Read `01-pod-minimal.yaml` in your editor

Walk through each field:

1. `apiVersion: v1` — core API for Pod.
2. `kind: Pod`
3. `metadata.name` / `metadata.namespace` / `metadata.labels`
4. `spec.containers` — list with one container, `image`, and `ports` list.

### Step 3: Apply the Pod

```bash
kubectl apply -f 01-pod-minimal.yaml
kubectl get pods -n yaml-lab
kubectl describe pod -n yaml-lab yaml-lab-pod
```

### Step 4: Optional — export live YAML

```bash
kubectl get pod -n yaml-lab yaml-lab-pod -o yaml
```

**Observe:** The API adds `status:` and other server-populated fields. When you copy exported YAML back into a file to re-apply, you usually **strip `status`** and read-only metadata (for example `uid`, `resourceVersion`) unless you know you need them.

### Cleanup before the next exercise (remove the standalone Pod)

```bash
kubectl delete pod -n yaml-lab yaml-lab-pod --ignore-not-found
```

---

<a id="ex4"></a>

## Exercise 4 — Multi-document file: Service + Deployment

**Goal:** Use `---` to separate two objects in one file and confirm **labels/selectors** match.

Open `02-deployment-and-service.yaml`. **Walkthrough:**

1. First document: `Service` with `spec.selector.app: yaml-lab-learn`.
2. Separator line: `---` alone.
3. Second document: `Deployment` whose Pod template has `metadata.labels.app: yaml-lab-learn`.

If those labels diverge, the Service will have **no endpoints**—a classic YAML/label thinking bug, not a network mystery.

### Apply both objects

```bash
kubectl apply -f 02-deployment-and-service.yaml
kubectl get svc,deploy,pods -n yaml-lab
kubectl get endpoints -n yaml-lab yaml-lab-svc
```

**Expected:** Endpoints show Pod IPs for port 80.

### Edit the live Deployment (optional)

```bash
kubectl -n yaml-lab edit deployment yaml-lab-deploy
```

Change `replicas` from `2` to `3`, save, exit. Re-run `kubectl get pods -n yaml-lab`.

**Practice:** Revert by editing the **file** `02-deployment-and-service.yaml` to match what you want in GitOps style, then:

```bash
kubectl apply -f 02-deployment-and-service.yaml
```

---

<a id="ex5"></a>

## Exercise 5 — Validation before apply (dry-run and diff)

**Goal:** Build safe habits from the HTML Part 3 material.

### Client dry-run (fast, no admission on server)

```bash
kubectl apply --dry-run=client -f 02-deployment-and-service.yaml
```

### Server dry-run (requires cluster; stronger checks)

```bash
kubectl apply --dry-run=server -f 02-deployment-and-service.yaml
```

### Compare file to live objects

After you change replicas or image in the file:

```bash
kubectl diff -f 02-deployment-and-service.yaml
```

**Takeaway:** Dry-run catches many mistakes **before** you change running workloads.

---

<a id="ex6"></a>

## Exercise 6 — ConfigMap and multiline `data`

**Goal:** Apply `03-configmap-multiline.yaml` and inspect the resulting object.

```bash
kubectl apply -f 03-configmap-multiline.yaml
kubectl get configmap -n yaml-lab yaml-lab-config -o yaml
```

**Walkthrough:** Under `data:`, key `app.properties` uses `|` so the following indented lines become a **single string value** with line breaks. `LOG_LEVEL` is a plain string; quoting `"info"` is valid and sometimes used for clarity.

---

<a id="ex7"></a>

## Exercise 7 — Break it on purpose: tab characters

**Goal:** Recognize YAML parse errors from **tabs**.

1. Copy `01-pod-minimal.yaml` to `scratch-tabs.yaml`.
2. On one line under `spec:` (for example before `containers:`), insert an indent using the **Tab** key in your editor.
3. Run:

```bash
kubectl apply --dry-run=client -f scratch-tabs.yaml
```

**Typical symptoms:** Errors mentioning **invalid character**, **tab**, or **yaml** parse failure **before** Kubernetes field validation.

**Fix:** Delete tabs; use spaces only. Turn on “render whitespace” in your editor.

**Cleanup:** Delete `scratch-tabs.yaml` when finished.

---

<a id="ex8"></a>

## Exercise 8 — Break it on purpose: broken list indentation

**Goal:** Fix `did not find expected key` style errors.

1. Copy `01-pod-minimal.yaml` to `scratch-list.yaml`.
2. Move `image:` so it aligns **with** `- name: web` instead of under it (wrong sibling level).
3. Run:

```bash
kubectl apply --dry-run=client -f scratch-list.yaml
```

**Fix pattern:** `image` and `ports` must be **children** of the same list item as `name`; they must be indented **deeper** than the `-` that starts the container entry.

---

<a id="ex9"></a>

## Exercise 9 — Break it on purpose: wrong field level (Deployment template)

**Goal:** Connect **unknown field** errors to **indentation / wrong parent**.

1. Copy `02-deployment-and-service.yaml` to `scratch-deploy.yaml`.
2. Under `spec:` (Deployment spec), add a **top-level** `containers:` list **beside** `replicas:` (as if the Pod fields belonged to the Deployment spec directly)—this mimics a common mistake.
3. Run:

```bash
kubectl apply --dry-run=client -f scratch-deploy.yaml
```

**Expected:** Validation or unknown-field errors for Deployment—containers belong under `spec.template.spec`, not directly under `spec`.

**Fix:** Restore `containers` under:

```text
spec.template.spec.containers
```

Use `kubectl explain deployment.spec.template.spec` if unsure.

---

<a id="ex10"></a>

## Exercise 10 — Break it on purpose: Service selector mismatch

**Goal:** Troubleshoot **logical** YAML: valid file, wrong wiring.

1. Apply known-good `02-deployment-and-service.yaml` if not already applied.
2. Copy to `scratch-svc.yaml`, edit **only** the Service `spec.selector` to use a different `app` value than the Deployment template labels.
3. Apply the Service document (you may split the file or use `kubectl apply -f scratch-svc.yaml` if it contains only the Service).

```bash
kubectl get endpoints -n yaml-lab yaml-lab-svc
kubectl describe svc -n yaml-lab yaml-lab-svc
```

**Symptom:** Service exists but **no endpoints** or empty subsets.

**Fix:** Make `spec.selector` labels match `spec.template.metadata.labels` on the Deployment (for the Pods you intend to target).

---

<a id="ex11"></a>

## Exercise 11 — Optional: `stringData` Secret (authoring-friendly)

**Goal:** See the difference between writing Secrets by hand vs base64 `data`.

Create `scratch-secret.yaml` (lab-only values; do not use real production secrets):

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: yaml-lab-secret
  namespace: yaml-lab
type: Opaque
stringData:
  demo_token: "replace-me-in-class-only"
```

```bash
kubectl apply --dry-run=client -f scratch-secret.yaml
kubectl apply -f scratch-secret.yaml
kubectl get secret -n yaml-lab yaml-lab-secret -o yaml
```

**Walkthrough:** `stringData` lets you write plain text; the API stores encoded data. Delete the Secret after the exercise.

```bash
kubectl delete secret -n yaml-lab yaml-lab-secret --ignore-not-found
```

---

<a id="ex12"></a>

## Exercise 12 — Editor and online tools (from HTML Part 3)

**Goal:** Use the same toolchain described in the HTML guide.

### VS Code extensions

- **YAML** (Red Hat) — `redhat.vscode-yaml`
- **Kubernetes** (Microsoft) — `ms-kubernetes-tools.vscode-kubernetes-tools`

### Online validators (paste **sanitized** YAML only)

- [YAML Lint](https://www.yamllint.com/)
- [YAML Validator (Code Beautify)](https://codebeautify.org/yaml-validator)

**Discussion:** When do you use an online linter vs `kubectl apply --dry-run=client`? (YAML lint for **syntax**; kubectl for **Kubernetes schema** and object shape.)

---

## Key takeaways

- **Spaces only**, consistent indent (typically **2 spaces** per level).
- **Lists** use `-`; properties of a list item are indented **past** the `-`.
- **Four pillars:** `apiVersion`, `kind`, `metadata`, `spec`.
- **Multi-doc:** `---` separates objects in one file.
- **Service ↔ Pod wiring** is **label matching**, not magic.
- **Break–fix drills** build muscle memory: read the error, classify (**parse** vs **schema** vs **labels**), fix one thing, re-run dry-run.

---

## Troubleshooting reference

| Symptom | Likely cause | First action |
|--------|----------------|--------------|
| Parse error / tab | Tabs or bad characters | Show whitespace; convert tabs to spaces |
| `did not find expected key` | Indentation / list structure | Re-align `-` and child keys |
| `unknown field` on Deployment | Fields under wrong parent | Move under `template.spec` |
| Service has no endpoints | Selector ≠ Pod labels | `kubectl describe svc` vs `kubectl get pod --show-labels` |
| Change not applied | Wrong file path or wrong namespace | `kubectl diff -f ...` and `-n yaml-lab` |

---

## Cleanup

Remove the lab namespace (deletes most resources in it):

```bash
kubectl delete namespace yaml-lab --ignore-not-found
```

Delete any scratch files you created (`scratch-*.yaml`).

---

## Next steps

- Return to workload labs with more confidence: [Lab 22: Deployment Strategies](lab22-deploy-deployment-strategies.md), [Lab 25: ConfigMaps](lab25-workload-configmaps.md)
- Networking: [Lab 45: DNS Configuration](lab45-net-dns-configuration.md)
- Security context and policies: [Lab 12](lab12-sec-security-context.md), [Lab 16](lab16-sec-pod-security-standards.md)
