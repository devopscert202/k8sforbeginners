# Lab 40: Kubernetes Cluster Upgrades with kubeadm

## Overview
In this lab, you will learn how to safely upgrade a Kubernetes cluster from one minor version to another using kubeadm. You'll understand version skew policies, backup procedures, and the step-by-step process of upgrading control plane nodes first, followed by worker nodes. This is a critical topic for the CKA exam and production cluster management.

## Prerequisites
- A running Kubernetes cluster with at least one control-plane node and one worker node
- Admin access to all nodes (SSH with sudo privileges)
- Cluster installed using kubeadm
- Basic understanding of Kubernetes architecture
- Completion of Lab 03 (ETCD Backup and Restore) recommended
- Current cluster running Kubernetes 1.29.x (or similar)

## Learning Objectives
By the end of this lab, you will be able to:
- Understand Kubernetes version skew policies
- Check current versions of cluster components
- Backup etcd before upgrading
- Upgrade the control plane node using kubeadm
- Upgrade kubelet and kubectl on control plane
- Drain worker nodes safely
- Upgrade worker nodes one by one
- Verify cluster health after upgrade
- Troubleshoot common upgrade issues
- Implement rollback procedures if needed

---

## What is a Kubernetes Cluster Upgrade?

### Introduction
Kubernetes follows a rapid release cycle with new minor versions released approximately every 4 months. Each release includes new features, bug fixes, security patches, and API changes. Upgrading your cluster ensures:

- **Security**: Latest security patches and vulnerability fixes
- **Stability**: Bug fixes and performance improvements
- **Features**: Access to new Kubernetes features
- **Support**: Community support for recent versions
- **Compliance**: Meeting organizational requirements

### Version Skew Policy

Kubernetes components follow strict version compatibility rules:

| Component | Supported Versions |
|-----------|-------------------|
| **kube-apiserver** | N (current version) |
| **kube-controller-manager** | N-1 (one version behind apiserver) |
| **kube-scheduler** | N-1 (one version behind apiserver) |
| **kubelet** | N-2 (up to two versions behind apiserver) |
| **kubectl** | N+1, N, N-1 (one version ahead or behind) |
| **kube-proxy** | N-2 (up to two versions behind apiserver) |

**Key Rules:**
- Upgrade one minor version at a time (e.g., 1.29 → 1.30, not 1.29 → 1.31)
- Always upgrade control plane before worker nodes
- Ensure backups before starting
- Test upgrades in non-production first

---

## Understanding the Upgrade Process

```
1. Backup ETCD → 2. Check Versions → 3. Upgrade Control Plane
         ↓
4. Drain First Worker → 5. Upgrade Worker → 6. Uncordon Worker
         ↓
7. Repeat for All Workers → 8. Verify Cluster → 9. Monitor Applications
```

### Component Upgrade Order

1. **Control Plane Node** (Master)
   - Upgrade kubeadm
   - Drain control plane (if it runs workloads)
   - Upgrade control plane components (apiserver, scheduler, controller-manager)
   - Upgrade kubelet and kubectl
   - Uncordon control plane

2. **Worker Nodes** (One at a time)
   - Drain node
   - Upgrade kubeadm
   - Upgrade kubelet configuration
   - Upgrade kubelet and kubectl
   - Restart kubelet
   - Uncordon node

---

## Exercise 1: Pre-Upgrade Preparation

### Step 1: Check Current Cluster Version

From the control plane node:

```bash
kubectl version --short
```

Expected output:
```
Client Version: v1.29.3
Kustomize Version: v5.0.1
Server Version: v1.29.3
```

Check all node versions:

```bash
kubectl get nodes -o wide
```

Expected output:
```
NAME                        STATUS   ROLES           AGE   VERSION   INTERNAL-IP     OS-IMAGE             KERNEL-VERSION
master.example.com          Ready    control-plane   90d   v1.29.3   172.31.28.251   Ubuntu 22.04.3 LTS   5.15.0-91-generic
worker-node-1.example.com   Ready    <none>          90d   v1.29.3   172.31.35.22    Ubuntu 22.04.3 LTS   5.15.0-91-generic
worker-node-2.example.com   Ready    <none>          90d   v1.29.3   172.31.40.18    Ubuntu 22.04.3 LTS   5.15.0-91-generic
```

### Step 2: Check Component Versions

Check individual component versions:

