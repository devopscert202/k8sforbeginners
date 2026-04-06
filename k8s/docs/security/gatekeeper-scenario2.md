# Enforcing Kubernetes Policies Using Gatekeeper

## Introduction

Gatekeeper is an admission controller webhook for Kubernetes that enforces policies defined using Open Policy Agent (OPA). It enables policy-based governance across a cluster by defining **ConstraintTemplates** (Rego + CRD schema) and **Constraints** (which resources and namespaces the policy applies to).

Common patterns include **limiting Pod resource limits** (for example maximum CPU or memory per container) and **enforcing naming conventions** on Namespaces (such as a required prefix for production namespaces). The admission webhook evaluates create/update requests; violations can be denied or audited depending on `enforcementAction` and cluster configuration.

## Prerequisites (conceptual)
- A running Kubernetes cluster with permission to install admission webhooks
- Familiarity with Pods, Namespaces, and how admission controllers interact with the API server
- Optional: Helm for installing the Gatekeeper chart

## Pattern 1: Pod resource limits via Rego
A ConstraintTemplate can inspect `input.review.object` for Pod specs and emit violations when container `resources.limits` exceed policy. The Constraint then matches `kind: Pod` so the template applies cluster-wide or per-namespace as you configure `match`.

**Illustrative ConstraintTemplate** (concept: reject Pods whose CPU or memory limits exceed caps):

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

**Illustrative Constraint** binding that template to Pods:

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

With this pattern, a Pod whose limits exceed the thresholds encoded in Rego is rejected at admission; Pods within the limits are allowed.

## Pattern 2: Namespace naming conventions
Another common use is ensuring Namespace names follow a convention— for example requiring a `prod-` prefix for production namespaces. The template matches `kind: Namespace` and uses string functions in Rego to compare `metadata.name`.

**Illustrative ConstraintTemplate**:

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

**Illustrative Constraint**:

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

## Conclusion
OPA Gatekeeper provides a robust mechanism to enforce compliance and governance in Kubernetes environments. By defining policies as code, organizations can ensure security and best practices across their clusters. Hands-on installation, apply order, and test cases belong in the lab manual linked below.

---

## Hands-On Labs

Practice these concepts with guided lab exercises:

| Lab | Description |
|-----|-------------|
| [Lab 14: OPA Gatekeeper - Policy Enforcement](../../labmanuals/lab14-sec-opa-gatekeeper.md) | Install Gatekeeper, create templates and constraints, and validate enforcement end to end. |
