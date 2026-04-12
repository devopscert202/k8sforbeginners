# Secrets mounted as volumes

## Overview
Kubernetes **Secrets** hold sensitive data (tokens, TLS material, credentials). Mounting a Secret as a **volume** exposes each key as a file under a chosen directory, with optional **read-only** mounts to reduce accidental modification. This is one consumption pattern alongside environment variables and `envFrom` (which are easier to leak via logs and process listings—volume mounts are often preferable for files).

## Concept
When a Secret is mounted as a volume, **each key becomes a filename** and the **decoded value** is the file body. Kubernetes stores Secrets at rest encrypted depending on cluster configuration (e.g. encryption at rest). Rotation still requires updating the Secret object and application reload behavior.

## Benefits
- **File-shaped secrets** for apps that read paths like `/etc/secrets/tls.crt`.
- **Read-only volume** reduces risk compared to writable config.
- **No secret literals in Pod command lines** when only files are needed.

## Use cases
- TLS keys and certificates for ingress sidecars or mesh proxies.
- Database credentials consumed as files by legacy frameworks.
- Token files for workloads that expect filesystem-based auth.

## Example manifests

**Secret** (values are base64-encoded in the API; prefer `stringData` for hand-authored manifests or tools that encode for you):

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: db-credentials
type: Opaque
data:
  username: c3VwZXJ1c2Vy # base64 for 'superuser'
  password: cGFzc3dvcmQ= # base64 for 'password'
```

**Deployment** mounting the Secret read-only at `/etc/secrets`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: secret-deployment
spec:
  replicas: 1
  selector:
    matchLabels:
      app: secret-app
  template:
    metadata:
      labels:
        app: secret-app
    spec:
      containers:
      - name: secret-container
        image: nginx
        volumeMounts:
        - name: secret-volume
          mountPath: /etc/secrets
          readOnly: true
      volumes:
      - name: secret-volume
        secret:
          secretName: db-credentials
```

Files appear as `/etc/secrets/username` and `/etc/secrets/password`. For production, integrate with a secret manager or CSI driver where possible instead of long-lived static Secrets in Git.

---

## Hands-On Labs

Practice these concepts with guided lab exercises:

| Lab | Description |
|-----|-------------|
| [Lab 47: Workload Secrets](../../labmanuals/lab47-workload-secrets.md) | Create Secrets and use them in Pods |
