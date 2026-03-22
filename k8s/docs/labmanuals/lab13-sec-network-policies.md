# Lab 10: Advanced Network Policies - Namespace Isolation

## Overview
In this lab, you will learn how to implement advanced network policies for namespace isolation in Kubernetes. You'll configure policies that restrict network traffic between namespaces, creating secure multi-tenant environments.

## Prerequisites
- A running Kubernetes cluster with a CNI plugin that supports NetworkPolicy (Calico, Cilium, or Weave)
- kubectl CLI tool installed and configured
- Basic understanding of Kubernetes namespaces
- Completion of Lab 07 (RBAC) recommended

## Learning Objectives
By the end of this lab, you will be able to:
- Understand namespace-level network isolation
- Configure NetworkPolicies to restrict cross-namespace traffic
- Allow intra-namespace communication while blocking external traffic
- Test and verify network policy enforcement
- Implement multi-tenant security patterns
- Troubleshoot network connectivity issues

---

## Understanding Namespace Isolation

### What is Namespace Isolation?

**Namespace isolation** is a security pattern that restricts network communication between different namespaces in a Kubernetes cluster. By default, all Pods in a cluster can communicate with each other regardless of namespace, which may not be desirable in multi-tenant environments.

### Why Implement Namespace Isolation?

Namespace isolation helps you:
- **Separate environments** - Isolate dev, staging, and production
- **Multi-tenancy** - Prevent one tenant from accessing another's resources
- **Compliance** - Meet regulatory requirements for data separation
- **Defense in depth** - Reduce lateral movement in case of compromise
- **Resource protection** - Prevent unauthorized access to sensitive workloads

### Default Kubernetes Network Behavior

Without NetworkPolicies:
- All Pods can communicate with all other Pods
- Namespaces provide logical separation only
- Network traffic flows freely across namespace boundaries
- No network-level isolation or protection

### NetworkPolicy for Namespace Isolation

With NetworkPolicies:
- Restrict traffic based on namespace selectors
- Allow only authorized cross-namespace communication
- Create default-deny policies for security
- Implement zero-trust networking

---

## Exercise 1: Environment Setup

### Step 1: Verify NetworkPolicy Support

Check if your cluster supports NetworkPolicy:

```bash
kubectl get nodes
kubectl describe node <node-name> | grep -i network
```

Or check for CNI plugin:

```bash
kubectl get pods -n kube-system | grep -E 'calico|cilium|weave|canal'
```

**Note**: If you don't see a NetworkPolicy-supporting CNI, network policies won't be enforced.

### Step 2: Create Test Namespaces

Create separate namespaces for testing:

```bash
kubectl create namespace prod
kubectl create namespace dev
kubectl create namespace test
```

Verify namespaces:

```bash
kubectl get namespaces
```

Expected output:
```
NAME              STATUS   AGE
default           Active   10d
dev               Active   5s
prod              Active   10s
test              Active   3s
```

### Step 3: Label Namespaces

Add labels to namespaces for identification:

```bash
kubectl label namespace prod environment=production
kubectl label namespace dev environment=development
kubectl label namespace test environment=testing
```

Verify labels:

```bash
kubectl get namespace --show-labels
```

---

## Exercise 2: Deploy Test Applications

### Step 1: Deploy Application in Production Namespace

Create a web application in the prod namespace:

```bash
kubectl create deployment web-prod --image=nginx:alpine -n prod
kubectl expose deployment web-prod --port=80 -n prod
```

Verify deployment:

```bash
kubectl get pods,svc -n prod
```

Expected output:
```
NAME                            READY   STATUS    RESTARTS   AGE
pod/web-prod-xxxxxxxxxx-xxxxx   1/1     Running   0          10s

NAME               TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)   AGE
service/web-prod   ClusterIP   10.96.xxx.xxx   <none>        80/TCP    5s
```

### Step 2: Deploy Application in Development Namespace

Create a similar application in the dev namespace:

```bash
kubectl create deployment web-dev --image=nginx:alpine -n dev
kubectl expose deployment web-dev --port=80 -n dev
```

### Step 3: Deploy Test Pod

Create a test Pod in the test namespace:

```bash
kubectl run test-client --image=busybox:1.28 -n test -- sleep 3600
```

### Step 4: Test Default Network Behavior

Before applying network policies, verify all Pods can communicate:

Get the ClusterIP of the prod service:

```bash
kubectl get svc -n prod
```

Test connectivity from test namespace to prod namespace:

```bash
kubectl exec -n test test-client -- wget -qO- --timeout=2 http://web-prod.prod.svc.cluster.local
```

