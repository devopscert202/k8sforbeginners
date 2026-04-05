# Lab 14: OPA Gatekeeper - Policy Enforcement

## Overview
In this lab, you will learn how to use Open Policy Agent (OPA) Gatekeeper to enforce security and compliance policies in Kubernetes. You'll install Gatekeeper, create constraint templates, define constraints, and test policy enforcement with compliant and non-compliant resources.

## Prerequisites
- A running Kubernetes cluster
- kubectl CLI tool installed and configured
- Cluster admin access
- Helm installed (optional)
- Basic understanding of Kubernetes admission controllers
- Completion of Lab 01 recommended

## Learning Objectives
By the end of this lab, you will be able to:
- Understand OPA Gatekeeper and admission control
- Install and configure Gatekeeper in your cluster
- Create ConstraintTemplates using Rego policy language
- Define Constraints to enforce policies
- Test policy enforcement with compliant and non-compliant Pods
- Audit existing resources for policy violations
- Troubleshoot policy issues

---

## Understanding OPA Gatekeeper

### What is OPA Gatekeeper?

**OPA Gatekeeper** is an admission controller webhook for Kubernetes that enforces policies defined using Open Policy Agent (OPA). It provides:
- **Policy-as-Code** - Define policies using the Rego language
- **Admission Control** - Block non-compliant resources at creation time
- **Audit** - Scan existing resources for violations
- **Compliance** - Ensure security and governance requirements
- **Custom Policies** - Create organization-specific rules

### How Gatekeeper Works

1. **ConstraintTemplate** - Defines the policy logic (the "what to check")
2. **Constraint** - Applies the template with specific parameters (the "when to enforce")
3. **Admission Webhook** - Intercepts resource creation/update requests
4. **Policy Evaluation** - Runs Rego code to validate resources
5. **Decision** - Allow or deny the request based on policy

### Gatekeeper Architecture

```
Kubernetes API Server
        |
        v
[Admission Webhook]
        |
        v
[OPA Gatekeeper]
        |
        v
[ConstraintTemplate + Constraint]
        |
        v
[Rego Policy Evaluation]
        |
        v
[Allow/Deny Decision]
```

### Use Cases

- **Security Hardening** - Enforce required labels, annotations, security contexts
- **Compliance** - Ensure resources meet regulatory requirements
- **Resource Management** - Enforce limits, quotas, naming conventions
- **Best Practices** - Require probes, resource requests, proper configurations
- **Governance** - Audit and report on policy violations

---

## Exercise 1: Install OPA Gatekeeper

### Step 1: Install Gatekeeper Using Manifests

Install the latest stable release:

```bash
kubectl apply -f https://raw.githubusercontent.com/open-policy-agent/gatekeeper/v3.17.1/deploy/gatekeeper.yaml
```

Expected output:
```
namespace/gatekeeper-system created
customresourcedefinition.apiextensions.k8s.io/configs.config.gatekeeper.sh created
customresourcedefinition.apiextensions.k8s.io/constrainttemplates.templates.gatekeeper.sh created
...
deployment.apps/gatekeeper-controller-manager created
```

**Alternative: Install via Helm**

If you prefer Helm:

```bash
helm repo add gatekeeper https://open-policy-agent.github.io/gatekeeper/charts
helm install gatekeeper gatekeeper/gatekeeper --namespace gatekeeper-system --create-namespace
```

### Step 2: Verify Installation

Check the gatekeeper-system namespace:

```bash
kubectl get namespace gatekeeper-system
```

Expected output:
```
NAME                STATUS   AGE
gatekeeper-system   Active   30s
```

Check Gatekeeper Pods:

```bash
kubectl get pods -n gatekeeper-system
```

Expected output:
```
NAME                                             READY   STATUS    RESTARTS   AGE
gatekeeper-audit-xxxxxxxxxx-xxxxx                1/1     Running   0          45s
gatekeeper-controller-manager-xxxxxxxxxx-xxxxx   1/1     Running   0          45s
gatekeeper-controller-manager-xxxxxxxxxx-xxxxx   1/1     Running   0          45s
```

Wait for all Pods to be in Running state:

```bash
kubectl wait --for=condition=ready pod --all -n gatekeeper-system --timeout=180s
```

### Step 3: Verify CRDs

Gatekeeper installs Custom Resource Definitions:

```bash
kubectl get crd | grep gatekeeper
```