```bash
# Check kubelet version on each node
kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.nodeInfo.kubeletVersion}{"\n"}{end}'

# Check control plane component versions
kubectl get pods -n kube-system -l component=kube-apiserver -o jsonpath='{.items[0].spec.containers[0].image}'
```

### Step 3: Document Current State

Capture current cluster state:

```bash
# List all namespaces
kubectl get namespaces > /tmp/pre-upgrade-namespaces.txt

# List all pods across all namespaces
kubectl get pods -A -o wide > /tmp/pre-upgrade-pods.txt

# List all deployments
kubectl get deployments -A > /tmp/pre-upgrade-deployments.txt

# List all services
kubectl get services -A > /tmp/pre-upgrade-services.txt

# Check cluster info
kubectl cluster-info > /tmp/pre-upgrade-cluster-info.txt
```

### Step 4: Backup ETCD

**CRITICAL**: Always backup etcd before upgrading!

```bash
# Create backup directory
sudo mkdir -p /var/backups/etcd/pre-upgrade

# Get etcd endpoint
export ETCD_ENDPOINTS=$(grep -oP '(?<=--advertise-client-urls=)\S+' /etc/kubernetes/manifests/etcd.yaml)

# Take snapshot
sudo ETCDCTL_API=3 /usr/bin/etcdctl \
  --endpoints="$ETCD_ENDPOINTS" \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  snapshot save /var/backups/etcd/pre-upgrade/etcd-backup-$(date +%Y%m%d-%H%M%S).db
```

Verify the backup:

```bash
sudo ETCDCTL_API=3 /usr/bin/etcdctl \
  snapshot status /var/backups/etcd/pre-upgrade/etcd-backup-*.db \
  --write-out=table
```

Expected output:
```
+----------+----------+------------+------------+
|   HASH   | REVISION | TOTAL KEYS | TOTAL SIZE |
+----------+----------+------------+------------+
| 123abcd  |   45678  |    3500    |   5.1 MB   |
+----------+----------+------------+------------+
```

### Step 5: Check Available Upgrade Versions

On the control plane node:

```bash
# Update package lists
sudo apt update

# Check available kubeadm versions
apt-cache madison kubeadm | head -10
```

Expected output:
```
   kubeadm | 1.30.0-00 | https://apt.kubernetes.io kubernetes-xenial/main amd64 Packages
   kubeadm | 1.29.3-00 | https://apt.kubernetes.io kubernetes-xenial/main amd64 Packages
   kubeadm | 1.29.2-00 | https://apt.kubernetes.io kubernetes-xenial/main amd64 Packages
```

**Note the target version**: In this example, we'll upgrade from 1.29.3 to 1.30.0

---

## Exercise 2: Upgrade Control Plane Node

Perform these steps **ONLY on the CONTROL PLANE node**.

### Step 1: Unhold and Upgrade kubeadm

First, remove the hold on kubeadm:

```bash
sudo apt-mark unhold kubeadm
```

Install the target version of kubeadm:

```bash
# Replace 1.30.0-00 with your target version
sudo apt-get update
sudo apt-get install -y kubeadm=1.30.0-00
```

Hold kubeadm again to prevent automatic updates:

```bash
sudo apt-mark hold kubeadm
```

Verify kubeadm version:

```bash
kubeadm version
```

Expected output:
```
kubeadm version: &version.Info{Major:"1", Minor:"30", GitVersion:"v1.30.0"...}
```

### Step 2: Plan the Upgrade

Check what will be upgraded:

```bash
sudo kubeadm upgrade plan
```

Expected output:
```
[upgrade/config] Making sure the configuration is correct:
[upgrade/config] Reading configuration from the cluster...
[upgrade/config] FYI: You can look at this config file with 'kubectl -n kube-system get cm kubeadm-config -o yaml'
[preflight] Running pre-flight checks.
[upgrade] Running cluster health checks
[upgrade] Fetching available versions to upgrade to
[upgrade/versions] Cluster version: v1.29.3
[upgrade/versions] kubeadm version: v1.30.0
[upgrade/versions] Target version: v1.30.0
[upgrade/versions] Latest version in the v1.29 series: v1.29.4

Components that must be upgraded manually after you have upgraded the control plane with 'kubeadm upgrade apply':
COMPONENT   CURRENT       TARGET
kubelet     3 x v1.29.3   v1.30.0

Upgrade to the latest version in the v1.30 series:

COMPONENT                 CURRENT   TARGET
kube-apiserver            v1.29.3   v1.30.0
kube-controller-manager   v1.29.3   v1.30.0
kube-scheduler            v1.29.3   v1.30.0
kube-proxy                v1.29.3   v1.30.0
CoreDNS                   v1.11.1   v1.11.1
etcd                      3.5.10    3.5.12-0

You can now apply the upgrade by executing the following command:

        kubeadm upgrade apply v1.30.0
```

