# Lab 45: DNS Configuration in Kubernetes

## Overview
In this lab, you will learn how to configure DNS settings for Pods in Kubernetes. You'll explore different DNS policies, custom DNS configurations, and host aliases to understand how Kubernetes handles name resolution for your applications.

## Prerequisites
- A running Kubernetes cluster (Minikube, Kind, or any K8s cluster)
- `kubectl` CLI tool installed and configured
- Basic understanding of DNS and networking concepts
- Completion of [Lab 01: Creating Pods](lab01-basics-creating-pods.md)

## Learning Objectives
By the end of this lab, you will be able to:
- Understand Kubernetes DNS architecture and components
- Configure different DNS policies for Pods
- Create custom DNS configurations
- Use host aliases to customize /etc/hosts in Pods
- Troubleshoot DNS resolution issues
- Understand DNS naming conventions in Kubernetes

---

## Understanding Kubernetes DNS

### What is Kubernetes DNS?

Kubernetes runs an internal DNS service that provides name resolution for:
- **Services** - Access services by name instead of IP
- **Pods** - Pods can discover each other
- **External domains** - Resolution of external DNS names

### DNS Components

By default, Kubernetes uses **CoreDNS** (or kube-dns in older versions):

- **CoreDNS Pods** - Run in kube-system namespace
- **DNS Service** - Usually named `kube-dns` at IP 10.96.0.10
- **kubelet** - Configures /etc/resolv.conf in each Pod

### DNS Naming Convention

Kubernetes creates DNS records with this pattern:

```
# Service DNS names
<service-name>.<namespace>.svc.cluster.local

# Pod DNS names
<pod-ip-with-dashes>.<namespace>.pod.cluster.local

# Examples
myservice.default.svc.cluster.local
10-244-0-5.default.pod.cluster.local
```

**Shorthand names** (within same namespace):
- `myservice` (shortest)
- `myservice.default` (includes namespace)
- `myservice.default.svc.cluster.local` (FQDN)

---

## Exercise 1: Understanding DNS Policies

### What are DNS Policies?

DNS Policy determines how DNS resolution is configured in a Pod. Kubernetes supports four DNS policies:

| Policy | Description | Use Case |
|--------|-------------|----------|
| **Default** | Inherits DNS from the node | Legacy applications needing node DNS |
| **ClusterFirst** | Uses cluster DNS (CoreDNS), falls back to node | Most Kubernetes workloads (default) |
| **ClusterFirstWithHostNet** | For Pods using hostNetwork=true | Pods on host network needing cluster DNS |
| **None** | Empty DNS config, must specify dnsConfig | Custom DNS setup |

### Step 1: Check CoreDNS Status

Verify CoreDNS is running:

```bash
kubectl get pods -n kube-system -l k8s-app=kube-dns
```

Expected output:
```
NAME                       READY   STATUS    RESTARTS   AGE
coredns-5d78c9869d-abc12   1/1     Running   0          5d
coredns-5d78c9869d-xyz89   1/1     Running   0          5d
```

Check CoreDNS Service:
```bash
kubectl get service -n kube-system kube-dns
```

Expected output:
```
NAME       TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)         AGE
kube-dns   ClusterIP   10.96.0.10   <none>        53/UDP,53/TCP   5d
```

---

## Exercise 2: Test Default DNS Behavior (ClusterFirst)

### Step 1: Create a Pod with Default DNS Policy