Expected output:
```
configs.config.gatekeeper.sh
constrainttemplatepodstatuses.status.gatekeeper.sh
constrainttemplates.templates.gatekeeper.sh
...
```

### Step 4: Check Webhook Configuration

Verify the admission webhook:

```bash
kubectl get validatingwebhookconfigurations | grep gatekeeper
```

Expected output:
```
gatekeeper-validating-webhook-configuration   1          2m
```

---

## Exercise 2: Understanding the Scenario

### Scenario: Enforce Required Pod Labels

**Business Requirement**: All Pods must have specific labels for tracking, cost allocation, and governance:
- `name` - Application name
- `environment` - Deployment environment (dev, staging, prod)
- `costApprover` - Team responsible for costs
- `businessOwner` - Business unit owner

**Security Goal**: Prevent creation of Pods without these required labels.

### Step 1: Review the ConstraintTemplate

Navigate to the security labs directory:

```bash
cd k8s/labs/security/gatekeeper
```

Let's examine the `constraint-template.yaml` file:

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
          required := {label | label := input.parameters.labels[_]}
          provided := {label | input.review.object.metadata.labels[label]}
          label := required - provided
        }

        violation[{"msg": message, "details": missing_labels}] {
          missing_labels[_]
          message := sprintf("Missing required labels: %v", [missing_labels])
        }
```

**Understanding the ConstraintTemplate:**

**CRD Specification:**
- `names.kind: K8sRequiredLabels` - Creates a new CRD type
- `validation.openAPIV3Schema` - Defines parameters (labels array)

**Rego Policy Logic:**
```rego
missing_labels[label] {
  required := {label | label := input.parameters.labels[_]}  # Get required labels from constraint
  provided := {label | input.review.object.metadata.labels[label]}  # Get labels from resource
  label := required - provided  # Calculate missing labels (set difference)
}

violation[{"msg": message, "details": missing_labels}] {
  missing_labels[_]  # If any missing labels exist
  message := sprintf("Missing required labels: %v", [missing_labels])  # Create error message
}
```

**What this policy does:**
1. Compares required labels (from Constraint) with provided labels (from resource)
2. Calculates missing labels using set difference
3. If any labels are missing, creates a violation message
4. Gatekeeper denies the request and returns the error message

### Step 2: Review the Constraint

Let's examine the `constraint.yaml` file:

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
    labels:
      - name
      - environment
      - costApprover
      - businessOwner
```

**Understanding the Constraint:**

- `kind: K8sRequiredLabels` - Uses the CRD created by ConstraintTemplate
- `enforcementAction: deny` - Block non-compliant resources (alternatives: warn, dryrun)
- `match.kinds` - Apply to Pods in core API group
- `parameters.labels` - List of required labels

**What this constraint does:**
- Applies the k8srequiredlabels policy to all Pods
- Requires four specific labels: name, environment, costApprover, businessOwner
- Denies Pod creation if any label is missing

---

## Exercise 3: Deploy and Test the Policy

### Step 1: Apply the ConstraintTemplate

Create the policy template:

```bash
kubectl apply -f constraint-template.yaml
```

Expected output:
```
constrainttemplate.templates.gatekeeper.sh/k8srequiredlabels created
```

Verify the template:

```bash
kubectl get constrainttemplate
```

Expected output:
```
NAME                AGE
k8srequiredlabels   10s
```

Describe for details:

```bash
kubectl describe constrainttemplate k8srequiredlabels
```

### Step 2: Apply the Constraint

Activate the policy:

```bash
kubectl apply -f constraint.yaml
```

Expected output:
```
k8srequiredlabels.constraints.gatekeeper.sh/require-pod-labels created
```

Verify the constraint:

```bash
kubectl get k8srequiredlabels
```

Expected output:
```
NAME                 ENFORCEMENT-ACTION   TOTAL-VIOLATIONS
require-pod-labels   deny                 0
```

**Note**: The TOTAL-VIOLATIONS column shows existing resources that violate the policy.

### Step 3: Test with Non-Compliant Pod

Let's examine the `noncompliant-pod.yaml` file:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: uncompliant-pod
spec:
  containers:
  - name: nginx
    image: nginx:latest