**Understanding the output:**
- Shows current and target versions
- Lists components that will be upgraded
- Warns about manual upgrades (kubelet, kubectl)
- Displays the command to proceed

### Step 3: Drain Control Plane (If Running Workloads)

If your control plane node runs workloads (not typical for production):

```bash
kubectl drain master.example.com --ignore-daemonsets --delete-emptydir-data
```

**Note**: This is usually optional for control plane nodes that only run system pods.

### Step 4: Apply the Upgrade

Execute the upgrade:

```bash
sudo kubeadm upgrade apply v1.30.0
```

**This will take 5-10 minutes. Do not interrupt!**

Expected output:
```
[upgrade/config] Making sure the configuration is correct:
[upgrade/config] Reading configuration from the cluster...
[upgrade/config] FYI: You can look at this config file with 'kubectl -n kube-system get cm kubeadm-config -o yaml'
[preflight] Running pre-flight checks.
[upgrade] Running cluster health checks
[upgrade/version] You have chosen to change the cluster version to "v1.30.0"
[upgrade/versions] Cluster version: v1.29.3
[upgrade/versions] kubeadm version: v1.30.0
[upgrade/confirm] Are you sure you want to proceed? [y/N]: y
[upgrade/prepull] Pulling images required for setting up a Kubernetes cluster
[upgrade/prepull] This might take a minute or two, depending on the speed of your internet connection
[upgrade/apply] Upgrading your Static Pod-hosted control plane to version "v1.30.0"...
[upgrade/staticpods] Writing new Static Pod manifests to "/etc/kubernetes/tmp/kubeadm-upgraded-manifests"
[upgrade/staticpods] Preparing for "kube-apiserver" upgrade
[upgrade/staticpods] Renewing apiserver certificate
[upgrade/staticpods] Renewing apiserver-kubelet-client certificate
[upgrade/staticpods] Renewing front-proxy-client certificate
[upgrade/staticpods] Renewing apiserver-etcd-client certificate
[upgrade/staticpods] Moved new manifest to "/etc/kubernetes/manifests/kube-apiserver.yaml" and backed up old manifest to "/etc/kubernetes/tmp/kubeadm-backup-manifests/kube-apiserver.yaml"
[upgrade/staticpods] Waiting for the kubelet to restart the component
[upgrade/staticpods] This might take a minute or longer depending on the component/version gap (timeout 5m0s)
Static pod: kube-apiserver-master.example.com hash: abc123
Static pod: kube-apiserver-master.example.com hash: def456
[apiclient] Found 1 Pods for label selector component=kube-apiserver
[upgrade/staticpods] Component "kube-apiserver" upgraded successfully!
[upgrade/staticpods] Preparing for "kube-controller-manager" upgrade
...
[upgrade/staticpods] Component "kube-scheduler" upgraded successfully!
[upload-config] Storing the configuration used in ConfigMap "kubeadm-config" in the "kube-system" Namespace
[kubelet] Creating a ConfigMap "kubelet-config" in namespace kube-system with the configuration for the kubelets in the cluster
[upgrade/successful] SUCCESS! Your cluster was upgraded to "v1.30.0". Enjoy!

[upgrade/kubelet] Now that your control plane is upgraded, please proceed with upgrading your kubelets if you haven't already done so.
```

### Step 5: Upgrade kubelet and kubectl on Control Plane

Unhold kubelet and kubectl:

```bash
sudo apt-mark unhold kubelet kubectl
```

Upgrade them:

```bash
sudo apt-get update
sudo apt-get install -y kubelet=1.30.0-00 kubectl=1.30.0-00
```

Hold them again:

```bash
sudo apt-mark hold kubelet kubectl
```

### Step 6: Restart kubelet

Reload daemon and restart kubelet:

```bash
sudo systemctl daemon-reload
sudo systemctl restart kubelet
```

Check kubelet status:

```bash
sudo systemctl status kubelet
```

Should show `active (running)`.

### Step 7: Uncordon Control Plane (If Drained)

