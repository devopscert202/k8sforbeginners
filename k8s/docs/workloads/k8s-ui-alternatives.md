# Kubernetes UI and Dashboard Alternatives

## Background

Kubernetes teams do not all need the same kind of interface. Some need a shared browser-based UI, some need a local desktop application, and some prefer a terminal-first workflow.

With Kubernetes Dashboard now treated as a legacy path, it is useful to compare the main alternatives and choose the right tool for the right operating model.

---

## Main Alternatives

## 1. Headlamp Web

**Headlamp** can run in-cluster as a web UI.

### Strengths

- browser-based cluster access
- Kubernetes-focused UI
- plugin extensibility
- current active documentation
- fits RBAC-based Kubernetes access patterns

### Best fit

- shared internal Kubernetes UI access
- current web-based Kubernetes operations
- teams that want a Kubernetes-first browser interface

---

## 2. Headlamp Desktop

Headlamp also has a **desktop application**.

### Strengths

- no in-cluster deployment required
- local access using kubeconfig
- works well across multiple clusters
- useful for workstation-driven administration

### Best fit

- platform engineers
- administrators
- developers with local kubeconfig access

---

## 3. FreeLens

**FreeLens** is a free and open-source Kubernetes IDE with a desktop-first model.

### Strengths

- local desktop interface
- multi-cluster access
- extension-oriented workflow
- GUI-based Kubernetes management without deploying a shared web UI

### Best fit

- users who prefer a local desktop console
- multi-cluster workstation usage
- GUI-first workflows

---

## 4. Portainer

**Portainer** is broader than a Kubernetes-only interface. It is a container management platform for Kubernetes, Docker, and Podman environments.

### Strengths

- centralized platform management
- broader governance and access control
- multi-environment visibility
- useful beyond Kubernetes-only operations

### Best fit

- enterprise IT teams
- mixed container environments
- centralized governance and broader platform operations

---

## 5. K9s

**K9s** is a terminal UI for Kubernetes.

### Strengths

- terminal-first workflow
- very fast navigation
- real-time watching of resources
- strong fit for shell-based operations

### Best fit

- SRE and operations teams
- terminal-heavy workflows
- fast troubleshooting without moving to a browser

---

## Quick Comparison

| Tool | Primary Mode | Best For | Main Strength |
|------|--------------|----------|---------------|
| Headlamp Web | In-cluster web UI | Shared browser access | Current Kubernetes-focused web path |
| Headlamp Desktop | Desktop app | Local workstation access | No in-cluster deployment required |
| FreeLens | Desktop app | GUI-first local usage | Kubernetes IDE-style experience |
| Portainer | Web platform | Enterprise platform operations | Broader governance and fleet control |
| K9s | Terminal UI | Fast shell-first operations | Speed and terminal-native navigation |

---

## How to Choose

### Choose Headlamp Web when:

- a shared browser UI is required
- a Kubernetes-focused web interface is preferred
- in-cluster deployment is acceptable

### Choose Headlamp Desktop or FreeLens when:

- desktop-based local access is preferred
- kubeconfig-driven workstation usage is enough
- a shared web service is not needed first

### Choose Portainer when:

- broader platform governance matters
- Kubernetes is only part of the container estate
- centralized control across environments is important

### Choose K9s when:

- the shell is the main operating environment
- speed matters more than a graphical browser UI
- terminal-based troubleshooting is preferred

---

## Recommended Direction for This Repository

For this repository, the most suitable default path is:

1. **Headlamp in-cluster** for shared browser-based Kubernetes UI access
2. **Headlamp Desktop** or **FreeLens** for local workstation-based UI access
3. **K9s** as the terminal-first operational companion

Portainer remains a strong option where the scope is broader than Kubernetes alone.

---

## Sources

- Kubernetes Dashboard archive note: https://github.com/kubernetes/dashboard
- Headlamp installation: https://headlamp.dev/docs/latest/installation/
- Headlamp desktop install: https://headlamp.dev/docs/latest/installation/desktop
- FreeLens repository: https://github.com/freelensapp/freelens
- Portainer platform overview: https://www.portainer.io/
- Portainer Kubernetes dashboard docs: https://docs.portainer.io/user/kubernetes/dashboard
- K9s homepage: https://k9scli.io/
