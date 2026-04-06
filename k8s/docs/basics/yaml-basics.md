# YAML 101 for Kubernetes Labs

A practical introduction to YAML for learners who are new to the format and need to read, write, and fix manifests used in this repository’s labs.

**Interactive HTML (same content, visual layout):**

- [Part 1 — Syntax and structure](../../html/yaml-k8s-part1-syntax.html)
- [Part 2 — Kubernetes objects, editing, and workflows](../../html/yaml-k8s-part2-objects-editing.html)
- [Part 3 — Editors, validation, and troubleshooting](../../html/yaml-k8s-part3-tools-troubleshooting.html)
- [Catalog home (all HTML guides)](../../html/index.html)

---

## Table of contents

1. [Why YAML in Kubernetes](#why-yaml-in-kubernetes)
2. [What you should be able to do after this guide](#what-you-should-be-able-to-do-after-this-guide)
3. [Core rules (memorize these)](#core-rules-memorize-these)
4. [Scalars, mappings, and lists](#scalars-mappings-and-lists)
5. [Comments and multiline strings](#comments-and-multiline-strings)
6. [Multiple documents in one file](#multiple-documents-in-one-file)
7. [The Kubernetes object shape](#the-kubernetes-object-shape)
8. [Labels and selectors (YAML view)](#labels-and-selectors-yaml-view)
9. [Lab-aligned examples](#lab-aligned-examples)
10. [Editing manifests in real labs](#editing-manifests-in-real-labs)
11. [Tools that make YAML easier](#tools-that-make-yaml-easier)
12. [Troubleshooting checklist](#troubleshooting-checklist)
13. [Cheat sheet](#cheat-sheet)
14. [Further reading](#further-reading)

---

## Why YAML in Kubernetes

Kubernetes stores desired state as **declarative API objects**. You usually express those objects as **YAML** files (JSON works too, but YAML is the default in docs and labs because it is readable and diff-friendly).

When you apply manifests in the labs, YAML is sent to the API server. Understanding indentation and structure prevents most beginner errors.

---

## What you should be able to do after this guide

- Read a manifest and identify `apiVersion`, `kind`, `metadata`, and `spec`.
- Spot invalid indentation and mixed tabs/spaces before you apply.
- Add or change fields (image, replicas, ports, labels) safely.
- Use `kubectl explain` and dry-run to validate ideas before changing the cluster.
- Use an editor or online linter when the API returns cryptic parse errors.

---

## Core rules (memorize these)

| Rule | Detail |
|------|--------|
| **Spaces only** | Do not use the Tab key. Many parsers reject tabs; others behave inconsistently. |
| **Indentation = nesting** | Child keys are indented more than their parent. |
| **Be consistent** | Pick **2 spaces** per level (Kubernetes examples almost always use 2). |
| **`-` starts a list item** | List items are a `-` at the same indent as siblings. |
| **Case matters** | `kind: Pod` is not the same as `kind: pod`. |

---

## Scalars, mappings, and lists

### Scalars (single values)

```yaml
name: nginx
replicas: 3
enabled: true
ratio: 0.5
```

Strings do not need quotes unless they contain special characters or look like numbers/booleans:

```yaml
message: "8080"          # force string
danger: yes              # avoid; some parsers treat yes/no oddly — prefer true/false
```

### Mappings (key/value objects)

```yaml
metadata:
  name: my-app
  namespace: default
```

### Lists (sequences)

```yaml
ports:
  - containerPort: 80
  - containerPort: 443
```

### Nesting (how labs are structured)

```yaml
spec:
  containers:
    - name: web
      image: nginx:1.25
      ports:
        - containerPort: 80
```

---

## Comments and multiline strings

### Comments

```yaml
# whole-line comment
image: nginx:1.25   # inline comment (keep the line readable)
```

### Multiline (ConfigMaps and long command args)

**Literal block** (`|`) keeps line breaks:

```yaml
script.sh: |
  #!/bin/sh
  echo hello
  echo world
```

**Folded block** (`>`) folds soft line breaks into spaces:

```yaml
description: >
  This appears as one paragraph when parsed,
  even though it spans lines in the file.
```

---

## Multiple documents in one file

Separate objects with `---` on its own line. The API server accepts multi-document streams; `kubectl apply -f` applies each document.

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: demo
---
apiVersion: v1
kind: Pod
metadata:
  name: demo-pod
  namespace: demo
spec:
  containers:
    - name: app
      image: nginx:1.25
```

---

## The Kubernetes object shape

Almost every object follows this pattern:

```yaml
apiVersion: ...   # which API group/version
kind: ...         # resource type (Pod, Service, Deployment, ...)
metadata:         # name, namespace, labels, annotations, ...
spec:             # desired state (shape depends on kind)
# status: ...     # written by the cluster; omit in manifests you apply
```

- **`metadata`**: identity and indexing (name, namespace, labels).
- **`spec`**: what you want; controllers reconcile the cluster toward this.

---

## Labels and selectors (YAML view)

Labels are arbitrary key/value pairs on metadata. Selectors connect objects (e.g. a Service to Pods).

```yaml
metadata:
  labels:
    app: nginx
    tier: frontend
```

```yaml
spec:
  selector:
    matchLabels:
      app: nginx
```

---

## Lab-aligned examples

### Pod (similar to `k8s/labs/basics/apache1.yaml`)

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: apache1
  labels:
    mycka: k8slearning
spec:
  containers:
    - name: mycontainer
      image: docker.io/httpd
      ports:
        - containerPort: 80
```

### Service (ClusterIP pattern)

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-service
spec:
  selector:
    app: myapp
  ports:
    - port: 80
      targetPort: 8080
      protocol: TCP
```

### Deployment (apps/v1)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-deployment
  labels:
    app: nginx
spec:
  replicas: 2
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
          image: nginx:1.25.3
          ports:
            - containerPort: 80
```

### ConfigMap `data` (string values)

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  LOG_LEVEL: "info"
  feature.conf: |
    enabled=true
```

### Secret (`data` is base64; prefer `stringData` when authoring by hand)

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secret
type: Opaque
stringData:
  api_key: "replace-me-in-real-life"
```

---

## Working with manifests in a cluster

Common workflows (covered in detail in the lab manuals): apply manifests from files under version control; use **`kubectl explain`** for schema; use **client and server dry-run** to catch parse and admission issues before committing changes; use **`kubectl get -o yaml`** and **`kubectl diff`** to compare declared state to what is running. Imperative **`kubectl edit`** updates live objects in an editor—convenient for experiments, but Git-tracked files plus `apply` is usually clearer for learning.

---

## Tools that make YAML easier

### VS Code (recommended)

Install extensions:

- **YAML** (Red Hat) — schema validation, hover docs for Kubernetes YAML when configured, basic linting.
- **Kubernetes** (Microsoft) — snippets, navigation, context-aware help for manifests.

**Tips:**

- Set **Files: Insert Final Newline** and show whitespace rendering to catch accidental tabs.
- Use the integrated terminal next to the manifest when validating with `kubectl`.

### Online validators (paste YAML)

Useful when you see `error converting YAML to JSON` or `did not find expected key`:

- [YAML Lint](https://www.yamllint.com/)
- [YAML Validator (Code Beautify)](https://codebeautify.org/yaml-validator)

Paste **sanitized** manifests only (no real Secret contents).

### Command-line checks

- `kubectl apply --dry-run=client -o yaml -f file.yaml` — ensures kubectl can parse the file.
- If you use Python: `python -c "import yaml,sys; yaml.safe_load_all(open(sys.argv[1]))" file.yaml` (requires PyYAML).

---

## Troubleshooting checklist

| Symptom | Likely cause | What to do |
|--------|----------------|------------|
| `found character that cannot start any token` | Tabs or wrong character | Replace tabs with spaces; re-indent. |
| `did not find expected key` | Indentation broke parent/child relationship | Align `- list` items with sibling keys; check spaces under `spec:`. |
| `error validating data: ValidationError(...)` | Wrong field names or types for that `apiVersion`/`kind` | Run `kubectl explain <kind>.spec` and match the schema. |
| `unknown field` in Pod spec | Field belongs under `template` in a Deployment, not top-level | Compare to a working Deployment example. |
| List item “swallowed” as string | Missing newline or `-` | Each list entry needs `-` at the correct indent. |

**Safe recovery in labs**

Fix the file (or revert from git), validate with **client dry-run**, apply when clean, then **`kubectl describe`** the resource if the workload still misbehaves.

---

## Cheat sheet

| Concept | YAML pattern |
|---------|----------------|
| Key / value | `key: value` |
| Nested map | indent child keys |
| List | `- item` (repeat per item) |
| Multi-doc file | `---` between objects |
| Comment | `#` to end of line |
| Multiline text | `|` or `>` |

---

## Hands-On Labs

Practice these concepts with guided lab exercises:

| Lab | Description |
|-----|-------------|
| [Lab 46: YAML manifests deep dive](../../labmanuals/lab46-basics-yaml-manifests.md) | Uses `k8s/labs/yaml-lab/` manifests and break-and-fix exercises for real-world YAML skills. |

---

## Further reading

- [Kubernetes configuration overview](https://kubernetes.io/docs/concepts/configuration/overview/)
- [Official YAML spec (reference)](https://yaml.org/spec/)
- [Kubernetes object management](https://kubernetes.io/docs/concepts/overview/working-with-objects/object-management/)

---

*Last updated: March 2026 — aligned with this repo’s lab manifests and HTML guides in `k8s/html/`.*