```

Notice: This Pod has NO labels!

Try to create this Pod:

```bash
kubectl apply -f noncompliant-pod.yaml
```

Expected output (SHOULD BE DENIED):
```
Error from server (Forbidden): error when creating "noncompliant-pod.yaml": admission webhook "validation.gatekeeper.sh" denied the request: [require-pod-labels] Missing required labels: {"businessOwner", "costApprover", "environment", "name"}
```

**Success!** Gatekeeper blocked the non-compliant Pod and provided a clear error message.

### Step 4: Test with Compliant Pod

Let's examine the `compliant-pod.yaml` file:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: compliant-pod
  labels:
    name: nginx-app
    environment: production
    costApprover: finance-team
    businessOwner: devops-team
spec:
  containers:
  - name: nginx
    image: nginx:latest
```

Notice: This Pod has ALL required labels!

Create the compliant Pod:

```bash
kubectl apply -f compliant-pod.yaml
```

Expected output (SHOULD SUCCEED):
```
pod/compliant-pod created
```

Verify the Pod is running:

```bash
kubectl get pod compliant-pod
```

Expected output:
```
NAME            READY   STATUS    RESTARTS   AGE
compliant-pod   1/1     Running   0          10s
```

Check the labels:

```bash
kubectl get pod compliant-pod --show-labels
```

Expected output:
```
NAME            READY   STATUS    RESTARTS   AGE   LABELS
compliant-pod   1/1     Running   0          30s   businessOwner=devops-team,costApprover=finance-team,environment=production,name=nginx-app
```

**Success!** The compliant Pod was created without issues.

---

## Exercise 4: Audit Existing Resources

### Step 1: Create Pods Before Policy

Let's simulate existing resources that were created before the policy:

First, temporarily disable the constraint:

```bash
kubectl delete k8srequiredlabels require-pod-labels
```

Create a non-compliant Pod:

```bash
kubectl run audit-test-1 --image=nginx:alpine
kubectl run audit-test-2 --image=nginx:alpine --labels="name=test"
```

Re-enable the constraint:

```bash
kubectl apply -f constraint.yaml
```

### Step 2: Check Audit Results

View constraint status:

```bash
kubectl get k8srequiredlabels require-pod-labels
```

Expected output:
```
NAME                 ENFORCEMENT-ACTION   TOTAL-VIOLATIONS
require-pod-labels   deny                 2
```

**Notice**: TOTAL-VIOLATIONS shows 2 existing resources violate the policy.

### Step 3: Get Detailed Violation Information

Describe the constraint to see violations:

```bash
kubectl describe k8srequiredlabels require-pod-labels
```

Look for the Status section:
```yaml
Status:
  Audit Timestamp:  2026-03-16T10:30:00Z
  Total Violations:  2
  Violations:
    Enforcement Action:  deny
    Kind:                Pod
    Message:             Missing required labels: {"businessOwner", "costApprover", "environment", "name"}
    Name:                audit-test-1
    Namespace:           default
    ---
    Enforcement Action:  deny
    Kind:                Pod
    Message:             Missing required labels: {"businessOwner", "costApprover", "environment"}
    Name:                audit-test-2
    Namespace:           default
```

**What this shows:**
- Gatekeeper audits existing resources periodically
- Identifies resources that violate policies
- Provides detailed violation information
- Helps identify remediation needs

### Step 4: Remediate Violations

Option 1: Delete non-compliant Pods:

```bash
kubectl delete pod audit-test-1 audit-test-2
```

Option 2: Add missing labels:

```bash
kubectl label pod audit-test-1 name=test environment=dev costApprover=team businessOwner=ops
kubectl label pod audit-test-2 environment=dev costApprover=team businessOwner=ops
```

Wait for audit cycle (default: 60 seconds) and check again:

```bash
kubectl get k8srequiredlabels require-pod-labels
```

---

## Exercise 5: Advanced Policy - Namespace Naming Convention

### Step 1: Create ConstraintTemplate for Namespace Names

Create a policy that enforces namespace naming conventions:

```bash
cat > namespace-prefix-template.yaml <<'EOF'
apiVersion: templates.gatekeeper.sh/v1beta1
kind: ConstraintTemplate
metadata:
  name: k8snamespaceprefix
spec:
  crd:
    spec:
      names:
        kind: K8sNamespacePrefix
      validation:
        openAPIV3Schema:
          properties:
            prefix:
              type: string
  targets:
    - target: admission.k8s.gatekeeper.sh
      rego: |
        package k8snamespaceprefix

        violation[{"msg": message}] {
          input.review.object.kind == "Namespace"
          name := input.review.object.metadata.name
          prefix := input.parameters.prefix
          not startswith(name, prefix)
          message := sprintf("Namespace name '%v' must start with '%v'", [name, prefix])
        }
EOF
```

