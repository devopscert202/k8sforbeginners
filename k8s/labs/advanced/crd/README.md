# Lab 43: Custom Resource Definitions (CRDs)

This directory contains YAML files for Lab 43 on Custom Resource Definitions.

## Files Overview

### CRD Definitions

- **website-crd.yaml** - Basic CRD definition without validation
- **website-crd-validated.yaml** - CRD with OpenAPI v3 schema validation
- **website-crd-with-status.yaml** - CRD with status subresource enabled
- **website-production-grade.yaml** - Production-grade CRD with all features

### Custom Resource Instances

- **website-instance-1.yaml** - Corporate website example (nginx, 3 replicas)
- **website-instance-2.yaml** - Blog website example (nodejs, 2 replicas)
- **website-instance-invalid.yaml** - Invalid resource for testing validation

## Quick Start

1. Create the basic CRD:
```bash
kubectl apply -f website-crd.yaml
```

2. Create a website instance:
```bash
kubectl apply -f website-instance-1.yaml
```

3. Verify:
```bash
kubectl get websites
kubectl describe website corporate-site
```

## Lab Progression

Follow these files in order as you progress through the lab:

1. Start with `website-crd.yaml` (Exercise 2)
2. Use `website-instance-1.yaml` and `website-instance-2.yaml` (Exercise 3)
3. Upgrade to `website-crd-validated.yaml` (Exercise 4)
4. Test validation with `website-instance-invalid.yaml` (Exercise 4)
5. Enable status with `website-crd-with-status.yaml` (Exercise 5)
6. Reference `website-production-grade.yaml` for advanced features (Appendix)

## Cleanup

Remove all resources:
```bash
kubectl delete websites --all
kubectl delete crd websites.example.com
```

## Documentation

Refer to the main lab manual: `k8s/labmanuals/lab43-adv-custom-resource-definitions.md`