Most Pods use `ClusterFirst` by default (doesn't need to be specified):

```bash
kubectl run dns-test --image=busybox --restart=Never --command -- sleep 3600
```

### Step 2: Examine DNS Configuration

Check the /etc/resolv.conf file inside the Pod:

```bash
kubectl exec dns-test -- cat /etc/resolv.conf
```

Expected output:
```
nameserver 10.96.0.10
search default.svc.cluster.local svc.cluster.local cluster.local
options ndots:5
```

**Understanding the output:**
- `nameserver 10.96.0.10` - CoreDNS service IP
- `search` - Domain search list (enables shorthand names)
- `options ndots:5` - Names with fewer than 5 dots are searched in search domains first

### Step 3: Test Service Name Resolution

Create a test service:
```bash
kubectl create deployment nginx --image=nginx
kubectl expose deployment nginx --port=80 --name=nginx-service
```

Test DNS resolution from the dns-test Pod:
```bash
# Short name (same namespace)
kubectl exec dns-test -- nslookup nginx-service

# With namespace
kubectl exec dns-test -- nslookup nginx-service.default

# Fully qualified domain name (FQDN)
kubectl exec dns-test -- nslookup nginx-service.default.svc.cluster.local
```

All three should resolve to the same IP (the nginx-service ClusterIP)!

### Step 4: Test External DNS Resolution

```bash
kubectl exec dns-test -- nslookup google.com
```

This should work because ClusterFirst falls back to upstream DNS for external names.

### Step 5: Cleanup

```bash
kubectl delete pod dns-test
kubectl delete deployment nginx
kubectl delete service nginx-service
```

---

## Exercise 3: DNS Policy "Default" (Node DNS)

### Step 1: Review the Manifest

Navigate to the labs directory:
```bash
cd k8s/labs/networking
```

Let's examine `dnsdefault.yaml`:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: dnsdefault
  namespace: default
spec:
  containers:
  - image: busybox:1.28
    command:
      - sleep
      - "3600"
    name: busybox
  restartPolicy: Always
  dnsPolicy: Default
```

**Key configuration:**
- `dnsPolicy: Default` - Uses node's DNS settings instead of cluster DNS

### Step 2: Deploy the Pod

```bash
kubectl apply -f dnsdefault.yaml
```

Expected output:
```
pod/dnsdefault created
```

### Step 3: Examine DNS Configuration

Check the DNS configuration:

```bash
kubectl exec dnsdefault -- cat /etc/resolv.conf
```

Expected output (will vary based on your node configuration):
```
nameserver 8.8.8.8
nameserver 8.8.4.4
search your-domain.com
```

**Notice**: This matches the node's /etc/resolv.conf, NOT the cluster DNS!

### Step 4: Test Cluster Service Resolution

Create a test service:
```bash
kubectl create deployment test-app --image=nginx
kubectl expose deployment test-app --port=80 --name=test-service
```

Try to resolve the service:
```bash
kubectl exec dnsdefault -- nslookup test-service
```

**Result**: This will FAIL because the Pod is not using cluster DNS!

```
nslookup: can't resolve 'test-service'
```

### Step 5: Test External Resolution

```bash
kubectl exec dnsdefault -- nslookup google.com
```

This should work (using node's DNS servers).

### Step 6: When to Use Default Policy

**Use cases for dnsPolicy: Default:**
- Legacy applications expecting specific DNS configuration
- Debugging DNS issues
- Applications that should NOT use cluster DNS
- Testing node-level DNS configuration

**Warning**: Avoid in production unless you have specific requirements!

---

## Exercise 4: DNS Policy "ClusterFirstWithHostNet"

### Step 1: Review the Manifest

Let's examine `dnspolicy.yaml`:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: dnspolicy
  namespace: default
spec:
  containers:
  - image: nginx:latest
    command:
      - sleep
      - "3600"
    name: busybox
  restartPolicy: Always
  hostNetwork: true
  dnsPolicy: ClusterFirstWithHostNet
```

**Key configuration:**
- `hostNetwork: true` - Pod uses host's network namespace (shares Node's IP)
- `dnsPolicy: ClusterFirstWithHostNet` - Uses cluster DNS despite hostNetwork

### Step 2: Understanding hostNetwork

When `hostNetwork: true`:
- Pod gets the Node's IP address (no separate Pod IP)
- Pod ports bind directly to Node ports
- By default, DNS would use node DNS (like Default policy)
- `ClusterFirstWithHostNet` forces cluster DNS usage

### Step 3: Deploy the Pod

```bash
kubectl apply -f dnspolicy.yaml
```

Expected output:
```
pod/dnspolicy created
```

### Step 4: Verify Network Configuration

Check the Pod's IP:
```bash
kubectl get pod dnspolicy -o wide
```

Notice the Pod IP matches the Node IP!

### Step 5: Examine DNS Configuration

```bash
kubectl exec dnspolicy -- cat /etc/resolv.conf
```

Expected output:
```
nameserver 10.96.0.10
search default.svc.cluster.local svc.cluster.local cluster.local
options ndots:5
```

**Notice**: Despite hostNetwork=true, it uses cluster DNS (10.96.0.10)!

### Step 6: Test Service Resolution

```bash
kubectl exec dnspolicy -- nslookup test-service
```

This should work (resolves to test-service ClusterIP).

### Step 7: When to Use ClusterFirstWithHostNet

**Use cases:**
- DaemonSets that need host network access
- Monitoring agents (Prometheus node exporter)
- Network plugins
- Pods requiring both host networking and service discovery

---

