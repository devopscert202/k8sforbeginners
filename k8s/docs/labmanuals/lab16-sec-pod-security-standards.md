# Lab 38: Pod Security Standards & Admission Control

## Overview
In this lab, you will learn how to implement Pod Security Standards (PSS) and Pod Security Admission (PSA) in Kubernetes. PSS is the modern replacement for the deprecated PodSecurityPolicy (PSP) and provides a simplified approach to enforcing security best practices at the namespace level. You'll explore the three security profiles - Privileged, Baseline, and Restricted - and learn how to apply them using different enforcement modes.

## Prerequisites
- A running Kubernetes cluster (version 1.25 or higher)
- kubectl CLI tool installed and configured
- Cluster admin access
- Basic understanding of Pod security contexts (Lab 09 recommended)
- Familiarity with Kubernetes namespaces

## Learning Objectives
By the end of this lab, you will be able to:
- Understand Pod Security Standards and their security levels
- Explain why PSS replaced PodSecurityPolicy
- Configure namespace-level Pod Security Admission
- Apply Privileged, Baseline, and Restricted security profiles
- Use enforce, audit, and warn modes effectively
- Combine PSS with Pod security contexts
- Troubleshoot Pod Security Standard violations
- Apply PSS best practices for CKA exam scenarios

---

## Understanding Pod Security Standards

### What are Pod Security Standards?

**Pod Security Standards (PSS)** define three security profiles that cover the security spectrum from highly permissive to highly restrictive. These standards are:

1. **Privileged** - Unrestricted policy, allows all possible privilege escalations
2. **Baseline** - Minimally restrictive, prevents known privilege escalations
3. **Restricted** - Heavily restricted, follows current Pod hardening best practices

### Why Replace PodSecurityPolicy?

**PodSecurityPolicy (PSP)** was deprecated in Kubernetes 1.21 and removed in 1.25 due to several issues:

| PodSecurityPolicy Issues | Pod Security Standards Benefits |
|-------------------------|--------------------------------|
| Complex to configure and understand | Simple, declarative namespace labels |
| Global scope made testing difficult | Namespace-level control |
| Hard to troubleshoot violations | Clear violation messages |
| Applied via RBAC (confusing) | Built-in admission controller |
| Difficult to migrate between clusters | Standardized across all clusters |

### Pod Security Admission (PSA)

**Pod Security Admission** is a built-in admission controller (enabled by default since 1.25) that enforces Pod Security Standards at the namespace level using labels.

**Three Enforcement Modes:**

| Mode | Action | Use Case |
|------|--------|----------|
| **enforce** | Rejects Pods that violate the policy | Production enforcement |
| **audit** | Allows Pod but logs violation to audit log | Compliance monitoring |
| **warn** | Allows Pod but returns warning to user | Migration and testing |

**Namespace Label Format:**
```
pod-security.kubernetes.io/<MODE>: <LEVEL>
pod-security.kubernetes.io/<MODE>-version: <VERSION>
```

---

## Understanding Security Levels

### Privileged Profile

**Security Level**: None
**Use Case**: System-level workloads, trusted applications

**Allows:**
- All privilege escalations
- Running as root
- Host namespaces access
- All Linux capabilities
- Privileged containers

**Example workloads**: CNI plugins, storage drivers, monitoring agents

### Baseline Profile

**Security Level**: Minimal restrictions
**Use Case**: Common containerized workloads

**Prevents:**
- HostPath volumes
- Host networking and ports
- Privileged containers
- Sharing host namespaces (IPC, PID, Network)
- Dangerous capabilities (e.g., SYS_ADMIN)
- AppArmor/SELinux/seccomp modifications

**Allows:**
- Running as root (but not privileged)
- Most standard capabilities
- Non-root volumes

**Example workloads**: Web applications, databases, microservices

### Restricted Profile

**Security Level**: Heavily restricted
**Use Case**: Security-critical applications

**Enforces:**
- Must run as non-root user (`runAsNonRoot: true`)
- Must drop all capabilities
- Cannot run privileged containers
- No host namespace access
- No host path volumes
- Required seccomp profile
- Read-only root filesystem (encouraged)

**Example workloads**: Multi-tenant applications, untrusted code

---

## Exercise 1: Verify PSA is Enabled

### Step 1: Check Kubernetes Version

Verify you're running Kubernetes 1.25 or higher:

```bash
kubectl version --short
```

Expected output (version should be 1.25+):
```
Client Version: v1.28.0
Server Version: v1.28.2
```