If you drained the control plane earlier:

```bash
kubectl uncordon master.example.com
```

### Step 8: Verify Control Plane Upgrade

Check node version:

```bash
kubectl get nodes
```

Expected output:
```
NAME                        STATUS   ROLES           AGE   VERSION
master.example.com          Ready    control-plane   90d   v1.30.0
worker-node-1.example.com   Ready    <none>          90d   v1.29.3
worker-node-2.example.com   Ready    <none>          90d   v1.29.3
```

Control plane should now show v1.30.0!

Check control plane pods:

```bash
kubectl get pods -n kube-system -o wide
```

All system pods should be `Running`.

---

## Exercise 3: Upgrade First Worker Node

Perform these steps **on the FIRST WORKER NODE**.

### Step 1: Drain the Worker Node

From the **control plane node**, drain the first worker:

```bash
kubectl drain worker-node-1.example.com --ignore-daemonsets --delete-emptydir-data
```

Expected output:
```
node/worker-node-1.example.com cordoned
WARNING: ignoring DaemonSet-managed Pods: kube-system/calico-node-xyz, kube-system/kube-proxy-abc
evicting pod default/nginx-deployment-abc123-def45
pod/nginx-deployment-abc123-def45 evicted
node/worker-node-1.example.com drained
```

**Understanding drain:**
- **cordon**: Marks node as unschedulable (no new pods)
- **evicting**: Gracefully terminates existing pods
- **DaemonSets ignored**: System pods like kube-proxy and CNI stay running

Verify node is cordoned:

```bash
kubectl get nodes
```

Expected output:
```
NAME                        STATUS                     ROLES           AGE   VERSION
master.example.com          Ready                      control-plane   90d   v1.30.0
worker-node-1.example.com   Ready,SchedulingDisabled   <none>          90d   v1.29.3
worker-node-2.example.com   Ready                      <none>          90d   v1.29.3
```

Notice `SchedulingDisabled` for worker-node-1.

### Step 2: Upgrade kubeadm on Worker

SSH into **worker-node-1**:

```bash
ssh worker-node-1.example.com
```

Unhold and upgrade kubeadm:

```bash
sudo apt-mark unhold kubeadm
sudo apt-get update
sudo apt-get install -y kubeadm=1.30.0-00
sudo apt-mark hold kubeadm
```

Verify:

```bash
kubeadm version
```

### Step 3: Upgrade Node Configuration

On the **worker node**, upgrade the kubelet configuration:

```bash
sudo kubeadm upgrade node
```

Expected output:
```
[upgrade] Reading configuration from the cluster...
[upgrade] FYI: You can look at this config file with 'kubectl -n kube-system get cm kubeadm-config -o yaml'
[preflight] Running pre-flight checks
[preflight] Skipping prepull. Not a control plane node.
[upgrade] Skipping phase. Not a control plane node.
[kubelet-start] Writing kubelet configuration to file "/var/lib/kubelet/config.yaml"
[upgrade] The configuration for this node was successfully updated!
[upgrade] Now you should go ahead and upgrade the kubelet package using your package manager.
```

### Step 4: Upgrade kubelet and kubectl

Still on **worker-node-1**:

```bash
sudo apt-mark unhold kubelet kubectl
sudo apt-get update
sudo apt-get install -y kubelet=1.30.0-00 kubectl=1.30.0-00
sudo apt-mark hold kubelet kubectl
```

### Step 5: Restart kubelet

Reload daemon and restart kubelet:

```bash
sudo systemctl daemon-reload
sudo systemctl restart kubelet
```

Check status:

```bash
sudo systemctl status kubelet
```

Should show `active (running)`.

### Step 6: Uncordon the Worker Node

From the **control plane node**, make the worker schedulable again:

```bash
kubectl uncordon worker-node-1.example.com
```

Expected output:
```
node/worker-node-1.example.com uncordoned
```

### Step 7: Verify Worker Node Upgrade

Check node status:

```bash
kubectl get nodes
```

Expected output:
```
NAME                        STATUS   ROLES           AGE   VERSION
master.example.com          Ready    control-plane   90d   v1.30.0
worker-node-1.example.com   Ready    <none>          90d   v1.30.0
worker-node-2.example.com   Ready    <none>          90d   v1.29.3
```

Worker-node-1 is now at v1.30.0!

Check pods redistributed:

```bash
kubectl get pods -A -o wide | grep worker-node-1
```

New pods should be scheduled on worker-node-1.

---

## Exercise 4: Upgrade Remaining Worker Nodes

Repeat Exercise 3 for each remaining worker node.

### For worker-node-2:

**From control plane:**
```bash
# 1. Drain the node
kubectl drain worker-node-2.example.com --ignore-daemonsets --delete-emptydir-data
```

**SSH to worker-node-2:**
```bash
# 2. Upgrade kubeadm
sudo apt-mark unhold kubeadm
sudo apt-get update
sudo apt-get install -y kubeadm=1.30.0-00
sudo apt-mark hold kubeadm

# 3. Upgrade node configuration
sudo kubeadm upgrade node

# 4. Upgrade kubelet and kubectl
sudo apt-mark unhold kubelet kubectl
sudo apt-get update
sudo apt-get install -y kubelet=1.30.0-00 kubectl=1.30.0-00
sudo apt-mark hold kubelet kubectl

# 5. Restart kubelet
sudo systemctl daemon-reload
sudo systemctl restart kubelet
```

**From control plane:**
```bash
# 6. Uncordon the node
kubectl uncordon worker-node-2.example.com

# 7. Verify
kubectl get nodes
```

**Best Practice**: Upgrade worker nodes one at a time, waiting for each to complete and verify before starting the next. This ensures cluster capacity and availability.

---

## Exercise 5: Post-Upgrade Verification

### Step 1: Verify All Nodes Upgraded

Check all nodes are at the target version:

```bash
kubectl get nodes -o wide
```

Expected output:
```
NAME                        STATUS   ROLES           AGE   VERSION   INTERNAL-IP     OS-IMAGE             KERNEL-VERSION
master.example.com          Ready    control-plane   90d   v1.30.0   172.31.28.251   Ubuntu 22.04.3 LTS   5.15.0-91-generic
worker-node-1.example.com   Ready    <none>          90d   v1.30.0   172.31.35.22    Ubuntu 22.04.3 LTS   5.15.0-91-generic
worker-node-2.example.com   Ready    <none>          90d   v1.30.0   172.31.40.18    Ubuntu 22.04.3 LTS   5.15.0-91-generic
```

All nodes should show `v1.30.0` and `Ready` status!

### Step 2: Verify System Pods

Check all system pods are running:

```bash
kubectl get pods -n kube-system
```

All pods should be `Running` with `1/1` or `2/2` ready.

### Step 3: Compare Pre and Post Upgrade State

Compare resource counts:

```bash
# Check namespace count
kubectl get namespaces --no-headers | wc -l
diff /tmp/pre-upgrade-namespaces.txt <(kubectl get namespaces)

# Check deployment count
kubectl get deployments -A --no-headers | wc -l

# Check pod count
kubectl get pods -A --no-headers | wc -l
```

### Step 4: Test Application Functionality

Deploy a test application:

```bash
kubectl create deployment upgrade-test --image=nginx
kubectl expose deployment upgrade-test --port=80 --type=NodePort
kubectl get svc upgrade-test
```

Test access:

```bash
# Get the NodePort
NODE_PORT=$(kubectl get svc upgrade-test -o jsonpath='{.spec.ports[0].nodePort}')

# Get node IP
NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')

# Test
curl http://$NODE_IP:$NODE_PORT
```

Should return nginx welcome page.

Clean up:

```bash
kubectl delete deployment upgrade-test
kubectl delete service upgrade-test
```

### Step 5: Check Cluster Info

```bash
kubectl cluster-info
kubectl version
```

Both should reflect v1.30.0.

### Step 6: Check API Resources

Verify new API resources are available:

```bash
kubectl api-resources | head -20
```

### Step 7: Review Logs

Check for errors in kubelet logs on any node:

```bash
sudo journalctl -u kubelet -n 100 --no-pager | grep -i error
```

Check for API server errors:

```bash
kubectl logs -n kube-system kube-apiserver-master.example.com | tail -50
```

---

## Exercise 6: Rollback Procedures

If the upgrade fails or causes issues, you may need to rollback.

### Option 1: Rollback Worker Node

If a worker node has issues after upgrade:

