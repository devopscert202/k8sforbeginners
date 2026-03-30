# Lab 15: Container Image Scanning with Trivy

## Overview
In this lab, you will learn how to use Trivy, an open-source vulnerability scanner, to scan container images and Kubernetes cluster resources for security vulnerabilities. You'll install Trivy, scan Docker images, generate various report formats, and scan running Kubernetes workloads.

## Prerequisites
- A running Kubernetes cluster
- kubectl CLI tool installed and configured
- Docker installed (for local image scanning)
- Internet access (for vulnerability database updates)
- Basic understanding of container images and CVEs

## Learning Objectives
By the end of this lab, you will be able to:
- Understand container image vulnerability scanning
- Install and configure Trivy
- Scan Docker images for security vulnerabilities
- Generate reports in multiple formats (text, JSON, HTML)
- Scan Kubernetes cluster resources
- Interpret scan results and severity levels
- Integrate scanning into development workflows
- Compare Trivy with other security scanning tools

---

## Understanding Container Security Scanning

### What is Trivy?

**Trivy** is a comprehensive security scanner developed by Aqua Security. It detects:
- **Vulnerabilities (CVEs)** in OS packages and application dependencies
- **Misconfigurations** in IaC files and Kubernetes manifests
- **Secrets** accidentally committed in code
- **License issues** in software dependencies

### Why Scan Container Images?

Container image scanning helps you:
- Identify known vulnerabilities before deployment
- Meet compliance and security requirements
- Reduce attack surface
- Prevent deploying compromised images
- Track and remediate security issues
- Shift security left in CI/CD pipelines

### Vulnerability Severity Levels

Trivy categorizes vulnerabilities by severity:

| Severity | Risk Level | Action Required |
|----------|------------|-----------------|
| **CRITICAL** | Highest | Immediate remediation required |
| **HIGH** | Severe | Urgent remediation required |
| **MEDIUM** | Moderate | Plan remediation |
| **LOW** | Minor | Monitor and plan |
| **UNKNOWN** | Unclear | Investigate further |

### Trivy vs Other Tools

| Tool | Type | Strengths | License |
|------|------|-----------|---------|
| **Trivy** | Scanner | Fast, comprehensive, easy to use | Open Source |
| **Clair** | Scanner | Static analysis of OCI images | Open Source |
| **Anchore** | Scanner | Policy-based scanning | Open Source |
| **Snyk** | Scanner | Developer-friendly, good UI | Commercial |
| **Grype** | Scanner | Fast vulnerability scanning | Open Source |
| **Kube-bench** | Auditor | CIS Benchmark checks | Open Source |

---

## Exercise 1: Install Trivy

### Step 1: Install on Linux/Ubuntu

Install Trivy on Linux using the official repository:

```bash
sudo apt-get update
sudo apt-get install -y wget apt-transport-https gnupg lsb-release
```

Add Trivy repository:

```bash
wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | gpg --dearmor | sudo tee /usr/share/keyrings/trivy.gpg > /dev/null
echo "deb [signed-by=/usr/share/keyrings/trivy.gpg] https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main" | sudo tee -a /etc/apt/sources.list.d/trivy.list
```

Install Trivy:

```bash
sudo apt-get update
sudo apt-get install -y trivy
```

### Step 2: Install on macOS

Using Homebrew:

```bash
brew install trivy
```

### Step 3: Install on Windows

Using Chocolatey:

```powershell
choco install trivy
```

Using Scoop:

```powershell
scoop install trivy
```

### Step 4: Install via Docker (Any Platform)

Pull the Trivy Docker image:

```bash
docker pull aquasec/trivy:latest
```

Create an alias for convenience:

```bash
alias trivy="docker run --rm -v /var/run/docker.sock:/var/run/docker.sock -v $HOME/.cache:/root/.cache aquasec/trivy"
```

### Step 5: Verify Installation

Check Trivy version:

```bash
trivy --version
```

Expected output:
```
Version: 0.50.0
```

