# Lab 48: Helm Charts — Kubernetes Package Manager

## Overview
In this lab, you will learn how to use Helm — the Kubernetes package manager — to install, configure, upgrade, rollback, and manage applications on your cluster. You will install Helm on Ubuntu, add repositories, deploy real charts, override values for different environments, create your own chart, and master the essential Helm command set.

## Prerequisites
- A running Kubernetes cluster (kubeadm, Kind, or any K8s cluster)
- `kubectl` CLI tool installed and configured
- Internet access (to download Helm and fetch charts from public repositories)
- Completion of Lab 01 (Pods) and Lab 02 (Services) is recommended

## Learning Objectives
By the end of this lab, you will be able to:
- Install Helm on Ubuntu / Linux / macOS
- Add, search, and manage chart repositories
- Install, upgrade, and rollback Helm releases
- Override chart values with `--set` and custom `values.yaml` files
- Inspect chart structure and rendered templates
- Create, lint, and package your own Helm chart
- Use `helm template` and `--dry-run` for debugging
- Understand Helm vs Kustomize vs plain `kubectl apply`

---

## What is Helm?

**Helm** is the package manager for Kubernetes. It packages Kubernetes manifests into reusable **charts** — versioned, configurable bundles that can be shared via repositories.

**Key Concepts:**

| Term | Meaning |
|------|---------|
| **Chart** | A package of templated Kubernetes YAML plus metadata |
| **Release** | A named instance of a chart running in the cluster |
| **Repository** | An HTTP server hosting packaged charts |
| **Values** | Configuration parameters that customize a chart at install time |
| **Revision** | A version of a release — every upgrade creates a new revision |

**Why Helm?**
- Deploy complex multi-resource apps with a single command
- Consistent, repeatable deployments across environments
- Built-in revision history and rollback
- Thousands of community charts on ArtifactHub

---

## Exercise 1: Installing Helm

### Option A — Official Install Script (Recommended)

```bash
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
```

### Option B — APT Package Manager (Debian / Ubuntu)

```bash
curl https://baltocdn.com/helm/signing.asc | gpg --dearmor | \
  sudo tee /usr/share/keyrings/helm.gpg > /dev/null

echo "deb [arch=$(dpkg --print-architecture) \
  signed-by=/usr/share/keyrings/helm.gpg] \
  https://baltocdn.com/helm/stable/debian/ all main" | \
  sudo tee /etc/apt/sources.list.d/helm-stable-debian.list

sudo apt-get update
sudo apt-get install helm
```

### Option C — Snap

```bash
sudo snap install helm --classic
```

### Option D — Manual Binary Download

```bash
HELM_VERSION="v3.16.3"
wget https://get.helm.sh/helm-${HELM_VERSION}-linux-amd64.tar.gz
tar -zxvf helm-${HELM_VERSION}-linux-amd64.tar.gz
sudo mv linux-amd64/helm /usr/local/bin/helm
rm -rf linux-amd64 helm-${HELM_VERSION}-linux-amd64.tar.gz
```

### Option E — macOS (Homebrew)

```bash
brew install helm
```

### Verify Installation

```bash
helm version
```

Expected output (version numbers may vary):
```
version.BuildInfo{Version:"v3.16.3", GitCommit:"...", GitTreeState:"clean", GoVersion:"go1.22.x"}
```

---

## Exercise 2: Adding and Managing Repositories

### Step 1: Add Popular Repositories

```bash
# Bitnami — extensive collection of production-grade charts
helm repo add bitnami https://charts.bitnami.com/bitnami

# Ingress-NGINX
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx

# Prometheus Community
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
```

### Step 2: Update the Local Cache

```bash
helm repo update
```

### Step 3: List Repositories

```bash
helm repo list
```

Expected output:
```
NAME                    URL
bitnami                 https://charts.bitnami.com/bitnami
ingress-nginx           https://kubernetes.github.io/ingress-nginx
prometheus-community    https://prometheus-community.github.io/helm-charts
```

### Step 4: Search for Charts

```bash
# Search local repos
helm search repo nginx

# Search ArtifactHub (public)
helm search hub wordpress
```

### Step 5: Remove a Repository

```bash
helm repo remove ingress-nginx
helm repo list
```

---