If your version is below 1.25, Pod Security Admission may not be enabled by default.

### Step 2: Check Admission Plugins

Verify that PodSecurity admission plugin is enabled:

```bash
kubectl -n kube-system get pods -l component=kube-apiserver -o yaml | grep -i admission
```

You should see `PodSecurity` in the admission plugins list.

### Step 3: View Default Pod Security Configuration

Check if there are any cluster-wide PSS defaults:

```bash
kubectl get configmap -n kube-system
```

Some clusters may have an `admission-control-config` ConfigMap that defines defaults.

---

## Exercise 2: Create Test Namespaces with Different Security Levels

### Step 1: Create Privileged Namespace

Create a namespace with privileged security profile:

```bash
kubectl create namespace pss-privileged
```

Label the namespace for privileged mode:

```bash
kubectl label namespace pss-privileged \
  pod-security.kubernetes.io/enforce=privileged \
  pod-security.kubernetes.io/audit=privileged \
  pod-security.kubernetes.io/warn=privileged
```

Expected output:
```
namespace/pss-privileged labeled
```

Verify the labels:

```bash
kubectl get namespace pss-privileged --show-labels
```

Expected output:
```
NAME             STATUS   AGE   LABELS
pss-privileged   Active   30s   pod-security.kubernetes.io/audit=privileged,pod-security.kubernetes.io/enforce=privileged,pod-security.kubernetes.io/warn=privileged
```

### Step 2: Create Baseline Namespace

Create a namespace with baseline security profile:

```bash
kubectl create namespace pss-baseline
```

Label the namespace:

```bash
kubectl label namespace pss-baseline \
  pod-security.kubernetes.io/enforce=baseline \
  pod-security.kubernetes.io/audit=baseline \
  pod-security.kubernetes.io/warn=baseline
```

### Step 3: Create Restricted Namespace

Create a namespace with restricted security profile:

```bash
kubectl create namespace pss-restricted
```

Label the namespace:

```bash
kubectl label namespace pss-restricted \
  pod-security.kubernetes.io/enforce=restricted \
  pod-security.kubernetes.io/audit=restricted \
  pod-security.kubernetes.io/warn=restricted
```

### Step 4: View All Test Namespaces

List all namespaces with PSS labels:

```bash
kubectl get namespaces -L pod-security.kubernetes.io/enforce
```

Expected output:
```
NAME              STATUS   AGE     ENFORCE
pss-privileged    Active   2m      privileged
pss-baseline      Active   90s     baseline
pss-restricted    Active   30s     restricted
default           Active   30d
kube-system       Active   30d
```

---

## Exercise 3: Testing Privileged Profile

### Step 1: Create a Privileged Pod

Create a highly privileged Pod in the privileged namespace:

```bash
cat > privileged-pod.yaml <<'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: privileged-pod
  namespace: pss-privileged
spec:
  hostNetwork: true
  hostPID: true
  hostIPC: true
  containers:
  - name: privileged-container
    image: nginx:alpine
    securityContext:
      privileged: true
      runAsUser: 0
    volumeMounts:
    - name: host-root
      mountPath: /host
  volumes:
  - name: host-root
    hostPath:
      path: /
      type: Directory
EOF
```

**Understanding the configuration:**
- `hostNetwork: true` - Uses host networking
- `hostPID: true` - Shares host PID namespace
- `hostIPC: true` - Shares host IPC namespace
- `privileged: true` - Runs in privileged mode
- `runAsUser: 0` - Runs as root
- `hostPath` volume - Mounts host root filesystem

Deploy the Pod:

```bash
kubectl apply -f privileged-pod.yaml
```

Expected output:
```
pod/privileged-pod created
```

**Result**: Pod is created successfully because the namespace allows privileged workloads.

### Step 2: Verify the Pod

Check the Pod status:

```bash
kubectl get pod -n pss-privileged privileged-pod
```

Expected output:
```
NAME             READY   STATUS    RESTARTS   AGE
privileged-pod   1/1     Running   0          20s
```

### Step 3: Test Host Access

Verify the Pod has host-level access:

```bash
kubectl exec -n pss-privileged privileged-pod -- ls /host/etc
```

You should see the host's `/etc` directory contents, demonstrating full host access.

---

## Exercise 4: Testing Baseline Profile

### Step 1: Try to Create Privileged Pod in Baseline Namespace

Attempt to create the same privileged Pod in the baseline namespace:

```bash
cat > baseline-test-privileged.yaml <<'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: baseline-test-privileged
  namespace: pss-baseline
spec:
  hostNetwork: true
  containers:
  - name: test-container
    image: nginx:alpine
    securityContext:
      privileged: true
EOF
```

