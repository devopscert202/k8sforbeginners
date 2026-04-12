# Kubernetes Vulnerabilities and Container Image Scanning

Security in Kubernetes spans the cluster infrastructure, the workloads running on it, and the container images those workloads are built from. This document walks through the vulnerability landscape — from general concepts to Kubernetes-specific risks to container image threats — and then covers the scanning tools and practices that help you find and fix problems before attackers do.

---

## 1. What Are Vulnerabilities?

A **vulnerability** is a weakness in software, configuration, or infrastructure that an attacker can exploit to compromise a system. Vulnerabilities arise from coding errors, outdated dependencies, misconfigurations, or improper access control.

### Vulnerability Databases

When a vulnerability is discovered, it is catalogued in public databases so defenders can track and remediate it:

| Database | Maintained by | Purpose |
|----------|--------------|---------|
| **CVE** (Common Vulnerabilities and Exposures) | MITRE | Unique identifiers for publicly known flaws |
| **NVD** (National Vulnerability Database) | NIST | CVE details with CVSS severity scores |
| **Exploit-DB** | Offensive Security | Known exploits for CVEs |
| **MITRE ATT&CK** | MITRE | Adversary tactics, techniques, and procedures |
| **Vendor advisories** | Microsoft, Red Hat, Google, etc. | Product-specific security bulletins |

### Why Vulnerability Management Is Hard

1. **Constantly evolving threats** — new CVEs are published daily
2. **Large attack surface** — a Kubernetes cluster has nodes, the API server, etcd, kubelet, container images, and application code
3. **Patch lag** — keeping every component up to date across environments is operationally challenging
4. **False positives** — scanners flag issues that may not be exploitable in your context
5. **Speed vs security** — security checks must fit into fast CI/CD delivery cycles

---

## 2. Kubernetes-Specific Vulnerabilities

Kubernetes introduces its own attack surface beyond traditional application vulnerabilities.

### Common Kubernetes Security Issues

| Risk | Description |
|------|-------------|
| **Misconfigured RBAC** | Overly broad roles grant attackers control over cluster resources |
| **Exposed API Server** | A publicly accessible API server is an easy entry point |
| **Unpatched components** | Outdated kubelet, API server, or etcd versions contain known exploits |
| **Container escape** | Kernel or runtime flaws let attackers break out of container isolation |
| **Supply chain attacks** | Malicious or compromised base images inject vulnerabilities at build time |
| **Missing Network Policies** | Unrestricted pod-to-pod communication enables lateral movement |
| **Privileged containers** | Containers running as root or with host namespaces bypass isolation |
| **Exposed Secrets** | Secrets stored in environment variables or unencrypted etcd are easily leaked |

### Notable Kubernetes CVEs

| CVE | Impact |
|-----|--------|
| **CVE-2018-1002105** | API Server privilege escalation via crafted requests |
| **CVE-2020-8554** | Man-in-the-middle attack in multi-tenant clusters via ExternalIP |
| **CVE-2021-25741** | Symlink-exchange vulnerability allowing container escape via subPath volumes |
| **CVE-2022-0185** | Linux kernel heap overflow exploitable from unprivileged containers |

### Hardening the Cluster

| Control | How |
|---------|-----|
| Keep Kubernetes updated | Run the latest stable minor release; apply patch versions promptly |
| Enforce RBAC | Grant minimal required permissions; avoid wildcard rules |
| Enable Network Policies | Restrict pod-to-pod and egress communication |
| Use Pod Security Standards | Enforce `restricted` or `baseline` profiles to block privileged containers |
| Restrict API access | Use authentication, authorization, and IP allowlisting |
| Encrypt Secrets at rest | Enable etcd encryption; use external secret managers |
| Scan images continuously | Detect CVEs in images before and after deployment |

---

## 3. Container Image Vulnerabilities

Container images are the **supply chain** of Kubernetes workloads. Every image bundles an OS layer, language runtime, libraries, and application code — each of which can contain vulnerabilities.

### Where Vulnerabilities Hide in Images