## Exercise 5: Custom DNS Configuration (dnsPolicy: None)

### Step 1: Review the Manifest

Let's examine `dnsconfig.yaml`:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: dnscustomconfig
  namespace: default
spec:
  containers:
    - name: test
      image: busybox
      command:
       - sleep
       - "3600"
  dnsPolicy: "None"
  dnsConfig:
    nameservers:
      - 1.2.3.4
    searches:
      - ns1.svc.cluster-domain.example
      - my.dns.search.suffix
    options:
      - name: ndots
        value: "2"
      - name: edns0
```

**Key configuration:**
- `dnsPolicy: "None"` - Start with empty DNS config
- `dnsConfig` - Completely custom DNS settings
  - `nameservers` - Custom DNS servers
  - `searches` - Custom search domains
  - `options` - DNS resolver options
    - `ndots: 2` - Query threshold for search domains
    - `edns0` - Enable DNS extension mechanisms

### Step 2: Understanding dnsConfig Fields

| Field | Description | Example |
|-------|-------------|---------|
| **nameservers** | List of DNS server IPs | `["8.8.8.8", "1.1.1.1"]` |
| **searches** | DNS search domains | `["my.namespace.svc.cluster.local"]` |
| **options** | Resolver options | `[{name: "ndots", value: "5"}]` |

**Common options:**
- `ndots` - Number of dots threshold for absolute query
- `timeout` - Resolver timeout in seconds
- `attempts` - Number of resolver attempts
- `edns0` - Enable EDNS0 extension

### Step 3: Deploy the Pod

```bash
kubectl apply -f dnsconfig.yaml
```

Expected output:
```
pod/dnscustomconfig created
```

### Step 4: Examine Custom DNS Configuration

```bash
kubectl exec dnscustomconfig -- cat /etc/resolv.conf
```

Expected output:
```
nameserver 1.2.3.4
search ns1.svc.cluster-domain.example my.dns.search.suffix
options ndots:2 edns0
```

**Notice**: Exactly matches our custom configuration!

### Step 5: Test Resolution (Will Fail)

```bash
kubectl exec dnscustomconfig -- nslookup google.com
```

**Result**: Will fail or timeout because 1.2.3.4 is not a real DNS server!

```
;; connection timed out; no servers could be reached
```

### Step 6: Create a Working Custom DNS Config

Let's create a Pod with valid DNS servers:

```bash
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: custom-dns-working
spec:
  containers:
  - name: test
    image: busybox
    command: ["sleep", "3600"]
  dnsPolicy: "None"
  dnsConfig:
    nameservers:
      - 8.8.8.8
      - 1.1.1.1
    searches:
      - default.svc.cluster.local
    options:
      - name: ndots
        value: "2"
EOF
```

Test it:
```bash
kubectl exec custom-dns-working -- nslookup google.com
```

This should work!

### Step 7: When to Use Custom DNS

**Use cases for dnsPolicy: None:**
- Multi-cluster setups requiring custom DNS
- Applications needing specific DNS servers
- Testing DNS configurations
- Integration with external DNS systems
- Air-gapped environments with custom DNS

---

## Exercise 6: Host Aliases (Custom /etc/hosts)

### Step 1: Review the Manifest

Let's examine `hostaliases.yaml`:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: hostaliases-pod
spec:
  restartPolicy: Never
  hostAliases:
  - ip: "127.0.0.1"
    hostnames:
    - "foo.local"
    - "bar.local"
  - ip: "10.1.2.3"
    hostnames:
    - "foo.remote"
    - "bar.remote"
  containers:
  - name: cat-hosts
    image: busybox:1.28
    command:
    - cat
    args:
    - "/etc/hosts"
```

**Key configuration:**
- `hostAliases` - Adds entries to /etc/hosts file
- Each entry maps an IP to one or more hostnames
- Useful for static name resolution without DNS

### Step 2: Understanding hostAliases

**hostAliases vs /etc/hosts:**
- Kubernetes manages /etc/hosts automatically
- Direct edits to /etc/hosts are lost on Pod restart
- hostAliases survives restarts (declarative)

### Step 3: Deploy the Pod

```bash
kubectl apply -f hostaliases.yaml
```

Expected output:
```
pod/hostaliases-pod created
```

### Step 4: View the /etc/hosts File

The Pod runs `cat /etc/hosts` and exits. View its logs:

```bash
kubectl logs hostaliases-pod
```

