# Lab 15: ConfigMaps in Kubernetes

## Overview
In this lab, you will learn how to use ConfigMaps to manage configuration data in Kubernetes. ConfigMaps allow you to decouple configuration artifacts from container images, making your applications more portable and easier to manage.

## Prerequisites
- A running Kubernetes cluster (Minikube, Kind, or any K8s cluster)
- `kubectl` CLI tool installed and configured
- Completion of Lab 01 (Creating Pods) is recommended

## Learning Objectives
By the end of this lab, you will be able to:
- Create ConfigMaps to store configuration data
- Inject ConfigMap data as environment variables in Pods
- Mount ConfigMaps as files in Pod volumes
- Use specific keys from ConfigMaps
- Understand different ways to consume ConfigMap data

---

## What is a ConfigMap?

A **ConfigMap** is a Kubernetes object used to store non-confidential configuration data in key-value pairs. ConfigMaps help you:
- Separate configuration from application code
- Make applications portable across environments
- Update configuration without rebuilding container images
- Share configuration across multiple Pods

**Key Characteristics:**
- Stores data as key-value pairs
- Can be consumed as environment variables or mounted as files
- Maximum size: 1MB per ConfigMap
- Not suitable for sensitive data (use Secrets instead)

---

## Exercise 1: Creating a ConfigMap

### Step 1: Review the ConfigMap Manifest

Let's look at the `configmap.yaml` file:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: example-configmap
data:
  database: mongodb
  database_uri: mongodb://localhost:27017
```

**Understanding the manifest:**
- `apiVersion: v1` - Uses the core Kubernetes API
- `kind: ConfigMap` - Defines this as a ConfigMap resource
- `metadata.name: example-configmap` - Names the ConfigMap
- `data` - Contains the key-value pairs:
  - `database: mongodb` - Simple string value
  - `database_uri: mongodb://localhost:27017` - Connection string

### Step 2: Create the ConfigMap

Navigate to the workloads directory:
```bash
cd k8s/labs/workloads
```

Create the ConfigMap:
```bash
kubectl apply -f configmap.yaml
```

Expected output:
```
configmap/example-configmap created
```

### Step 3: Verify the ConfigMap

View the ConfigMap:
```bash
kubectl get configmaps
```

Expected output:
```
NAME                DATA   AGE
example-configmap   2      10s
```

Get detailed ConfigMap information:
```bash
kubectl describe configmap example-configmap
```

Expected output:
```
Name:         example-configmap
Namespace:    default
Labels:       <none>
Annotations:  <none>

Data
====
database:
----
mongodb
database_uri:
----
mongodb://localhost:27017

Events:  <none>
```

View ConfigMap data in YAML format:
```bash
kubectl get configmap example-configmap -o yaml
```

---

## Exercise 2: Using ConfigMap as Environment Variables (envFrom)

### What is envFrom?
The `envFrom` field allows you to expose all keys in a ConfigMap as environment variables in a Pod. This is useful when you want to inject multiple configuration values at once.

### Step 1: Review the Pod Manifest

Let's look at `configpod.yaml`:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod-env-var
spec:
  containers:
  - name: env-var-configmap
    image: nginx:1.7.9
    envFrom:
    - configMapRef:
        name: example-configmap
```

**Understanding the manifest:**
- `envFrom` - Injects all ConfigMap keys as environment variables
- `configMapRef.name: example-configmap` - References our ConfigMap
- All keys become environment variables (database, database_uri)

### Step 2: Deploy the Pod

```bash
kubectl apply -f configpod.yaml
```

Expected output:
```
pod/pod-env-var created
```

### Step 3: Verify Environment Variables

Wait for the Pod to be running:
```bash
kubectl get pod pod-env-var
```

Access the Pod and check environment variables:
```bash
kubectl exec pod-env-var -- env | grep -E "(database|DATABASE)"
```

Expected output:
```
database=mongodb
database_uri=mongodb://localhost:27017
```

You can also enter the Pod interactively:
```bash
kubectl exec -it pod-env-var -- /bin/bash
```

Inside the container:
```bash
echo $database
echo $database_uri
exit
```

---

## Exercise 3: Using Specific ConfigMap Keys (env with valueFrom)

### What is valueFrom?
The `valueFrom` field allows you to selectively inject specific ConfigMap keys as environment variables with custom names.

### Step 1: Review the Pod Manifest

Let's look at `config-svc.yaml`:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod-env12
spec:
  containers:
  - name: env-var-configmap
    image: nginx:1.7.9
    env:
    - name: testenv
      valueFrom:
        configMapKeyRef:
          name: example-configmap
          key: database
```

