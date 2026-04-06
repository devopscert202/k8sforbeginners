**Scanning Kubernetes Cluster Resources Using the Trivy CLI**

## Introduction to Trivy
Trivy is an open-source vulnerability scanner developed by Aqua Security. It is widely used for scanning container images, file systems, and Kubernetes resources for security vulnerabilities. Trivy helps identify Common Vulnerabilities and Exposures (CVEs) in images and misconfigurations in cloud infrastructure. With its ease of use and integration into CI/CD pipelines, Trivy has become a go-to tool for DevSecOps teams.

## Prerequisites (conceptual)
To use Trivy against a cluster or images you typically need: a Kubernetes cluster and working `kubectl` access when scanning workloads; a local or CI environment where the Trivy binary or container image can run; and network access to refresh vulnerability databases. Helm is optional if you deploy the **Trivy Operator** in-cluster rather than using the CLI only.

## Installation and deployment options
Trivy can be installed via OS package managers, the upstream install script, Docker (`aquasec/trivy`), or as the **Trivy Operator** with Helm. Platform-specific steps change frequently; use the [Trivy documentation](https://aquasecurity.github.io/trivy/) for authoritative install and upgrade instructions.

## What Trivy Does
Trivy performs security scans on:
- Container images (Docker, Podman, and OCI-compliant images)
- Kubernetes resources (Deployments, Pods, Secrets, ConfigMaps)
- File systems and code repositories
- Infrastructure as Code (IaC) files (Terraform, Kubernetes manifests, Dockerfiles)
- Cloud services (AWS, GCP, and Azure)

## Use Cases
- **Container Security**: Scanning images for vulnerabilities before deployment
- **Kubernetes Security**: Identifying vulnerabilities in running workloads
- **CI/CD Integration**: Ensuring secure software delivery pipelines
- **Compliance Auditing**: Verifying adherence to security benchmarks like CIS Kubernetes Benchmark
- **Infrastructure Security**: Scanning Terraform and Kubernetes manifests for misconfigurations

## Other Tools Similar to Trivy
| Tool           | Features                                             | License        |
|--------------|--------------------------------------------------|-------------|
| Clair         | Static analysis of vulnerabilities in OCI images | Open Source |
| Anchore       | Policy-based container security scanning         | Open Source |
| Snyk          | Developer-friendly security scanning             | Commercial  |
| Grype         | Vulnerability scanning for container images      | Open Source |
| Kube-bench    | Kubernetes CIS Benchmark security checks         | Open Source |

## Scanning patterns (conceptual)
- **Image scans**: Point Trivy at an image reference to list CVEs by severity; JSON or HTML report formats help automation and human review.
- **Cluster / workload scans**: The `trivy k8s` family of commands evaluates resources visible to your current kubeconfig against policies and vulnerability data.
- **CI/CD gates**: Fail builds or promotions when severities exceed organizational thresholds, and attach reports to tickets or chat for triage.

## Conclusion
Trivy is an essential tool for security scanning in Kubernetes and containerized environments. Its ease of use, integration capabilities, and comprehensive scanning make it a preferred choice for DevSecOps professionals. Incorporating Trivy into CI/CD pipelines and cluster workflows helps organizations proactively identify and mitigate vulnerabilities.

---

## Hands-On Labs

Practice these concepts with guided lab exercises:

| Lab | Description |
|-----|-------------|
| [Lab 15: Container Image Scanning with Trivy](../../labmanuals/lab15-sec-image-scanning-trivy.md) | Install Trivy, run image and cluster scans, and interpret reports. |
