# Lab 34: Kubernetes Dashboard

## Overview
In this lab, you will learn about the Kubernetes Dashboard, a web-based user interface for managing and monitoring Kubernetes clusters. The Dashboard provides a graphical interface to view cluster resources, deploy applications, troubleshoot issues, and perform administrative tasks. You'll install the Dashboard, configure secure access, explore its features, and understand security best practices.

## Prerequisites
- A running Kubernetes cluster (Minikube, Kind, or any K8s cluster)
- `kubectl` CLI tool installed and configured
- Cluster admin access
- Basic understanding of Pods, Deployments, and Services (Lab 01-02)
- Understanding of Kubernetes RBAC
- Metrics Server installed (Lab 30) - recommended for full functionality

## Learning Objectives
By the end of this lab, you will be able to:
- Understand Kubernetes Dashboard architecture and features
- Install and deploy Kubernetes Dashboard
- Configure secure access methods
- Create and manage ServiceAccounts for Dashboard access
- Use Dashboard to view and manage cluster resources
- Deploy applications through the Dashboard UI
- Troubleshoot issues using Dashboard
- Understand Dashboard security considerations
- Implement Dashboard best practices

---

## What is Kubernetes Dashboard?

**Kubernetes Dashboard** is a general-purpose, web-based UI for Kubernetes clusters. It allows users to manage applications running in the cluster and troubleshoot them, as well as manage the cluster itself.

### Key Features

- **Cluster Overview**: View cluster health and resource usage
- **Workload Management**: Deploy, scale, and manage applications
- **Resource Viewing**: Browse Pods, Services, ConfigMaps, Secrets
- **Log Viewing**: Access container logs
- **Shell Access**: Execute commands in containers
- **Resource Metrics**: View CPU and memory usage
- **YAML Editor**: Edit resource configurations
- **Resource Creation**: Create resources from YAML or forms

### Dashboard Architecture

```
┌──────────────────────────────────────────────┐
│           Browser (User)                     │
└──────────────┬───────────────────────────────┘
               │ HTTPS (Port-Forward/Ingress)
┌──────────────▼───────────────────────────────┐
│     Kubernetes Dashboard Service             │
│     (kubernetes-dashboard namespace)         │
│  ┌────────────────────────────────────────┐ │
│  │  Dashboard Pod                         │ │
│  │  - Web Server                          │ │
│  │  - Backend API                         │ │
│  └────────────────────────────────────────┘ │
└──────────────┬───────────────────────────────┘
               │
┌──────────────▼───────────────────────────────┐
│     Kubernetes API Server                    │
│     (with ServiceAccount Token)              │
└──────────────────────────────────────────────┘
```

### Dashboard vs CLI

| Feature | Dashboard | kubectl CLI |
|---------|-----------|-------------|
| **Interface** | Graphical | Command-line |
| **Learning Curve** | Lower | Higher |
| **Speed** | Slower | Faster |
| **Automation** | Limited | Full |
| **Visualization** | Excellent | Limited |
| **Use Case** | Exploration, Monitoring | Automation, Scripting |

### Common Use Cases

1. **Cluster Monitoring**: Visual overview of cluster health
2. **Troubleshooting**: Quick access to logs and Pod status
3. **Learning**: Explore Kubernetes resources and relationships
4. **Demonstrations**: Show cluster state to stakeholders
5. **Quick Operations**: Simple deployments and scaling

---

## Exercise 1: Install Kubernetes Dashboard

### Step 1: Deploy Dashboard

Install the latest Dashboard version:

```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.7.0/aio/deploy/recommended.yaml
```

Expected output:
```
namespace/kubernetes-dashboard created
serviceaccount/kubernetes-dashboard created
service/kubernetes-dashboard created
secret/kubernetes-dashboard-certs created
secret/kubernetes-dashboard-csrf created
secret/kubernetes-dashboard-key-holder created
configmap/kubernetes-dashboard-settings created
role.rbac.authorization.k8s.io/kubernetes-dashboard created
clusterrole.rbac.authorization.k8s.io/kubernetes-dashboard created
rolebinding.rbac.authorization.k8s.io/kubernetes-dashboard created
clusterrolebinding.rbac.authorization.k8s.io/kubernetes-dashboard created
deployment.apps/kubernetes-dashboard created
service/dashboard-metrics-scraper created
deployment.apps/dashboard-metrics-scraper created
```