Apply the template:

```bash
kubectl apply -f namespace-prefix-template.yaml
```

### Step 2: Create Constraint

Create a constraint requiring "team-" prefix:

```bash
cat > namespace-prefix-constraint.yaml <<'EOF'
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sNamespacePrefix
metadata:
  name: namespace-must-have-team-prefix
spec:
  enforcementAction: deny
  match:
    kinds:
      - apiGroups: [""]
        kinds: ["Namespace"]
  parameters:
    prefix: "team-"
EOF
```

Apply the constraint:

```bash
kubectl apply -f namespace-prefix-constraint.yaml
```

### Step 3: Test Namespace Policy

Try to create a non-compliant namespace:

```bash
kubectl create namespace development
```

Expected output (SHOULD BE DENIED):
```
Error from server (Forbidden): admission webhook "validation.gatekeeper.sh" denied the request: [namespace-must-have-team-prefix] Namespace name 'development' must start with 'team-'
```

Create a compliant namespace:

```bash
kubectl create namespace team-development
```

Expected output (SHOULD SUCCEED):
```
namespace/team-development created
```

**Success!** Namespace naming policy is enforced.

---

## Exercise 6: Enforcement Actions

### Step 1: Understand Enforcement Actions

Gatekeeper supports three enforcement actions:

| Action | Behavior | Use Case |
|--------|----------|----------|
| **deny** | Block resource creation | Production enforcement |
| **warn** | Allow creation, show warning | Soft enforcement, monitoring |
| **dryrun** | Allow creation, audit only | Testing policies before enforcement |

### Step 2: Test Warn Mode

Modify the constraint to use warn mode:

```bash
kubectl patch k8srequiredlabels require-pod-labels --type='merge' -p '{"spec":{"enforcementAction":"warn"}}'
```

Try to create a non-compliant Pod:

```bash
kubectl run warn-test --image=nginx:alpine
```

Expected output (SHOULD SUCCEED WITH WARNING):
```
Warning: [require-pod-labels] Missing required labels: {"businessOwner", "costApprover", "environment", "name"}
pod/warn-test created
```

The Pod is created, but you receive a warning!

### Step 3: Test Dryrun Mode

Change to dryrun mode:

```bash
kubectl patch k8srequiredlabels require-pod-labels --type='merge' -p '{"spec":{"enforcementAction":"dryrun"}}'
```

Create a non-compliant Pod:

```bash
kubectl run dryrun-test --image=nginx:alpine
```

Expected output (SHOULD SUCCEED, NO WARNING):
```
pod/dryrun-test created
```

Check audit violations:

```bash
kubectl describe k8srequiredlabels require-pod-labels | grep -A 20 "Violations:"
```

Violations are tracked but not enforced!

### Step 4: Restore Deny Mode

Restore enforcement:

```bash
kubectl patch k8srequiredlabels require-pod-labels --type='merge' -p '{"spec":{"enforcementAction":"deny"}}'
```

---

## Lab Cleanup

### Step 1: Delete Test Pods

```bash
kubectl delete pod compliant-pod --ignore-not-found
kubectl delete pod warn-test --ignore-not-found
kubectl delete pod dryrun-test --ignore-not-found
kubectl delete pod audit-test-1 --ignore-not-found
kubectl delete pod audit-test-2 --ignore-not-found
```

### Step 2: Delete Constraints

```bash
kubectl delete k8srequiredlabels require-pod-labels
kubectl delete k8snamespaceprefix namespace-must-have-team-prefix
```

### Step 3: Delete ConstraintTemplates

```bash
kubectl delete constrainttemplate k8srequiredlabels
kubectl delete constrainttemplate k8snamespaceprefix
```

### Step 4: Delete Test Namespace

```bash
kubectl delete namespace team-development --ignore-not-found
```

### Step 5: Uninstall Gatekeeper (Optional)

If you want to completely remove Gatekeeper:

```bash
kubectl delete -f https://raw.githubusercontent.com/open-policy-agent/gatekeeper/v3.17.1/deploy/gatekeeper.yaml
```

Or with Helm:

```bash
helm uninstall gatekeeper -n gatekeeper-system
kubectl delete namespace gatekeeper-system
```