```bash
# 1. Drain the problematic node
kubectl drain worker-node-1.example.com --ignore-daemonsets --delete-emptydir-data

# 2. SSH to the worker node
ssh worker-node-1.example.com

# 3. Downgrade kubeadm, kubelet, kubectl
sudo apt-mark unhold kubeadm kubelet kubectl
sudo apt-get update
sudo apt-get install -y kubeadm=1.29.3-00 kubelet=1.29.3-00 kubectl=1.29.3-00
sudo apt-mark hold kubeadm kubelet kubectl

# 4. Reconfigure node
sudo kubeadm upgrade node

# 5. Restart kubelet
sudo systemctl daemon-reload
sudo systemctl restart kubelet

# 6. Uncordon node
kubectl uncordon worker-node-1.example.com
```

### Option 2: Restore ETCD (Control Plane Issues)

If the control plane has serious issues:

```bash
# 1. Stop API server
sudo mv /etc/kubernetes/manifests/kube-apiserver.yaml /tmp/

# 2. Restore etcd from backup
sudo ETCDCTL_API=3 /usr/bin/etcdctl snapshot restore \
  /var/backups/etcd/pre-upgrade/etcd-backup-*.db \
  --data-dir=/var/lib/etcd-restored \
  --name=master-restored \
  --initial-cluster=master-restored=https://172.31.28.251:2380 \
  --initial-cluster-token=etcd-cluster-restored \
  --initial-advertise-peer-urls=https://172.31.28.251:2380

# 3. Update etcd manifest to use restored data
sudo nano /etc/kubernetes/manifests/etcd.yaml
# Change --data-dir to /var/lib/etcd-restored

# 4. Restart API server
sudo mv /tmp/kube-apiserver.yaml /etc/kubernetes/manifests/

# 5. Downgrade control plane
sudo apt-mark unhold kubeadm kubelet kubectl
sudo apt-get install -y kubeadm=1.29.3-00 kubelet=1.29.3-00 kubectl=1.29.3-00
sudo apt-mark hold kubeadm kubelet kubectl

sudo systemctl daemon-reload
sudo systemctl restart kubelet
```

Refer to Lab 03 for detailed etcd restore procedures.

---

## Lab Cleanup

No cleanup is necessary after a successful upgrade. The cluster is now running the new version.

If you want to clean up test resources:

```bash
# Remove test files
rm -f /tmp/pre-upgrade-*.txt

# Keep etcd backup for safety
# Only remove after confirming stability for several days
# sudo rm -rf /var/backups/etcd/pre-upgrade/
```

---

## Key Takeaways

1. **Always backup etcd** before upgrading
2. **Version skew policy** - Upgrade one minor version at a time
3. **Control plane first** - Always upgrade control plane before workers
4. **One worker at a time** - Ensures cluster capacity during upgrade
5. **Drain before upgrade** - Safely evicts pods before maintenance
6. **kubeadm upgrade plan** - Shows what will be upgraded
7. **kubeadm upgrade apply** - Upgrades control plane components
8. **kubeadm upgrade node** - Upgrades worker node configuration
9. **Separate upgrades** - kubeadm, then kubelet/kubectl
10. **Uncordon after** - Makes nodes schedulable again
11. **Verify at each step** - Catch issues early
12. **Test applications** - Ensure functionality after upgrade

---

## Version Skew Support Matrix

| kube-apiserver | controller-manager | scheduler | kubelet | kube-proxy | kubectl |
|----------------|-------------------|-----------|---------|------------|---------|
| 1.30 | 1.30 or 1.29 | 1.30 or 1.29 | 1.30, 1.29, or 1.28 | 1.30, 1.29, or 1.28 | 1.31, 1.30, or 1.29 |
| 1.29 | 1.29 or 1.28 | 1.29 or 1.28 | 1.29, 1.28, or 1.27 | 1.29, 1.28, or 1.27 | 1.30, 1.29, or 1.28 |
| 1.28 | 1.28 or 1.27 | 1.28 or 1.27 | 1.28, 1.27, or 1.26 | 1.28, 1.27, or 1.26 | 1.29, 1.28, or 1.27 |

**Never run mismatched versions in production beyond the support window!**

---

## Best Practices

### Before Upgrade
- **Test in non-production** first
- **Read release notes** for breaking changes
- **Backup everything** (etcd, configs, manifests)
- **Document current state** comprehensively
- **Check application compatibility** with new version
- **Schedule maintenance window** during low-traffic period
- **Notify stakeholders** about upgrade window

### During Upgrade
- **One node at a time** - Never rush
- **Monitor continuously** - Watch logs and metrics
- **Verify each step** - Don't skip validation
- **Keep backups accessible** - Ready for quick restore
- **Document issues** - Track problems for future reference

