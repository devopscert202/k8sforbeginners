# Lab 43: Custom Resource Definitions (Optional Advanced Lab)

## Overview

**IMPORTANT: This is an OPTIONAL ADVANCED LAB** - This lab covers Custom Resource Definitions (CRDs), an advanced Kubernetes feature that extends the Kubernetes API with your own custom resources. While CRDs are part of the CKA exam curriculum, implementing them in production requires careful design and consideration.

Custom Resource Definitions allow you to create your own Kubernetes resources beyond the built-in ones like Pods, Services, and Deployments. This is the foundation for the Operator pattern, which powers many cloud-native applications like Prometheus, Istio, and ArgoCD.

**Who should complete this lab:**
- Those preparing for the CKA certification (CRDs are in the exam)
- Platform engineers building internal developer platforms
- Those working with Kubernetes Operators
- Advanced learners interested in extending Kubernetes

**You can skip this lab if:**
- You're just starting with Kubernetes
- You only need to consume existing Kubernetes resources
- You're not building custom controllers or operators

## Prerequisites

- A running Kubernetes cluster (Minikube, Kind, or any K8s cluster)
- `kubectl` CLI tool installed and configured
- Completion of Labs 01-10 recommended (basic Kubernetes knowledge)
- Understanding of Kubernetes API and resources
- Cluster admin permissions (CRDs are cluster-scoped)

## Learning Objectives

By the end of this lab, you will be able to:
- Understand what Custom Resource Definitions are and their purpose
- Explain when to use CRDs vs built-in Kubernetes resources
- Create a custom resource definition with proper structure
- Create and manage custom resource instances using kubectl
- Implement validation rules using OpenAPI v3 schema
- Use status subresources to separate spec from status
- Understand the operator pattern conceptually
- Recognize real-world CRD use cases

---

## What are Custom Resource Definitions?

### Introduction

A **Custom Resource Definition (CRD)** is a Kubernetes extension mechanism that allows you to define your own resource types. Once a CRD is created, you can use `kubectl` to create and manage instances of that custom resource just like built-in resources.

### Key Concepts

- **Custom Resource (CR)**: An instance of a CRD (like a Pod is an instance of the Pod resource type)
- **Custom Resource Definition (CRD)**: The schema/blueprint that defines a custom resource type
- **API Extension**: CRDs extend the Kubernetes API without modifying core Kubernetes code
- **Controller/Operator**: Optional software that watches custom resources and performs actions

### CRD vs ConfigMap

| Feature | CRD | ConfigMap |
|---------|-----|-----------|
| **Purpose** | Define new resource types | Store configuration data |
| **API Integration** | Full kubectl support | Built-in resource |
| **Validation** | OpenAPI schema validation | Limited validation |
| **Versioning** | Multiple API versions | Single resource |
| **Status** | Separate status subresource | No status concept |
| **Use Case** | Application definitions, operators | Config files, env vars |

### Real-World Examples

| Tool/Platform | CRD Purpose |
|---------------|-------------|
| **Prometheus Operator** | `ServiceMonitor`, `PrometheusRule` - Define monitoring targets |
| **Istio** | `VirtualService`, `Gateway` - Define service mesh routing |
| **ArgoCD** | `Application` - Define GitOps applications |
| **Cert-Manager** | `Certificate`, `Issuer` - Manage TLS certificates |
| **Crossplane** | `Database`, `Bucket` - Provision cloud infrastructure |
| **Velero** | `Backup`, `Restore` - Define backup schedules |

---

## Exercise 1: Understanding CRDs in Your Cluster

### Step 1: List Existing CRDs

Check if your cluster has any CRDs installed:

```bash
kubectl get crds
```

On a fresh cluster, you might see no CRDs or just a few default ones. On clusters with additional tools, you'll see many:

```
NAME                                  CREATED AT
certificates.cert-manager.io          2026-03-10T10:15:30Z
issuers.cert-manager.io               2026-03-10T10:15:30Z
```

### Step 2: Examine a CRD (If Available)

If you have any CRDs, inspect one:

