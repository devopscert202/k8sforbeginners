### **Tutorial: Namespace-Level Traffic Isolation Using NetworkPolicy**

This tutorial demonstrates how to use Kubernetes **NetworkPolicy** to block traffic from Pods in other namespaces while allowing traffic from Pods in the same namespace.

---

### **Background: Default Kubernetes Behavior**

1. **Default Behavior Without NetworkPolicy**:
   - **Ingress**: All Pods can accept traffic from any source, whether within the same namespace or a different namespace.
   - **Egress**: All Pods can send traffic to any destination.

2. **Inter-namespace Traffic**:
   - By default, Pods in **namespace A** can freely communicate with Pods in **namespace B** unless a NetworkPolicy is applied to restrict this behavior.

3. **Purpose of the Policy**:
   - This policy ensures **namespace isolation** by allowing traffic only from Pods within the same namespace, effectively blocking all ingress traffic from other namespaces.

---

### **Objective**

We will:
- Apply a NetworkPolicy to block ingress traffic from Pods in other namespaces.
- Verify communication between Pods within the same namespace and across namespaces.
- Compare default behavior with behavior after applying the policy.

---

### **Prerequisites**

1. A Kubernetes cluster is running.
2. Kubernetes CLI tool (`kubectl`) is installed.
3. A CNI plugin that supports NetworkPolicy (e.g., Calico) is installed.

---

### **Steps**

#### **1. Create Namespaces**

We will use two namespaces for this tutorial: `default` and `test`.

```bash
kubectl create namespace test
```

Verify the namespaces:
```bash
kubectl get namespaces
```

---

#### **2. Create Pods in Both Namespaces**

Create Pods and Services in each namespace:

1. **Default Namespace**:
   ```bash
   kubectl run pod1 --image=nginx --labels="app=default-app" --expose --port=80
   ```

2. **Test Namespace**:
   ```bash
   kubectl run pod2 --image=nginx --labels="app=test-app" --namespace=test --expose --port=80
   ```

Verify that both Pods and Services are running:
```bash
kubectl get pods,svc -n default
kubectl get pods,svc -n test
```

---

#### **3. Test Default Behavior**

1. **Check Connectivity From `default` to `test` Namespace**:
   ```bash
   kubectl exec pod1 -- curl pod2.test.svc.cluster.local
   ```
   **Expected Result**: The request succeeds, showing the NGINX default page.

2. **Check Connectivity Within the Same Namespace (`default`)**:
   ```bash
   kubectl exec pod1 -- curl pod1.default.svc.cluster.local
   ```
   **Expected Result**: The request succeeds.

---

#### **4. Apply the Namespace-Level NetworkPolicy**

Create a file `deny-from-other-namespaces.yaml`:
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

Apply the policy:
```bash
kubectl apply -f deny-from-other-namespaces.yaml
```

Verify the policy is applied:
```bash
kubectl get networkpolicy -n default
```

---

#### **5. Test the Policy**

1. **Check Connectivity From `default` to `test` Namespace**:
   ```bash
   kubectl exec pod2 -- curl pod1.default.svc.cluster.local
   ```
   **Expected Result**: The request fails because the NetworkPolicy blocks traffic from other namespaces. Here networkpolicy is applied to default namespace, so pod1 running in that namespace is blocking traffic from pod2 running in other namespace.  For the same behavior for test namespace, apply and test the network policy for test name space also.

2. **Check Connectivity Within the Same Namespace (`default`)**:
   ```bash
   kubectl exec pod1 -- curl pod1.default.svc.cluster.local
   ```
   **Expected Result**: The request succeeds because the policy allows traffic from Pods in the same namespace.

---

### **Analysis: Behavior Comparison**

| **Scenario**                       | **Without NetworkPolicy** | **With NetworkPolicy** |
|-------------------------------------|---------------------------|-------------------------|
| Pod in `default` → Pod in `default` | Allowed                   | Allowed                |
| Pod in `default` → Pod in `test`    | Allowed                   | Denied  (policy applied on the test namespace)                |
| Pod in `test` → Pod in `default`    | Allowed                   | Denied   (policy applied on the default namespace)               |
| Pod in `test` → Pod in `test`       | Allowed                   | Allowed (unaffected)   |

---

### **How the Policy Works**

1. **Default Behavior**:
   - Without a NetworkPolicy, Pods can communicate freely across namespaces.

2. **With the `deny-from-other-namespaces` Policy**:
   - Pods in the `default` namespace can only accept traffic from other Pods in the same namespace (`podSelector: {}` matches all Pods in the namespace).
   - All ingress traffic from Pods in other namespaces is blocked.

---

### **Cleanup**

To remove the resources created during this tutorial:

1. Delete the Pods and Services:
   ```bash
   kubectl delete pod pod1 -n default
   kubectl delete svc pod1 -n default
   kubectl delete pod pod2 -n test
   kubectl delete svc pod2 -n test
   ```

2. Delete the NetworkPolicy:
   ```bash
   kubectl delete networkpolicy deny-from-other-namespaces -n default
   ```

3. Delete the `test` namespace:
   ```bash
   kubectl delete namespace test
   ```

---

### **Conclusion**

By applying the `deny-from-other-namespaces` NetworkPolicy:
- Traffic between namespaces is blocked, ensuring namespace-level isolation.
- Traffic within the same namespace is allowed.
- This demonstrates how NetworkPolicies enforce fine-grained control over network traffic in Kubernetes. 

---

