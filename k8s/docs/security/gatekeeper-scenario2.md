# Enforcing Kubernetes Policies Using Gatekeeper

## Introduction

Gatekeeper is an admission controller webhook for Kubernetes that enforces policies defined using Open Policy Agent (OPA). It enables policy-based governance across a Kubernetes cluster by defining constraints and validating resource configurations.

In this tutorial, you will learn how to:
1. Install OPA Gatekeeper
2. Create and enforce constraints for resource limits on pods
3. Create and enforce constraints for namespace naming conventions
4. Validate the policies with test cases

## Prerequisites
- A running Kubernetes cluster
- `kubectl` configured to interact with the cluster
- Basic knowledge of Kubernetes objects like Pods and Namespaces

## Step 1: Install OPA Gatekeeper

Run the following command to install OPA Gatekeeper in your cluster:

```sh
kubectl apply -f https://raw.githubusercontent.com/open-policy-agent/gatekeeper/v3.17.1/deploy/gatekeeper.yaml
```

Verify that Gatekeeper is installed successfully:

```sh
kubectl get ns
kubectl get pods -n gatekeeper-system
```

## Step 2: Create a ConstraintTemplate for Pod Resource Limits

### Define the ConstraintTemplate
Create a file `resourcequota-template.yaml` and add the following content:

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

          # Check CPU limit
          limits.cpu > "500m"
          msg := sprintf("CPU limit exceeds the allowed maximum: %v", [limits.cpu])
        }

        violation[{"msg": msg}] {
          input.review.object.kind == "Pod"
          limits := input.review.object.spec.containers[_].resources.limits

          # Check memory limit
          limits.memory > "256Mi"
          msg := sprintf("Memory limit exceeds the allowed maximum: %v", [limits.memory])
        }
```

Apply the ConstraintTemplate:
```sh
kubectl apply -f resourcequota-template.yaml
```

### Define the Constraint
Create a file `resourcequota-constraint.yaml` and add:

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

Apply the constraint:
```sh
kubectl apply -f resourcequota-constraint.yaml
```

## Step 3: Test the Resource Limit Policy

### Create a Pod that Violates the Policy
Create a file `excessive-pod.yaml` and add:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: excessive-cpu-pod
spec:
  containers:
  - name: nginx
    image: nginx
    resources:
      limits:
        cpu: "600m"
        memory: "128Mi"
```

Attempt to apply the pod configuration:
```sh
kubectl apply -f excessive-pod.yaml
```
This should result in an error.

### Create a Valid Pod
Create a file `valid-pod.yaml` and add:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: valid-pod
spec:
  containers:
  - name: nginx
    image: nginx
    resources:
      limits:
        cpu: "400m"
        memory: "128Mi"
```

Apply the configuration:
```sh
kubectl apply -f valid-pod.yaml
```
This pod should be successfully created.

## Step 4: Create a ConstraintTemplate for Namespace Naming

### Define the ConstraintTemplate
Create a file `namespace-template.yaml` and add:

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

          # Check if the namespace starts with "prod-"
          not startswith(name, "prod-")
          msg := sprintf("Namespace name %v must start with 'prod-'", [name])
        }
```

Apply the ConstraintTemplate:
```sh
kubectl apply -f namespace-template.yaml
```

### Define the Constraint
Create a file `namespace-constraint.yaml` and add:

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

Apply the constraint:
```sh
kubectl apply -f namespace-constraint.yaml
```

## Step 5: Test the Namespace Naming Policy

### Create an Invalid Namespace
Create a file `invalid-namespace.yaml` and add:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: test-environment
```

Apply the configuration:
```sh
kubectl apply -f invalid-namespace.yaml
```
This should result in an error.

### Create a Valid Namespace
Create a file `valid-namespace.yaml` and add:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: prod-environment
```

Apply the configuration:
```sh
kubectl apply -f valid-namespace.yaml
```
This namespace should be successfully created.

## Conclusion
In this lab, you successfully:
- Installed OPA Gatekeeper
- Defined and enforced policies for pod resource limits
- Defined and enforced policies for namespace naming
- Validated the policies with test cases

OPA Gatekeeper provides a robust mechanism to enforce compliance and governance in Kubernetes environments. By defining policies as code, organizations can ensure security and best practices across their clusters.