Update vulnerability database:

```bash
trivy image --download-db-only
```

Expected output:
```
2026-03-16T10:00:00.000Z  INFO  Downloading vulnerability database...
2026-03-16T10:00:05.000Z  INFO  Vulnerability database updated successfully
```

---

## Exercise 2: Basic Image Scanning

### Step 1: Pull a Sample Image

Pull the nginx image for testing:

```bash
docker pull nginx:latest
```

### Step 2: Scan the Image

Run a basic scan:

```bash
trivy image nginx:latest
```

Expected output (partial):
```
2026-03-16T10:05:00.000Z  INFO  Detected OS: debian
2026-03-16T10:05:00.000Z  INFO  Detecting Debian vulnerabilities...
2026-03-16T10:05:01.000Z  INFO  Number of language-specific files: 0

nginx:latest (debian 12.5)
==========================
Total: 45 (UNKNOWN: 0, LOW: 23, MEDIUM: 15, HIGH: 5, CRITICAL: 2)

┌──────────────┬────────────────┬──────────┬───────────────────┬───────────────┬──────────────────────────────────────┐
│   Library    │ Vulnerability  │ Severity │ Installed Version │ Fixed Version │                Title                 │
├──────────────┼────────────────┼──────────┼───────────────────┼───────────────┼──────────────────────────────────────┤
│ libssl3      │ CVE-2024-XXXX  │ CRITICAL │ 3.0.11-1          │ 3.0.11-2      │ OpenSSL: Buffer overflow vulnerability│
│ libcrypto3   │ CVE-2024-XXXX  │ CRITICAL │ 3.0.11-1          │ 3.0.11-2      │ OpenSSL: Buffer overflow vulnerability│
│ libcurl4     │ CVE-2024-YYYY  │ HIGH     │ 7.88.1-1          │ 7.88.1-2      │ curl: Use-after-free vulnerability    │
└──────────────┴────────────────┴──────────┴───────────────────┴───────────────┴──────────────────────────────────────┘
```

**Understanding the output:**
- **Library** - Package or dependency name
- **Vulnerability** - CVE identifier
- **Severity** - Risk level (CRITICAL, HIGH, MEDIUM, LOW)
- **Installed Version** - Current version in the image
- **Fixed Version** - Version that fixes the vulnerability
- **Title** - Brief description

### Step 3: Filter by Severity

Scan for only CRITICAL and HIGH vulnerabilities:

```bash
trivy image --severity CRITICAL,HIGH nginx:latest
```

This reduces noise by focusing on the most important issues.

### Step 4: Scan a Specific Version

Compare with an older version:

```bash
docker pull nginx:1.20
trivy image --severity CRITICAL,HIGH nginx:1.20
```

Older versions typically have more vulnerabilities!

---

## Exercise 3: Generate Reports

### Step 1: JSON Output

Generate a JSON report for automated processing:

```bash
trivy image -f json -o nginx-report.json nginx:latest
```

View the report:

```bash
cat nginx-report.json | jq '.Results[0].Vulnerabilities[0]'
```

Expected output (formatted):
```json
{
  "VulnerabilityID": "CVE-2024-XXXX",
  "PkgName": "libssl3",
  "InstalledVersion": "3.0.11-1",
  "FixedVersion": "3.0.11-2",
  "Severity": "CRITICAL",
  "Title": "OpenSSL: Buffer overflow vulnerability",
  "Description": "A buffer overflow vulnerability exists in OpenSSL...",
  "References": [
    "https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2024-XXXX"
  ]
}
```

### Step 2: HTML Output

Generate an HTML report:

```bash
trivy image --format template --template "@/usr/local/share/trivy/templates/html.tpl" -o nginx-report.html nginx:latest
```

**Note**: Template path may vary by installation method. Find templates:

```bash
trivy --help | grep template
# Or check: /usr/local/share/trivy/templates/
```

Alternative method using Docker:

```bash
docker run --rm -v $(pwd):/report aquasec/trivy image --format template --template "@contrib/html.tpl" -o /report/nginx-report.html nginx:latest
```

Open the HTML file in a browser:

```bash
# On Linux
xdg-open nginx-report.html

# On macOS
open nginx-report.html

# On Windows
start nginx-report.html
```

The HTML report provides a user-friendly interface to review vulnerabilities.

### Step 3: Table Output (Default)

Generate a text table report:

```bash
trivy image -o nginx-report.txt nginx:latest
```

This is the default format, suitable for logs and CI/CD pipelines.

### Step 4: SARIF Output (for GitHub)

Generate SARIF format for GitHub Security:

```bash
trivy image --format sarif -o nginx-report.sarif nginx:latest
```

SARIF format integrates with GitHub Advanced Security for vulnerability tracking.

---

## Exercise 4: Scan Kubernetes Workloads

### Step 1: Deploy a Test Application

Create a deployment with a potentially vulnerable image:

```bash
kubectl create deployment nginx-app --image=nginx:1.20
```

Wait for the Pod to be ready:

```bash
kubectl wait --for=condition=ready pod -l app=nginx-app --timeout=60s
```

### Step 2: Scan Kubernetes Cluster

Scan all resources in the default namespace:

```bash
trivy k8s --report summary namespace default
```

Expected output:
```
2026-03-16T10:15:00.000Z  INFO  Scanning namespace: default
2026-03-16T10:15:05.000Z  INFO  Found 1 deployment

Summary Report for default namespace
=====================================

Workload: deployment/nginx-app
Image: nginx:1.20
Vulnerabilities: CRITICAL: 5, HIGH: 12, MEDIUM: 23, LOW: 45

Total Workloads: 1
Total Images: 1
Total Vulnerabilities: CRITICAL: 5, HIGH: 12, MEDIUM: 23, LOW: 45
```

### Step 3: Detailed Kubernetes Scan

Get detailed vulnerability information:

```bash
trivy k8s --report all namespace default
```

This shows detailed CVE information for all images in the namespace.

### Step 4: Scan Specific Workload

Scan a specific deployment:

```bash
trivy k8s deployment/nginx-app
```

### Step 5: Scan All Namespaces

Scan the entire cluster:

```bash
trivy k8s --report summary all
```

**Warning**: This can take a while in large clusters!

### Step 6: Scan with Filters

Scan only CRITICAL vulnerabilities:

```bash
trivy k8s --severity CRITICAL --report summary namespace default
```

Scan specific resource types:

```bash
trivy k8s --include-kinds Deployment,StatefulSet --report summary namespace default
```

---

## Exercise 5: Scan Local Files and Configurations

### Step 1: Scan a Dockerfile

Create a sample Dockerfile:

```bash
cat > Dockerfile <<'EOF'
FROM ubuntu:20.04

RUN apt-get update && \
    apt-get install -y nginx curl

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
EOF
```

Scan the Dockerfile for misconfigurations:

```bash
trivy config Dockerfile
```

Expected output:
```
Dockerfile (dockerfile)
=======================
Tests: 23 (SUCCESSES: 20, FAILURES: 3, EXCEPTIONS: 0)
Failures: 3 (UNKNOWN: 0, LOW: 1, MEDIUM: 1, HIGH: 1, CRITICAL: 0)

MEDIUM: Specify at least 1 USER command in Dockerfile with non-root user
════════════════════════════════════════
Running as root increases security risk. Use USER to switch to a non-root user.

HIGH: Last USER command should not be 'root'
════════════════════════════════════════
The last USER should not be root for security reasons.
```

### Step 2: Scan Kubernetes Manifests

Create a Pod manifest:

```bash
cat > pod.yaml <<'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: test-pod
spec:
  containers:
  - name: nginx
    image: nginx:latest
    securityContext:
      privileged: true
EOF
```

Scan for misconfigurations:

```bash
trivy config pod.yaml
```

