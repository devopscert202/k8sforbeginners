# Lab 11: Role-Based Access Control (RBAC)

## Overview
In this lab, you will learn how to implement Role-Based Access Control (RBAC) in Kubernetes. You'll create users with certificates, define roles with specific permissions, bind users to roles, and verify access controls work as expected.

## Prerequisites
- A running Kubernetes cluster with control-plane access
- SSH access to the master node
- Root or sudo privileges
- `kubectl` configured as cluster admin
- OpenSSL installed
- Basic understanding of certificates and authentication
- Completion of Lab 01 and Lab 02 (recommended)

## Learning Objectives
By the end of this lab, you will be able to:
- Understand Kubernetes RBAC concepts
- Generate X.509 certificates for user authentication
- Create Roles with specific API permissions
- Create RoleBindings to associate users with roles
- Configure kubectl contexts for multiple users
- Test and verify permission boundaries
- Troubleshoot RBAC issues

---

## Understanding Kubernetes RBAC

### What is RBAC?
**Role-Based Access Control (RBAC)** is a method of regulating access to computer or network resources based on the roles of individual users within an organization.

In Kubernetes, RBAC allows you to:
- **Control access** to Kubernetes API resources
- **Define granular permissions** at namespace or cluster level
- **Implement least privilege principle**
- **Manage multi-tenant clusters** securely

### RBAC Components

| Component | Scope | Description |
|-----------|-------|-------------|
| **Role** | Namespace | Defines permissions within a specific namespace |
| **ClusterRole** | Cluster-wide | Defines permissions across the entire cluster |
| **RoleBinding** | Namespace | Binds a Role to users/groups/service accounts in a namespace |
| **ClusterRoleBinding** | Cluster-wide | Binds a ClusterRole to users/groups/service accounts cluster-wide |

### RBAC Rules Structure

```yaml
rules:
- apiGroups: [""]           # Core API group (empty string)
  resources: ["pods"]        # Resource type
  verbs: ["get", "list"]     # Allowed actions
```

**Common API Groups:**
- `""` - Core API (pods, services, configmaps, secrets)
- `apps` - Deployments, StatefulSets, DaemonSets
- `batch` - Jobs, CronJobs
- `networking.k8s.io` - NetworkPolicies, Ingresses

**Common Verbs:**
- `get` - Read a single resource
- `list` - List resources
- `watch` - Watch for resource changes
- `create` - Create new resources
- `update` - Update existing resources
- `patch` - Partially update resources
- `delete` - Delete resources
- `deletecollection` - Delete multiple resources

---

## Exercise 1: Environment Setup

### Step 1: Create a Namespace

Create a dedicated namespace for RBAC testing:

```bash
kubectl create namespace role
```

Expected output:
```
namespace/role created
```

Verify:
```bash
kubectl get namespace role
```

### Step 2: Create Working Directory

Create a directory to store certificates and keys:

```bash
mkdir -p ~/role
cd ~/role
```

Verify you're in the correct directory:
```bash
pwd
```

Expected output:
```
/home/<your-username>/role
```

---

## Exercise 2: Generate User Certificates

Kubernetes uses X.509 certificates for client authentication. We'll create a certificate for a user named "user3".

### Step 1: Generate Private Key

Create an RSA private key (2048 bits):

```bash
sudo openssl genrsa -out user3.key 2048
```

Expected output:
```
Generating RSA private key, 2048 bit long modulus
.......+++
............................+++
e is 65537 (0x10001)
```

**Understanding the command:**
- `genrsa` - Generate RSA key pair
- `-out user3.key` - Output file name
- `2048` - Key size in bits

Verify the key was created:
```bash
ls -lh user3.key
```

### Step 2: Create Certificate Signing Request (CSR)

Generate a CSR using the private key:

```bash
sudo openssl req -new -key user3.key -out user3.csr
```

You'll be prompted for information. Enter these values:

```
Country Name (2 letter code) [AU]: US
State or Province Name (full name) [Some-State]: California
Locality Name (eg, city) []: San Francisco
Organization Name (eg, company) [Internet Widgits Pty Ltd]: dev-team
Organizational Unit Name (eg, section) []: development
Common Name (e.g., your name or your server's hostname) []: user3
Email Address []: user3@example.com

Please enter the following 'extra' attributes
to be sent with your certificate request
A challenge password []: (leave blank)
An optional company name []: (leave blank)
```

**⚠️ IMPORTANT**: The **Common Name (CN)** must be `user3` - this becomes the username in Kubernetes!

Verify CSR was created:
```bash
ls -lh user3.csr
```

### Step 3: Sign the Certificate

