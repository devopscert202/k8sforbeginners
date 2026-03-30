# Lab 47: Kubernetes Secrets

## Overview
In this lab, you will learn how to use Kubernetes Secrets to store and manage sensitive data such as passwords, API keys, TLS certificates, and Docker registry credentials. Secrets keep confidential information out of container images and Pod specs, enabling independent lifecycle management for sensitive data.

## Prerequisites
- A running Kubernetes cluster (kubeadm, Kind, or any K8s cluster)
- `kubectl` CLI tool installed and configured
- Completion of Lab 25 (ConfigMaps) is recommended for context on how configuration injection works

## Learning Objectives
By the end of this lab, you will be able to:
- Create Opaque, TLS, and Docker-registry Secrets (imperative and declarative)
- Inject Secret data as environment variables in Pods
- Mount Secrets as files in Pod volumes
- Decode and inspect Secret values
- Understand Secret types and when to use each one
- Apply security best practices for Secret management

---

## What is a Secret?

A **Secret** is a Kubernetes object that holds a small amount of sensitive data — passwords, tokens, keys, or certificates. Secrets keep these values separate from Pod specs and container images.

**Key Characteristics:**
- Values are **base64-encoded** in the API (not encrypted by default)
- Maximum size: **1 MiB** per Secret
- **Namespace-scoped** — Pods can only reference Secrets in the same namespace
- Can be consumed as **environment variables** or **volume-mounted files**
- Supports typed validation via the `type:` field

> **Important:** Base64 encoding is **not** encryption. Enable etcd encryption-at-rest for real protection.

---

## Exercise 1: Creating an Opaque Secret (Imperative)

### Step 1: Create a Secret from Literal Values

```bash
kubectl create secret generic db-credentials \
  --from-literal=username=admin \
  --from-literal=password='p@ssw0rd'
```

Expected output:
```
secret/db-credentials created
```

### Step 2: Verify the Secret

```bash
kubectl get secrets
```

Expected output:
```
NAME              TYPE     DATA   AGE
db-credentials    Opaque   2      5s
```

### Step 3: Describe the Secret

```bash
kubectl describe secret db-credentials
```

Expected output (note that values are hidden):
```
Name:         db-credentials
Namespace:    default
Type:         Opaque

Data
====
password:  8 bytes
username:  5 bytes
```

### Step 4: Decode Secret Values

```bash
kubectl get secret db-credentials -o jsonpath='{.data.username}' | base64 -d
echo ""
kubectl get secret db-credentials -o jsonpath='{.data.password}' | base64 -d
echo ""
```

Expected output:
```
admin
p@ssw0rd
```

### Step 5: View the Full Secret YAML

```bash
kubectl get secret db-credentials -o yaml
```

Notice the `data` section contains base64-encoded values.

---

## Exercise 2: Creating a Secret from YAML (Declarative)

### Step 1: Encode Values

```bash
echo -n 'mydbuser' | base64
echo -n 'S3cur3P@ss!' | base64
```

Expected output:
```
bXlkYnVzZXI=
UzNjdXIzUEBzcyE=
```

### Step 2: Create the Secret YAML

Create a file called `app-secret.yaml`:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secret
type: Opaque
data:
  db-user: bXlkYnVzZXI=
  db-pass: UzNjdXIzUEBzcyE=
```

### Step 3: Apply the Secret

```bash
kubectl apply -f app-secret.yaml
```

### Step 4: Verify

```bash
kubectl get secret app-secret -o jsonpath='{.data.db-user}' | base64 -d
echo ""
```

Expected output:
```
mydbuser
```

---

## Exercise 3: Using stringData (Plain-Text Convenience)

### Step 1: Create a Secret with stringData

Create a file called `api-secret.yaml`:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: api-secret
type: Opaque
stringData:
  api-key: my-super-secret-api-key
  connection-string: "postgresql://user:pass@db:5432/mydb"
```

### Step 2: Apply and Verify

```bash
kubectl apply -f api-secret.yaml
kubectl get secret api-secret -o yaml
```

Notice that Kubernetes automatically base64-encodes the `stringData` values and stores them under `data`.

---

## Exercise 4: Consuming Secrets as Environment Variables

### Step 1: Create a Pod with Secret Env Vars

Create a file called `secret-env-pod.yaml`:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: secret-env-pod
spec:
  containers:
  - name: app
    image: busybox
    command: ["sh", "-c", "echo DB_USER=$DB_USER DB_PASS=$DB_PASS && sleep 3600"]
    env:
    - name: DB_USER
      valueFrom:
        secretKeyRef:
          name: db-credentials
          key: username
    - name: DB_PASS
      valueFrom:
        secretKeyRef:
          name: db-credentials
          key: password
  restartPolicy: Never
```

### Step 2: Apply and Check Logs

```bash
kubectl apply -f secret-env-pod.yaml
kubectl logs secret-env-pod
```

Expected output:
```
DB_USER=admin DB_PASS=p@ssw0rd
```

### Step 3: Verify Environment Inside the Container

```bash
kubectl exec secret-env-pod -- env | grep DB_
```

---

## Exercise 5: Consuming All Keys with envFrom

### Step 1: Create a Pod Using envFrom

Create a file called `secret-envfrom-pod.yaml`:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: secret-envfrom-pod
spec:
  containers:
  - name: app
    image: busybox
    command: ["sh", "-c", "echo username=$username password=$password && sleep 3600"]
    envFrom:
    - secretRef:
        name: db-credentials
  restartPolicy: Never
```

### Step 2: Apply and Check

```bash
kubectl apply -f secret-envfrom-pod.yaml
kubectl logs secret-envfrom-pod
```

Expected output:
```
username=admin password=p@ssw0rd
```

---

