### **NetworkPolicy: Allow Lists and Deny-All Ingress**

This document introduces **Kubernetes NetworkPolicy**: what it controls, when to use it, how it depends on your **CNI**, and how **allow-list** versus **empty ingress** rules change Pod reachability.

---

> **Related:** [Namespace-Scoped Network Isolation](./networkpolicy-namespace.md) | [Kubernetes Hardening Guide](./k8s-hardening.md) (includes NetworkPolicy in the hardening checklist)

### **What is a NetworkPolicy?**

A **NetworkPolicy** defines rules for **ingress** and/or **egress** for Pods that match a `podSelector` (and optional `namespaceSelector`). By default, Kubernetes does not restrict Pod-to-Pod traffic; without policies, traffic is generally allowed subject to CNI and cloud networking. Once you attach policies to selected Pods, only traffic matching the declared rules is permitted for the directions the policy covers.

---

### **Use Cases for NetworkPolicy**

1. **Application Isolation**: Ensure one application cannot unintentionally communicate with another.
2. **Compliance**: Enforce network segmentation for regulatory or internal standards.
3. **Traffic Restriction**: Limit sources to trusted Pods, namespaces, or IP blocks.
4. **Improved Security**: Reduce exposure of sensitive APIs or data stores.

---

### **Dependencies: Container Networking Interface (CNI)**

NetworkPolicies are **implemented by the CNI** (and related datapath), not by the Kubernetes API server alone. Examples:

1. **Calico**: Broad NetworkPolicy support; common in production.
2. **Flannel**: Does not enforce NetworkPolicy by itself; often paired with another policy engine.
3. **Cilium**: BPF-based enforcement and rich L3/L4/L7 options.
4. **Weave Net**: Basic NetworkPolicy support suitable for smaller clusters.

Always confirm in your environment that the installed CNI **enforces** policies before relying on them for security.

---

### **Pattern: Allow ingress only from matching Pods**

The following policy selects Pods with `app: k8slearning` and allows ingress **only** from Pods in the same namespace that also have `app: k8slearning`. Other sources are not listed and therefore cannot reach those Pods on ingress (for this policy’s selected set).

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: k8slearning-allow-ingress
spec:
  podSelector:
    matchLabels:
      app: k8slearning
  ingress:
  - from:
      - podSelector:
          matchLabels:
            app: k8slearning
```

---

### **Pattern: Deny all ingress to selected Pods**

An **empty `ingress` list** means **no ingress rules** are defined for the selected Pods. For implementations that interpret this as “no ingress allowed,” **all ingress to matching Pods is blocked** unless another policy also applies and permits traffic (multiple policies can stack).

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: k8slearning-deny-all
spec:
  podSelector:
    matchLabels:
      app: k8slearning
  ingress: []
```

---

### **Allow vs deny-all (conceptual)**

- **Allow-list policy**: Only explicitly described `from` (and ports) are permitted; useful for microservice “talks only to X.”
- **Deny-all ingress**: A hard stop for inbound connections to labeled Pods—pair with Services, health checks, and mesh or CNI features so you do not break required probes or control-plane paths.

---

### **Summary**

- **NetworkPolicies** express intent for Pod traffic; the **CNI** enforces them.
- **Label selectors** and **namespace selectors** determine which Pods and which remote endpoints participate in a rule.
- Combining **default-deny** patterns with **narrow allows** is a common zero-trust style approach in Kubernetes.

---

## Hands-On Labs

Practice these concepts with guided lab exercises:

| Lab | Description |
|-----|-------------|
| [Lab 13: Advanced Network Policies - Namespace Isolation](../../labmanuals/lab13-sec-network-policies.md) | Install or verify a policy-capable CNI and exercise allow/deny scenarios. |
| [Lab 57: Network Policies — Pod and Application Traffic Control](../../labmanuals/lab57-sec-network-policy-advanced.md) | Deepen ingress/egress patterns and troubleshooting. |
