# OPA Gatekeeper — Policy Enforcement in Kubernetes

Kubernetes does not enforce organizational policies out of the box. Anyone with the right RBAC permissions can create any resource — a privileged container, a Pod without labels, a Namespace that breaks naming conventions, or a container with unbounded CPU. **OPA Gatekeeper** fills this gap by acting as an admission controller that evaluates every create/update request against policies you define as code.

---

## 1. What Is OPA Gatekeeper?

**Open Policy Agent (OPA)** is a general-purpose policy engine. **Gatekeeper** is the Kubernetes-native integration of OPA — it runs as a validating admission webhook, intercepts API requests, and allows or denies them based on **Rego** policies.

### How It Works

```
kubectl apply ──► API Server ──► Authentication ──► Authorization (RBAC)
                                                        │
                                                        ▼
                                              Admission Controllers
                                                        │
                                                        ▼
                                              Gatekeeper Webhook
                                              (evaluates Rego policies)
                                                        │
                                                  ┌─────┴─────┐
                                                  │           │
                                               ALLOW       DENY
                                             (resource    (violation
                                              created)     message)
```

### The Two Key Objects

| Object | Purpose | Created by |
|--------|---------|-----------|
| **ConstraintTemplate** | Defines the policy logic in Rego and declares a new CRD kind | Platform / security team |
| **Constraint** | Instantiates a template — specifies which resources to match and what parameters to enforce | Cluster admin |

Think of a ConstraintTemplate as a **policy blueprint** and a Constraint as a **deployed instance** of that blueprint with specific settings.

### Enforcement Actions

| Action | Behavior |
|--------|----------|
| `deny` | Reject the API request and return the violation message |
| `dryrun` | Allow the request but log the violation (audit mode) |
| `warn` | Allow the request but return a warning to the user |

---

## 2. What Problems Does Gatekeeper Solve?

| Problem | Gatekeeper solution |
|---------|-------------------|
| Developers deploy Pods without required labels | ConstraintTemplate checks `metadata.labels` → denied if missing |
| Containers request unbounded CPU/memory | ConstraintTemplate caps `resources.limits` → denied if exceeded |
| Namespaces don't follow naming conventions | ConstraintTemplate enforces prefix/suffix rules on Namespace names |
| Privileged containers bypass security boundaries | ConstraintTemplate blocks `securityContext.privileged: true` |
| Images use `:latest` tags (unpinned, unauditable) | ConstraintTemplate requires explicit image tags |
| No network policies attached to namespaces | ConstraintTemplate audits for missing NetworkPolicy objects |

### Use Cases

- **Security hardening** — block privileged containers, require non-root users, enforce read-only root filesystems
- **Governance** — require cost-center labels, owner annotations, environment tags on all workloads
- **Resource management** — cap CPU/memory limits per container to prevent noisy neighbors
- **Naming conventions** — enforce namespace prefixes (`prod-`, `dev-`, `staging-`) for organizational clarity
- **Compliance** — audit existing resources against policies without disrupting running workloads (`dryrun` mode)
- **CI/CD integration** — test manifests against Gatekeeper policies in pipelines before deployment

---

## 3. Gatekeeper Architecture

```
┌────────────────────────────────┐
│        Gatekeeper System       │
│                                │
│  ┌──────────────────────────┐  │
│  │  ConstraintTemplate CRDs │  │  ← Define policy logic (Rego)
│  │  (K8sRequiredLabels,     │  │
│  │   ResourceLimits, etc.)  │  │
│  └──────────┬───────────────┘  │
│             │ creates CRD      │
│  ┌──────────▼───────────────┐  │
│  │  Constraint instances     │  │  ← Match specific resources + parameters
│  │  (require-pod-labels,    │  │
│  │   pod-resource-limits)   │  │
│  └──────────┬───────────────┘  │
│             │                  │
│  ┌──────────▼───────────────┐  │
│  │  Webhook Server           │  │  ← Evaluates admission requests
│  │  (validates against Rego) │  │
│  └──────────┬───────────────┘  │
│             │                  │
│  ┌──────────▼───────────────┐  │
│  │  Audit Controller         │  │  ← Periodically scans existing resources
│  │  (reports violations)     │  │
│  └───────────────────────────┘ │
└────────────────────────────────┘
```