Expected output:
```
pod.yaml (kubernetes)
=====================
Tests: 28 (SUCCESSES: 25, FAILURES: 3, EXCEPTIONS: 0)
Failures: 3 (UNKNOWN: 0, LOW: 0, MEDIUM: 1, HIGH: 2, CRITICAL: 0)

HIGH: Container is running in privileged mode
════════════════════════════════════════
Privileged containers have access to all devices and can compromise the host.

See https://avd.aquasec.com/misconfig/ksv017
```

### Step 3: Scan a Directory

Scan an entire directory of manifests:

```bash
mkdir k8s-manifests
cp pod.yaml k8s-manifests/
trivy config k8s-manifests/
```

---

## Exercise 6: CI/CD Integration

### Step 1: Create a Scan Script

Create a script for CI/CD integration:

```bash
cat > scan-images.sh <<'EOF'
#!/bin/bash

IMAGE=$1
SEVERITY="CRITICAL,HIGH"

echo "Scanning image: $IMAGE"
trivy image --severity $SEVERITY --exit-code 1 $IMAGE

if [ $? -eq 0 ]; then
  echo "✅ No critical vulnerabilities found"
  exit 0
else
  echo "❌ Critical vulnerabilities detected"
  exit 1
fi
EOF

chmod +x scan-images.sh
```

### Step 2: Test the Script

Test with a vulnerable image:

```bash
./scan-images.sh nginx:1.20
```

The script exits with code 1 if vulnerabilities are found, perfect for CI/CD gates.

### Step 3: Ignore Specific Vulnerabilities

Create a .trivyignore file for known false positives:

```bash
cat > .trivyignore <<'EOF'
# Ignore CVE-2024-12345 - False positive confirmed by security team
CVE-2024-12345

# Ignore CVE-2024-67890 - No fix available, mitigated by network policies
CVE-2024-67890
EOF
```

Run scan with ignore file:

```bash
trivy image --ignorefile .trivyignore nginx:latest
```

### Step 4: Cache Database for CI/CD

Download the database once for faster subsequent scans:

```bash
trivy image --download-db-only
```

Use cached database in scans:

```bash
trivy image --skip-db-update nginx:latest
```

---

## Exercise 7: Remediation Workflow

### Step 1: Identify Vulnerable Packages

Scan and identify fixable vulnerabilities:

```bash
trivy image --severity CRITICAL,HIGH nginx:1.20 | grep -E "CRITICAL|HIGH"
```

### Step 2: Update to Patched Version

Pull a newer image version:

```bash
docker pull nginx:latest
trivy image --severity CRITICAL,HIGH nginx:latest
```

Compare vulnerability counts between versions.

### Step 3: Update Kubernetes Deployment

Update the deployment to use the patched image:

```bash
kubectl set image deployment/nginx-app nginx=nginx:latest
```

Verify the update:

```bash
kubectl rollout status deployment/nginx-app
```

### Step 4: Rescan the Cluster

Verify vulnerabilities are reduced:

```bash
trivy k8s --severity CRITICAL,HIGH --report summary namespace default
```

---

## Lab Cleanup

### Step 1: Delete Kubernetes Resources

```bash
kubectl delete deployment nginx-app
```

### Step 2: Remove Docker Images

```bash
docker rmi nginx:latest nginx:1.20
```

### Step 3: Clean Up Files

```bash
rm -f nginx-report.json nginx-report.html nginx-report.txt nginx-report.sarif
rm -f Dockerfile pod.yaml scan-images.sh .trivyignore
rm -rf k8s-manifests/
```

---

## Trivy Best Practices

### Scanning Strategy

- **Scan early** - Integrate scanning in development workflow
- **Scan often** - Regular scans catch new vulnerabilities
- **Fail fast** - Block deployments with critical vulnerabilities
- **Prioritize** - Focus on CRITICAL and HIGH severity first
- **Update regularly** - Keep vulnerability database current

### CI/CD Integration