### After Upgrade
- **Extended monitoring** - Watch for 24-48 hours
- **Performance testing** - Ensure no degradation
- **Keep old backups** - For at least 7 days
- **Update documentation** - Record new version
- **Review deprecated APIs** - Plan for future removals

### Common Mistakes to Avoid
- Skipping etcd backup
- Upgrading multiple minor versions at once
- Upgrading all workers simultaneously
- Not testing drain/uncordon process
- Ignoring preflight check warnings
- Not reading release notes
- Forgetting to upgrade kubelet after kubeadm

---

## Troubleshooting Guide

### Issue: kubeadm upgrade plan fails

**Symptoms**: `couldn't create a Kubernetes client from file`

**Solutions**:
```bash
# Check kubeconfig
export KUBECONFIG=/etc/kubernetes/admin.conf
kubectl get nodes

# Verify kubeadm version
kubeadm version

# Check API server connectivity
kubectl cluster-info

# Review kubeadm config
kubectl -n kube-system get cm kubeadm-config -o yaml
```

### Issue: Control plane components not upgrading

**Symptoms**: Pods stuck in old version after upgrade

**Solutions**:
```bash
# Check pod status
kubectl get pods -n kube-system -l tier=control-plane

# View pod events
kubectl describe pod -n kube-system kube-apiserver-master.example.com

# Check manifests
ls -l /etc/kubernetes/manifests/

# Verify image pull
sudo crictl images | grep v1.30

# Force pod restart by removing from manifests temporarily
sudo mv /etc/kubernetes/manifests/kube-apiserver.yaml /tmp/
# Wait 30 seconds
sudo mv /tmp/kube-apiserver.yaml /etc/kubernetes/manifests/
```

### Issue: kubelet fails to start after upgrade

**Symptoms**: Node shows NotReady, kubelet crashes

**Solutions**:
```bash
# Check kubelet status
sudo systemctl status kubelet

# View kubelet logs
sudo journalctl -u kubelet -n 100 --no-pager

# Common issues and fixes:

# 1. Config mismatch
sudo kubeadm upgrade node

# 2. Certificate issues
sudo kubeadm upgrade node phase kubelet-config

# 3. Restart kubelet
sudo systemctl daemon-reload
sudo systemctl restart kubelet

# 4. Check kubelet config
sudo cat /var/lib/kubelet/config.yaml
```

### Issue: Drain command hangs

**Symptoms**: kubectl drain doesn't complete

**Solutions**:
```bash
# Check which pods are blocking
kubectl get pods -A -o wide | grep <node-name>

# Common causes:

# 1. Pod with emptyDir - use flag
kubectl drain <node> --delete-emptydir-data

# 2. DaemonSet pods - use flag
kubectl drain <node> --ignore-daemonsets

# 3. PodDisruptionBudget blocking - check PDB
kubectl get pdb -A

# 4. Pods with local storage - force if safe
kubectl drain <node> --force --delete-emptydir-data --ignore-daemonsets

# 5. Check for stuck terminating pods
kubectl get pods -A | grep Terminating
kubectl delete pod <pod-name> -n <namespace> --force --grace-period=0
```

### Issue: Version mismatch after upgrade

**Symptoms**: kubectl version shows different client/server versions

**Solutions**:
```bash
# Check all component versions
kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.nodeInfo.kubeletVersion}{"\n"}{end}'

# Check control plane
kubectl get pods -n kube-system -o yaml | grep "image:" | grep "kube-"

# Verify packages installed
dpkg -l | grep -E 'kubeadm|kubelet|kubectl'

# If mismatch found, reinstall correct version
sudo apt-mark unhold kubelet kubectl
sudo apt-get install -y kubelet=1.30.0-00 kubectl=1.30.0-00
sudo apt-mark hold kubelet kubectl
sudo systemctl restart kubelet
```

### Issue: Pods not scheduling after uncordon

**Symptoms**: New pods not placed on upgraded node

**Solutions**:
```bash
# Check node status
kubectl get nodes
kubectl describe node <node-name>

# Check for taints
kubectl describe node <node-name> | grep -i taint

# Remove unschedulable taint if present
kubectl taint nodes <node-name> node.kubernetes.io/unschedulable-

# Check resource availability
kubectl top nodes
kubectl describe node <node-name> | grep -A 10 "Allocated resources"

# Force pod scheduling to test
kubectl run test-pod --image=nginx --overrides='{"spec":{"nodeName":"<node-name>"}}'
```