```
┌─────────────────────────────────┐
│  Application code (your code)   │  ← Logic bugs, hardcoded secrets
├─────────────────────────────────┤
│  Application dependencies       │  ← npm, pip, Maven packages with CVEs
├─────────────────────────────────┤
│  Language runtime (Node, Python) │  ← Runtime CVEs
├─────────────────────────────────┤
│  OS packages (apt, apk, yum)    │  ← Unpatched system libraries (openssl, glibc)
├─────────────────────────────────┤
│  Base image (ubuntu, alpine)    │  ← Inherited vulnerabilities from upstream
└─────────────────────────────────┘
```

### Image Security Best Practices

| Practice | Why |
|----------|-----|
| **Use minimal base images** | Alpine or distroless images have fewer packages to be vulnerable |
| **Pin image tags** | `nginx:1.25-alpine` not `nginx:latest` — reproducible and auditable |
| **Scan in CI/CD** | Catch CVEs before images reach the cluster |
| **Rebuild regularly** | Even if your code hasn't changed, base image patches close CVEs |
| **Don't run as root** | Set `USER` in Dockerfile; use `securityContext.runAsNonRoot` in K8s |
| **Sign and verify images** | Use cosign/sigstore to ensure image provenance |

---

## 4. Vulnerability Scanning Tools

Multiple tools address different parts of the Kubernetes security landscape:

### Scanning Tool Comparison

| Tool | What it scans | Type | License |
|------|--------------|------|---------|
| **Trivy** | Images, K8s resources, IaC, filesystems, SBOM | All-in-one scanner | Open Source (Apache 2.0) |
| **Grype** | Container images and filesystems | Image vulnerability scanner | Open Source |
| **Clair** | OCI container images (static analysis) | Image vulnerability scanner | Open Source |
| **Anchore** | Images with policy-based gates | Image + policy scanner | Open Source / Commercial |
| **Snyk** | Images, code, dependencies, IaC | Developer-focused scanner | Commercial (free tier) |
| **Kube-bench** | Cluster configuration vs CIS Benchmark | Cluster compliance checker | Open Source |
| **Kube-hunter** | Active probing for K8s security issues | Cluster penetration tester | Open Source |
| **Kubescape** | K8s compliance (NSA, MITRE, CIS) | Cluster compliance scanner | Open Source |
| **Falco** | Runtime syscall monitoring | Runtime threat detection | Open Source (CNCF) |

### Choosing the Right Tool

- **Image scanning in CI/CD** → Trivy or Grype (fast, CLI-friendly, no server needed)
- **Cluster compliance** → Kube-bench (CIS) or Kubescape (NSA/MITRE)
- **Runtime detection** → Falco (monitors live container behavior)
- **Policy gates** → Anchore or Snyk (block deployments that fail policy)

---

## 5. Deep Dive: Trivy

**Trivy** (by Aqua Security) is the most widely adopted open-source scanner for Kubernetes environments. It covers the full spectrum — images, clusters, IaC, and filesystems — in a single tool.

### What Trivy Scans

| Target | Command pattern | What it finds |
|--------|----------------|---------------|
| Container images | `trivy image nginx:1.25` | CVEs in OS packages and language dependencies |
| Kubernetes cluster | `trivy k8s --report summary` | Vulnerabilities and misconfigurations in running workloads |
| Filesystem / repo | `trivy fs .` | CVEs in project dependencies (package-lock.json, requirements.txt, etc.) |
| IaC files | `trivy config .` | Misconfigurations in Kubernetes manifests, Dockerfiles, Terraform |
| SBOM generation | `trivy image --format spdx nginx:1.25` | Software Bill of Materials for compliance |

### Trivy Output Severity Levels

| Severity | CVSS Score | Action |
|----------|-----------|--------|
| **CRITICAL** | 9.0 – 10.0 | Fix immediately — active exploits likely exist |
| **HIGH** | 7.0 – 8.9 | Fix in current sprint — significant risk |
| **MEDIUM** | 4.0 – 6.9 | Schedule fix — moderate risk |
| **LOW** | 0.1 – 3.9 | Track — minimal immediate risk |
| **UNKNOWN** | N/A | Investigate — severity not yet assigned |

### Installation Options