## Exercise 3: Inspecting a Chart Before Installing

### Step 1: Show Chart Metadata

```bash
helm show chart bitnami/nginx
```

### Step 2: Show Default Values

```bash
helm show values bitnami/nginx
```

Pipe to a file for easy reading:
```bash
helm show values bitnami/nginx > nginx-defaults.yaml
less nginx-defaults.yaml
```

### Step 3: Pull and Explore Locally

```bash
helm pull bitnami/nginx --untar
ls nginx/
cat nginx/Chart.yaml
cat nginx/values.yaml | head -50
```

Clean up:
```bash
rm -rf nginx/ nginx-defaults.yaml
```

---

## Exercise 4: Installing a Chart

### Step 1: Install NGINX

```bash
helm install my-nginx bitnami/nginx --namespace helm-lab --create-namespace
```

Expected output includes release name, namespace, status, and post-install notes.

### Step 2: Check the Release

```bash
helm list -n helm-lab
```

### Step 3: Check Kubernetes Resources

```bash
kubectl get all -n helm-lab
```

### Step 4: View Release Status and Notes

```bash
helm status my-nginx -n helm-lab
```

---

## Exercise 5: Installing with Custom Values

### Step 1: Install with --set

```bash
helm install my-nginx-custom bitnami/nginx \
  --namespace helm-lab \
  --set replicaCount=3 \
  --set service.type=ClusterIP
```

### Step 2: Verify Override

```bash
helm get values my-nginx-custom -n helm-lab
kubectl get pods -n helm-lab -l app.kubernetes.io/instance=my-nginx-custom
```

### Step 3: Install with a Custom Values File

Create `values-prod.yaml`:

```yaml
replicaCount: 2
service:
  type: ClusterIP
resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 250m
    memory: 256Mi
```

```bash
helm install my-nginx-prod bitnami/nginx \
  --namespace helm-lab \
  -f values-prod.yaml
```

---

## Exercise 6: Upgrading a Release

### Step 1: Upgrade Replica Count

```bash
helm upgrade my-nginx bitnami/nginx \
  --namespace helm-lab \
  --set replicaCount=4
```

### Step 2: Check Revision History

```bash
helm history my-nginx -n helm-lab
```

Expected output:
```
REVISION  UPDATED                   STATUS      CHART          APP VERSION  DESCRIPTION
1         2026-03-29 ...            superseded  nginx-18.x.x   1.27.x       Install complete
2         2026-03-29 ...            deployed    nginx-18.x.x   1.27.x       Upgrade complete
```

### Step 3: Verify

```bash
kubectl get pods -n helm-lab -l app.kubernetes.io/instance=my-nginx
```

---

## Exercise 7: Rolling Back a Release

### Step 1: Rollback to Revision 1

```bash
helm rollback my-nginx 1 -n helm-lab
```

### Step 2: Verify

```bash
helm history my-nginx -n helm-lab
kubectl get pods -n helm-lab -l app.kubernetes.io/instance=my-nginx
```

The history now shows revision 3 as the rollback.

---

## Exercise 8: Debugging with Template Rendering

### Step 1: Render Templates Locally (No Install)

```bash
helm template my-debug bitnami/nginx --set replicaCount=2 | head -80
```

This outputs the raw Kubernetes YAML that Helm would apply without actually contacting the cluster.

### Step 2: Dry-Run with Server-Side Validation

```bash
helm install my-dryrun bitnami/nginx \
  --namespace helm-lab \
  --dry-run --debug 2>&1 | head -100
```

---

## Exercise 9: Creating Your Own Helm Chart

### Step 1: Scaffold a Chart

```bash
helm create myapp
```

### Step 2: Explore the Structure

```bash
ls myapp/
cat myapp/Chart.yaml
cat myapp/values.yaml
ls myapp/templates/
```

### Step 3: Lint the Chart

```bash
helm lint myapp/
```

Expected output:
```
==> Linting myapp/
[INFO] Chart.yaml: icon is recommended
1 chart(s) linted, 0 chart(s) failed
```

### Step 4: Render Templates

```bash
helm template my-release myapp/
```

### Step 5: Install from Local Chart

```bash
helm install my-release myapp/ --namespace helm-lab
kubectl get all -n helm-lab -l app.kubernetes.io/instance=my-release
```