Sign the CSR with the Kubernetes CA to create a valid certificate:

```bash
sudo openssl x509 -req -in user3.csr \
  -CA /etc/kubernetes/pki/ca.crt \
  -CAkey /etc/kubernetes/pki/ca.key \
  -CAcreateserial \
  -out user3.crt \
  -days 500
```

Expected output:
```
Signature ok
subject=/C=US/ST=California/L=San Francisco/O=dev-team/OU=development/CN=user3/emailAddress=user3@example.com
Getting CA Private Key
```

**Understanding the command:**
- `-req` - Process a CSR
- `-in user3.csr` - Input CSR file
- `-CA /etc/kubernetes/pki/ca.crt` - Kubernetes CA certificate
- `-CAkey /etc/kubernetes/pki/ca.key` - Kubernetes CA private key
- `-CAcreateserial` - Create a serial number file
- `-out user3.crt` - Output certificate file
- `-days 500` - Certificate validity period

### Step 4: Verify Certificate Files

List all generated files:

```bash
ls -lh user3.*
```

Expected output:
```
-rw-r--r-- 1 root root 1.3K Mar 16 16:00 user3.crt
-rw-r--r-- 1 root root 1.0K Mar 16 15:58 user3.csr
-rw-r--r-- 1 root root 1.7K Mar 16 15:55 user3.key
```

View certificate details (optional):
```bash
sudo openssl x509 -in user3.crt -text -noout | head -20
```

---

## Exercise 3: Create Role and RoleBinding

### Step 1: Create Role YAML

Create a Role that defines what user3 can do:

```bash
cat > role.yaml <<'EOF'
kind: Role
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  namespace: role
  name: user3-role
rules:
- apiGroups: ["", "extensions", "apps"]
  resources: ["deployments", "pods", "services"]
  verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
EOF
```

**Understanding the Role:**

```yaml
kind: Role                           # Namespace-scoped permissions
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  namespace: role                    # Only applies to 'role' namespace
  name: user3-role                   # Role name
rules:
- apiGroups: ["", "extensions", "apps"]  # API groups
  resources: ["deployments", "pods", "services"]  # Resource types
  verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]  # Actions allowed
```

**Permissions granted:**
- ✅ Can manage deployments, pods, and services
- ✅ Full CRUD operations (create, read, update, delete)
- ❌ Cannot access ConfigMaps, Secrets, PersistentVolumes
- ❌ Cannot access resources in other namespaces

### Step 2: Apply the Role

```bash
kubectl create -f role.yaml
```

Expected output:
```
role.rbac.authorization.k8s.io/user3-role created
```

Verify the role:
```bash
kubectl get roles -n role
```

Expected output:
```
NAME         CREATED AT
user3-role   2026-03-16T16:05:00Z
```

Describe the role to see permissions:
```bash
kubectl describe role user3-role -n role
```

### Step 3: Create RoleBinding YAML

Create a RoleBinding to associate user3 with the role:

```bash
cat > rolebinding.yaml <<'EOF'
kind: RoleBinding
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: role-test
  namespace: role
subjects:
- kind: User
  name: user3
  apiGroup: ""
roleRef:
  kind: Role
  name: user3-role
  apiGroup: ""
EOF
```

**Understanding the RoleBinding:**

```yaml
kind: RoleBinding                    # Binds user to role
metadata:
  name: role-test                    # Binding name
  namespace: role                    # Must match Role namespace
subjects:
- kind: User                         # Binding to a User
  name: user3                        # Username (from certificate CN)
  apiGroup: ""                       # rbac.authorization.k8s.io
roleRef:
  kind: Role                         # Binding to a Role
  name: user3-role                   # Role name to bind
  apiGroup: ""                       # rbac.authorization.k8s.io
```

**What this does:**
- Binds the user `user3` to the `user3-role` Role
- Only applies in the `role` namespace
- user3 inherits all permissions defined in user3-role

### Step 4: Apply the RoleBinding

```bash
kubectl create -f rolebinding.yaml
```

Expected output:
```
rolebinding.rbac.authorization.k8s.io/role-test created
```

Verify the RoleBinding:
```bash
kubectl get rolebinding -n role
```

Expected output:
```
NAME        ROLE              AGE
role-test   Role/user3-role   10s
```

Describe for details:
```bash
kubectl describe rolebinding role-test -n role
```

---

## Exercise 4: Configure kubectl for user3

### Step 1: Set User Credentials

Register user3's certificate and key with kubectl:

```bash
kubectl config set-credentials user3 \
  --client-certificate=$HOME/role/user3.crt \
  --client-key=$HOME/role/user3.key
```