### Step 6: Clean Up YAML Files

```bash
rm -f namespace-prefix-template.yaml
rm -f namespace-prefix-constraint.yaml
```

---

## Common Gatekeeper Policies

### Require Resource Limits

```yaml
apiVersion: templates.gatekeeper.sh/v1beta1
kind: ConstraintTemplate
metadata:
  name: k8srequiredlimits
spec:
  crd:
    spec:
      names:
        kind: K8sRequiredLimits
  targets:
    - target: admission.k8s.gatekeeper.sh
      rego: |
        package k8srequiredlimits

        violation[{"msg": msg}] {
          container := input.review.object.spec.containers[_]
          not container.resources.limits.cpu
          msg := sprintf("Container %v is missing CPU limit", [container.name])
        }
```

### Block Privileged Containers

```yaml
violation[{"msg": msg}] {
  container := input.review.object.spec.containers[_]
  container.securityContext.privileged == true
  msg := sprintf("Privileged container is not allowed: %v", [container.name])
}
```

### Enforce Image Registry

```yaml
violation[{"msg": msg}] {
  container := input.review.object.spec.containers[_]
  not startswith(container.image, "myregistry.com/")
  msg := sprintf("Container %v uses unauthorized image registry", [container.name])
}
```

---

## Best Practices

### Policy Development

- Start with dryrun mode to test policies
- Use warn mode for gradual rollout
- Test policies in non-production first
- Document policy intent and parameters
- Version control all policies

### Policy Design

- Create reusable ConstraintTemplates
- Use meaningful constraint names
- Provide clear violation messages
- Parameterize policies for flexibility
- Consider audit performance impact

### Operations

- Monitor audit violations regularly
- Set up alerts for policy violations
- Review and update policies periodically
- Maintain policy documentation
- Train teams on policy requirements

### Security

- Protect Gatekeeper configuration
- Limit access to ConstraintTemplates
- Review admission webhook configuration
- Monitor Gatekeeper logs
- Keep Gatekeeper updated

---

## Troubleshooting Guide

### Issue: Gatekeeper Pods not starting

**Solution**:
```bash
kubectl logs -n gatekeeper-system -l control-plane=controller-manager
kubectl describe pod -n gatekeeper-system
```

### Issue: Policies not enforcing

**Solution**:
```bash
# Check webhook is registered
kubectl get validatingwebhookconfigurations

# Check constraint status
kubectl get constraints --all-namespaces

# Verify rego syntax
kubectl describe constrainttemplate <name>
```

### Issue: Violations not showing in audit

**Solution**:
```bash
# Check audit interval (default 60s)
kubectl get config -n gatekeeper-system config -o yaml

# Check audit logs
kubectl logs -n gatekeeper-system -l control-plane=audit-controller
```

---

## Key Takeaways

1. OPA Gatekeeper provides powerful policy enforcement for Kubernetes
2. ConstraintTemplates define reusable policy logic using Rego
3. Constraints apply templates with specific parameters
4. Policies can block, warn, or audit non-compliant resources
5. Audit mode helps identify existing violations
6. Test policies thoroughly before production enforcement
7. Clear violation messages improve user experience
8. Regular policy reviews ensure continued effectiveness

---

## Exercise 7: Alternative Approach - Native CEL Validation (K8s 1.25+)

### Understanding Native CEL Validation

Starting with Kubernetes 1.25, you can use **Common Expression Language (CEL)** for admission control without installing external controllers like OPA Gatekeeper. CEL validation is built directly into the Kubernetes API server.

### What is CEL?

**Common Expression Language (CEL)** is a simple expression language that:
- Is built into Kubernetes 1.25+
- Provides lightweight validation rules
- Requires no external dependencies
- Offers fast evaluation performance
- Uses familiar syntax (similar to JavaScript/Go)

### When to Use OPA Gatekeeper vs Native CEL

| Feature | OPA Gatekeeper | Native CEL Validation |
|---------|---------------|---------------------|
| **Installation** | External CRDs + Controller | Built into K8s 1.25+ |
| **Language** | Rego | CEL (Common Expression Language) |
| **Complexity** | Handles complex policies | Best for simple validations |
| **Performance** | Slight overhead | Native, lightweight |
| **Learning Curve** | Steeper (Rego) | Easier (CEL expressions) |
| **Policy Reusability** | Excellent (templates) | Good (policies) |
| **Ecosystem** | Rich policy library | Growing |
| **Audit Mode** | Built-in audit controller | Manual implementation |