**Understanding the manifest:**
- `env` - Defines individual environment variables
- `name: testenv` - Custom environment variable name
- `valueFrom.configMapKeyRef` - References a specific ConfigMap key
- `key: database` - Uses only the "database" key from ConfigMap

### Step 2: Deploy the Pod

```bash
kubectl apply -f config-svc.yaml
```

Expected output:
```
pod/pod-env12 created
```

### Step 3: Verify the Environment Variable

Check the custom environment variable:
```bash
kubectl exec pod-env12 -- env | grep testenv
```

Expected output:
```
testenv=mongodb
```

Notice that:
- Only the selected key is available
- The environment variable has a custom name (testenv)
- Other ConfigMap keys are not exposed

---

## Exercise 4: Mounting ConfigMap as Files

### What are Volume Mounts?
You can mount ConfigMaps as files in a Pod's filesystem. Each key becomes a file, and the value becomes the file content. This is useful for configuration files.

### Step 1: Review the Pod Manifest

Let's look at `configfile.yaml`:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: testconfig
spec:
  containers:
  - name: test
    image: docker.io/httpd
    volumeMounts:
    - name: config-volume
      mountPath: /tmp/myenvs/
  volumes:
  - name: config-volume
    configMap:
      name: example-configmap
  restartPolicy: Never
```

**Understanding the manifest:**
- `volumes` - Defines a volume from the ConfigMap
- `volumes[].configMap.name` - References our ConfigMap
- `volumeMounts` - Mounts the volume into the container
- `mountPath: /tmp/myenvs/` - Directory where files will appear
- Each ConfigMap key becomes a file in this directory

### Step 2: Deploy the Pod

```bash
kubectl apply -f configfile.yaml
```

Expected output:
```
pod/testconfig created
```

### Step 3: Verify the Files

Wait for the Pod to be running:
```bash
kubectl get pod testconfig
```

List files in the mount directory:
```bash
kubectl exec testconfig -- ls -la /tmp/myenvs/
```

Expected output:
```
total 12
drwxrwxrwx 3 root root 4096 Jan 15 10:30 .
drwxrwxrwt 1 root root 4096 Jan 15 10:30 ..
drwxr-xr-x 2 root root 4096 Jan 15 10:30 ..2026_01_15_10_30_12345678
lrwxrwxrwx 1 root root   31 Jan 15 10:30 ..data -> ..2026_01_15_10_30_12345678
lrwxrwxrwx 1 root root   15 Jan 15 10:30 database -> ..data/database
lrwxrwxrwx 1 root root   19 Jan 15 10:30 database_uri -> ..data/database_uri
```

Read the file contents:
```bash
kubectl exec testconfig -- cat /tmp/myenvs/database
```

Expected output:
```
mongodb
```

```bash
kubectl exec testconfig -- cat /tmp/myenvs/database_uri
```

Expected output:
```
mongodb://localhost:27017
```

### Step 4: Understand Atomic Updates

Notice the symlink structure:
- Files are symlinks to a timestamped directory
- This enables atomic updates when ConfigMap changes
- Applications can watch for file changes without restarts

---

## Exercise 5: ConfigMap Usage Comparison

### Summary of Methods

| Method | Use Case | Example | Pros | Cons |
|--------|----------|---------|------|------|
| **envFrom** | Inject all keys as env vars | `configpod.yaml` | Simple, all keys available | Can't rename variables |
| **env with valueFrom** | Inject specific keys with custom names | `config-svc.yaml` | Selective, custom naming | Verbose for many keys |
| **volumeMounts** | Mount as configuration files | `configfile.yaml` | Supports file formats, atomic updates | More complex setup |

### When to Use Each Method

**Use envFrom when:**
- You need all ConfigMap values as environment variables
- Variable names match your application's expectations
- You're migrating from docker-compose or similar tools

**Use env with valueFrom when:**
- You need only specific ConfigMap keys
- You want to rename environment variables
- You're mapping ConfigMaps to existing application variables

**Use volumeMounts when:**
- Your application reads configuration files
- You need complex file formats (JSON, XML, YAML, properties)
- You want automatic updates without Pod restarts
- You're configuring applications like Apache, Nginx, or databases

---

## Exercise 6: Creating ConfigMaps with kubectl

### Method 1: From Literal Values

Create a ConfigMap from command line:
```bash
kubectl create configmap app-config \
  --from-literal=app_mode=production \
  --from-literal=log_level=info