Try to apply:

```bash
kubectl apply -f baseline-test-privileged.yaml
```

Expected output (ERROR):
```
Error from server (Forbidden): error when creating "baseline-test-privileged.yaml": pods "baseline-test-privileged" is forbidden: violates PodSecurity "baseline:latest": privileged (container "test-container" must not set securityContext.privileged=true), host namespaces (hostNetwork=true)
```

**Result**: Pod is rejected because it violates the baseline profile.

### Step 2: Create Baseline-Compliant Pod

Create a Pod that complies with baseline standards:

```bash
cat > baseline-compliant-pod.yaml <<'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: baseline-compliant-pod
  namespace: pss-baseline
spec:
  containers:
  - name: nginx-container
    image: nginx:alpine
    ports:
    - containerPort: 80
    securityContext:
      runAsUser: 0  # Running as root is allowed in baseline
      allowPrivilegeEscalation: false
EOF
```

Apply the Pod:

```bash
kubectl apply -f baseline-compliant-pod.yaml
```

Expected output:
```
pod/baseline-compliant-pod created
```

**Result**: Pod is created successfully because it meets baseline requirements.

### Step 3: Verify Baseline Restrictions

Check what the baseline profile prevents:

```bash
kubectl explain pod.spec.hostNetwork
kubectl explain pod.spec.hostPID
```

List common violations:
- ❌ `hostNetwork: true`
- ❌ `hostPID: true`
- ❌ `hostIPC: true`
- ❌ `privileged: true`
- ❌ `hostPath` volumes
- ✅ Running as root (allowed)
- ✅ Most capabilities (allowed)

---

## Exercise 5: Testing Restricted Profile

### Step 1: Try Baseline-Compliant Pod in Restricted Namespace

Attempt to create the baseline-compliant Pod in the restricted namespace:

```bash
cat > restricted-test-baseline.yaml <<'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: restricted-test-baseline
  namespace: pss-restricted
spec:
  containers:
  - name: nginx-container
    image: nginx:alpine
    securityContext:
      runAsUser: 0  # Running as root
      allowPrivilegeEscalation: false
EOF
```

Try to apply:

```bash
kubectl apply -f restricted-test-baseline.yaml
```

Expected output (ERROR):
```
Error from server (Forbidden): error when creating "restricted-test-baseline.yaml": pods "restricted-test-baseline" is forbidden: violates PodSecurity "restricted:latest": allowPrivilegeEscalation != false (container "nginx-container" must set securityContext.allowPrivilegeEscalation=false), unrestricted capabilities (container "nginx-container" must set securityContext.capabilities.drop=["ALL"]), runAsNonRoot != true (pod or container "nginx-container" must set securityContext.runAsNonRoot=true), seccompProfile (pod or container "nginx-container" must set securityContext.seccompProfile.type to "RuntimeDefault" or "Localhost")
```

**Result**: Pod is rejected because it doesn't meet restricted requirements (running as root).

### Step 2: Create Restricted-Compliant Pod

Create a fully restricted-compliant Pod:

```bash
cat > restricted-compliant-pod.yaml <<'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: restricted-compliant-pod
  namespace: pss-restricted
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    seccompProfile:
      type: RuntimeDefault
  containers:
  - name: nginx-container
    image: nginx:alpine
    ports:
    - containerPort: 8080
    securityContext:
      allowPrivilegeEscalation: false
      runAsNonRoot: true
      capabilities:
        drop:
        - ALL
    volumeMounts:
    - name: tmp
      mountPath: /tmp
    - name: cache
      mountPath: /var/cache/nginx
    - name: run
      mountPath: /var/run
  volumes:
  - name: tmp
    emptyDir: {}
  - name: cache
    emptyDir: {}
  - name: run
    emptyDir: {}
EOF
```

**Understanding the restricted configuration:**

**Pod-level security context:**
- `runAsNonRoot: true` - Enforces non-root execution
- `runAsUser: 1000` - Specific non-root user ID
- `seccompProfile: RuntimeDefault` - Required seccomp profile

**Container-level security context:**
- `allowPrivilegeEscalation: false` - No privilege escalation
- `runAsNonRoot: true` - Container must be non-root
- `capabilities.drop: ["ALL"]` - Drop all Linux capabilities

**Volume mounts:**
- emptyDir volumes for directories nginx needs to write to

Apply the Pod:

```bash
kubectl apply -f restricted-compliant-pod.yaml
```