### When to Use OPA Gatekeeper

- Complex policy logic requiring advanced features
- Need for policy-as-code with version control
- Preference for Rego language
- Require audit mode for existing resources
- Want to leverage existing Gatekeeper policy library
- Need centralized policy management

### When to Use Native CEL

- Simple validation rules
- Prefer native Kubernetes features
- Want minimal dependencies
- Need optimal performance
- Kubernetes 1.25+ environment
- Straightforward admission control

### Step 1: Understanding CEL Syntax

CEL expressions are simple and intuitive:

```cel
// Check if a label exists
has(object.metadata.labels.app)

// Check a value
object.spec.replicas <= 10

// String matching
object.metadata.name.startsWith('prod-')

// Logical operations
has(object.metadata.labels.env) && object.metadata.labels.env in ['dev', 'staging', 'prod']

// Array operations
object.spec.containers.all(c, has(c.resources.limits.memory))
```

### Step 2: Review the CEL Validation Policy

Navigate to the security labs directory:

```bash
cd k8s/labs/security
```

Let's examine the `cel-validation.yaml` file that enforces required labels:

```yaml
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingAdmissionPolicy
metadata:
  name: "require-labels"
spec:
  failurePolicy: Fail
  matchConstraints:
    resourceRules:
    - apiGroups: ["apps"]
      apiVersions: ["v1"]
      operations: ["CREATE", "UPDATE"]
      resources: ["deployments"]
  validations:
  - expression: "has(object.metadata.labels.app)"
    message: "Deployment must have 'app' label"
  - expression: "has(object.metadata.labels.env)"
    message: "Deployment must have 'env' label"
---
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingAdmissionPolicyBinding
metadata:
  name: "require-labels-binding"
spec:
  policyName: "require-labels"
  validationActions: ["Deny"]
  matchResources:
    namespaceSelector:
      matchLabels:
        cel-validation: "enabled"
```

**Understanding the CEL Policy:**

**ValidatingAdmissionPolicy:**
- `matchConstraints.resourceRules` - Applies to Deployments in apps/v1
- `validations` - List of CEL expressions to evaluate
- `expression` - CEL expression that must evaluate to true
- `message` - Error message shown when validation fails

**ValidatingAdmissionPolicyBinding:**
- `policyName` - References the policy to bind
- `validationActions: ["Deny"]` - Block non-compliant resources
- `matchResources.namespaceSelector` - Only applies to namespaces with label `cel-validation: enabled`

### Step 3: Apply the CEL Policy

First, create a namespace with CEL validation enabled:

```bash
kubectl create namespace cel-demo
kubectl label namespace cel-demo cel-validation=enabled
```

Apply the CEL validation policy:

```bash
kubectl apply -f cel-validation.yaml
```

Expected output:
```
validatingadmissionpolicy.admissionregistration.k8s.io/require-labels created
validatingadmissionpolicybinding.admissionregistration.k8s.io/require-labels-binding created
```

Verify the policy:

```bash
kubectl get validatingadmissionpolicy
```

Expected output:
```
NAME              AGE
require-labels    10s
```

### Step 4: Test with Non-Compliant Deployment

Create a deployment without required labels:

```bash
kubectl create deployment test-app --image=nginx:alpine -n cel-demo
```

Expected output (SHOULD BE DENIED):
```
Error from server (Forbidden): admission webhook "validatingadmissionpolicy.k8s.io" denied the request: ValidatingAdmissionPolicy 'require-labels' with binding 'require-labels-binding' denied request: Deployment must have 'app' label
```

**Success!** CEL validation blocked the non-compliant deployment.

### Step 5: Test with Compliant Deployment

Create a compliant deployment:

```bash
cat > cel-compliant-deployment.yaml <<'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: compliant-app
  namespace: cel-demo
  labels:
    app: nginx
    env: production
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
        image: nginx:alpine
EOF
```

Apply the compliant deployment:

```bash
kubectl apply -f cel-compliant-deployment.yaml
```

Expected output (SHOULD SUCCEED):
```
deployment.apps/compliant-app created
```

Verify the deployment:

```bash
kubectl get deployment compliant-app -n cel-demo --show-labels
```

Expected output:
```
NAME            READY   UP-TO-DATE   AVAILABLE   AGE   LABELS
compliant-app   2/2     2            2           20s   app=nginx,env=production
```

