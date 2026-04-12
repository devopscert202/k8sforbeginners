# ConfigMap as a volume

## Overview
Kubernetes ConfigMaps store configuration data as key-value pairs and decouple configuration from container images. Mounting a ConfigMap as a **volume** exposes each key as a file under a directory you choose, so applications can read settings like ordinary files. When the ConfigMap is updated, kubelet syncs projected files over time (behavior depends on kubelet sync and how the app reloads config).

> **Concepts:** For ConfigMap creation, environment variable injection, and general use cases, see [ConfigMaps](../workloads/configmap.md).

## Concept
A ConfigMap mounted as a volume maps **keys to filenames** and **values to file contents**. Multiple containers in a Pod can mount the same ConfigMap. This complements other consumption patterns (environment variables, `envFrom`, or the `subPath` field for a single file).

## Benefits
- **Separation of config and code**: Keeps configuration out of images and build pipelines.
- **Live updates**: File contents can reflect ConfigMap changes without rebuilding images (apps must reload or watch files to benefit).
- **Simpler multi-key config**: Several files from one object instead of many env vars.

## Use cases
- Application config files (feature flags, non-secret tuning).
- Environment-specific settings via different ConfigMaps per namespace or overlay.
- Sidecar or main container sharing the same mounted directory.

## Example manifests

**ConfigMap** with two keys:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  database_url: "jdbc:mysql://localhost:3306/mydb"
  api_key: "your-api-key-here"
```

**Deployment** mounting that ConfigMap at `/etc/config`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: configmap-deployment
spec:
  replicas: 1
  selector:
    matchLabels:
      app: configmap-app
  template:
    metadata:
      labels:
        app: configmap-app
    spec:
      containers:
      - name: configmap-container
        image: nginx
        volumeMounts:
        - name: config-volume
          mountPath: /etc/config
      volumes:
      - name: config-volume
        configMap:
          name: app-config
```

Under `/etc/config`, Kubernetes creates files named `database_url` and `api_key` with the corresponding values. Prefer **Secrets** (or external secret stores) for credentials rather than plain ConfigMaps.

---

## Hands-On Labs

Practice these concepts with guided lab exercises:

| Lab | Description |
|-----|-------------|
| [Lab 25: Workload ConfigMaps](../../labmanuals/lab25-workload-configmaps.md) | Create ConfigMaps and wire them into workloads |