Expected output (before network policy):
```
<!DOCTYPE html>
<html>
...nginx welcome page...
</html>
```

This shows that by default, Pods in different namespaces can communicate freely.

---

## Exercise 3: Implement Namespace Isolation

### Step 1: Review the Network Policy Manifest

Navigate to the security labs directory:

```bash
cd k8s/labs/security
```

Let's examine the `deny-from-other-namespaces.yaml` file:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  namespace: prod
  name: deny-from-other-namespaces
spec:
  podSelector:
    matchLabels: {}
  ingress:
  - from:
      - podSelector: {}
```

**Understanding the policy:**

- `metadata.namespace: prod` - Policy applies to the prod namespace
- `spec.podSelector.matchLabels: {}` - Applies to all Pods in prod namespace (empty selector matches all)
- `ingress` - Controls incoming traffic
- `from.podSelector: {}` - Allow traffic from Pods within the same namespace

**What this policy does:**
- Applies to all Pods in the prod namespace
- Allows ingress traffic ONLY from Pods in the same namespace (prod)
- Blocks all traffic from other namespaces (dev, test, default)
- Default behavior: deny all ingress not explicitly allowed

### Step 2: Apply the Network Policy

Apply the policy to the prod namespace:

```bash
kubectl apply -f deny-from-other-namespaces.yaml
```

Expected output:
```
networkpolicy.networking.k8s.io/deny-from-other-namespaces created
```

Verify the policy:

```bash
kubectl get networkpolicy -n prod
```

Expected output:
```
NAME                          POD-SELECTOR   AGE
deny-from-other-namespaces    <none>         10s
```

Describe the policy for details:

```bash
kubectl describe networkpolicy deny-from-other-namespaces -n prod
```

---

## Exercise 4: Test Network Isolation

### Step 1: Test Cross-Namespace Communication (Should Fail)

Try to access the prod service from the test namespace:

```bash
kubectl exec -n test test-client -- wget -qO- --timeout=2 http://web-prod.prod.svc.cluster.local
```

Expected output (SHOULD TIMEOUT):
```
wget: download timed out
command terminated with exit code 1
```

**Success!** The network policy is blocking cross-namespace traffic.

### Step 2: Test Intra-Namespace Communication (Should Work)

Create a test Pod in the prod namespace:

```bash
kubectl run test-prod --image=busybox:1.28 -n prod -- sleep 3600
```

Wait for the Pod to be ready:

```bash
kubectl wait --for=condition=ready pod/test-prod -n prod --timeout=60s
```

Test connectivity within the same namespace:

```bash
kubectl exec -n prod test-prod -- wget -qO- --timeout=2 http://web-prod.prod.svc.cluster.local
```

Expected output (SHOULD WORK):
```
<!DOCTYPE html>
<html>
...nginx welcome page...
</html>
```

**Success!** Pods within the same namespace can still communicate.

### Step 3: Test from Development Namespace

Try to access prod from dev namespace:

```bash
kubectl run test-dev --image=busybox:1.28 -n dev -- sleep 3600
```

Wait for Pod to be ready:

```bash
kubectl wait --for=condition=ready pod/test-dev -n dev --timeout=60s
```

Test connectivity:

```bash
kubectl exec -n dev test-dev -- wget -qO- --timeout=2 http://web-prod.prod.svc.cluster.local
```

Expected output (SHOULD TIMEOUT):
```
wget: download timed out
command terminated with exit code 1
```

The dev namespace is also blocked from accessing prod.

---

## Exercise 5: Allow Selective Cross-Namespace Access

### Step 1: Create a Policy That Allows Specific Namespaces

Sometimes you need to allow specific namespaces to communicate. Let's modify the policy:

Create a new policy that allows traffic from the test namespace:

```bash
cat > allow-from-test-namespace.yaml <<'EOF'
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  namespace: prod
  name: allow-from-test-namespace
spec:
  podSelector:
    matchLabels:
      app: web-prod
  ingress:
  - from:
    - podSelector: {}
    - namespaceSelector:
        matchLabels:
          environment: testing