### Step 2: Verify Dashboard Installation

Check the namespace:

```bash
kubectl get namespace kubernetes-dashboard
```

Check all resources:

```bash
kubectl get all -n kubernetes-dashboard
```

Expected output:
```
NAME                                             READY   STATUS    RESTARTS   AGE
pod/dashboard-metrics-scraper-5cb4f4bb9c-xxxxx   1/1     Running   0          1m
pod/kubernetes-dashboard-6967859bff-xxxxx        1/1     Running   0          1m

NAME                                TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)    AGE
service/dashboard-metrics-scraper   ClusterIP   10.96.100.100   <none>        8000/TCP   1m
service/kubernetes-dashboard        ClusterIP   10.96.100.101   <none>        443/TCP    1m

NAME                                        READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/dashboard-metrics-scraper   1/1     1            1           1m
deployment.apps/kubernetes-dashboard        1/1     1            1           1m
```

### Step 3: Check Dashboard Pods

Wait for Pods to be Running:

```bash
kubectl get pods -n kubernetes-dashboard -w
```

Press `Ctrl+C` once all Pods are Running.

Check Dashboard logs:

```bash
kubectl logs -n kubernetes-dashboard deployment/kubernetes-dashboard
```

---

## Exercise 2: Create Admin User for Dashboard Access

### Step 1: Review the Admin User Manifest

Navigate to the workloads directory:
```bash
cd k8s/labs/workloads
```

View `k8s-dashboard.yaml`:

```yaml
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: admin-user
  namespace: kubernetes-dashboard
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: admin-user
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: cluster-admin
subjects:
- kind: ServiceAccount
  name: admin-user
  namespace: kubernetes-dashboard
---
```

**Understanding the manifest:**

- `ServiceAccount`: Creates an identity for Dashboard authentication
- `ClusterRoleBinding`: Grants cluster-admin privileges to the ServiceAccount
- `cluster-admin` role: Full cluster access (use carefully!)

**Security Warning**: This gives full admin access. In production, use more restrictive roles.

### Step 2: Create Admin User

Apply the manifest:

```bash
kubectl apply -f k8s-dashboard.yaml
```

Expected output:
```
serviceaccount/admin-user created
clusterrolebinding.rbac.authorization.k8s.io/admin-user created
```

### Step 3: Verify ServiceAccount Creation

Check the ServiceAccount:

```bash
kubectl get serviceaccount admin-user -n kubernetes-dashboard
```

Expected output:
```
NAME         SECRETS   AGE
admin-user   0         30s
```

Check the ClusterRoleBinding:

```bash
kubectl get clusterrolebinding admin-user
```

### Step 4: Get Authentication Token

For Kubernetes 1.24+, create a token manually:

```bash
kubectl create token admin-user -n kubernetes-dashboard
```

Expected output (save this token):
```
eyJhbGciOiJSUzI1NiIsImtpZCI6IjRxN3F2....[long token string]
```

For Kubernetes 1.23 and earlier:

```bash
kubectl get secret -n kubernetes-dashboard $(kubectl get serviceaccount admin-user -n kubernetes-dashboard -o jsonpath="{.secrets[0].name}") -o jsonpath="{.data.token}" | base64 --decode
```

**Important**: Save this token securely. You'll need it to log into the Dashboard.

To get a long-lived token (not recommended for production):

```bash
kubectl apply -f - <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: admin-user-token
  namespace: kubernetes-dashboard
  annotations:
    kubernetes.io/service-account.name: admin-user
type: kubernetes.io/service-account-token
EOF
```

Then retrieve it:

```bash
kubectl get secret admin-user-token -n kubernetes-dashboard -o jsonpath="{.data.token}" | base64 --decode
```