Expected output:
```
pod/restricted-compliant-pod created
```

### Step 3: Verify Restricted Pod

Check the Pod status:

```bash
kubectl get pod -n pss-restricted restricted-compliant-pod
```

Verify the security settings:

```bash
kubectl exec -n pss-restricted restricted-compliant-pod -- id
```

Expected output:
```
uid=1000 gid=0(root) groups=0(root)
```

The Pod runs as non-root user 1000, meeting restricted requirements.

### Step 4: Understand Restricted Requirements

Summary of restricted profile requirements:

**Required settings:**
- ✅ `runAsNonRoot: true` (Pod or container level)
- ✅ `allowPrivilegeEscalation: false`
- ✅ `capabilities.drop: ["ALL"]`
- ✅ `seccompProfile.type: RuntimeDefault or Localhost`

**Forbidden settings:**
- ❌ `privileged: true`
- ❌ Host namespaces (hostNetwork, hostPID, hostIPC)
- ❌ Host path volumes
- ❌ Running as root (UID 0)
- ❌ Adding capabilities without dropping ALL first

---

## Exercise 6: Using Audit and Warn Modes

### Step 1: Create Mixed-Mode Namespace

Create a namespace with different modes for different levels:

```bash
kubectl create namespace pss-mixed
```

Apply mixed security modes:

```bash
kubectl label namespace pss-mixed \
  pod-security.kubernetes.io/enforce=baseline \
  pod-security.kubernetes.io/audit=restricted \
  pod-security.kubernetes.io/warn=restricted
```

**Understanding this configuration:**
- `enforce=baseline` - Blocks baseline violations
- `audit=restricted` - Logs restricted violations to audit log
- `warn=restricted` - Warns users about restricted violations

### Step 2: Test with Baseline-Compliant Pod

Create a Pod that passes baseline but fails restricted:

```bash
cat > mixed-mode-test.yaml <<'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: mixed-mode-test
  namespace: pss-mixed
spec:
  containers:
  - name: nginx-container
    image: nginx:alpine
    securityContext:
      runAsUser: 0  # Root - baseline OK, restricted violation
      allowPrivilegeEscalation: false
EOF
```

Apply the Pod:

```bash
kubectl apply -f mixed-mode-test.yaml
```

Expected output (with warnings):
```
Warning: would violate PodSecurity "restricted:latest": allowPrivilegeEscalation != false (container "nginx-container" must set securityContext.allowPrivilegeEscalation=false), unrestricted capabilities (container "nginx-container" must set securityContext.capabilities.drop=["ALL"]), runAsNonRoot != true (pod or container "nginx-container" must set securityContext.runAsNonRoot=true), seccompProfile (pod or container "nginx-container" must set securityContext.seccompProfile.type to "RuntimeDefault" or "Localhost")
pod/mixed-mode-test created
```

**Result**:
- Pod is created (enforce=baseline allows it)
- Warning is displayed (warn=restricted detects violations)
- Audit log entry is created (audit=restricted logs violations)

### Step 3: View Audit Logs (Optional)

If you have access to API server logs:

```bash
kubectl logs -n kube-system -l component=kube-apiserver | grep "pod-security-audit"
```

You should see audit log entries for the restricted violations.

### Step 4: Use Cases for Different Modes

| Mode | Use Case | Example Scenario |
|------|----------|-----------------|
| **enforce** | Production security enforcement | Block non-compliant Pods in prod |
| **audit** | Compliance monitoring | Log violations without blocking |
| **warn** | Migration and testing | Alert developers during migration |
| **Mixed** | Gradual enforcement | Enforce baseline, warn about restricted |

**Best practice**: Use warn/audit modes during PSS migration, then switch to enforce.

---

## Exercise 7: Version Pinning

### Step 1: Understand Version Pinning

Pod Security Standards evolve over time. You can pin to specific Kubernetes versions:

```bash
kubectl label namespace pss-baseline \
  pod-security.kubernetes.io/enforce-version=v1.28 \
  --overwrite
```

**Why pin versions?**
- Prevent unexpected changes when upgrading Kubernetes
- Maintain consistent behavior across clusters
- Plan for future standard changes

### Step 2: Use Latest Version (Default)

To always use the latest PSS definitions:

```bash
kubectl label namespace pss-baseline \
  pod-security.kubernetes.io/enforce-version=latest \
  --overwrite
```

**Recommendation**: Use version pinning in production, `latest` in development.

---

## Exercise 8: Combining PSS with Pod Security Context