### Issue: API deprecation warnings

**Symptoms**: Warnings about deprecated APIs

**Solutions**:
```bash
# List deprecated API usage
kubectl get --raw /metrics | grep apiserver_requested_deprecated_apis

# Check for deprecated APIs in your manifests
kubectl api-resources --verbs=list --namespaced -o wide

# Update manifests before APIs are removed
# Example: extensions/v1beta1 → apps/v1 for Deployments

# Use kubectl convert (if available)
kubectl convert -f old-manifest.yaml --output-version apps/v1
```

---

## Additional Commands Reference

```bash
# Check upgrade path
sudo kubeadm upgrade plan

# Upgrade control plane
sudo kubeadm upgrade apply v1.30.0

# Upgrade worker node config
sudo kubeadm upgrade node

# Drain node safely
kubectl drain <node> --ignore-daemonsets --delete-emptydir-data

# Uncordon node
kubectl uncordon <node>

# Check component versions
kubectl get nodes -o wide
kubectl version
kubeadm version

# View upgrade history
kubectl rollout history deployment/<name>

# Check for deprecated APIs
kubectl api-versions | sort

# Force certificate renewal during upgrade
sudo kubeadm certs renew all

# View static pod manifests
ls -l /etc/kubernetes/manifests/

# Check kubelet config
sudo cat /var/lib/kubelet/config.yaml

# View upgrade logs
sudo journalctl -u kubelet -f
kubectl logs -n kube-system <control-plane-pod>
```

---

## CKA Exam Tips

For the Certified Kubernetes Administrator exam:

1. **Know the exact upgrade process** - Control plane first, then workers
2. **Remember drain/uncordon** - Critical for safe node maintenance
3. **Understand version skew** - Know supported version combinations
4. **Practice backup/restore** - Often combined with upgrade questions
5. **Speed matters** - Practice the commands to build muscle memory
6. **Read question carefully** - May ask for partial upgrade or specific version
7. **Check current version first** - Always verify before starting
8. **Don't forget --ignore-daemonsets** - Drain won't work without it

### Common CKA Scenarios
- Upgrade control plane from 1.29 to 1.30
- Upgrade specific worker node to match control plane
- Drain node for maintenance
- Backup etcd before upgrade
- Verify upgrade was successful

### Time-Saving Commands
```bash
# Quick upgrade aliases (practice environment only)
alias k='kubectl'
alias kgn='kubectl get nodes'
alias kgp='kubectl get pods -A'

# Drain shorthand
kubectl drain <node> --ignore-daemonsets --delete-emptydir-data --force
```

---

## Next Steps

After mastering cluster upgrades:

1. Practice upgrading in a test environment regularly
2. Explore automated upgrade tools (e.g., kOps, Rancher, managed services)
3. Learn about blue-green cluster upgrades for zero-downtime
4. Study Kubernetes release notes for each new version
5. Implement cluster monitoring to detect upgrade issues quickly
6. Set up alerting for version drift detection

---

## Additional Resources

- [Kubernetes Official Upgrade Documentation](https://kubernetes.io/docs/tasks/administer-cluster/kubeadm/kubeadm-upgrade/)
- [Upgrading kubeadm clusters](https://kubernetes.io/docs/tasks/administer-cluster/kubeadm/kubeadm-upgrade/)
- [Version Skew Policy](https://kubernetes.io/releases/version-skew-policy/)
- [Kubernetes Release Notes](https://kubernetes.io/releases/)
- [CKA Exam Curriculum](https://training.linuxfoundation.org/certification/certified-kubernetes-administrator-cka/)
- [kubeadm Configuration](https://kubernetes.io/docs/reference/setup-tools/kubeadm/)
- [Cluster Upgrade Best Practices](https://kubernetes.io/docs/tasks/administer-cluster/cluster-upgrade/)

---

**Lab Created**: March 2026
**Compatible with**: Kubernetes 1.28, 1.29, 1.30+
**Based on**: CKA exam requirements and production best practices
**Tested on**: Ubuntu 20.04, Ubuntu 22.04, kubeadm clusters
**Estimated Time**: 90-120 minutes (including verification)
**Difficulty**: Advanced
**CKA Relevance**: High - Critical exam topic