```bash
# Get details about a CRD
kubectl describe crd <crd-name>

# View the full CRD YAML
kubectl get crd <crd-name> -o yaml
```

Notice the structure - this is what we'll create in the next exercise.

### Step 3: Check API Resources

List all API resources, including custom ones:

```bash
kubectl api-resources | grep -i custom
```

This shows all resource types your cluster understands.

---

## Exercise 2: Create Your First CRD

### Step 1: Understand the Use Case

We'll create a `Website` custom resource that represents a web application deployment. This is a simplified example that's easy to understand but demonstrates CRD concepts.

**Scenario**: You want developers to deploy websites by simply defining:
- Domain name
- Web framework (nginx, apache, nodejs)
- Number of replicas

Instead of creating Deployments, Services, and Ingresses manually, developers just create a `Website` resource.

### Step 2: Review the CRD Manifest

Navigate to the CRD labs directory:

```bash
cd k8s/labs/advanced/crd
```

Examine the `website-crd.yaml` file:

```yaml
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: websites.example.com
spec:
  group: example.com
  names:
    kind: Website
    listKind: WebsiteList
    plural: websites
    singular: website
    shortNames:
    - ws
  scope: Namespaced
  versions:
  - name: v1
    served: true
    storage: true
    schema:
      openAPIV3Schema:
        type: object
        properties:
          spec:
            type: object
            properties:
              domain:
                type: string
              framework:
                type: string
              replicas:
                type: integer
                minimum: 1
```

**Understanding the CRD Structure:**

- `apiVersion: apiextensions.k8s.io/v1` - CRD API group
- `metadata.name` - Must be `<plural>.<group>` format
- `spec.group` - API group for your custom resources (use your domain)
- `spec.names` - How to refer to this resource
  - `kind: Website` - Resource type name (capitalized, singular)
  - `plural: websites` - Plural form for API URLs
  - `singular: website` - Singular form
  - `shortNames` - Aliases (like `po` for pods)
- `spec.scope` - `Namespaced` or `Cluster` level
- `spec.versions` - API versions (start with v1)
  - `served: true` - Accept API requests for this version
  - `storage: true` - Store resources in this version
  - `schema` - Defines the structure of the custom resource

### Step 3: Create the CRD

Apply the CRD to your cluster:

```bash
kubectl apply -f website-crd.yaml
```

Expected output:
```
customresourcedefinition.apiextensions.k8s.io/websites.example.com created
```

### Step 4: Verify CRD Creation

Check that the CRD exists:

```bash
kubectl get crds | grep website
```

Output:
```
websites.example.com   2026-03-16T10:30:00Z
```

Get detailed information:

```bash
kubectl describe crd websites.example.com
```

Verify the new API resource:

```bash
kubectl api-resources | grep website
```

Output:
```
websites    ws    example.com/v1    true    Website
```

Notice you can now use `kubectl get websites` or `kubectl get ws`!

---

## Exercise 3: Create Custom Resource Instances

### Step 1: Review a Website Instance

Examine the `website-instance-1.yaml` file:

```yaml
apiVersion: example.com/v1
kind: Website
metadata:
  name: corporate-site
  namespace: default
spec:
  domain: www.example.com
  framework: nginx
  replicas: 3
```

**Understanding the Custom Resource:**

- `apiVersion: example.com/v1` - Uses the group and version from the CRD
- `kind: Website` - The resource type we defined
- `metadata` - Standard Kubernetes metadata (name, namespace, labels)
- `spec` - Custom fields we defined in the CRD schema

### Step 2: Create the Website Resource

Apply the custom resource:

```bash
kubectl apply -f website-instance-1.yaml
```

Expected output:
```
website.example.com/corporate-site created
```

### Step 3: List Custom Resources

Use kubectl like any other resource:

```bash
# Full command
kubectl get websites

# Using short name
kubectl get ws

# With more details
kubectl get websites -o wide

# YAML output
kubectl get website corporate-site -o yaml
```

Expected output:
```
NAME             AGE
corporate-site   10s
```

### Step 4: Describe the Custom Resource

```bash
kubectl describe website corporate-site
```