### Step 6: Package the Chart

```bash
helm package myapp/
ls myapp-*.tgz
```

---

## Exercise 10: Uninstalling Releases

### Step 1: List All Releases

```bash
helm list -n helm-lab
```

### Step 2: Uninstall

```bash
helm uninstall my-nginx -n helm-lab
helm uninstall my-nginx-custom -n helm-lab
helm uninstall my-nginx-prod -n helm-lab
helm uninstall my-release -n helm-lab
```

### Step 3: Verify Resources Are Gone

```bash
kubectl get all -n helm-lab
```

### Step 4: Uninstall with History Preserved (Optional)

```bash
# If you want to keep release history for audit
helm uninstall my-release --keep-history -n helm-lab
```

---

## Quick Reference: Essential Helm Commands

| Action | Command |
|--------|---------|
| Add repo | `helm repo add NAME URL` |
| Update repos | `helm repo update` |
| Search repo | `helm search repo KEYWORD` |
| Search hub | `helm search hub KEYWORD` |
| Show values | `helm show values CHART` |
| Install | `helm install RELEASE CHART` |
| Install + values | `helm install RELEASE CHART -f values.yaml` |
| Install + set | `helm install RELEASE CHART --set key=val` |
| Upgrade | `helm upgrade RELEASE CHART` |
| Rollback | `helm rollback RELEASE REVISION` |
| History | `helm history RELEASE` |
| List releases | `helm list` |
| Status | `helm status RELEASE` |
| Get values | `helm get values RELEASE` |
| Template render | `helm template RELEASE CHART` |
| Dry run | `helm install --dry-run --debug RELEASE CHART` |
| Uninstall | `helm uninstall RELEASE` |
| Create chart | `helm create CHARTNAME` |
| Lint | `helm lint CHARTDIR` |
| Package | `helm package CHARTDIR` |
| Pull chart | `helm pull CHART --untar` |

---

## Key Takeaways

| Concept | Summary |
|---------|---------|
| **Helm** | Kubernetes package manager — install, upgrade, rollback apps with one command |
| **Chart** | Bundled templates + values + metadata in a versioned directory |
| **Release** | A named, running instance of a chart in a namespace |
| **Repository** | HTTP server hosting packaged charts (e.g. Bitnami, ArtifactHub) |
| **Values** | Override defaults with `--set` or `-f values.yaml` for different environments |
| **Revision history** | Every upgrade creates a new revision; rollback anytime with `helm rollback` |
| **helm template** | Render YAML locally without deploying — great for CI/CD and debugging |
| **Helm 3** | Client-only; no server-side Tiller component |

---

## Troubleshooting

### Helm command not found after install
```bash
# Check if helm is in PATH
which helm
# If installed manually, ensure /usr/local/bin is in PATH
export PATH=$PATH:/usr/local/bin
```

### Repository update fails
```bash
# Remove and re-add the repo
helm repo remove bitnami
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
```

### Release stuck in pending-install
```bash
# Check Pod events
kubectl describe pods -n <namespace> -l app.kubernetes.io/instance=<release>

# Force uninstall if stuck
helm uninstall <release> -n <namespace>
```

### Template rendering errors
```bash
# Use lint to catch issues early
helm lint mychart/

# Enable debug output
helm template my-release mychart/ --debug
```

---

## Cleanup

```bash
# Uninstall all lab releases
helm list -n helm-lab -q | xargs -I {} helm uninstall {} -n helm-lab

# Delete namespace
kubectl delete namespace helm-lab --ignore-not-found

# Remove scaffold chart
rm -rf myapp/ myapp-*.tgz values-prod.yaml
```

---

## Next Steps

- **Lab 32: Headlamp UI** — Headlamp is installed via Helm; revisit with your new Helm knowledge
- **Lab 41: WordPress on Kubernetes** — Deploy WordPress using Helm for a real-world multi-tier application
- **Lab 25: ConfigMaps** and **Lab 47: Secrets** — Understand how Helm templates inject ConfigMaps and Secrets
- **Interactive HTML**: [Helm Charts Overview](../html/helm-charts-overview.html) — Visual explainer for Helm architecture, rendering pipeline, and command reference