EOF
```

**Understanding the enhanced policy:**

- `podSelector.matchLabels.app: web-prod` - Applies only to Pods with label app=web-prod
- `from` - Allow traffic from two sources:
  1. `podSelector: {}` - Pods in the same namespace (prod)
  2. `namespaceSelector.matchLabels.environment: testing` - Any Pod from namespaces labeled environment=testing

### Step 2: Apply the Enhanced Policy

```bash
kubectl apply -f allow-from-test-namespace.yaml
```

Verify both policies exist:

```bash
kubectl get networkpolicy -n prod
```

Expected output:
```
NAME                           POD-SELECTOR   AGE
deny-from-other-namespaces     <none>         5m
allow-from-test-namespace      app=web-prod   10s
```

### Step 3: Test Selective Access

Test from the test namespace (should now work):

```bash
kubectl exec -n test test-client -- wget -qO- --timeout=2 http://web-prod.prod.svc.cluster.local
```

Expected output (SHOULD WORK):
```
<!DOCTYPE html>
<html>
...nginx welcome page...
</html>
```

Test from the dev namespace (should still be blocked):

```bash
kubectl exec -n dev test-dev -- wget -qO- --timeout=2 http://web-prod.prod.svc.cluster.local
```

Expected output (SHOULD TIMEOUT):
```
wget: download timed out
command terminated with exit code 1
```

**Perfect!** We've implemented selective namespace access.

---

## Exercise 6: Create Default Deny Policy

### Step 1: Understand Default Deny

A **default deny** policy blocks all ingress traffic unless explicitly allowed. This is a security best practice.

Create a default deny policy for the dev namespace:

```bash
cat > deny-all-ingress-dev.yaml <<'EOF'
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  namespace: dev
  name: deny-all-ingress
spec:
  podSelector: {}
  policyTypes:
  - Ingress
EOF
```

**Understanding the policy:**

- `podSelector: {}` - Applies to all Pods in the namespace
- `policyTypes: [Ingress]` - Policy affects ingress traffic
- No `ingress` rules defined - Means "deny all" by default

### Step 2: Apply Default Deny Policy

```bash
kubectl apply -f deny-all-ingress-dev.yaml
```

### Step 3: Test Complete Isolation

Try to access the dev service from within its own namespace:

```bash
kubectl exec -n dev test-dev -- wget -qO- --timeout=2 http://web-dev.dev.svc.cluster.local
```

Expected output (SHOULD TIMEOUT):
```
wget: download timed out
command terminated with exit code 1
```

Even intra-namespace traffic is now blocked! This is a complete lockdown.

### Step 4: Selectively Allow Traffic

Now allow specific traffic. Create a policy to allow traffic from Pods with specific labels:

```bash
cat > allow-specific-ingress-dev.yaml <<'EOF'
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  namespace: dev
  name: allow-specific-ingress
spec:
  podSelector:
    matchLabels:
      app: web-dev
  ingress:
  - from:
    - podSelector:
        matchLabels:
          access: allowed
EOF
```

Apply the policy:

```bash
kubectl apply -f allow-specific-ingress-dev.yaml
```

### Step 5: Label Test Pod and Test Access

Label the test Pod:

```bash
kubectl label pod test-dev access=allowed -n dev
```

Test connectivity again:

```bash
kubectl exec -n dev test-dev -- wget -qO- --timeout=2 http://web-dev.dev.svc.cluster.local
```

Expected output (SHOULD NOW WORK):
```
<!DOCTYPE html>
<html>
...nginx welcome page...
</html>
```

**Success!** Only Pods with the correct label can access the service.

---

## Exercise 7: Egress Policy (Outbound Control)

### Step 1: Create an Egress Policy

Control outbound traffic from the prod namespace:

```bash
cat > deny-all-egress-prod.yaml <<'EOF'
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  namespace: prod
  name: deny-all-egress
spec:
  podSelector: {}
  policyTypes:
  - Egress
  egress:
  - to:
    - podSelector: {}
  - to:
    - namespaceSelector:
        matchLabels:
          kubernetes.io/metadata.name: kube-system
    ports:
    - protocol: UDP
      port: 53