Output:
```
Name:         corporate-site
Namespace:    default
API Version:  example.com/v1
Kind:         Website
Metadata:
  ...
Spec:
  Domain:      www.example.com
  Framework:   nginx
  Replicas:    3
```

### Step 5: Create Multiple Instances

Apply another website:

```bash
kubectl apply -f website-instance-2.yaml
```

The `website-instance-2.yaml` file:

```yaml
apiVersion: example.com/v1
kind: Website
metadata:
  name: blog-site
  namespace: default
spec:
  domain: blog.example.com
  framework: nodejs
  replicas: 2
```

List all websites:

```bash
kubectl get websites
```

Output:
```
NAME             AGE
blog-site        5s
corporate-site   2m
```

### Step 6: Update a Custom Resource

Edit the resource:

```bash
kubectl edit website corporate-site
```

Or apply changes from a file:

```bash
# Modify website-instance-1.yaml (change replicas to 5)
kubectl apply -f website-instance-1.yaml
```

### Step 7: Delete a Custom Resource

```bash
kubectl delete website blog-site

# Or using the file
kubectl delete -f website-instance-2.yaml
```

**Important Note**: Deleting a custom resource just removes the data from etcd. Without a controller watching these resources, nothing actually happens to create or delete workloads. Controllers are covered in Exercise 6.

---

## Exercise 4: Adding Validation Rules

### Step 1: Why Validation Matters

Without validation, users could create invalid resources:
- Empty domain names
- Invalid framework names
- Zero or negative replicas

Let's add validation using OpenAPI v3 schema.

### Step 2: Review the Validated CRD

Examine the `website-crd-validated.yaml` file:

```yaml
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: websites.example.com
spec:
  group: example.com
  names:
    kind: Website
    listKind: WebsiteList
    plural: websites
    singular: website
    shortNames:
    - ws
  scope: Namespaced
  versions:
  - name: v1
    served: true
    storage: true
    schema:
      openAPIV3Schema:
        type: object
        required:
        - spec
        properties:
          spec:
            type: object
            required:
            - domain
            - framework
            properties:
              domain:
                type: string
                minLength: 1
                pattern: '^[a-z0-9]([-a-z0-9]*[a-z0-9])?(\.[a-z0-9]([-a-z0-9]*[a-z0-9])?)*$'
                description: "Valid domain name"
              framework:
                type: string
                enum:
                - nginx
                - apache
                - nodejs
                - python
                default: nginx
                description: "Web server framework"
              replicas:
                type: integer
                minimum: 1
                maximum: 10
                default: 1
                description: "Number of replicas (1-10)"
```

**New Validation Features:**

- `required` - Fields that must be present
- `minLength` - Minimum string length
- `pattern` - Regex validation for domain names
- `enum` - Allowed values only
- `minimum/maximum` - Numeric bounds
- `default` - Default value if not specified
- `description` - Field documentation

### Step 3: Update the CRD

Apply the updated CRD:

```bash
kubectl apply -f website-crd-validated.yaml
```

Output:
```
customresourcedefinition.apiextensions.k8s.io/websites.example.com configured
```

### Step 4: Test Validation

Try to create an invalid resource:

```bash
kubectl apply -f website-instance-invalid.yaml
```

The `website-instance-invalid.yaml` file:

```yaml
apiVersion: example.com/v1
kind: Website
metadata:
  name: invalid-site
spec:
  domain: ""  # Empty domain - should fail
  framework: tomcat  # Not in enum - should fail
  replicas: 0  # Below minimum - should fail
```

Expected error:
```
Error from server (BadRequest): error when creating "website-instance-invalid.yaml":
Website in version "v1" cannot be created:
- spec.domain: Invalid value: "": spec.domain in body should be at least 1 chars long
- spec.framework: Unsupported value: "tomcat": supported values: "nginx", "apache", "nodejs", "python"
- spec.replicas: Invalid value: 0: spec.replicas in body should be greater than or equal to 1
```

### Step 5: Test Default Values

Create a minimal website:

