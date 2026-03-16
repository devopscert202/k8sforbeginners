# Lab 43: CRD Quick Reference

## Common Commands

### CRD Management
```bash
# List all CRDs in the cluster
kubectl get crds

# Describe a CRD
kubectl describe crd websites.example.com

# View CRD YAML
kubectl get crd websites.example.com -o yaml

# Delete a CRD (deletes all instances too!)
kubectl delete crd websites.example.com

# Check API resources
kubectl api-resources | grep website
```

### Custom Resource Operations
```bash
# Create a custom resource
kubectl apply -f website-instance-1.yaml

# List all website resources
kubectl get websites
kubectl get ws  # Using short name

# Get specific website
kubectl get website corporate-site

# Describe a website
kubectl describe website corporate-site

# View as YAML
kubectl get website corporate-site -o yaml

# Edit a website
kubectl edit website corporate-site

# Delete a website
kubectl delete website corporate-site

# Delete all websites
kubectl delete websites --all
```

### Validation Testing
```bash
# Test with invalid resource (should fail)
kubectl apply -f website-instance-invalid.yaml

# Dry-run to test validation
kubectl apply -f website-instance-1.yaml --dry-run=server
```

### Status Operations
```bash
# Update status subresource
kubectl patch website corporate-site --subresource=status --type=merge -p '
{
  "status": {
    "phase": "Running",
    "availableReplicas": 3,
    "url": "http://www.example.com"
  }
}'

# View just the status
kubectl get website corporate-site -o jsonpath='{.status}' | jq .
```

### Debugging
```bash
# Check CRD structure
kubectl get crd websites.example.com -o jsonpath='{.spec.versions[0].schema}' | jq .

# Check if status subresource is enabled
kubectl get crd websites.example.com -o jsonpath='{.spec.versions[0].subresources}'

# View all websites across namespaces
kubectl get websites --all-namespaces

# Watch for changes
kubectl get websites -w
```

## Lab Exercise Flow

### Exercise 2: Basic CRD
```bash
cd k8s/labs/advanced/crd
kubectl apply -f website-crd.yaml
kubectl get crds | grep website
```

### Exercise 3: Create Instances
```bash
kubectl apply -f website-instance-1.yaml
kubectl apply -f website-instance-2.yaml
kubectl get websites
kubectl describe website corporate-site
```

### Exercise 4: Add Validation
```bash
kubectl apply -f website-crd-validated.yaml
kubectl apply -f website-instance-invalid.yaml  # Should fail
```

### Exercise 5: Status Subresource
```bash
kubectl apply -f website-crd-with-status.yaml
kubectl apply -f website-instance-1.yaml
kubectl patch website corporate-site --subresource=status --type=merge -p '{"status":{"phase":"Running","availableReplicas":3}}'
kubectl get website corporate-site -o yaml
```

## Troubleshooting

### CRD Won't Apply
```bash
# Check YAML syntax
kubectl apply -f website-crd.yaml --dry-run=server

# Check for errors
kubectl apply -f website-crd.yaml -v=8
```

### CRD Stuck Deleting
```bash
# Check for remaining instances
kubectl get websites --all-namespaces

# Force delete instances
kubectl delete websites --all --force --grace-period=0

# Remove finalizers if stuck
kubectl patch crd websites.example.com -p '{"metadata":{"finalizers":[]}}' --type=merge
```

### Custom Resource Invalid
```bash
# Check CRD schema
kubectl get crd websites.example.com -o yaml | grep -A 50 openAPIV3Schema

# Verify API version
kubectl api-versions | grep example.com
```

## Useful JSONPath Queries

```bash
# Get all domains
kubectl get websites -o jsonpath='{.items[*].spec.domain}'

# Get website with specific label
kubectl get websites -l app=corporate

# Get all replicas
kubectl get websites -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.replicas}{"\n"}{end}'

# Get status phase
kubectl get websites -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.phase}{"\n"}{end}'
```

## Validation Examples

### Valid Website
```yaml
apiVersion: example.com/v1
kind: Website
metadata:
  name: valid-site
spec:
  domain: example.com
  framework: nginx
  replicas: 3
```

### Invalid Examples
```yaml
# Empty domain (fails minLength)
domain: ""

# Invalid framework (not in enum)
framework: "tomcat"

# Too many replicas (exceeds maximum)
replicas: 15

# Too few replicas (below minimum)
replicas: 0

# Invalid domain pattern
domain: "INVALID_DOMAIN"
```

## Production Tips

1. **Always validate CRDs** before applying to production
2. **Use meaningful names** for CRDs and instances
3. **Add descriptions** to all fields for documentation
4. **Version properly** (start with v1alpha1 for experimental)
5. **Test validation** with invalid resources
6. **Enable status** if you plan to build controllers
7. **Use short names** for easier kubectl commands
8. **Document examples** in CRD annotations
9. **Plan for migration** when changing schemas
10. **Monitor etcd size** - CRDs are stored in etcd

## CKA Exam Tips

For the CKA exam, know how to:
- Create a basic CRD from scratch
- Create custom resource instances
- Use kubectl with custom resources
- Understand scope (Namespaced vs Cluster)
- Add basic validation rules
- Troubleshoot CRD issues

You will NOT need to:
- Write controllers/operators
- Implement complex validation
- Handle API versioning
- Create admission webhooks

## Quick Lab Cleanup
```bash
# Remove everything
kubectl delete websites --all
kubectl delete crd websites.example.com

# Verify
kubectl get crds | grep website
kubectl get websites 2>&1  # Should error
```

## Next Steps

1. Complete all exercises in the main lab manual
2. Try creating your own CRD for a different use case
3. Explore existing CRDs in popular operators (Prometheus, Istio)
4. Learn Kubebuilder if interested in controller development
5. Study operator patterns and best practices