```

Verify:
```bash
kubectl get configmap app-config -o yaml
```

### Method 2: From Files

Create a sample configuration file:
```bash
cat > app.properties <<EOF
server.port=8080
server.host=0.0.0.0
app.name=MyApplication
EOF
```

Create ConfigMap from file:
```bash
kubectl create configmap app-properties --from-file=app.properties
```

Verify:
```bash
kubectl describe configmap app-properties
```

### Method 3: From Directory

Create multiple configuration files:
```bash
mkdir config-dir
echo "debug=true" > config-dir/debug.conf
echo "cache_size=100" > config-dir/cache.conf
```

Create ConfigMap from directory:
```bash
kubectl create configmap app-configs --from-file=config-dir/
```

Verify:
```bash
kubectl get configmap app-configs -o yaml
```

---

## Exercise 7: Updating ConfigMaps

### Step 1: Update the ConfigMap

Edit the existing ConfigMap:
```bash
kubectl edit configmap example-configmap
```

Or update using YAML:
```bash
kubectl apply -f configmap.yaml
```

Or patch specific values:
```bash
kubectl patch configmap example-configmap \
  --type merge \
  -p '{"data":{"database":"postgresql"}}'
```

### Step 2: Observe Pod Behavior

**For environment variables:**
- Existing Pods do NOT see the changes
- You must recreate the Pod to get new values

Delete and recreate:
```bash
kubectl delete pod pod-env-var
kubectl apply -f configpod.yaml
kubectl exec pod-env-var -- env | grep database
```

**For mounted volumes:**
- Changes are reflected automatically (after ~60 seconds)
- Kubernetes uses atomic symlink updates
- Your application must watch for file changes

Test with the file-mounted Pod:
```bash
# Update ConfigMap
kubectl patch configmap example-configmap \
  --type merge \
  -p '{"data":{"database":"postgresql"}}'

# Wait a minute and check
sleep 70
kubectl exec testconfig -- cat /tmp/myenvs/database
```

Expected output:
```
postgresql
```

---

## Lab Cleanup

Remove all resources created in this lab:

```bash
# Delete Pods
kubectl delete pod pod-env-var
kubectl delete pod pod-env12
kubectl delete pod testconfig

# Delete ConfigMaps
kubectl delete configmap example-configmap
kubectl delete configmap app-config
kubectl delete configmap app-properties
kubectl delete configmap app-configs

# Verify cleanup
kubectl get configmaps
kubectl get pods
```

Alternative: Delete using YAML files:
```bash
kubectl delete -f configmap.yaml
kubectl delete -f configpod.yaml
kubectl delete -f config-svc.yaml
kubectl delete -f configfile.yaml
```

Clean up local files:
```bash
rm -f app.properties
rm -rf config-dir/
```

---

## Key Takeaways

1. **ConfigMaps** store non-sensitive configuration data as key-value pairs
2. Three main ways to consume ConfigMaps:
   - **envFrom**: All keys as environment variables
   - **env with valueFrom**: Specific keys with custom names
   - **volumeMounts**: Keys as files in the filesystem
3. Environment variables are **static** - Pod restart required for updates
4. Volume mounts support **automatic updates** - no Pod restart needed
5. Use ConfigMaps for portability across environments
6. Never store sensitive data in ConfigMaps (use Secrets instead)
7. ConfigMaps are namespace-scoped

---

## Additional Commands Reference

```bash
# List all ConfigMaps
kubectl get configmaps