```bash
cat <<EOF | kubectl apply -f -
apiVersion: example.com/v1
kind: Website
metadata:
  name: minimal-site
spec:
  domain: minimal.example.com
EOF
```

Check the created resource:

```bash
kubectl get website minimal-site -o yaml | grep -A 5 spec:
```

Output shows default values applied:
```yaml
spec:
  domain: minimal.example.com
  framework: nginx
  replicas: 1
```

---

## Exercise 5: Status Subresource

### Step 1: Understanding Spec vs Status

In Kubernetes resources:
- **spec** - Desired state (what you want)
- **status** - Actual state (what exists)

For example, in a Deployment:
- `spec.replicas: 3` - You want 3 replicas
- `status.availableReplicas: 2` - Currently 2 are running

Controllers update the status to reflect reality.

### Step 2: Enable Status Subresource

Create `website-crd-with-status.yaml`:

```yaml
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: websites.example.com
spec:
  group: example.com
  names:
    kind: Website
    listKind: WebsiteList
    plural: websites
    singular: website
    shortNames:
    - ws
  scope: Namespaced
  versions:
  - name: v1
    served: true
    storage: true
    subresources:
      status: {}  # Enable status subresource
    schema:
      openAPIV3Schema:
        type: object
        required:
        - spec
        properties:
          spec:
            type: object
            required:
            - domain
            - framework
            properties:
              domain:
                type: string
                minLength: 1
              framework:
                type: string
                enum:
                - nginx
                - apache
                - nodejs
                - python
                default: nginx
              replicas:
                type: integer
                minimum: 1
                maximum: 10
                default: 1
          status:
            type: object
            properties:
              phase:
                type: string
                enum:
                - Pending
                - Running
                - Failed
              availableReplicas:
                type: integer
              url:
                type: string
```

### Step 3: Apply the CRD with Status

```bash
kubectl apply -f website-crd-with-status.yaml
```

### Step 4: Create a Website Resource

```bash
kubectl apply -f website-instance-1.yaml
```

### Step 5: Manually Update Status (Simulating a Controller)

Without a controller, we can manually update the status to demonstrate:

```bash
kubectl patch website corporate-site --subresource=status --type=merge -p '
{
  "status": {
    "phase": "Running",
    "availableReplicas": 3,
    "url": "http://www.example.com"
  }
}'
```

### Step 6: View the Status

```bash
kubectl get website corporate-site -o yaml
```

Output shows both spec and status:
```yaml
spec:
  domain: www.example.com
  framework: nginx
  replicas: 3
status:
  availableReplicas: 3
  phase: Running
  url: http://www.example.com
```

**Key Points:**

- Status is updated separately from spec
- Normal `kubectl edit` cannot change status
- Only controllers (or admin tools) should update status
- This separation ensures spec is the source of truth

---

## Exercise 6: Understanding the Operator Pattern

### What is an Operator?

An **Operator** is a controller that watches custom resources and performs actions to make reality match the desired state. It's the "brain" that gives meaning to custom resources.

### Operator Components

```
┌─────────────────────────────────────────────┐
│         Kubernetes API Server                │
│                                               │
│  ┌──────────────┐       ┌─────────────────┐ │
│  │  Website CRD  │       │ Website Instance│ │
│  └──────────────┘       └─────────────────┘ │
└─────────────────┬───────────────────────────┘
                  │ Watches
                  ▼
        ┌─────────────────┐
        │ Website Operator │ (Controller)
        └────────┬─────────┘
                 │ Creates/Manages
                 ▼
    ┌────────────────────────────┐
    │  Deployment, Service, etc. │
    └────────────────────────────┘
```

### What a Website Operator Would Do

If we built a controller for our Website CRD, it would:

1. **Watch** for Website custom resources
2. **Create** a Deployment with the specified framework image
3. **Create** a Service to expose the Deployment
4. **Create** an Ingress with the specified domain
5. **Update** the status field with the URL and replica count
6. **Delete** resources when the Website is deleted

### Popular Operators in Production