---

## Exercise 3: Access Dashboard Using Port-Forward

### Step 1: Start Port-Forward

Forward local port to Dashboard service:

```bash
kubectl port-forward -n kubernetes-dashboard service/kubernetes-dashboard 8443:443
```

Expected output:
```
Forwarding from 127.0.0.1:8443 -> 8443
Forwarding from [::1]:8443 -> 8443
```

**Note**: Keep this terminal window open while using the Dashboard.

### Step 2: Access Dashboard in Browser

Open your web browser and navigate to:

```
https://localhost:8443
```

You'll see a security warning because the Dashboard uses a self-signed certificate. This is normal for local development.

**In Chrome/Edge**: Click "Advanced" → "Proceed to localhost (unsafe)"
**In Firefox**: Click "Advanced" → "Accept the Risk and Continue"

### Step 3: Log In to Dashboard

You'll see the Dashboard login screen with two options:
1. **Token** (recommended)
2. **Kubeconfig**

Select **Token** and paste the token you saved earlier.

Click **Sign In**.

### Step 4: Explore Dashboard Home

After logging in, you'll see the Dashboard home page showing:
- Cluster overview
- Namespace selector
- Resource counts
- Workload status

---

## Exercise 4: Exploring Dashboard Features

### Section 1: Overview Dashboard

**Cluster Overview**:
- Navigate to: **Cluster** → **Overview**
- View cluster-wide statistics
- See resource utilization (requires Metrics Server)

**Namespace View**:
- Use the namespace dropdown (top-left)
- Select "All namespaces" to see everything
- Filter by specific namespace

### Section 2: Workloads

**Deployments**:
```
Workloads → Deployments
```
- View all deployments
- See replica counts and status
- Click on a deployment to see details

**Pods**:
```
Workloads → Pods
```
- List all Pods
- View Pod status, age, and restarts
- Click on a Pod to see:
  - Container information
  - Events
  - Logs
  - Shell access

**ReplicaSets**:
```
Workloads → Replica Sets
```
- View ReplicaSets managed by Deployments
- See desired vs actual replicas

**StatefulSets and DaemonSets**:
```
Workloads → StatefulSets
Workloads → Daemon Sets
```
- Manage stateful applications
- View node-level deployments

**Jobs and CronJobs**:
```
Workloads → Jobs
Workloads → Cron Jobs
```
- View batch workloads
- See job execution history

### Section 3: Services and Discovery

**Services**:
```
Service → Services
```
- View all Services
- See Service types (ClusterIP, NodePort, LoadBalancer)
- View endpoints

**Ingresses**:
```
Service → Ingresses
```
- View Ingress rules
- See routing configuration

### Section 4: Configuration

**ConfigMaps**:
```
Config and Storage → Config Maps
```
- View configuration data
- Edit ConfigMaps

**Secrets**:
```
Config and Storage → Secrets
```
- View Secrets (values are masked)
- Create new Secrets

**Persistent Volumes**:
```
Config and Storage → Persistent Volumes
Config and Storage → Persistent Volume Claims
```
- View storage resources
- See PVC bindings

### Section 5: RBAC

**Service Accounts**:
```
Cluster → Service Accounts
```
- View ServiceAccounts
- See associated Secrets

**Roles and ClusterRoles**:
```
Cluster → Roles
Cluster → Cluster Roles
```
- View RBAC permissions

---

## Exercise 5: Deploy Application Through Dashboard

### Step 1: Create Deployment via UI

1. Click the **"+"** button (top-right corner)
2. Select **"Create from form"**
3. Fill in the form:
   - **App name**: nginx-dashboard
   - **Container image**: nginx:latest
   - **Number of pods**: 3
   - **Service**: External, Port: 80, Target port: 80
4. Click **Deploy**

### Step 2: Create Deployment via YAML

1. Click the **"+"** button
2. Select **"Create from input"**
3. Paste the following YAML:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: webapp
  labels:
    app: webapp