Expected output:
```
User "user3" set.
```

**Understanding the command:**
- `set-credentials` - Adds user credentials to kubeconfig
- `user3` - Username identifier
- `--client-certificate` - Path to user's certificate
- `--client-key` - Path to user's private key

### Step 2: Create a Context for user3

Create a context that combines cluster, namespace, and user:

```bash
kubectl config set-context user3-context \
  --cluster=kubernetes \
  --namespace=role \
  --user=user3
```

Expected output:
```
Context "user3-context" created.
```

**Understanding contexts:**
- **Context** = Cluster + User + Namespace
- Allows quick switching between different configurations
- No need to specify namespace/user with every command

### Step 3: View All Contexts

List all available contexts:

```bash
kubectl config get-contexts
```

Expected output:
```
CURRENT   NAME                          CLUSTER      AUTHINFO           NAMESPACE
*         kubernetes-admin@kubernetes   kubernetes   kubernetes-admin
          user3-context                 kubernetes   user3              role
```

**Understanding the output:**
- `*` indicates the currently active context
- `kubernetes-admin@kubernetes` - Admin context (full permissions)
- `user3-context` - Limited user context (RBAC controlled)

### Step 4: View kubeconfig File

Inspect the complete kubeconfig:

```bash
cat ~/.kube/config
```

Look for the `users` section:
```yaml
users:
- name: kubernetes-admin
  user:
    client-certificate-data: <redacted>
    client-key-data: <redacted>
- name: user3
  user:
    client-certificate: /home/<user>/role/user3.crt
    client-key: /home/<user>/role/user3.key
```

And the `contexts` section:
```yaml
contexts:
- context:
    cluster: kubernetes
    namespace: role
    user: user3
  name: user3-context
```

---

## Exercise 5: Test RBAC Permissions

### Step 1: Switch to user3 Context

Switch from admin to user3:

```bash
kubectl config use-context user3-context
```

Expected output:
```
Switched to context "user3-context".
```

Verify the active context:
```bash
kubectl config current-context
```

Expected output:
```
user3-context
```

### Step 2: Fix Certificate Permissions

Allow user3 to read the certificate files:

```bash
cd ~/role
sudo chmod 644 user3.key user3.crt
```

**Why?** kubectl needs read access to these files when authenticating as user3.

### Step 3: Test Allowed Operations

**List pods (should work):**

```bash
kubectl get pods
```

Expected output (empty namespace):
```
No resources found in role namespace.
```

**Create a deployment (should work):**

```bash
kubectl create deployment test --image=docker.io/httpd
```

Expected output:
```
deployment.apps/test created
```

**Verify deployment:**

```bash
kubectl get deployments
```

Expected output:
```
NAME   READY   UP-TO-DATE   AVAILABLE   AGE
test   1/1     1            1           10s
```

**List pods again:**

```bash
kubectl get pods
```

Now you should see the test pod:
```
NAME                    READY   STATUS    RESTARTS   AGE
test-xxxxxxxxxx-xxxxx   1/1     Running   0          15s
```

**Delete a pod (should work):**

```bash
kubectl delete pod test-xxxxxxxxxx-xxxxx
```

(Replace with your actual pod name)

Expected output:
```
pod "test-xxxxxxxxxx-xxxxx" deleted
```

The Deployment will automatically create a new pod (self-healing).

### Step 4: Test Forbidden Operations

**Try to create a ConfigMap (should FAIL):**

```bash
kubectl create configmap my-config --from-literal=key1=config1
```

Expected output (ERROR):
```
Error from server (Forbidden): configmaps is forbidden: User "user3" cannot create resource "configmaps" in API group "" in the namespace "role"
```

**Why does this fail?**
- The Role only grants permissions for `deployments`, `pods`, and `services`
- ConfigMaps are not in the allowed resources list

**Try to list ConfigMaps (should FAIL):**

```bash
kubectl get configmaps
```

Expected output (ERROR):
```
Error from server (Forbidden): configmaps is forbidden: User "user3" cannot list resource "configmaps" in API group "" in the namespace "role"
```

**Try to access a different namespace (should FAIL):**

```bash
kubectl get pods -n default
```

Expected output (ERROR):
```
Error from server (Forbidden): pods is forbidden: User "user3" cannot list resource "pods" in API group "" in the namespace "default"
```

**Why does this fail?**
- Role and RoleBinding are namespace-scoped
- user3 only has permissions in the `role` namespace

---

## Exercise 6: Verify Permission Boundaries

### Step 1: Check What user3 Can Do

Use the `can-i` command to check permissions:

```bash
# Can user3 list pods?
kubectl auth can-i list pods --as user3 -n role
```