| Operator | Purpose | CRDs |
|----------|---------|------|
| **Prometheus Operator** | Monitoring | ServiceMonitor, PodMonitor, PrometheusRule |
| **Istio** | Service Mesh | VirtualService, DestinationRule, Gateway |
| **Cert-Manager** | Certificate Management | Certificate, ClusterIssuer, CertificateRequest |
| **ArgoCD** | GitOps Continuous Delivery | Application, AppProject |
| **Strimzi** | Apache Kafka | Kafka, KafkaTopic, KafkaUser |
| **Elasticsearch Operator** | Elasticsearch Clusters | Elasticsearch, Kibana |
| **PostgreSQL Operator** | PostgreSQL Databases | Postgresql, PostgresqlBackup |

### Why We're Not Building a Controller

Building a production-grade controller requires:
- Go programming (or Python with Kopf)
- Understanding of Kubernetes client libraries
- Proper error handling and retry logic
- Leader election for high availability
- Testing infrastructure

This is beyond the scope of this lab. Focus on understanding:
1. How to create CRDs
2. How to use custom resources
3. What controllers conceptually do

### Learning Controller Development

If you want to build controllers/operators:

**Tools/Frameworks:**
- **Kubebuilder** - Official Go framework for building operators
- **Operator SDK** - Red Hat's operator framework
- **Kopf** - Python framework for operators
- **KUDO** - Kubernetes Universal Declarative Operator

**Learning Resources:**
- Kubernetes Official Docs: "Extend the Kubernetes API"
- Kubebuilder Book: book.kubebuilder.io
- Operator SDK Tutorial: sdk.operatorframework.io
- Sample Controllers: github.com/kubernetes/sample-controller

---

## CKA/CKAD Exam Relevance

### CKA Exam Coverage

CRDs appear in the CKA exam under "Cluster Architecture, Installation & Configuration" (25%):
- Understanding API extension mechanisms
- Creating basic CRDs
- Working with custom resources
- No controller implementation required

### What You Need to Know for CKA

1. Create a CRD with proper structure
2. Create custom resource instances
3. Use kubectl to manage custom resources
4. Understand CRD scope (Namespaced vs Cluster)
5. Know basic validation concepts

### What's NOT in CKA

- Writing controllers/operators
- Complex validation schemas
- API versioning strategies
- Custom admission webhooks
- Controller-runtime internals

---

## Real-World Use Cases

### When to Use CRDs

| Scenario | Why CRD? |
|----------|----------|
| **Internal Developer Platform** | Abstract complex Kubernetes patterns into simple resources |
| **Multi-Resource Orchestration** | One custom resource creates many K8s resources |
| **Domain-Specific Resources** | Model business concepts (Database, Application, Environment) |
| **Operator Pattern** | Automate operational knowledge |
| **API Standardization** | Consistent interface across teams |

### When NOT to Use CRDs

| Scenario | Better Alternative |
|----------|-------------------|
| **Simple Configuration** | Use ConfigMaps or Secrets |
| **Temporary Data** | Use built-in resources |
| **No Automation Needed** | Use standard Helm charts |
| **Learning Basic K8s** | Master built-in resources first |
| **Simple State** | Use annotations or labels |

### CRD Design Best Practices

1. **Start Simple** - Add complexity only when needed
2. **Use Meaningful Names** - Clear, business-domain names
3. **Version Properly** - Plan for v1alpha1, v1beta1, v1
4. **Validate Everything** - Prevent invalid resources early
5. **Document Fields** - Use descriptions in schema
6. **Status Subresource** - Separate desired from actual state
7. **Default Values** - Provide sensible defaults
8. **Think About Scale** - CRDs are stored in etcd
9. **Namespace Scope** - Prefer Namespaced over Cluster scope
10. **Test Thoroughly** - Invalid CRDs can break the API

---

## Repository YAML Files

The following pre-built YAML manifests are available in the repository for this lab:

| File | Description |
|------|-------------|
| `k8s/labs/advanced/crd/website-production-grade.yaml` | Full `Website` CRD (`websites.example.com`) with OpenAPI validation, `status` and `scale` subresources, `additionalPrinterColumns`, optional `tlsEnabled` in spec, and a `status.conditions` array schema—matches the lab appendix “production-grade” example as a single apply-ready file. |