spec:
  replicas: 2
  selector:
    matchLabels:
      app: webapp
  template:
    metadata:
      labels:
        app: webapp
    spec:
      containers:
      - name: webapp
        image: nginx:alpine
        ports:
        - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: webapp-service
spec:
  selector:
    app: webapp
  ports:
  - protocol: TCP
    port: 80
    targetPort: 80
  type: ClusterIP
```

4. Click **Upload**

### Step 3: View Created Resources

Navigate to **Workloads → Deployments** and find your deployments:
- nginx-dashboard
- webapp

Click on each to see:
- Pod details
- Events
- YAML configuration

### Step 4: View Application Logs

1. Navigate to **Workloads → Pods**
2. Click on one of your webapp Pods
3. Click the **"Logs"** icon (top-right)
4. View container logs in real-time
5. Use the search and filter options

### Step 5: Access Pod Shell

1. From the Pod details page
2. Click the **"Exec"** icon (terminal icon)
3. A shell opens in the container
4. Try commands:

```bash
ls -la
cat /etc/nginx/nginx.conf
curl localhost
```

---

## Exercise 6: Scale and Manage Deployments

### Step 1: Scale via Dashboard

1. Navigate to **Workloads → Deployments**
2. Click the three dots next to your webapp deployment
3. Select **"Scale"**
4. Change replicas to **5**
5. Click **Scale**

### Step 2: Monitor Scaling

1. Navigate to **Workloads → Pods**
2. Watch as new Pods are created
3. View the deployment events

### Step 3: Edit Deployment

1. Go back to **Workloads → Deployments**
2. Click on **webapp** deployment
3. Click the **"Edit"** icon (pencil icon)
4. Modify the YAML (e.g., change image tag)
5. Click **Update**

### Step 4: View Rollout Status

1. In the deployment details
2. Check the **Replica Sets** section
3. See the old and new ReplicaSets
4. View rollout events

---

## Exercise 7: Alternative Access Methods

### Method 1: kubectl proxy (Insecure - Development Only)

Start the proxy:

```bash
kubectl proxy
```

Access Dashboard at:
```
http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/
```

**Note**: This method bypasses authentication. Use only in trusted environments.

### Method 2: NodePort Service (Not Recommended)

Edit the Dashboard service:

```bash
kubectl edit service kubernetes-dashboard -n kubernetes-dashboard
```

Change `type: ClusterIP` to `type: NodePort`:

```yaml
spec:
  type: NodePort
  ports:
  - port: 443
    targetPort: 8443
    nodePort: 30443
```

Access Dashboard at:
```
https://<node-ip>:30443
```

**Security Warning**: This exposes Dashboard externally. Not recommended for production.

### Method 3: Ingress (Production)

Create an Ingress resource:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: dashboard-ingress
  namespace: kubernetes-dashboard
  annotations:
    nginx.ingress.kubernetes.io/backend-protocol: "HTTPS"
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - dashboard.example.com
    secretName: dashboard-tls
  rules:
  - host: dashboard.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: kubernetes-dashboard
            port:
              number: 443
```

Apply:

```bash
kubectl apply -f dashboard-ingress.yaml
```

Access at: `https://dashboard.example.com`

---

## Exercise 8: Create Read-Only User

### Step 1: Create Read-Only ServiceAccount

Create `dashboard-readonly.yaml`:

```yaml
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: dashboard-viewer
  namespace: kubernetes-dashboard
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: dashboard-viewer-role
rules:
- apiGroups: [""]
  resources: ["*"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["*"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["batch"]
  resources: ["*"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: dashboard-viewer-binding
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: dashboard-viewer-role
subjects:
- kind: ServiceAccount
  name: dashboard-viewer
  namespace: kubernetes-dashboard
---
```

Apply:

```bash
kubectl apply -f dashboard-readonly.yaml
```

### Step 2: Get Read-Only Token

```bash
kubectl create token dashboard-viewer -n kubernetes-dashboard
```

### Step 3: Test Read-Only Access

Log into Dashboard with this token and verify:
- Can view resources
- Cannot create, update, or delete
- Edit buttons are disabled

---

## Lab Cleanup