- Add Trivy scanning to CI pipelines (GitHub Actions, GitLab CI, Jenkins)
- Set severity thresholds for build failures
- Generate reports for security dashboards
- Cache vulnerability database for faster scans
- Use .trivyignore for accepted risks

### Operational Security

- Schedule periodic cluster scans
- Monitor for new vulnerabilities in deployed images
- Establish remediation SLAs by severity
- Track vulnerability trends over time
- Integrate with incident response processes

### Image Management

- Use minimal base images (alpine, distroless)
- Keep base images updated
- Use specific image tags, not :latest
- Scan images before pushing to registry
- Maintain image inventory with scan results

---

## Common Trivy Commands Reference

### Image Scanning

```bash
# Basic scan
trivy image <image-name>

# Scan with severity filter
trivy image --severity CRITICAL,HIGH <image-name>

# Scan without updating DB
trivy image --skip-db-update <image-name>

# Scan and fail on vulnerabilities
trivy image --exit-code 1 --severity CRITICAL <image-name>

# Scan with custom timeout
trivy image --timeout 10m <image-name>
```

### Kubernetes Scanning

```bash
# Scan namespace
trivy k8s namespace <namespace>

# Scan all namespaces
trivy k8s all

# Scan specific workload
trivy k8s deployment/<name>

# Summary report
trivy k8s --report summary namespace default
```

### Configuration Scanning

```bash
# Scan Dockerfile
trivy config Dockerfile

# Scan Kubernetes manifests
trivy config deployment.yaml

# Scan directory
trivy config /path/to/configs/
```

### Output Formats

```bash
# JSON output
trivy image -f json -o report.json <image>

# Table output (default)
trivy image -o report.txt <image>

# SARIF output
trivy image --format sarif -o report.sarif <image>
```

---

## Troubleshooting Guide

### Issue: "Error downloading vulnerability database"

**Cause**: Network connectivity or proxy issues

**Solution**:
```bash
# Check internet connectivity
curl -I https://github.com

# Use proxy if needed
export HTTP_PROXY=http://proxy.example.com:8080
export HTTPS_PROXY=http://proxy.example.com:8080

# Manual download
trivy image --download-db-only
```

### Issue: Scans are very slow

**Cause**: Database updates or large images

**Solution**:
```bash
# Skip DB update if recently updated
trivy image --skip-db-update <image>

# Use cache
trivy image --cache-dir /tmp/trivy-cache <image>

# Scan specific layers only
trivy image --skip-dirs /usr/share/doc <image>
```

### Issue: Too many low-severity findings

**Cause**: Default scans all severities

**Solution**:
```bash
# Filter by severity
trivy image --severity CRITICAL,HIGH <image>

# Ignore unfixed vulnerabilities
trivy image --ignore-unfixed <image>
```

---

## Key Takeaways

1. Trivy is a comprehensive vulnerability scanner for containers and Kubernetes
2. Regular scanning helps identify and remediate security issues early
3. Different output formats support various use cases (CI/CD, reporting, dashboards)
4. Kubernetes cluster scanning identifies vulnerabilities in running workloads
5. Configuration scanning detects misconfigurations in IaC files
6. Severity filtering helps prioritize remediation efforts
7. CI/CD integration enables shift-left security practices
8. Regular updates to vulnerability database are essential

---

## Additional Reading

- [Trivy Documentation](https://aquasecurity.github.io/trivy/)
- [Trivy GitHub Repository](https://github.com/aquasecurity/trivy)
- [CVE Database](https://cve.mitre.org/)
- [Container Security Best Practices](https://kubernetes.io/docs/concepts/security/pod-security-standards/)
- [NIST Vulnerability Database](https://nvd.nist.gov/)

---

**Lab Created**: March 2026
**Compatible with**: Trivy 0.50+, Kubernetes 1.24+
**Based on**: labs/security/image_scanning.md
**Tested on**: Linux, macOS, Windows
**Estimated Time**: 60-75 minutes