Expected output:
```
# Kubernetes-managed hosts file.
127.0.0.1       localhost
::1     localhost ip6-localhost ip6-loopback
fe00::0 ip6-localnet
fe00::0 ip6-mcastprefix
fe00::1 ip6-allnodes
fe00::2 ip6-allrouters
10.244.0.5      hostaliases-pod

# Entries added by HostAliases.
127.0.0.1       foo.local       bar.local
10.1.2.3        foo.remote      bar.remote
```

**Notice**: The hostAliases entries are added at the bottom!

### Step 5: Test with a Long-Running Pod

Create a test Pod with hostAliases:

```bash
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: hostalias-test
spec:
  hostAliases:
  - ip: "127.0.0.1"
    hostnames:
    - "myapp.local"
  - ip: "192.168.1.100"
    hostnames:
    - "database.internal"
    - "db.internal"
  containers:
  - name: test
    image: busybox
    command: ["sleep", "3600"]
EOF
```

### Step 6: Test Name Resolution

Test the custom hostnames:

```bash
# Ping the custom hostname
kubectl exec hostalias-test -- ping -c 2 myapp.local

# Check if hostname resolves
kubectl exec hostalias-test -- nslookup myapp.local

# View the /etc/hosts file
kubectl exec hostalias-test -- cat /etc/hosts
```

### Step 7: When to Use hostAliases

**Use cases:**
- Development/testing environments
- Mocking external services
- Custom internal name resolution
- Legacy applications expecting specific hostnames
- Static name-to-IP mappings

**Best practices:**
- Use Services and DNS for dynamic environments
- Use hostAliases for static mappings only
- Don't use for production service discovery

---

## Exercise 7: DNS Troubleshooting

### Common DNS Issues and Solutions

#### Issue 1: Service Not Resolving

**Symptoms:**
```bash
kubectl exec my-pod -- nslookup my-service
# nslookup: can't resolve 'my-service'
```

**Diagnosis:**
```bash
# Check if service exists
kubectl get service my-service

# Check if CoreDNS is running
kubectl get pods -n kube-system -l k8s-app=kube-dns

# Check Pod's DNS policy
kubectl get pod my-pod -o jsonpath='{.spec.dnsPolicy}'

# Check Pod's resolv.conf
kubectl exec my-pod -- cat /etc/resolv.conf
```

**Solutions:**
1. Verify service name spelling
2. Ensure CoreDNS Pods are running
3. Check dnsPolicy is ClusterFirst (or not explicitly Default)
4. Verify namespace (use FQDN: service.namespace.svc.cluster.local)

#### Issue 2: CoreDNS Pod Issues

**Check CoreDNS logs:**
```bash
kubectl logs -n kube-system -l k8s-app=kube-dns
```

**Common errors:**
- Plugin errors in CoreDNS configuration
- Resource exhaustion
- Network policy blocking DNS traffic

**Restart CoreDNS:**
```bash
kubectl rollout restart deployment/coredns -n kube-system
```

#### Issue 3: Slow DNS Resolution

**Symptoms:** Long delays when resolving names

**Check ndots setting:**
```bash
kubectl exec my-pod -- cat /etc/resolv.conf | grep ndots
```

**Problem:** High ndots value (default 5) causes multiple queries

**Solution:** Use FQDNs or reduce ndots:
```yaml
dnsConfig:
  options:
  - name: ndots
    value: "2"
```

#### Issue 4: External DNS Not Working

**Test:**
```bash
kubectl exec my-pod -- nslookup google.com
```

**Check CoreDNS forward configuration:**
```bash
kubectl get configmap coredns -n kube-system -o yaml
```

Look for `forward` directive:
```
forward . /etc/resolv.conf
```

### DNS Debug Pod

Create a comprehensive DNS testing Pod:

```bash
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: dns-debug
spec:
  containers:
  - name: dnsutils
    image: registry.k8s.io/e2e-test-images/jessie-dnsutils:1.3
    command:
      - sleep
      - "3600"
EOF
```

Use it for testing:
```bash
# Test DNS lookup
kubectl exec dns-debug -- nslookup kubernetes.default

# Test dig
kubectl exec dns-debug -- dig kubernetes.default.svc.cluster.local

# Test host command
kubectl exec dns-debug -- host kubernetes.default

# Interactive shell
kubectl exec -it dns-debug -- /bin/bash
```

---

## Lab Cleanup

Remove all resources created in this lab:

```bash
# Delete test Pods
kubectl delete pod dnsdefault dnspolicy dnscustomconfig hostaliases-pod hostalias-test custom-dns-working dns-debug --ignore-not-found=true

# Delete test deployment and service (if still exists)
kubectl delete deployment test-app --ignore-not-found=true
kubectl delete service test-service --ignore-not-found=true

# Verify cleanup
kubectl get pods
```

---

## Key Takeaways

1. **CoreDNS** provides DNS services for Kubernetes clusters
2. **ClusterFirst** is the default and recommended DNS policy
3. **dnsPolicy: Default** uses node DNS instead of cluster DNS
4. **ClusterFirstWithHostNet** enables cluster DNS for Pods using hostNetwork
5. **dnsPolicy: None** with dnsConfig allows complete custom DNS setup
6. **hostAliases** provides custom /etc/hosts entries
7. **Service DNS names** follow pattern: `<service>.<namespace>.svc.cluster.local`
8. **ndots** option affects DNS query behavior
9. Always use **FQDNs** for cross-namespace service access
10. DNS issues are common but easily diagnosed with proper tools

---

## DNS Best Practices

### 1. Use ClusterFirst (Default)

Let Kubernetes handle DNS configuration for most workloads.

### 2. Use FQDNs for Cross-Namespace Access

```bash
# Instead of:
curl http://api-service

# Use:
curl http://api-service.production.svc.cluster.local
```

### 3. Monitor CoreDNS Performance

```bash
# Check CoreDNS metrics
kubectl top pods -n kube-system -l k8s-app=kube-dns

# View CoreDNS logs
kubectl logs -n kube-system -l k8s-app=kube-dns --tail=50
```

### 4. Configure Resource Limits

Ensure CoreDNS has adequate resources:

```yaml
resources:
  limits:
    memory: 170Mi
  requests:
    cpu: 100m
    memory: 70Mi
```

### 5. Use DNS Caching

Consider tools like NodeLocal DNSCache for improved performance.

### 6. Avoid Hardcoded IPs

Use service names instead of IPs:

```bash
# Bad
DATABASE_HOST=10.96.100.50

# Good
DATABASE_HOST=postgres-service.database.svc.cluster.local
```

---

## Advanced Topics

### Custom CoreDNS Configuration

Edit CoreDNS ConfigMap:

```bash
kubectl edit configmap coredns -n kube-system
```

Example custom forward:

```
forward . 8.8.8.8 1.1.1.1
```

Example conditional forwarding:

```
example.com {
    forward . 192.168.1.1
}
```

### DNS-Based Service Discovery Patterns

**Pattern 1: Headless Service**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: stateful-service
spec:
  clusterIP: None  # Headless
  selector:
    app: statefulset
```

DNS returns Pod IPs directly instead of service VIP.

**Pattern 2: ExternalName Service**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: external-db
spec:
  type: ExternalName
  externalName: database.example.com
```

Creates CNAME record pointing to external service.

---

## Additional Commands Reference

```bash
# Check DNS service
kubectl get service -n kube-system kube-dns

# View CoreDNS configuration
kubectl get configmap coredns -n kube-system -o yaml

# Check CoreDNS version
kubectl get deployment coredns -n kube-system -o jsonpath='{.spec.template.spec.containers[0].image}'

# Scale CoreDNS (if needed)
kubectl scale deployment coredns -n kube-system --replicas=3

# Test DNS from any Pod
kubectl run tmp-shell --rm -i --tty --image nicolaka/netshoot -- /bin/bash

# Inside the Pod:
nslookup kubernetes.default
dig kubernetes.default.svc.cluster.local
host kubernetes.default

# Check all DNS-related resources
kubectl get all,cm,sa -n kube-system | grep -E 'dns|coredns'

# View DNS query logs (if enabled)
kubectl logs -n kube-system -l k8s-app=kube-dns --tail=100 -f
```

---

## Next Steps

1. **Lab 11**: Learn about Multi-Port Services
2. **Lab 12**: Explore Ingress Controllers and EndpointSlices
3. **Advanced**: Implement NodeLocal DNSCache for improved DNS performance

---

## Additional Reading

- [Kubernetes DNS Documentation](https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/)
- [CoreDNS Documentation](https://coredns.io/manual/toc/)
- [DNS for Services and Pods](https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/)
- [Debugging DNS Resolution](https://kubernetes.io/docs/tasks/administer-cluster/dns-debugging-resolution/)
- [DNS Configuration Options](https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/#pod-dns-config)

---

**Lab Created**: March 2026
**Compatible with**: Kubernetes 1.24+
**Tested on**: Minikube, Kind, AWS EKS, GCP GKE