EOF
```

**Understanding egress policy:**

- `policyTypes: [Egress]` - Controls outbound traffic
- `egress.to.podSelector: {}` - Allow egress to Pods in same namespace
- Allow DNS (kube-system, port 53) for name resolution

### Step 2: Apply Egress Policy

```bash
kubectl apply -f deny-all-egress-prod.yaml
```

### Step 3: Test Egress Restrictions

From a Pod in prod, try to access the internet:

```bash
kubectl exec -n prod test-prod -- wget -qO- --timeout=2 http://google.com
```

Expected output (SHOULD TIMEOUT):
```
wget: download timed out
command terminated with exit code 1
```

Try to access a Pod in the same namespace (should work):

```bash
kubectl exec -n prod test-prod -- wget -qO- --timeout=2 http://web-prod.prod.svc.cluster.local
```

Expected output (SHOULD WORK):
```
<!DOCTYPE html>
<html>
...nginx welcome page...
</html>
```

---

## Lab Cleanup

### Step 1: Delete Network Policies

Remove all network policies:

```bash
kubectl delete networkpolicy -n prod --all
kubectl delete networkpolicy -n dev --all
```

### Step 2: Delete Test Pods

Remove test Pods:

```bash
kubectl delete pod test-client -n test
kubectl delete pod test-prod -n prod
kubectl delete pod test-dev -n dev
```

### Step 3: Delete Deployments and Services

```bash
kubectl delete deployment,service web-prod -n prod
kubectl delete deployment,service web-dev -n dev
```

### Step 4: Delete Namespaces (Optional)

If you want to completely clean up:

```bash
kubectl delete namespace prod
kubectl delete namespace dev
kubectl delete namespace test
```

### Step 5: Clean Up YAML Files

Remove temporary files:

```bash
rm -f allow-from-test-namespace.yaml
rm -f deny-all-ingress-dev.yaml
rm -f allow-specific-ingress-dev.yaml
rm -f deny-all-egress-prod.yaml
```

### Step 6: Verify Cleanup

```bash
kubectl get networkpolicy --all-namespaces
kubectl get namespaces
```

---

## Network Policy Best Practices

### Design Principles

- **Default Deny** - Start with deny-all policies, then add allow rules
- **Least Privilege** - Allow only necessary traffic
- **Namespace Isolation** - Isolate sensitive workloads in separate namespaces
- **Label Strategy** - Use consistent labels for policy selectors
- **Documentation** - Document all network policies and their purpose

### Common Patterns

#### Complete Namespace Isolation
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-from-other-namespaces
spec:
  podSelector: {}
  ingress:
  - from:
    - podSelector: {}
```

#### Allow Specific Namespace
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-from-monitoring
spec:
  podSelector: {}
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: monitoring
```

#### Default Deny All Ingress
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-ingress
spec:
  podSelector: {}
  policyTypes:
  - Ingress
```

#### Allow DNS Only
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-dns-only
spec:
  podSelector: {}
  policyTypes:
  - Egress
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          kubernetes.io/metadata.name: kube-system
    ports:
    - protocol: UDP
      port: 53
```

---

## Troubleshooting Guide

### Issue: Network policies not taking effect

**Cause**: CNI plugin doesn't support NetworkPolicy

**Solution**:
```bash
# Check if CNI plugin supports NetworkPolicy
kubectl get pods -n kube-system | grep -E 'calico|cilium|weave'

# If not present, install a NetworkPolicy-capable CNI
```

### Issue: Can't access DNS after applying egress policy

**Cause**: DNS traffic blocked by egress policy

**Solution**:
```yaml
egress:
- to:
  - namespaceSelector:
      matchLabels:
        kubernetes.io/metadata.name: kube-system
  ports:
  - protocol: UDP
    port: 53
```

### Issue: Pods can still communicate despite deny policy

**Cause**: Multiple policies might be conflicting, or policy not applied correctly

**Solution**:
```bash
# Check all policies in namespace
kubectl get networkpolicy -n <namespace>

# Describe policy to verify configuration
kubectl describe networkpolicy <policy-name> -n <namespace>

# Verify pod labels match selectors
kubectl get pods -n <namespace> --show-labels
```

### Issue: Can't determine why traffic is blocked

**Cause**: Need better visibility into network policy decisions

**Solution**:
```bash
# Use kubectl debug or logs
kubectl logs -n kube-system <cni-plugin-pod>

# Check pod connectivity
kubectl exec -it <pod> -n <namespace> -- sh
# Then use wget, curl, or nc to test connectivity
```

---

## Key Takeaways

1. NetworkPolicies provide network-level isolation in Kubernetes
2. Default behavior allows all traffic - policies create restrictions
3. Namespace isolation is critical for multi-tenancy
4. Use default-deny policies for maximum security
5. Label namespaces for easier policy targeting
6. Test policies thoroughly before production deployment
7. Document all network policies and their purpose
8. Monitor policy effectiveness and adjust as needed

---

## Additional Reading

- [Kubernetes NetworkPolicy Documentation](https://kubernetes.io/docs/concepts/services-networking/network-policies/)
- [NetworkPolicy Recipes](https://github.com/ahmetb/kubernetes-network-policy-recipes)
- [Calico Network Policy](https://docs.projectcalico.org/security/calico-network-policy)
- [Cilium Network Policy](https://docs.cilium.io/en/stable/policy/)

---

**Lab Created**: March 2026
**Compatible with**: Kubernetes 1.24+
**Based on**: labs/security/deny-from-other-namespaces.yaml
**CNI Requirements**: Calico, Cilium, Weave, or other NetworkPolicy-capable CNI
**Tested on**: kubeadm clusters with Calico
**Estimated Time**: 60-75 minutes