### Step 1: Understand the Relationship

Pod Security Standards enforce minimum security requirements, while Pod Security Context provides the actual implementation:

| Component | Purpose | Level |
|-----------|---------|-------|
| **PSS (Namespace)** | Defines what's allowed | Admission Control |
| **Security Context (Pod)** | Implements security settings | Pod Configuration |

**Example**:
- Restricted profile requires `runAsNonRoot: true`
- Security context implements `runAsUser: 1000`

### Step 2: Create Pod with Both

Create a Pod that uses both PSS and security context:

```bash
cat > pss-with-context.yaml <<'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: pss-with-context
  namespace: pss-restricted
spec:
  # Pod-level security context
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    runAsGroup: 3000
    fsGroup: 2000
    seccompProfile:
      type: RuntimeDefault
  containers:
  - name: secure-app
    image: busybox:1.28
    command: ["sh", "-c", "sleep 3600"]
    # Container-level security context
    securityContext:
      allowPrivilegeEscalation: false
      runAsNonRoot: true
      readOnlyRootFilesystem: true
      capabilities:
        drop:
        - ALL
    volumeMounts:
    - name: tmp
      mountPath: /tmp
  volumes:
  - name: tmp
    emptyDir: {}
EOF
```

Apply the Pod:

```bash
kubectl apply -f pss-with-context.yaml
```

**This Pod:**
- Passes restricted PSS requirements (namespace admission)
- Implements additional security hardening (security context)
- Uses principle of least privilege

### Step 3: Verify Combined Security

Check the Pod's security configuration:

```bash
kubectl get pod -n pss-restricted pss-with-context -o yaml | grep -A 10 securityContext
```

Verify runtime security:

```bash
kubectl exec -n pss-restricted pss-with-context -- id
```

Expected output:
```
uid=1000 gid=3000 groups=2000
```

Test read-only filesystem:

```bash
kubectl exec -n pss-restricted pss-with-context -- touch /test.txt
```

Expected output (ERROR):
```
touch: /test.txt: Read-only file system
command terminated with exit code 1
```

---

## Exercise 9: Handling System Namespaces

### Step 1: Check System Namespace PSS Labels

View PSS configuration for kube-system:

```bash
kubectl get namespace kube-system --show-labels | grep pod-security
```

Most clusters have kube-system set to privileged by default.

### Step 2: Understand System Namespace Exemptions

Certain namespaces typically need privileged access:

| Namespace | Typical Level | Reason |
|-----------|--------------|--------|
| `kube-system` | privileged | System components (DNS, CNI) |
| `kube-node-lease` | privileged | Node heartbeat mechanism |
| `kube-public` | baseline | Public information |
| `default` | baseline | User workloads (should enforce) |

**⚠️ Warning**: Never apply restricted profile to kube-system - it will break your cluster!

### Step 3: Set Default Namespace to Baseline

It's a best practice to enforce at least baseline on the default namespace:

```bash
kubectl label namespace default \
  pod-security.kubernetes.io/enforce=baseline \
  pod-security.kubernetes.io/audit=baseline \
  pod-security.kubernetes.io/warn=baseline
```

---

## Troubleshooting Guide

### Issue: Pod Rejected with PSS Violation

**Error message:**
```
Error from server (Forbidden): pods "my-pod" is forbidden: violates PodSecurity "baseline:latest": privileged (container "my-container" must not set securityContext.privileged=true)
```

**Cause**: Pod configuration violates the namespace's enforced PSS profile.

**Solution**:

1. Check the namespace's PSS labels:
```bash
kubectl get namespace <namespace> --show-labels | grep pod-security
```

2. Identify the specific violation in the error message

3. Fix the Pod configuration:
   - Remove `privileged: true`
   - Remove host namespace settings
   - Add required security context settings

4. For testing, temporarily use warn mode:
```bash
kubectl label namespace <namespace> \
  pod-security.kubernetes.io/enforce=privileged \
  --overwrite
```

### Issue: Can't Tell What's Violating Restricted Profile

**Problem**: Error message is long and lists multiple violations.

**Solution**:

1. Use `--dry-run=server` to test without creating:
```bash
kubectl apply -f pod.yaml --dry-run=server
```

2. Fix violations one at a time, starting with:
   - Add `runAsNonRoot: true` at pod level
   - Add `allowPrivilegeEscalation: false` at container level
   - Add `capabilities.drop: ["ALL"]` at container level
   - Add `seccompProfile.type: RuntimeDefault` at pod level

3. Use kubectl explain for requirements:
```bash
kubectl explain pod.spec.securityContext
```

