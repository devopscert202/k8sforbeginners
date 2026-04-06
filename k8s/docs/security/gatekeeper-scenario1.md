**Enforcing Kubernetes Policies Using Gatekeeper**

## Introduction to Gatekeeper
Gatekeeper is an admission controller webhook for Kubernetes that enforces policies defined using Open Policy Agent (OPA). It helps organizations ensure compliance, security, and governance by restricting the creation of resources that do not adhere to predefined policies. By leveraging Constraint Templates and Constraints, Gatekeeper allows cluster administrators to enforce custom rules dynamically.

Gatekeeper is typically installed with Helm or the upstream project manifests into a dedicated namespace (for example `gatekeeper-system`). After the controller pods are healthy, you define **ConstraintTemplates** (which declare the CRD shape and Rego logic) and **Constraints** (which select API kinds and supply parameters).

## What Gatekeeper Does
Gatekeeper enforces Kubernetes security and governance policies by:
- Blocking non-compliant resource creation
- Auditing existing resources against defined policies
- Providing visibility into policy violations
- Integrating with OPA for advanced policy definitions
- Enforcing RBAC and compliance requirements dynamically

## Use Cases
- **Security Hardening**: Ensuring workloads follow best security practices (e.g., preventing privileged containers)
- **Resource Quotas**: Limiting resource usage per namespace or team
- **RBAC Enforcement**: Ensuring users and roles have appropriate access levels
- **Labeling Enforcement**: Requiring specific labels on deployments for tracking and governance
- **Network Policy Enforcement**: Ensuring all workloads follow defined network policies

## Other Tools Similar to Gatekeeper
| Tool           | Features                                     | License        |
|--------------|--------------------------------|-------------|
| Kyverno       | Kubernetes-native policy management         | Open Source |
| OPA (Standalone) | Policy engine for cloud-native environments | Open Source |
| K-Rail        | Security policy enforcement for Kubernetes   | Open Source |
| Kube-bench    | CIS Benchmark checks for Kubernetes         | Open Source |
| Kube-hunter   | Penetration testing for Kubernetes clusters | Open Source |

## Example: Required Labels on Pods
The following illustrates how a **ConstraintTemplate** expresses Rego that checks for missing labels, and how a **Constraint** scopes that logic to Pods and lists the required label keys. A Pod without those labels is rejected at admission; a Pod that includes them is allowed.

**ConstraintTemplate** (defines the `K8sRequiredLabels` kind and validation logic):

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

**Constraint** (enforces the template on Pods):

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

**Non-compliant Pod** (would be denied—missing required labels):

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: uncompliant-pod
spec:
  containers:
  - name: busybox
    image: busybox
```

**Compliant Pod** (illustrates the metadata Gatekeeper expects):

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
  - name: busybox
    image: busybox
```

## Conclusion
Gatekeeper is a powerful Kubernetes admission controller that enforces security and governance policies across clusters. By defining Constraint Templates and Constraints, administrators can enforce policies dynamically, ensuring compliance with security best practices. With integration into CI/CD pipelines and auditing capabilities, Gatekeeper plays a critical role in strengthening Kubernetes security.

---

## Hands-On Labs

Practice these concepts with guided lab exercises:

| Lab | Description |
|-----|-------------|
| [Lab 14: OPA Gatekeeper - Policy Enforcement](../../labmanuals/lab14-sec-opa-gatekeeper.md) | Install Gatekeeper, author constraints, and test allow/deny behavior. |