Trivy can be installed via:
- **OS package managers** — `apt`, `yum`, `brew`
- **Install script** — `curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh`
- **Docker** — `docker run aquasec/trivy image nginx:1.25`
- **Trivy Operator** — Helm chart for continuous in-cluster scanning

See the [Trivy documentation](https://aquasecurity.github.io/trivy/) for the latest installation instructions.

### Scanning Patterns

**Image scans** — point Trivy at an image reference to list CVEs by severity; use `--format json` or `--format table` for automation or human review:

```
trivy image nginx:1.25-alpine
trivy image --severity CRITICAL,HIGH myregistry/myapp:v2.1
```

**Cluster / workload scans** — evaluate resources visible to your current kubeconfig:

```
trivy k8s --report summary
trivy k8s --report all --namespace production
```

**CI/CD gates** — fail builds when severities exceed thresholds:

```
trivy image --exit-code 1 --severity CRITICAL myapp:latest
```

### Trivy Use Cases

| Use case | How |
|----------|-----|
| **Pre-deployment scanning** | Scan images in CI pipeline before pushing to registry |
| **Admission control** | Use Trivy Operator + OPA/Kyverno to block vulnerable images |
| **Continuous monitoring** | Trivy Operator rescans running workloads on database updates |
| **Compliance reporting** | Generate SBOM and vulnerability reports for auditors |
| **IaC review** | Scan Kubernetes manifests and Dockerfiles in pull requests |

---

## 6. Prioritizing and Remediating Vulnerabilities

Not all vulnerabilities require the same urgency. A structured approach helps focus effort where it matters most.

### Prioritization Framework

| Factor | Question to ask |
|--------|----------------|
| **CVSS score** | Is it Critical (9+) or High (7+)? |
| **Exploitability** | Does a public exploit exist? Is it being used in the wild? |
| **Exposure** | Is the vulnerable component internet-facing or internal-only? |
| **Business impact** | Does it affect customer data, revenue, or compliance? |
| **Fix availability** | Is a patched version available? How hard is the upgrade? |

### Remediation Workflow

```
Scan → Triage → Prioritize → Fix → Verify → Monitor
  │                                          │
  └──────── continuous loop ─────────────────┘
```

1. **Scan** — run Trivy (or your chosen tool) against images, clusters, and IaC
2. **Triage** — filter false positives, group by component
3. **Prioritize** — CRITICAL + exploitable + exposed = fix first
4. **Fix** — update base image, bump dependency, apply patch
5. **Verify** — rescan to confirm the fix; ensure no regressions
6. **Monitor** — new CVEs appear daily; schedule regular rescans

---

## 7. The Operations Team's Role

| Responsibility | Tools / approach |
|---------------|-----------------|
| **Monitoring & logging** | Prometheus, Grafana, ELK/Loki for observability; Falco for runtime alerts |
| **Incident response** | Documented runbooks; automated alerting on CRITICAL findings |
| **Regular security audits** | CIS benchmark checks (kube-bench), penetration testing (kube-hunter) |
| **Patch & upgrade management** | Keep Kubernetes, node OS, container images, and dependencies current |
| **Training & awareness** | Educate developers on secure Dockerfiles, least-privilege RBAC, and image hygiene |
| **Policy enforcement** | Admission controllers (OPA Gatekeeper, Kyverno) to block non-compliant workloads |

---

## Conclusion

Kubernetes security is not a one-time setup — it is a continuous practice spanning the cluster, its configuration, the images it runs, and the CI/CD pipelines that deliver them. By understanding where vulnerabilities hide (cluster components, RBAC misconfigurations, container images, supply chain), choosing the right scanning tools, and building remediation into your workflow, you significantly reduce the attack surface and respond faster when new threats emerge.

---

## Hands-On Labs

Practice these concepts with guided lab exercises:

| Lab | Description |
|-----|-------------|
| [Lab 15: Container Image Scanning with Trivy](../../labmanuals/lab15-sec-image-scanning-trivy.md) | Install Trivy, scan container images and cluster resources, interpret severity reports, and integrate scanning into workflows |
| [Lab 16: Pod Security Standards & Admission Control](../../labmanuals/lab16-sec-pod-security-standards.md) | Enforce pod security profiles (`restricted`, `baseline`) to block privileged containers and reduce workload risk |