## Exercise 6: Mounting Secrets as Volume Files

### Step 1: Create a Pod with Secret Volume Mount

Create a file called `secret-vol-pod.yaml`:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: secret-vol-pod
spec:
  containers:
  - name: app
    image: busybox
    command: ["sh", "-c", "ls -la /etc/secrets && cat /etc/secrets/username && echo '' && cat /etc/secrets/password && sleep 3600"]
    volumeMounts:
    - name: creds
      mountPath: /etc/secrets
      readOnly: true
  volumes:
  - name: creds
    secret:
      secretName: db-credentials
      defaultMode: 0400
  restartPolicy: Never
```

### Step 2: Apply and Check

```bash
kubectl apply -f secret-vol-pod.yaml
kubectl logs secret-vol-pod
```

Expected output:
```
total 0
lrwxrwxrwx    1 root     root            15 ...  password -> ..data/password
lrwxrwxrwx    1 root     root            15 ...  username -> ..data/username
admin
p@ssw0rd
```

### Step 3: Verify File Permissions

```bash
kubectl exec secret-vol-pod -- stat /etc/secrets/username
```

Note the `0400` permissions set by `defaultMode`.

---

## Exercise 7: Creating a TLS Secret

### Step 1: Generate a Self-Signed Certificate

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout tls.key -out tls.crt \
  -subj "/CN=myapp.example.com"
```

### Step 2: Create the TLS Secret

```bash
kubectl create secret tls my-tls-secret \
  --cert=tls.crt \
  --key=tls.key
```

### Step 3: Verify

```bash
kubectl describe secret my-tls-secret
```

Expected output shows type `kubernetes.io/tls` with keys `tls.crt` and `tls.key`.

### Step 4: Clean Up Certificates

```bash
rm tls.crt tls.key
```

---

## Exercise 8: Creating a Docker Registry Secret

### Step 1: Create the Registry Secret

```bash
kubectl create secret docker-registry regcred \
  --docker-server=https://index.docker.io/v1/ \
  --docker-username=myuser \
  --docker-password=mypass \
  --docker-email=me@example.com
```

### Step 2: Verify the Type

```bash
kubectl get secret regcred -o jsonpath='{.type}'
echo ""
```

Expected output:
```
kubernetes.io/dockerconfigjson
```

### Step 3: Reference in a Pod

Create a file called `private-image-pod.yaml`:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: private-image-pod
spec:
  containers:
  - name: app
    image: myuser/private-app:latest
  imagePullSecrets:
  - name: regcred
  restartPolicy: Never
```

> **Note:** This Pod will fail unless `myuser/private-app:latest` exists. The point is to understand how `imagePullSecrets` references a docker-registry Secret.

---

## Exercise 9: Dry-Run YAML Generation

### Step 1: Generate a Secret YAML Without Creating It

```bash
kubectl create secret generic generated-secret \
  --from-literal=token=abc123 \
  --dry-run=client -o yaml
```

This is useful for creating Secret manifests that you can store (carefully) or pipe into other tools.

---

## Exercise 10: Immutable Secrets (K8s 1.21+)

### Step 1: Create an Immutable Secret

Create a file called `immutable-secret.yaml`:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: immutable-secret
type: Opaque
immutable: true
stringData:
  static-key: this-value-cannot-change
```

```bash
kubectl apply -f immutable-secret.yaml
```

### Step 2: Attempt to Modify

```bash
kubectl patch secret immutable-secret -p '{"stringData":{"static-key":"new-value"}}'
```

Expected: the API server rejects the change because the Secret is immutable.

---

## Key Takeaways

| Concept | Summary |
|---------|---------|
| **Secret** | Stores sensitive data (passwords, tokens, certs) as base64-encoded key/value pairs |
| **Opaque** | Default type for arbitrary key/value secrets |
| **TLS** | Validated type requiring `tls.crt` and `tls.key` |
| **docker-registry** | Image pull credentials for private registries |
| **stringData** | Convenience field — Kubernetes encodes values for you |
| **secretKeyRef** | Inject a single key as an env var |
| **secretRef (envFrom)** | Inject all keys as env vars |
| **Volume mount** | Project Secret keys as files; supports auto-update |
| **Immutable** | `immutable: true` prevents modifications (K8s 1.21+) |
| **Encryption at rest** | Required for real protection — base64 is not encryption |

---

## Troubleshooting

### Secret not found by Pod
```bash
# Verify the Secret exists in the same namespace as the Pod
kubectl get secrets -n <namespace>
```

### Base64 decode errors
```bash
# Ensure you used -n flag (no newline) when encoding
echo -n 'value' | base64
```

### Permission denied reading mounted Secret files
```bash
# Check defaultMode in the volume spec
kubectl get pod <name> -o yaml | grep -A5 defaultMode
```

---

## Cleanup

```bash
kubectl delete pod secret-env-pod secret-envfrom-pod secret-vol-pod --ignore-not-found
kubectl delete secret db-credentials app-secret api-secret my-tls-secret regcred immutable-secret generated-secret --ignore-not-found
kubectl delete -f private-image-pod.yaml --ignore-not-found
rm -f app-secret.yaml api-secret.yaml secret-env-pod.yaml secret-envfrom-pod.yaml secret-vol-pod.yaml private-image-pod.yaml immutable-secret.yaml
```

---

## Next Steps

- **Lab 25: ConfigMaps** — Compare Secrets with ConfigMaps for non-sensitive data
- **Lab 39: Persistent Storage** — Combine Secrets with PVs for stateful apps
- **Lab 12: Security Context** — Restrict container privileges alongside Secret usage
- **Interactive HTML**: [Secrets Management](../html/secrets-management.html) — Visual explainer for Secret consumption patterns