# View ConfigMap details
kubectl describe configmap <name>

# View ConfigMap in YAML format
kubectl get configmap <name> -o yaml

# View ConfigMap in JSON format
kubectl get configmap <name> -o json

# Create ConfigMap from literals
kubectl create configmap <name> --from-literal=key=value

# Create ConfigMap from file
kubectl create configmap <name> --from-file=<file-path>

# Create ConfigMap from directory
kubectl create configmap <name> --from-file=<dir-path>

# Edit ConfigMap
kubectl edit configmap <name>

# Delete ConfigMap
kubectl delete configmap <name>

# Export ConfigMap to file
kubectl get configmap <name> -o yaml > configmap-backup.yaml
```

---

## Best Practices

1. **Naming Convention**: Use descriptive names (e.g., `app-config`, `db-config`)
2. **Size Limits**: Keep ConfigMaps under 1MB
3. **Namespace Organization**: Group related ConfigMaps in appropriate namespaces
4. **Version Control**: Store ConfigMap YAML files in Git
5. **Environment Separation**: Create separate ConfigMaps for dev, staging, production
6. **Documentation**: Comment your ConfigMap keys in the YAML files
7. **Testing**: Test ConfigMap changes in non-production first
8. **Immutability**: Consider using immutable ConfigMaps (Kubernetes 1.21+) for critical configs

---

## Troubleshooting

**Pod fails with "ConfigMap not found"?**
- Verify ConfigMap exists: `kubectl get configmap`
- Check ConfigMap name in Pod specification
- Ensure ConfigMap and Pod are in the same namespace

**Environment variables not showing up?**
- Verify ConfigMap was created before the Pod
- Check Pod events: `kubectl describe pod <name>`
- Restart the Pod to pick up ConfigMap changes

**Mounted files not updating?**
- Wait up to 60 seconds for propagation
- Check if volumeMount is configured correctly
- Verify Pod has read permissions

**ConfigMap too large?**
- Split into multiple ConfigMaps
- Use external configuration management tools
- Consider storing large files elsewhere (PV, object storage)

---

## Real-World Use Cases

### Use Case 1: Multi-Environment Configuration
```yaml
# configmap-dev.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: development
data:
  ENVIRONMENT: "development"
  DEBUG: "true"
  API_URL: "https://api-dev.example.com"
  LOG_LEVEL: "debug"

---
# configmap-prod.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: production
data:
  ENVIRONMENT: "production"
  DEBUG: "false"
  API_URL: "https://api.example.com"
  LOG_LEVEL: "error"
```

### Use Case 2: Application Configuration File
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: nginx-config
data:
  nginx.conf: |
    user nginx;
    worker_processes auto;
    error_log /var/log/nginx/error.log;

    events {
      worker_connections 1024;
    }

    http {
      server {
        listen 80;
        location / {
          root /usr/share/nginx/html;
          index index.html;
        }
      }
    }
```

### Use Case 3: Database Connection Pool
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: db-pool-config
data:
  max_connections: "100"
  min_connections: "10"
  connection_timeout: "30"
  pool_size: "20"
  checkout_timeout: "5"
```

---

## Next Steps

Proceed to [Lab 18: Jobs and Batch Processing](lab18-jobs-batch.md) to learn about running batch workloads and scheduled tasks in Kubernetes.

## Additional Resources

- [Kubernetes ConfigMap Documentation](https://kubernetes.io/docs/concepts/configuration/configmap/)
- [Configure Pods using ConfigMaps](https://kubernetes.io/docs/tasks/configure-pod-container/configure-pod-configmap/)
- [Secrets Management (for sensitive data)](https://kubernetes.io/docs/concepts/configuration/secret/)

---

**Lab Created**: March 2026
**Compatible with**: Kubernetes 1.24+