**Success!** The compliant deployment was created without issues.

### Step 6: Advanced CEL Example - Container Resource Limits

Create a more advanced CEL policy for container resource limits:

```bash
cat > cel-resource-limits.yaml <<'EOF'
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingAdmissionPolicy
metadata:
  name: "require-resource-limits"
spec:
  failurePolicy: Fail
  matchConstraints:
    resourceRules:
    - apiGroups: ["apps"]
      apiVersions: ["v1"]
      operations: ["CREATE", "UPDATE"]
      resources: ["deployments"]
  validations:
  - expression: "object.spec.template.spec.containers.all(c, has(c.resources.limits.memory))"
    message: "All containers must have memory limits"
  - expression: "object.spec.template.spec.containers.all(c, has(c.resources.limits.cpu))"
    message: "All containers must have CPU limits"
  - expression: "object.spec.replicas <= 10"
    message: "Deployment cannot have more than 10 replicas"
---
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingAdmissionPolicyBinding
metadata:
  name: "require-resource-limits-binding"
spec:
  policyName: "require-resource-limits"
  validationActions: ["Deny"]
  matchResources:
    namespaceSelector:
      matchLabels:
        cel-validation: "enabled"
EOF
```

Apply the advanced policy:

```bash
kubectl apply -f cel-resource-limits.yaml
```

Test with a deployment missing resource limits:

```bash
cat > no-limits-deployment.yaml <<'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: no-limits
  namespace: cel-demo
  labels:
    app: test
    env: dev
spec:
  replicas: 2
  selector:
    matchLabels:
      app: test
  template:
    metadata:
      labels:
        app: test
    spec:
      containers:
      - name: nginx
        image: nginx:alpine
EOF

kubectl apply -f no-limits-deployment.yaml
```

Expected output (SHOULD BE DENIED):
```
Error from server (Forbidden): admission webhook "validatingadmissionpolicy.k8s.io" denied the request: ValidatingAdmissionPolicy 'require-resource-limits' with binding 'require-resource-limits-binding' denied request: All containers must have memory limits
```

### Step 7: CEL Policy Cleanup

Delete the test resources:

```bash
kubectl delete deployment compliant-app -n cel-demo --ignore-not-found
kubectl delete namespace cel-demo
rm -f cel-compliant-deployment.yaml
rm -f cel-resource-limits.yaml
rm -f no-limits-deployment.yaml
```

Delete the CEL policies:

```bash
kubectl delete validatingadmissionpolicybinding require-labels-binding
kubectl delete validatingadmissionpolicybinding require-resource-limits-binding --ignore-not-found
kubectl delete validatingadmissionpolicy require-labels
kubectl delete validatingadmissionpolicy require-resource-limits --ignore-not-found
```

### CEL vs Gatekeeper Comparison Summary

**Both approaches are valid** for Kubernetes admission control. Your choice depends on:

**Choose OPA Gatekeeper if you need:**
- Complex policy logic with advanced features
- Centralized policy management across clusters
- Audit mode for existing resources
- Rich policy library and ecosystem
- Policy-as-code with versioning

**Choose Native CEL if you prefer:**
- Simple, straightforward validations
- Native Kubernetes features without external dependencies
- Minimal operational overhead
- Optimal performance
- Kubernetes 1.25+ environment

Many organizations use **both** approaches:
- CEL for simple, common validations
- Gatekeeper for complex, organization-specific policies

---

## Additional Reading

- [OPA Gatekeeper Documentation](https://open-policy-agent.github.io/gatekeeper/)
- [Rego Policy Language](https://www.openpolicyagent.org/docs/latest/policy-language/)
- [Gatekeeper Policy Library](https://github.com/open-policy-agent/gatekeeper-library)
- [OPA Playground](https://play.openpolicyagent.org/)
- [Kubernetes CEL Documentation](https://kubernetes.io/docs/reference/using-api/cel/)
- [ValidatingAdmissionPolicy Guide](https://kubernetes.io/docs/reference/access-authn-authz/validating-admission-policy/)

---

**Lab Created**: March 2026
**Compatible with**: Kubernetes 1.24+, Gatekeeper v3.17+, CEL validation requires K8s 1.25+
**Based on**: gatekeeper-scenario1.md, labs/security/gatekeeper/
**Tested on**: kubeadm clusters
**Estimated Time**: 90-110 minutes
