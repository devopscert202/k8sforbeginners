## Kubernetes Policies

Kubernetes does not rely on a single "policy engine." Instead, it combines API objects, admission-time checks, and cluster add-ons so teams can enforce networking rules, access control, workload hardening, and fair resource use. Different mechanisms apply at different scopes—namespace, cluster, or webhook—and often work best together. This page is a **catalog**: short descriptions plus links to the dedicated guides and labs for each area.

---

## Policy types (catalog)

### Network policy

**NetworkPolicy** restricts Pod-to-Pod and Pod-to-external traffic using labels and ports (ingress/egress). It only takes effect if your CNI implements it; default-allow clusters stay open until you define policies.

→ [Network policies](./networkpolicy.md)

### RBAC

**Role-Based Access Control** binds users, groups, or service accounts to Roles and ClusterRoles so the API server allows only the verbs and resources you intend. It is the foundation for who can create workloads and secrets—not a substitute for network or Pod hardening.

→ [RBAC concepts](./rbac-concepts.md)

### Security context

**Security context** fields on Pods and containers control user/group IDs, capabilities, read-only root filesystem, privilege escalation, and similar runtime settings. Tightening these settings reduces the impact of a compromised container.

→ [Security context](./securitycontext.md)

### Pod Security Standards (admission)

**Pod Security Admission** enforces the *privileged*, *baseline*, and *restricted* [Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/) per namespace via labels—replacing deprecated PodSecurityPolicy for most clusters.

→ Hands-on: [Lab 16: Pod security standards](../../labmanuals/lab16-sec-pod-security-standards.md)

### OPA Gatekeeper

**Gatekeeper** (OPA on Kubernetes) registers validating admission webhooks so you can express organization-specific rules (labels, naming, disallowed fields) as constraints, beyond built-in admission plugins.

→ [Gatekeeper scenarios](./gatekeeper-scenarios.md)

### Resource quotas

**ResourceQuota** caps aggregate CPU, memory, storage, and object counts per namespace so teams cannot exhaust shared capacity. Requests are checked at admission time against the namespace totals.

→ [Resource quotas](../workloads/resourcequota.md)

### Limit ranges

**LimitRange** sets default, min, and max requests/limits for containers and Pods in a namespace, helping enforce consistent sizing and preventing tiny or huge allocations.

→ [Scheduling practical guide (LimitRange)](../scheduling/scheduling-practical-guide.md)

### Related built-ins (no separate guide here)

**PodDisruptionBudget** limits voluntary disruptions (drains, evictions) so enough replicas stay up during upgrades. **Built-in admission controllers** (mutating/validating) run before objects are persisted; Pod Security Admission and webhooks like Gatekeeper are common ways to extend that pipeline.

---

## At-a-glance comparison

| Mechanism | Primary focus | Typical scope |
|-----------|----------------|---------------|
| Network policy | East-west / ingress traffic | Namespace |
| RBAC | API who can do what | Cluster / namespace |
| Security context | Container process & filesystem hardening | Pod / container |
| Pod Security Standards | Disallow unsafe Pod specs | Namespace (labels) |
| OPA Gatekeeper | Custom validation rules | Cluster (webhook) |
| Resource quota | Namespace resource budgets | Namespace |
| Limit range | Defaults & min/max per Pod/container | Namespace |
| Pod disruption budget | Min available during voluntary disruption | Namespace |

---

## Hands-on labs

| Lab | Topic |
|-----|--------|
| [Lab 11: RBAC and security](../../labmanuals/lab11-sec-rbac-security.md) | Roles, bindings, and API access patterns. |
| [Lab 12: Security context](../../labmanuals/lab12-sec-security-context.md) | Pod and container security settings. |
| [Lab 13: Network policies](../../labmanuals/lab13-sec-network-policies.md) | Ingress/egress and label-based traffic control. |
| [Lab 14: OPA Gatekeeper](../../labmanuals/lab14-sec-opa-gatekeeper.md) | Admission-time constraints with Gatekeeper. |
| [Lab 16: Pod security standards](../../labmanuals/lab16-sec-pod-security-standards.md) | Namespace labels and Pod Security Admission (PSA). |
| [Lab 37: Resource quotas and limits](../../labmanuals/lab37-resmgmt-resource-quotas-limits.md) | Quotas, limits, and admission behavior when caps are hit. |