### Option 1: Keep Dashboard Installed

Just stop port-forward (Ctrl+C in the terminal).

### Option 2: Remove Custom Resources

```bash
# Delete ServiceAccounts and bindings
kubectl delete -f k8s-dashboard.yaml
kubectl delete -f dashboard-readonly.yaml

# Delete sample applications
kubectl delete deployment nginx-dashboard webapp
kubectl delete service webapp-service
```

### Option 3: Completely Uninstall Dashboard

```bash
# Delete all Dashboard resources
kubectl delete -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.7.0/aio/deploy/recommended.yaml

# Verify deletion
kubectl get all -n kubernetes-dashboard
```

---

## Key Takeaways

1. **Graphical Interface** - Dashboard provides visual access to cluster resources
2. **Authentication Required** - Always use token-based authentication
3. **RBAC Integration** - Permissions are controlled by ServiceAccount roles
4. **Security First** - Never expose Dashboard publicly without proper security
5. **Port-Forward for Local** - Safest access method for development
6. **Not a Replacement for kubectl** - Dashboard complements CLI, doesn't replace it
7. **Read-Only Users** - Create limited-access accounts for viewers
8. **Metrics Server Integration** - Requires Metrics Server for resource graphs

---

## Best Practices

### 1. Security Best Practices

**Never use cluster-admin in production**:

```yaml
# Bad: Full admin access
roleRef:
  kind: ClusterRole
  name: cluster-admin

# Good: Namespace-specific access
kind: Role
metadata:
  namespace: my-app
rules:
- apiGroups: ["", "apps"]
  resources: ["pods", "deployments"]
  verbs: ["get", "list", "watch", "create", "update"]
```

### 2. Access Control

```yaml
# Create namespace-specific users
apiVersion: v1
kind: ServiceAccount
metadata:
  name: dev-user
  namespace: development
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: dev-user-binding
  namespace: development
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: dev-role
subjects:
- kind: ServiceAccount
  name: dev-user
  namespace: development
```

### 3. Network Security

```bash
# Use port-forward for local access
kubectl port-forward -n kubernetes-dashboard service/kubernetes-dashboard 8443:443

# Use Ingress with TLS for production
# Add authentication proxy (OAuth, OIDC)
# Restrict network policies
```

### 4. Token Management

```bash
# Use short-lived tokens (default 1 hour)
kubectl create token admin-user -n kubernetes-dashboard --duration=1h

# For longer sessions (max 24h for v1.24+)
kubectl create token admin-user -n kubernetes-dashboard --duration=24h

# Revoke access by deleting ServiceAccount
kubectl delete serviceaccount admin-user -n kubernetes-dashboard
```

### 5. Monitoring and Auditing

```bash
# Enable audit logging for Dashboard access
# Monitor Dashboard pod logs
kubectl logs -n kubernetes-dashboard deployment/kubernetes-dashboard -f

# Set up alerts for:
# - Failed login attempts
# - Unauthorized access attempts
# - Suspicious API calls
```

### 6. Regular Updates

```bash
# Check for new versions
# https://github.com/kubernetes/dashboard/releases

# Update Dashboard
kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.7.0/aio/deploy/recommended.yaml
```

---

## Additional Commands Reference

```bash
# Install Dashboard
kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.7.0/aio/deploy/recommended.yaml

# Check Dashboard status
kubectl get all -n kubernetes-dashboard
kubectl get pods -n kubernetes-dashboard

# Access Dashboard (port-forward)
kubectl port-forward -n kubernetes-dashboard service/kubernetes-dashboard 8443:443

# Create token
kubectl create token <serviceaccount> -n kubernetes-dashboard

# Get long-lived token (K8s < 1.24)
kubectl get secret -n kubernetes-dashboard $(kubectl get sa <name> -n kubernetes-dashboard -o jsonpath="{.secrets[0].name}") -o jsonpath="{.data.token}" | base64 --decode

# View Dashboard logs
kubectl logs -n kubernetes-dashboard deployment/kubernetes-dashboard
kubectl logs -n kubernetes-dashboard deployment/dashboard-metrics-scraper

# Delete Dashboard
kubectl delete -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.7.0/aio/deploy/recommended.yaml

# Edit Dashboard service
kubectl edit service kubernetes-dashboard -n kubernetes-dashboard

# Scale Dashboard
kubectl scale deployment kubernetes-dashboard --replicas=2 -n kubernetes-dashboard
```