**Installation**: Gatekeeper is typically installed via Helm or the upstream manifests into a dedicated `gatekeeper-system` namespace. After the controller pods are healthy, you define ConstraintTemplates and Constraints.

---

## 4. Policy Scenarios

### Scenario 1: Required Labels on Pods

**Problem**: Pods are created without labels needed for cost tracking, ownership, and environment identification.

**ConstraintTemplate** — defines the `K8sRequiredLabels` kind and Rego validation logic:

```yaml
apiVersion: templates.gatekeeper.sh/v1beta1
kind: ConstraintTemplate
metadata:
  name: k8srequiredlabels
spec:
  crd:
    spec:
      names:
        kind: K8sRequiredLabels
      validation:
        openAPIV3Schema:
          properties:
            labels:
              type: array
              items:
                type: string
  targets:
    - target: admission.k8s.gatekeeper.sh
      rego: |
        package k8srequiredlabels
        missing_labels[label] {
          required := {"name", "environment", "costApprover", "businessOwner"}
          provided := {label | input.review.object.metadata.labels[label]}
          label := required - provided
        }
        violation["Missing required labels"] {
          missing_labels[_]
        }
```

**Constraint** — enforces the template on Pods:

```yaml
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sRequiredLabels
metadata:
  name: require-pod-labels
spec:
  enforcementAction: deny
  match:
    kinds:
      - apiGroups: [""]
        kinds: ["Pod"]
  parameters:
    labels: ["name", "environment", "costApprover", "businessOwner"]
```

**Non-compliant Pod** (denied — missing required labels):

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: noncompliant-pod
spec:
  containers:
  - name: nginx
    image: nginx:1.25-alpine
```

**Compliant Pod** (allowed — all required labels present):

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: compliant-pod
  labels:
    name: "compliant-pod"
    environment: "production"
    costApprover: "finance"
    businessOwner: "operations"
spec:
  containers:
  - name: nginx
    image: nginx:1.25-alpine
```

---

### Scenario 2: Pod Resource Limits

**Problem**: Containers with no resource limits can consume all available CPU/memory on a node, starving other workloads.

**ConstraintTemplate** — rejects Pods whose CPU or memory limits exceed caps:

```yaml
apiVersion: templates.gatekeeper.sh/v1beta1
kind: ConstraintTemplate
metadata:
  name: resourcelimits
spec:
  crd:
    spec:
      names:
        kind: ResourceLimits
  targets:
    - target: admission.k8s.gatekeeper.sh
      rego: |
        package resourcelimits

        violation[{"msg": msg}] {
          input.review.object.kind == "Pod"
          limits := input.review.object.spec.containers[_].resources.limits

          limits.cpu > "500m"
          msg := sprintf("CPU limit exceeds the allowed maximum: %v", [limits.cpu])
        }

        violation[{"msg": msg}] {
          input.review.object.kind == "Pod"
          limits := input.review.object.spec.containers[_].resources.limits

          limits.memory > "256Mi"
          msg := sprintf("Memory limit exceeds the allowed maximum: %v", [limits.memory])
        }
```

**Constraint** — applies to all Pods:

```yaml
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: ResourceLimits
metadata:
  name: pod-resource-limits
spec:
  match:
    kinds:
      - apiGroups: [""]
        kinds: ["Pod"]
```

A Pod requesting `cpu: 1000m` or `memory: 512Mi` would be denied; a Pod within `500m` CPU and `256Mi` memory would pass.

---

### Scenario 3: Namespace Naming Conventions

