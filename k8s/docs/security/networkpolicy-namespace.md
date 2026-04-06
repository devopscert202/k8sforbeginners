### **Namespace-Level Traffic Isolation Using NetworkPolicy**

This document explains how Kubernetes **NetworkPolicy** can isolate ingress so Pods accept traffic from workloads in the **same namespace** while blocking ingress from **other namespaces** (when you apply a matching policy in each namespace you want to protect).

---

> **Related:** [NetworkPolicy Basics](./networkpolicy.md) | [Kubernetes Hardening Guide](./k8s-hardening.md)

### **Background: Default Kubernetes Behavior**

1. **Default Behavior Without NetworkPolicy**:
   - **Ingress**: All Pods can accept traffic from any source, whether within the same namespace or a different namespace.
   - **Egress**: All Pods can send traffic to any destination.

2. **Inter-namespace Traffic**:
   - By default, Pods in **namespace A** can freely communicate with Pods in **namespace B** unless a NetworkPolicy selects those Pods and restricts ingress or egress.

3. **Purpose of This Pattern**:
   - A **same-namespace-only** ingress rule helps achieve **namespace isolation**: workloads only trust peers that share their namespace, which limits lateral movement from other teams or environments.

---

### **Objective (conceptual)**

- Understand how a policy that pairs an empty `podSelector` with `from.podSelector: {}` limits **ingress sources** to Pods in the same namespace.
- Contrast default open cluster networking with **deny-by-implication** semantics: once a Pod is selected by a policy, only rules listed in that policy apply to the traffic types the policy declares.

---

### **Prerequisites (conceptual)**

1. A Kubernetes cluster with a **CNI that enforces NetworkPolicy** (for example Calico, Cilium, or Kind with a compatible CNI).
2. Awareness that policies are **additive per Pod**: if multiple policies select a Pod, traffic must satisfy **all** of them for each direction (ingress/egress) that any policy defines.

---

### **Illustrative policy: deny ingress from other namespaces**

The following policy applies to **all Pods in its namespace** (`podSelector: {}`) and allows ingress **only from Pods in that same namespace** (`from: - podSelector: {}`). It does not define egress rules; egress behavior depends on whether other policies exist and on your CNI defaults.

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  namespace: default
  name: deny-from-other-namespaces
spec:
  podSelector:
    matchLabels: {}
  ingress:
  - from:
      - podSelector: {}
```

To get symmetric isolation, apply an equivalent policy in **each** namespace that should be isolated. Traffic from another namespace will not match `podSelector: {}` in the **target** namespace’s rule set (namespace boundaries apply to empty pod selectors).

---

### **Behavior comparison**

| **Scenario**                       | **Without NetworkPolicy** | **With same-namespace ingress policy** |
|-------------------------------------|---------------------------|------------------------------------------|
| Pod in `default` → Pod in `default` | Allowed                   | Allowed                                  |
| Pod in `default` → Pod in `test`    | Allowed                   | Allowed (unless `test` has its own restrictions) |
| Pod in `test` → Pod in `default`    | Allowed                   | Denied when policy protects `default`    |
| Pod in `test` → Pod in `test`       | Allowed                   | Allowed if `test` uses the same pattern  |

Exact results depend on which namespaces have policies and whether Services, NodePort, or external traffic need additional `ingress.from` clauses (namespace selectors, IP blocks, etc.).

---

### **How the policy works**

1. **Default behavior**: Without a NetworkPolicy, Pods are not restricted by Kubernetes’ policy objects (the CNI still routes traffic normally).

2. **With `deny-from-other-namespaces` (pattern above)**:
   - Selected Pods can accept ingress **only** from Pod IPs in the **same namespace** that the policy also allows—here, any Pod in that namespace because both selectors are empty within the namespace.
   - Ingress from Pods in **other namespaces** does not satisfy `from.podSelector: {}` in the target namespace’s policy plane, so it is dropped for selected Pods.

---

### **Conclusion**

This pattern demonstrates **namespace-scoped trust**: fine-grained control over who may connect to workloads without listing every remote Pod by label. Combine with explicit egress policies, DNS allowances, and observability when hardening production clusters.

---

## Hands-On Labs

Practice these concepts with guided lab exercises:

| Lab | Description |
|-----|-------------|
| [Lab 13: Advanced Network Policies - Namespace Isolation](../../labmanuals/lab13-sec-network-policies.md) | Create and verify NetworkPolicies on a cluster with a supporting CNI. |
| [Lab 57: Network Policies — Pod and Application Traffic Control](../../labmanuals/lab57-sec-network-policy-advanced.md) | Explore richer ingress/egress and application-level rules. |