Expected output:
```
yes
```

```bash
# Can user3 create services?
kubectl auth can-i create services --as user3 -n role
```

Expected output:
```
yes
```

```bash
# Can user3 create configmaps?
kubectl auth can-i create configmaps --as user3 -n role
```

Expected output:
```
no
```

```bash
# Can user3 list pods in default namespace?
kubectl auth can-i list pods --as user3 -n default
```

Expected output:
```
no
```

### Step 2: Switch Back to Admin Context

Return to the admin context:

```bash
kubectl config use-context kubernetes-admin@kubernetes
```

Expected output:
```
Switched to context "kubernetes-admin@kubernetes".
```

Verify you're admin:
```bash
kubectl get pods --all-namespaces
```

This should work without errors.

---

## Exercise 7: Expanding Permissions (Optional)

### Scenario: Grant ConfigMap Access

Let's update user3-role to allow ConfigMap access.

### Step 1: Edit the Role

Edit the existing role:

```bash
kubectl edit role user3-role -n role
```

Or update the YAML file and reapply:

```bash
cat > role.yaml <<'EOF'
kind: Role
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  namespace: role
  name: user3-role
rules:
- apiGroups: ["", "extensions", "apps"]
  resources: ["deployments", "pods", "services", "configmaps"]
  verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
EOF

kubectl apply -f role.yaml
```

**Change made**: Added `"configmaps"` to the resources list.

### Step 2: Test Updated Permissions

Switch to user3 context:

```bash
kubectl config use-context user3-context
```

Try creating a ConfigMap again:

```bash
kubectl create configmap my-config --from-literal=key1=config1
```

Expected output (should work now):
```
configmap/my-config created
```

List ConfigMaps:

```bash
kubectl get configmaps
```

Expected output:
```
NAME        DATA   AGE
my-config   1      10s
```

**Success!** user3 now has ConfigMap permissions.

---

## Exercise 8: Distributing User Access (Optional)

If you want user3 to access the cluster from worker nodes or other machines:

### Step 1: Copy Certificate Files

From the master node, copy files to the target machine:

```bash
# Copy to worker node
scp ~/role/user3.crt worker-node-1:/tmp/
scp ~/role/user3.key worker-node-1:/tmp/
```

### Step 2: Set Up on Target Machine

On the worker node:

```bash
# Create directory
mkdir -p ~/role
mv /tmp/user3.crt ~/role/
mv /tmp/user3.key ~/role/

# Set up kubectl context
kubectl config set-credentials user3 \
  --client-certificate=$HOME/role/user3.crt \
  --client-key=$HOME/role/user3.key

kubectl config set-context user3-context \
  --cluster=kubernetes \
  --namespace=role \
  --user=user3

# Use the context
kubectl config use-context user3-context
```

### Step 3: Test Access

```bash
kubectl get pods
```

Should work with the same permissions as on the master node.

---

## Lab Cleanup

### Step 1: Switch to Admin Context

```bash
kubectl config use-context kubernetes-admin@kubernetes
```

### Step 2: Delete Namespace

This deletes all resources in the namespace:

```bash
kubectl delete namespace role
```

Expected output:
```
namespace "role" deleted
```

### Step 3: Remove kubectl Configuration

Remove user3 from kubeconfig:

```bash
kubectl config delete-context user3-context
kubectl config unset users.user3
```

### Step 4: Clean Up Files

Remove certificate files:

```bash
rm -rf ~/role
```

### Step 5: Verify Cleanup

```bash
kubectl config get-contexts
kubectl get namespace role
```

The namespace should be gone and user3-context removed.

---

## Key Takeaways

1. **RBAC is mandatory** for multi-user Kubernetes clusters
2. **Certificates authenticate** users to the Kubernetes API
3. **Roles define** what actions are allowed on which resources
4. **RoleBindings associate** users with Roles
5. **Namespaces provide** isolation boundaries for RBAC
6. **Contexts make** switching between users easy
7. **Least privilege** - grant only necessary permissions
8. **Regular audits** - review and update permissions periodically

---

## RBAC Best Practices

### Security
- ✅ Use namespace-scoped Roles instead of ClusterRoles when possible
- ✅ Grant minimum required permissions (least privilege principle)
- ✅ Regularly audit RoleBindings and ClusterRoleBindings
- ✅ Use ServiceAccounts for applications, not user certificates
- ✅ Rotate certificates periodically (before expiration)

### Organization
- ✅ Create Roles per team or application
- ✅ Use meaningful names (e.g., `dev-team-editor`, `app-viewer`)
- ✅ Document permissions in Role descriptions
- ✅ Use groups instead of individual users for easier management
- ✅ Separate read-only and read-write Roles