You can apply this directly:

```bash
kubectl apply -f k8s/labs/advanced/crd/website-production-grade.yaml
```

---

## Lab Cleanup

Remove all resources created in this lab:

```bash
# Delete custom resource instances
kubectl delete websites --all

# Delete the CRD (this deletes all instances too)
kubectl delete crd websites.example.com

# Verify cleanup
kubectl get crds | grep website
kubectl get websites 2>&1
```

Expected final output:
```
error: the server doesn't have a resource type "websites"
```

---

## Troubleshooting

### CRD Won't Create

**Error**: `The CustomResourceDefinition "websites.example.com" is invalid`

**Solutions**:
```bash
# Check YAML syntax
kubectl apply -f website-crd.yaml --dry-run=server

# Validate the schema
kubectl explain --api-version=apiextensions.k8s.io/v1 customresourcedefinition

# Check for naming issues (must be <plural>.<group>)
# Correct: websites.example.com
# Wrong: website.example.com (should be plural)
```

### Custom Resource Rejected

**Error**: `error validating data: unknown field "spec.domainName"`

**Solutions**:
```bash
# Check the CRD schema
kubectl get crd websites.example.com -o yaml | grep -A 50 openAPIV3Schema

# Verify field names match exactly
# Field names are case-sensitive

# Check API version matches
# apiVersion: example.com/v1 (must match CRD group and version)
```

### Cannot Delete CRD

**Error**: CRD stuck in "Terminating" state

**Solutions**:
```bash
# Check for remaining custom resource instances
kubectl get websites --all-namespaces

# Force delete instances
kubectl delete websites --all --force --grace-period=0

# Check for finalizers
kubectl get crd websites.example.com -o yaml | grep finalizers

# Remove finalizers if stuck
kubectl patch crd websites.example.com -p '{"metadata":{"finalizers":[]}}' --type=merge
```

### Validation Not Working

**Problem**: Invalid resources are accepted

**Solutions**:
```bash
# Check if validation is defined
kubectl get crd websites.example.com -o jsonpath='{.spec.versions[0].schema}'

# Update CRD with validation
kubectl apply -f website-crd-validated.yaml

# Wait for API server to reload
kubectl get crd websites.example.com -w
```

### Status Updates Not Persisting

**Problem**: Status changes are lost

**Solutions**:
```bash
# Check if status subresource is enabled
kubectl get crd websites.example.com -o jsonpath='{.spec.versions[0].subresources}'

# Should show: {"status":{}}

# Update status using --subresource flag
kubectl patch website corporate-site --subresource=status --type=merge -p '{"status":{"phase":"Running"}}'

# Don't edit status directly with kubectl edit (won't work)
```

---

## Key Takeaways

1. **CRDs extend the Kubernetes API** without modifying core Kubernetes code
2. **Custom Resources are just data** - controllers give them behavior
3. **Validation is critical** - prevent invalid resources with OpenAPI schemas
4. **Status subresource** separates desired state (spec) from actual state (status)
5. **The Operator pattern** combines CRDs with controllers for automation
6. **CRDs are in the CKA exam** - know how to create and use them
7. **Use CRDs for domain-specific resources** - not for simple configuration
8. **Popular tools use CRDs** - Prometheus, Istio, ArgoCD, Cert-Manager
9. **Design matters** - plan versioning, validation, and scope carefully
10. **Controllers are optional** - CRDs can be used for data modeling alone

---

## Additional Resources

