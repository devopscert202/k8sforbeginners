# DNS for Kubernetes Services and Pods

Kubernetes clusters resolve Service and Pod names through cluster DNS (typically **CoreDNS**). Pods can change how that resolution works using **`dnsPolicy`**, optional **`dnsConfig`**, and **`hostNetwork`**. This page explains the behavior, trade-offs, and when to use each approach.

---

## Default cluster DNS

- Services get DNS names such as `<service>.<namespace>.svc.cluster.local`.
- Pods usually inherit cluster DNS configuration from the node and kubelet unless you override it.
- Verifying that CoreDNS (or the cluster DNS deployment) is healthy is a normal operational check before debugging application DNS issues.

---

## `hostNetwork` and `ClusterFirstWithHostNet`

Pods with **`hostNetwork: true`** use the host’s network namespace (the Pod’s IP is the node’s IP). Without a special policy, cluster Service DNS may not behave like a normal Pod.

**`dnsPolicy: ClusterFirstWithHostNet`** keeps **cluster DNS first** (Service names still resolve) while the Pod uses the host network stack—typical when a workload must bind host ports or talk to the LAN with the host’s interfaces but still needs Kubernetes service discovery.

Illustrative Pod spec:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: busybox-hostnetwork
spec:
  containers:
  - name: busybox
    image: busybox:1.28
    command: ["sleep", "3600"]
  hostNetwork: true
  dnsPolicy: ClusterFirstWithHostNet
```

---

## Custom resolvers: `dnsPolicy: None` and `dnsConfig`

**`dnsPolicy: "None"`** turns off the default DNS setup for that Pod; you must supply **`dnsConfig`** (nameservers, searches, options) or the Pod will not have usable resolver settings.

Use cases include:

- Pointing specific workloads at external resolvers or split-horizon DNS.
- Tight control over search lists and resolver options (for example `ndots`) for legacy clients.

Illustrative Pod spec:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: custom-dns-pod
spec:
  containers:
  - name: nginx
    image: nginx
  dnsPolicy: "None"
  dnsConfig:
    nameservers:
      - 8.8.8.8
    searches:
      - my-custom.search.suffix
    options:
      - name: ndots
        value: "1"
```

**Field summary:**

- **`nameservers`**: Upstream DNS servers for this Pod.
- **`searches`**: Additional search suffixes appended for non-FQDN queries.
- **`options`**: Resolver behavior (for example `ndots` controls when the resolver tries absolute vs. search-domain resolution).

---

## Comparison: DNS-related Pod settings

| **Configuration** | **Purpose** | **Behavior** |
|-------------------|-------------|--------------|
| **`hostNetwork: true`** | Use the host’s network stack. | Pod shares the node’s IP and bypasses normal Pod networking (CNI path differs). |
| **`dnsPolicy: ClusterFirstWithHostNet`** | Cluster DNS with host networking. | Resolves Kubernetes Service names and external names; pairs with `hostNetwork: true`. |
| **`dnsPolicy: None`** | No default cluster DNS for the Pod. | Requires explicit **`dnsConfig`**; use when you fully own resolver settings. |
| **`dnsConfig.nameservers`** | Custom DNS servers. | Overrides default cluster DNS servers for that Pod. |
| **`dnsConfig.searches`** | Custom search domains. | Appends domains when resolving short names. |
| **`dnsConfig.options`** | Resolver tuning. | Examples include `ndots`, extended DNS options. |

### How to use this table

- Use **`hostNetwork`** with **`ClusterFirstWithHostNet`** when the Pod must use the host network but still participate in cluster Service DNS.
- Use **`dnsPolicy: None`** with **`dnsConfig`** when you need resolver settings that the cluster default cannot express (custom upstreams, search lists, or options).

---

## Hands-On Labs

Practice these concepts with guided lab exercises:

| Lab | Description |
|-----|-------------|
| [Lab 45: DNS Configuration in Kubernetes](../../labmanuals/lab45-net-dns-configuration.md) | DNS policies, custom `dnsConfig`, and host aliases for Pods. |
| [Lab 56: CoreDNS — Kubernetes DNS Deep Dive](../../labmanuals/lab56-net-coredns.md) | CoreDNS architecture, records, and cluster DNS troubleshooting. |