### Issue: Restricted Profile Too Strict for My App

**Problem**: Application requires root or specific capabilities.

**Solutions**:

**Option 1**: Use baseline profile instead
```bash
kubectl label namespace <namespace> \
  pod-security.kubernetes.io/enforce=baseline \
  --overwrite
```

**Option 2**: Modify application to run as non-root
- Update Dockerfile to create non-root user
- Change ownership of required directories
- Use init container if needed

**Option 3**: Use mixed modes (enforce baseline, audit restricted)
```bash
kubectl label namespace <namespace> \
  pod-security.kubernetes.io/enforce=baseline \
  pod-security.kubernetes.io/audit=restricted \
  pod-security.kubernetes.io/warn=restricted
```

### Issue: Migration from PodSecurityPolicy

**Problem**: Cluster upgraded to 1.25+, PSPs are gone.

**Solution**:

1. Audit existing PSPs before removal:
```bash
kubectl get psp
kubectl describe psp <psp-name>
```

2. Map PSPs to PSS profiles:
   - Unrestricted PSP → Privileged profile
   - Restricted PSP → Baseline or Restricted profile

3. Apply PSS labels to namespaces:
```bash
# Start with warn mode
kubectl label namespace <namespace> \
  pod-security.kubernetes.io/warn=baseline

# Test workloads, then enforce
kubectl label namespace <namespace> \
  pod-security.kubernetes.io/enforce=baseline \
  --overwrite
```

4. Update Pod manifests to include required security context settings

### Issue: Pods in kube-system Rejected

**Error**: System Pods (CoreDNS, CNI) fail to start after applying PSS.

**Cause**: Applied restricted or baseline profile to kube-system namespace.

**Solution**:

Remove the PSS labels or set to privileged:
```bash
kubectl label namespace kube-system \
  pod-security.kubernetes.io/enforce=privileged \
  pod-security.kubernetes.io/audit=privileged \
  pod-security.kubernetes.io/warn=privileged \
  --overwrite
```

**Prevention**: Never apply restricted/baseline to system namespaces.

### Issue: Warning Messages Are Annoying

**Problem**: Getting warnings for every Pod creation in development.

**Solution**:

Remove warn labels if you don't need them:
```bash
kubectl label namespace <namespace> \
  pod-security.kubernetes.io/warn- \
  --overwrite
```

Keep only enforce and audit:
```bash
kubectl label namespace <namespace> \
  pod-security.kubernetes.io/enforce=baseline \
  pod-security.kubernetes.io/audit=baseline
```

---

## Lab Cleanup

### Step 1: Delete Test Pods

Remove all test Pods:

```bash
kubectl delete pod -n pss-privileged privileged-pod
kubectl delete pod -n pss-baseline baseline-compliant-pod
kubectl delete pod -n pss-restricted restricted-compliant-pod
kubectl delete pod -n pss-mixed mixed-mode-test
kubectl delete pod -n pss-restricted pss-with-context
```

Or delete all Pods in test namespaces:

```bash
kubectl delete pods --all -n pss-privileged
kubectl delete pods --all -n pss-baseline
kubectl delete pods --all -n pss-restricted
kubectl delete pods --all -n pss-mixed
```

### Step 2: Delete Test Namespaces

Remove test namespaces:

```bash
kubectl delete namespace pss-privileged
kubectl delete namespace pss-baseline
kubectl delete namespace pss-restricted
kubectl delete namespace pss-mixed
```

### Step 3: Remove Default Namespace Labels (Optional)

If you added PSS labels to the default namespace:

```bash
kubectl label namespace default \
  pod-security.kubernetes.io/enforce- \
  pod-security.kubernetes.io/audit- \
  pod-security.kubernetes.io/warn-
```

### Step 4: Clean Up YAML Files

Remove temporary files:

```bash
rm -f privileged-pod.yaml
rm -f baseline-test-privileged.yaml
rm -f baseline-compliant-pod.yaml
rm -f restricted-test-baseline.yaml
rm -f restricted-compliant-pod.yaml
rm -f mixed-mode-test.yaml
rm -f pss-with-context.yaml
```

### Step 5: Verify Cleanup

Confirm all test resources are removed:

```bash
kubectl get namespaces | grep pss-
```

Expected output: No results

---

## Pod Security Standards Best Practices

### Namespace Security Strategy

1. **Default to Baseline**: Apply baseline profile to most namespaces
2. **Use Restricted for Multi-Tenancy**: Apply restricted profile for untrusted workloads
3. **Privileged for System Components**: Only use privileged for system namespaces
4. **Progressive Enforcement**: Start with warn/audit, then enforce