---

## Troubleshooting

**Issue**: Cannot access Dashboard (connection refused)

```bash
# Verify Dashboard is running
kubectl get pods -n kubernetes-dashboard

# Check service
kubectl get service kubernetes-dashboard -n kubernetes-dashboard

# Verify port-forward is active
# Run: kubectl port-forward -n kubernetes-dashboard service/kubernetes-dashboard 8443:443
```

**Issue**: "Not enough data to create a graph" in resource view

```bash
# Install Metrics Server (Lab 30)
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# Wait for metrics to be available
kubectl top nodes
kubectl top pods -n kubernetes-dashboard
```

**Issue**: Token authentication fails

```bash
# Verify ServiceAccount exists
kubectl get serviceaccount admin-user -n kubernetes-dashboard

# Verify ClusterRoleBinding
kubectl get clusterrolebinding admin-user

# Create new token
kubectl create token admin-user -n kubernetes-dashboard

# Check Dashboard logs for errors
kubectl logs -n kubernetes-dashboard deployment/kubernetes-dashboard
```

**Issue**: "Forbidden" errors when viewing resources

```bash
# Check ServiceAccount permissions
kubectl describe clusterrolebinding admin-user

# The ServiceAccount needs appropriate RBAC permissions
# For full access, bind to cluster-admin role
# For limited access, create custom roles
```

**Issue**: Dashboard pod CrashLoopBackOff

```bash
# Check pod events
kubectl describe pod -n kubernetes-dashboard -l k8s-app=kubernetes-dashboard

# View logs
kubectl logs -n kubernetes-dashboard -l k8s-app=kubernetes-dashboard --previous

# Common causes:
# - Invalid certificates
# - Resource constraints
# - Configuration errors
```

---

## Security Considerations

### Critical Security Measures

1. **Never expose Dashboard publicly without authentication**
2. **Use strong RBAC policies** - avoid cluster-admin
3. **Use TLS/HTTPS** - never HTTP
4. **Implement network policies** - restrict Dashboard access
5. **Regular token rotation** - use short-lived tokens
6. **Audit logging** - monitor Dashboard access
7. **Update regularly** - patch security vulnerabilities

### Production Security Checklist

- [ ] Dashboard behind authentication proxy (OAuth2, OIDC)
- [ ] TLS certificates from trusted CA
- [ ] Network policies restricting access
- [ ] Namespace-specific ServiceAccounts
- [ ] Short-lived tokens (1-24 hours)
- [ ] Regular security audits
- [ ] Disabled anonymous access
- [ ] Ingress with authentication
- [ ] Regular Dashboard updates

---

## Next Steps

Now that you've mastered the Kubernetes Dashboard, proceed to:
- [Lab 31: Metrics Server](lab31-metrics-server.md) - Deep dive into metrics collection
- [Lab 20: Horizontal Pod Autoscaling](lab20-hpa.md) - Use metrics for autoscaling
- [Lab 30: Health Checks and Probes](lab30-probes.md) - Implement application health monitoring
- Explore Prometheus and Grafana for advanced monitoring

## Further Reading

- [Kubernetes Dashboard GitHub](https://github.com/kubernetes/dashboard)
- [Dashboard Documentation](https://kubernetes.io/docs/tasks/access-application-cluster/web-ui-dashboard/)
- [Dashboard Access Control](https://github.com/kubernetes/dashboard/blob/master/docs/user/access-control/README.md)
- [Dashboard Installation Guide](https://github.com/kubernetes/dashboard/blob/master/docs/user/installation.md)

---

**Lab Created**: March 2026
**Compatible with**: Kubernetes 1.24+ | Dashboard v2.7.0+
