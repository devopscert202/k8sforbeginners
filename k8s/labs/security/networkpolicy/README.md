# Network Policy Lab YAML Files

Pre-built manifests for **Lab 57** (Network Policies -- Pod and Application Traffic Control).

Apply these files instead of typing inline YAML during training sessions.

## Files

| File | Exercise | Purpose |
|------|----------|---------|
| `lab57-ex1-apps.yaml` | Ex 1 | Three workloads (frontend, backend, database) in netpol-lab |
| `lab57-ex1-deny-ingress.yaml` | Ex 1 | Default deny all ingress |
| `lab57-ex1-deny-egress.yaml` | Ex 1 | Default deny all egress |
| `lab57-ex2-allow-dns.yaml` | Ex 2 | Allow DNS egress to kube-system CoreDNS |
| `lab57-ex3-paths.yaml` | Ex 3 | Pod-to-pod path policies (fe->be, be->db) |
| `lab57-ex4-backend-monitor.yaml` | Ex 4 | Dual-port backend + monitoring deployment |
| `lab57-ex4-policies.yaml` | Ex 4 | Port-level access control policies |
| `lab57-ex5-workloads.yaml` | Ex 5 | Cross-namespace workloads (team-a, team-b) |
| `lab57-ex5-deny-all.yaml` | Ex 5 | Default deny + DNS for both team namespaces |
| `lab57-ex5-and-policies.yaml` | Ex 5 | AND pattern cross-namespace policies |
| `lab57-ex6-ipblock.yaml` | Ex 6 | ipBlock/CIDR egress and ingress policies |
| `lab57-ex7-3tier.yaml` | Ex 7 | 3-tier application (fe/be/db) manifests |
| `lab57-ex7-policies.yaml` | Ex 7 | Full 3-tier network isolation policies |

## Lab 13 Policies (in parent security/ directory)

| File | Purpose |
|------|---------|
| `deny-from-other-namespaces.yaml` | Block cross-namespace ingress (Exercise 3) |
| `allow-from-test-namespace.yaml` | Allow test namespace to reach prod (Exercise 5) |
| `deny-all-ingress-dev.yaml` | Default deny ingress for dev namespace (Exercise 6) |
| `allow-specific-ingress-dev.yaml` | Allow labeled pods to dev service (Exercise 6) |
| `deny-all-egress-prod.yaml` | Egress control with DNS allowance (Exercise 7) |