### Security Profile Selection

| Workload Type | Recommended Profile | Justification |
|--------------|-------------------|--------------|
| Web applications | Baseline or Restricted | Standard apps don't need host access |
| Databases | Baseline | May need specific UIDs |
| CI/CD runners | Baseline | Build processes need flexibility |
| System DaemonSets | Privileged | Require host-level access |
| Multi-tenant apps | Restricted | Maximum security isolation |
| Development namespaces | Baseline with warn=restricted | Balance flexibility and security awareness |

### Implementation Best Practices

1. **Start with Audit and Warn**:
```bash
kubectl label namespace <namespace> \
  pod-security.kubernetes.io/audit=baseline \
  pod-security.kubernetes.io/warn=baseline
```

2. **Test thoroughly before enforcing**:
   - Deploy all workloads
   - Check for warnings
   - Review audit logs
   - Fix violations

3. **Then enable enforcement**:
```bash
kubectl label namespace <namespace> \
  pod-security.kubernetes.io/enforce=baseline \
  --overwrite
```

4. **Use version pinning in production**:
```bash
kubectl label namespace <namespace> \
  pod-security.kubernetes.io/enforce-version=v1.28
```

### Security Context Templates

**Baseline-compliant template**:
```yaml
securityContext:
  runAsUser: 1000
  allowPrivilegeEscalation: false
```

**Restricted-compliant template**:
```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  seccompProfile:
    type: RuntimeDefault
containers:
- securityContext:
    allowPrivilegeEscalation: false
    capabilities:
      drop:
      - ALL
```

### Migration Strategy

**Phase 1: Assessment (Week 1)**
- Inventory all namespaces
- Document current security posture
- Identify privileged workloads

**Phase 2: Preparation (Week 2-3)**
- Update Pod manifests
- Add security contexts
- Test in development

**Phase 3: Audit Mode (Week 4-5)**
- Apply audit/warn labels
- Monitor violations
- Fix applications

**Phase 4: Enforcement (Week 6+)**
- Enable enforce mode
- Monitor for issues
- Document exemptions

---

## CKA Exam Relevance

### Exam Topics Covered

Pod Security Standards are part of the CKA exam "Cluster Hardening" domain (15% of exam):

**CKA-relevant skills from this lab:**
1. Understanding PSS security levels (Privileged, Baseline, Restricted)
2. Applying PSS to namespaces using labels
3. Troubleshooting PSS violations
4. Combining PSS with Pod security contexts
5. Understanding PSS as PSP replacement

### Common CKA Questions

**Question 1**: "Configure the namespace 'webapp' to enforce baseline Pod security standards."

**Solution**:
```bash
kubectl label namespace webapp \
  pod-security.kubernetes.io/enforce=baseline
```

**Question 2**: "Why is this Pod failing to start in the 'secure-apps' namespace?"

**Solution approach**:
1. Check namespace PSS labels
2. Review error message for violations
3. Fix Pod manifest (add required security context)
4. Reapply

**Question 3**: "Configure namespace 'dev' to warn about restricted violations but only enforce baseline."

**Solution**:
```bash
kubectl label namespace dev \
  pod-security.kubernetes.io/enforce=baseline \
  pod-security.kubernetes.io/warn=restricted
```

### Exam Tips

1. **Know the three profiles**: Memorize requirements for privileged, baseline, and restricted
2. **Label syntax**: Practice the namespace label format
3. **Quick fixes**: Know how to quickly make Pods baseline/restricted compliant
4. **Don't break system namespaces**: Never apply restricted to kube-system
5. **Use kubectl explain**: `kubectl explain pod.spec.securityContext` for reference
6. **Dry-run first**: Use `--dry-run=server` to test before applying

### Time-Saving Commands

```bash
# Quick baseline enforcement
kubectl label ns <namespace> pod-security.kubernetes.io/enforce=baseline

# View all PSS labels
kubectl get ns --show-labels | grep pod-security

# Test Pod without creating
kubectl apply -f pod.yaml --dry-run=server

# Quick security context for restricted
cat <<EOF | kubectl apply -f -
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  seccompProfile:
    type: RuntimeDefault
containers:
- securityContext:
    allowPrivilegeEscalation: false
    capabilities:
      drop: ["ALL"]
EOF
```

---

## Key Takeaways