**Problem**: Teams create namespaces with arbitrary names, making it hard to identify environment, team, or purpose.

**ConstraintTemplate** — requires namespace names to start with a specific prefix:

```yaml
apiVersion: templates.gatekeeper.sh/v1beta1
kind: ConstraintTemplate
metadata:
  name: musthaveprefix
spec:
  crd:
    spec:
      names:
        kind: MustHavePrefix
  targets:
    - target: admission.k8s.gatekeeper.sh
      rego: |
        package musthaveprefix

        violation[{"msg": msg}] {
          input.review.object.kind == "Namespace"
          name := input.review.object.metadata.name

          not startswith(name, "prod-")
          msg := sprintf("Namespace name %v must start with 'prod-'", [name])
        }
```

**Constraint** — enforces on Namespace creation:

```yaml
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: MustHavePrefix
metadata:
  name: require-prod-prefix
spec:
  match:
    kinds:
      - apiGroups: [""]
        kinds: ["Namespace"]
```

`kubectl create namespace prod-payments` → allowed. `kubectl create namespace payments` → denied.

---

## 5. Gatekeeper vs Other Policy Tools

| Feature | OPA Gatekeeper | Kyverno | Pod Security Standards (PSS) |
|---------|---------------|---------|------------------------------|
| **Policy language** | Rego (general-purpose) | YAML (Kubernetes-native) | Built-in labels (no custom policies) |
| **Learning curve** | Steeper (Rego syntax) | Lower (familiar YAML) | Minimal (just labels) |
| **Flexibility** | Very high — any policy expressible in Rego | High — mutation + validation in YAML | Limited to 3 profiles (privileged, baseline, restricted) |
| **Mutation support** | Yes (via assign/modify) | Yes (native) | No |
| **Audit mode** | Yes (`dryrun` enforcement) | Yes (audit policy mode) | Yes (`warn` and `audit` label modes) |
| **Generate/auto-create** | No | Yes (can auto-generate resources) | No |
| **CRD-based** | Yes (ConstraintTemplate → CRD) | Yes (ClusterPolicy) | No (namespace labels) |
| **Best for** | Complex, cross-resource policies | Simple to moderate policies | Basic pod security baselines |

---

## 6. Best Practices

| Practice | Why |
|----------|-----|
| **Start with `dryrun`** | Audit existing resources before enforcing — avoid breaking running workloads |
| **Version control policies** | Store ConstraintTemplates and Constraints in Git alongside manifests |
| **Test in CI/CD** | Use `gator test` or Conftest to validate manifests against policies before deployment |
| **Use parameterized templates** | Make templates reusable — pass label lists, limit values, prefixes as Constraint parameters |
| **Monitor constraint violations** | Export Gatekeeper metrics to Prometheus; alert on new violations |
| **Limit webhook failure mode** | Configure `failurePolicy: Ignore` during rollout to avoid blocking all API requests if Gatekeeper is down |
| **Combine with PSS** | Use Pod Security Standards for baseline pod security + Gatekeeper for organization-specific policies |

---

## Conclusion

OPA Gatekeeper turns Kubernetes policy into code — ConstraintTemplates define the logic, Constraints deploy it, and the webhook enforces it at admission time. Whether you need label governance, resource caps, naming conventions, or security baselines, the ConstraintTemplate + Constraint pattern scales from a single rule to hundreds of policies across a multi-team cluster. Start in `dryrun` mode, iterate on Rego, and graduate to `deny` when the policy is proven.

---

## Hands-On Labs

Practice these concepts with guided lab exercises:

| Lab | Description |
|-----|-------------|
| [Lab 14: OPA Gatekeeper — Policy Enforcement](../../labmanuals/lab14-sec-opa-gatekeeper.md) | Install Gatekeeper via Helm, author ConstraintTemplates and Constraints, test compliant and non-compliant resources, and validate enforcement end to end |