### Official Documentation
- [Kubernetes CRD Documentation](https://kubernetes.io/docs/tasks/extend-kubernetes/custom-resources/custom-resource-definitions/)
- [API Extensions](https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/)
- [OpenAPI v3 Schema](https://kubernetes.io/docs/tasks/extend-kubernetes/custom-resources/custom-resource-definitions/#validation)

### Operator Development
- [Kubebuilder Book](https://book.kubebuilder.io/) - Build operators in Go
- [Operator SDK](https://sdk.operatorframework.io/) - Red Hat operator framework
- [Kopf](https://kopf.readthedocs.io/) - Python operators
- [Sample Controller](https://github.com/kubernetes/sample-controller) - Reference implementation

### Learning Resources
- [OperatorHub.io](https://operatorhub.io/) - Browse existing operators
- [Kubernetes Programming with Go](https://www.oreilly.com/library/view/programming-kubernetes/9781492047094/)
- [CRD Tutorial](https://github.com/kubernetes/sample-controller/blob/master/docs/controller-client-go.md)

### Tools
- [controller-runtime](https://github.com/kubernetes-sigs/controller-runtime) - Core operator libraries
- [controller-tools](https://github.com/kubernetes-sigs/controller-tools) - CRD generation tools
- [kube-openapi](https://github.com/kubernetes/kube-openapi) - OpenAPI spec generator

---

## Next Steps

- **Lab 44** (if available) - Continue with advanced topics
- **Practice CRDs** on your local cluster
- **Explore existing operators** - Install Prometheus or Cert-Manager and examine their CRDs
- **Learn Kubebuilder** - Build a simple operator for the Website CRD
- **Study for CKA** - Practice creating CRDs from memory

---

## Appendix: Complete CRD Example

Here's a production-grade CRD with all features:

```yaml
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: websites.example.com
  annotations:
    controller-gen.kubebuilder.io/version: v0.12.0
spec:
  group: example.com
  names:
    kind: Website
    listKind: WebsiteList
    plural: websites
    singular: website
    shortNames:
    - ws
  scope: Namespaced
  versions:
  - name: v1
    served: true
    storage: true
    subresources:
      status: {}
      scale:
        specReplicasPath: .spec.replicas
        statusReplicasPath: .status.replicas
    additionalPrinterColumns:
    - name: Domain
      type: string
      jsonPath: .spec.domain
    - name: Framework
      type: string
      jsonPath: .spec.framework
    - name: Replicas
      type: integer
      jsonPath: .spec.replicas
    - name: Status
      type: string
      jsonPath: .status.phase
    - name: Age
      type: date
      jsonPath: .metadata.creationTimestamp
    schema:
      openAPIV3Schema:
        description: Website is a custom resource for deploying websites
        type: object
        required:
        - spec
        properties:
          spec:
            description: WebsiteSpec defines the desired state of Website
            type: object
            required:
            - domain
            - framework
            properties:
              domain:
                type: string
                minLength: 1
                pattern: '^[a-z0-9]([-a-z0-9]*[a-z0-9])?(\.[a-z0-9]([-a-z0-9]*[a-z0-9])?)*$'
                description: Valid domain name for the website
              framework:
                type: string
                enum:
                - nginx
                - apache
                - nodejs
                - python
                default: nginx
                description: Web server framework to use
              replicas:
                type: integer
                minimum: 1
                maximum: 10
                default: 1
                description: Number of pod replicas (1-10)
              tlsEnabled:
                type: boolean
                default: false
                description: Enable TLS/HTTPS
          status:
            description: WebsiteStatus defines the observed state of Website
            type: object
            properties:
              phase:
                type: string
                enum:
                - Pending
                - Running
                - Failed
                description: Current phase of the website
              replicas:
                type: integer
                description: Total number of pod replicas
              availableReplicas:
                type: integer
                description: Number of available pod replicas
              url:
                type: string
                description: Access URL for the website
              conditions:
                type: array
                items:
                  type: object
                  required:
                  - type
                  - status
                  properties:
                    type:
                      type: string
                    status:
                      type: string
                    lastTransitionTime:
                      type: string
                      format: date-time
                    reason:
                      type: string
                    message:
                      type: string
```

This includes:
- Status subresource
- Scale subresource (for HPA)
- Additional printer columns (shown in `kubectl get`)
- Comprehensive validation
- Detailed descriptions
- Conditions array (standard status pattern)

---

**Lab Created**: March 2026
**Compatible with**: Kubernetes 1.16+ (CRD v1 API)
**CRD v1beta1**: Deprecated in 1.22, removed in 1.25 - always use v1
