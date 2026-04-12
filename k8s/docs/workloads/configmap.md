### **ConfigMaps in Kubernetes: A Brief Overview**

#### **What is a ConfigMap?**
A **ConfigMap** is a Kubernetes object used to decouple application configuration from the containerized application code. It stores configuration data as key-value pairs, which can be injected into Pods as environment variables, command-line arguments, or mounted as files.

#### **Use Cases**
1. **Application Configuration:**
   - Storing database connection strings, feature flags, or API endpoints.
2. **Environment Management:**
   - Changing configuration values without rebuilding or redeploying containers.
3. **Shared Configuration:**
   - Sharing common configuration data across multiple Pods.

#### **Benefits**
- **Separation of Concerns:** Keeps application configuration separate from the code.
- **Flexibility:** Supports dynamic updates without requiring Pod restarts (when mounted as files).
- **Portability:** Simplifies application deployment across environments (e.g., development, staging, production).

> **Deep dive:** For volume-mount patterns, projected volumes, and live-reload behavior, see [ConfigMap as a Volume](../storage/configmap-volume.md).

---

### **How ConfigMaps are Consumed**

1. **All keys as environment variables** — `envFrom` with `configMapRef`.
2. **Selected keys** — `valueFrom.configMapKeyRef` on individual `env` entries.
3. **Files** — mount the ConfigMap as a volume; each key becomes a file under the mount path.

#### **Example: ConfigMap and Pod (envFrom)**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: example-configmap
data:
  database: mongodb
  database_uri: mongodb://localhost:27017
---
apiVersion: v1
kind: Pod
metadata:
  name: pod-env-var
spec:
  containers:
  - name: app
    image: nginx:1.7.9
    envFrom:
    - configMapRef:
        name: example-configmap
```

#### **Example: Single key as an environment variable**

```yaml
env:
- name: DATABASE_KIND
  valueFrom:
    configMapKeyRef:
      name: example-configmap
      key: database
```

#### **Example: Mounted as files**

```yaml
spec:
  containers:
  - name: app
    image: docker.io/httpd
    volumeMounts:
    - name: config-volume
      mountPath: /tmp/myenvs/
  volumes:
  - name: config-volume
    configMap:
      name: example-configmap
```

---

### **Summary**
ConfigMaps provide a clean way to manage application configuration separate from container images. They support environment injection and file-based configuration, which improves portability and operational flexibility.

**Benefits of ConfigMaps:**
- Decouples configuration from application code.
- Simplifies updates across multiple environments.
- Avoids hardcoding configuration values in containers.

---

## Hands-On Labs

Practice these concepts with guided lab exercises:

| Lab | Description |
|-----|-------------|
| [Lab 25: ConfigMaps in Kubernetes](../../labmanuals/lab25-workload-configmaps.md) | Create ConfigMaps, inject keys as env vars, and mount configuration as volumes. |