### Testing
- ✅ Always test RBAC rules after creation
- ✅ Use `kubectl auth can-i` to verify permissions
- ✅ Test both allowed and forbidden actions
- ✅ Validate in staging before applying to production

---

## Common RBAC Patterns

### Read-Only User

```yaml
rules:
- apiGroups: ["", "apps", "batch"]
  resources: ["*"]
  verbs: ["get", "list", "watch"]
```

### Developer Role

```yaml
rules:
- apiGroups: ["", "apps", "batch"]
  resources: ["pods", "deployments", "services", "configmaps", "secrets"]
  verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
```

### Namespace Admin

```yaml
rules:
- apiGroups: ["*"]
  resources: ["*"]
  verbs: ["*"]
```

---

## Troubleshooting Guide

### Issue: "x509: certificate signed by unknown authority"

**Cause**: Certificate not signed by Kubernetes CA

**Solution**:
```bash
# Ensure you're using the correct CA
ls -l /etc/kubernetes/pki/ca.crt
ls -l /etc/kubernetes/pki/ca.key

# Re-sign certificate
sudo openssl x509 -req -in user3.csr \
  -CA /etc/kubernetes/pki/ca.crt \
  -CAkey /etc/kubernetes/pki/ca.key \
  -CAcreateserial -out user3.crt -days 500
```

### Issue: "Forbidden: User cannot create resource"

**Cause**: Missing permissions in Role

**Solution**:
```bash
# Check current role
kubectl describe role user3-role -n role

# Check if RoleBinding exists
kubectl get rolebinding -n role

# Verify user in RoleBinding
kubectl describe rolebinding role-test -n role
```

### Issue: "error: You must be logged in to the server"

**Cause**: Certificate file permissions or path issues

**Solution**:
```bash
# Fix permissions
chmod 644 ~/role/user3.crt
chmod 644 ~/role/user3.key

# Verify paths in kubeconfig
kubectl config view | grep client-certificate
```

### Issue: Context not switching

**Cause**: Context not properly created

**Solution**:
```bash
# Recreate context
kubectl config set-context user3-context \
  --cluster=kubernetes \
  --namespace=role \
  --user=user3

# List contexts
kubectl config get-contexts
```

---

## Additional Commands Reference

### RBAC Discovery
```bash
# List all roles in a namespace
kubectl get roles -n <namespace>

# List all rolebindings in a namespace
kubectl get rolebindings -n <namespace>

# List all clusterroles
kubectl get clusterroles

# List all clusterrolebindings
kubectl get clusterrolebindings

# Describe a role
kubectl describe role <role-name> -n <namespace>

# Describe a rolebinding
kubectl describe rolebinding <binding-name> -n <namespace>
```

### Permission Checking
```bash
# Check current user permissions
kubectl auth can-i create pods
kubectl auth can-i get secrets -n kube-system

# Check another user's permissions
kubectl auth can-i list pods --as user3 -n role
kubectl auth can-i delete deployments --as user3 -n default

# List all permissions for current user
kubectl auth can-i --list
```

### Certificate Management
```bash
# View certificate details
openssl x509 -in user3.crt -text -noout

# Check certificate expiration
openssl x509 -in user3.crt -noout -dates

# Verify certificate is signed by CA
openssl verify -CAfile /etc/kubernetes/pki/ca.crt user3.crt
```

---

## Next Steps

After mastering RBAC:
1. Explore **ServiceAccounts** for pod authentication
2. Learn about **ClusterRoles and ClusterRoleBindings** for cluster-wide permissions
3. Implement **Pod Security Policies** (PSP) or **Pod Security Standards**
4. Set up **Audit Logging** to track RBAC events
5. Integrate with **LDAP/Active Directory** for enterprise user management

---

## Additional Reading

- [Kubernetes RBAC Documentation](https://kubernetes.io/docs/reference/access-authn-authz/rbac/)
- [Certificate-based Authentication](https://kubernetes.io/docs/reference/access-authn-authz/authentication/#x509-client-certs)
- [Using RBAC Authorization](https://kubernetes.io/docs/reference/access-authn-authz/rbac/)
- [Configure Service Accounts](https://kubernetes.io/docs/tasks/configure-pod-container/configure-service-account/)

---

**Lab Created**: March 2026
**Compatible with**: Kubernetes 1.24+
**Based on**: docs/security/rbac-concepts.md, labs/security/role.yaml, labs/security/rolebinding.yaml
**Tested on**: kubeadm clusters
**Estimated Time**: 60-75 minutes