1. **PSS replaces PSP**: Pod Security Standards are the modern, simpler alternative to PodSecurityPolicy
2. **Three security levels**: Privileged (unrestricted), Baseline (minimal), Restricted (hardened)
3. **Namespace-level enforcement**: Apply PSS using namespace labels, not global policies
4. **Three enforcement modes**: enforce (block), audit (log), warn (notify)
5. **Graduated enforcement**: Use warn/audit during migration, then enforce
6. **Restricted is strict**: Requires non-root, no privileges, dropped capabilities, seccomp
7. **Baseline prevents escalation**: Blocks host access and privileged containers
8. **System namespaces need privileged**: Never restrict kube-system
9. **Combine with security context**: PSS enforces minimums, security context implements specifics
10. **CKA exam relevant**: Know how to apply, troubleshoot, and fix PSS violations

---

## Additional Resources

### Official Kubernetes Documentation
- [Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/)
- [Pod Security Admission](https://kubernetes.io/docs/concepts/security/pod-security-admission/)
- [Pod Security Standards Migration Guide](https://kubernetes.io/docs/tasks/configure-pod-container/migrate-from-psp/)
- [Security Context Documentation](https://kubernetes.io/docs/tasks/configure-pod-container/security-context/)

### Security Best Practices
- [NSA/CISA Kubernetes Hardening Guide](https://media.defense.gov/2022/Aug/29/2003066362/-1/-1/0/CTR_KUBERNETES_HARDENING_GUIDANCE_1.2_20220829.PDF)
- [CIS Kubernetes Benchmark](https://www.cisecurity.org/benchmark/kubernetes)
- [OWASP Kubernetes Top 10](https://owasp.org/www-project-kubernetes-top-ten/)

### Related Labs
- Lab 09: Pod Security Context (Foundation for PSS)
- Lab 07: RBAC Security (Complementary access control)
- Lab 11: OPA Gatekeeper (Advanced policy enforcement)
- Lab 12: Image Scanning (Container security)

### Tools and Utilities
- [kubectl-pss](https://github.com/kubernetes-sigs/kubectl-pss) - CLI tool for PSS management
- [kubectl-neat](https://github.com/itaysk/kubectl-neat) - Clean kubectl output for review
- [Polaris](https://github.com/FairwindsOps/polaris) - Kubernetes best practices validation

---

## Quick Reference

### PSS Label Commands

```bash
# Enforce baseline on namespace
kubectl label namespace <ns> pod-security.kubernetes.io/enforce=baseline

# Enforce restricted on namespace
kubectl label namespace <ns> pod-security.kubernetes.io/enforce=restricted

# Mixed mode (enforce baseline, warn restricted)
kubectl label namespace <ns> \
  pod-security.kubernetes.io/enforce=baseline \
  pod-security.kubernetes.io/warn=restricted

# Pin to specific version
kubectl label namespace <ns> \
  pod-security.kubernetes.io/enforce=baseline \
  pod-security.kubernetes.io/enforce-version=v1.28

# Remove PSS labels
kubectl label namespace <ns> \
  pod-security.kubernetes.io/enforce- \
  pod-security.kubernetes.io/audit- \
  pod-security.kubernetes.io/warn-
```

### Security Level Requirements

**Baseline Profile Blocks:**
- ❌ privileged: true
- ❌ hostNetwork: true
- ❌ hostPID: true
- ❌ hostIPC: true
- ❌ hostPath volumes
- ❌ Dangerous capabilities (SYS_ADMIN, NET_ADMIN, etc.)

**Restricted Profile Requires:**
- ✅ runAsNonRoot: true
- ✅ allowPrivilegeEscalation: false
- ✅ capabilities.drop: ["ALL"]
- ✅ seccompProfile.type: RuntimeDefault or Localhost

### Minimal Compliant Configurations

**Baseline-compliant Pod:**
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: baseline-pod
spec:
  containers:
  - name: app
    image: myapp:latest
    securityContext:
      allowPrivilegeEscalation: false
```

**Restricted-compliant Pod:**
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: restricted-pod
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    seccompProfile:
      type: RuntimeDefault
  containers:
  - name: app
    image: myapp:latest
    securityContext:
      allowPrivilegeEscalation: false
      capabilities:
        drop:
        - ALL
```

---

**Lab Created**: March 2026
**Compatible with**: Kubernetes 1.25+
**Replaces**: PodSecurityPolicy (deprecated in 1.21, removed in 1.25)
**Prerequisites**: Lab 09 (Security Context) recommended
**Estimated Time**: 60-75 minutes
**CKA Exam Domain**: Cluster Hardening (15%)
