# Kubernetes Interactive HTML Diagrams

This directory contains 26 interactive HTML diagrams for learning Kubernetes concepts.

## ✅ Browser Compatibility

All HTML files are:
- **Self-contained** - No external CDN dependencies
- **Pure HTML/CSS/JavaScript** - Standard browser APIs only
- **Cross-browser compatible** - Works on Chrome, Firefox, Safari, Edge
- **No CORS issues** - No external API calls or resources
- **Mobile responsive** - Works on tablets and phones

## 🚀 GitHub Pages / Jekyll Compatibility

### Configuration Applied:
The repository's `_config.yml` has been configured to properly serve these HTML files:

```yaml
include:
  - k8s/docs/html

keep_files:
  - k8s/docs/html
```

### Accessing on GitHub Pages:
Once deployed, files will be accessible at:
```
https://devopscert202.github.io/k8sforbeginners/k8s/docs/html/[filename].html
```

Example:
```
https://devopscert202.github.io/k8sforbeginners/k8s/docs/html/k8s-architecture-interactive.html
```

### `.nojekyll` File:
A `.nojekyll` file has been created in this directory to ensure Jekyll doesn't process these HTML files.

## 📁 Files Overview (26 Total)

### TIER 1: Foundations (8 diagrams)
1. `k8s-architecture-interactive.html` - Control Plane + Worker Nodes
2. `service-types-comparison.html` - ClusterIP, NodePort, LoadBalancer, ExternalName
3. `pod-lifecycle.html` - Pod phases and states
4. `deployment-hierarchy.html` - Deployment → ReplicaSet → Pod
5. `rolling-update.html` - Rolling update strategy
6. `deployment-rollback.html` - Rollback flow
7. `pod-communication.html` - Pod-to-Pod and Service networking
8. `dns-resolution.html` - DNS query flow

### TIER 2: Operations (10 diagrams)
9. `pv-pvc-binding.html` - PV/PVC binding lifecycle
10. `volume-types.html` - Volume types comparison
11. `rbac-flow.html` - RBAC authorization
12. `security-context.html` - Security context hierarchy
13. `network-policy.html` - NetworkPolicy traffic filtering
14. `node-selection.html` - Node selection process
15. `taints-tolerations.html` - Taints and tolerations
16. `affinity-antiaffinity.html` - Affinity and anti-affinity
17. `replicaset-scaling.html` - ReplicaSet scaling
18. `statefulset-vs-deployment.html` - StatefulSet vs Deployment

### TIER 3: Production (7 diagrams)
19. `cordon-drain.html` - Node maintenance workflow
20. `service-lb-rollout.html` - Service load balancing during rollout
21. `daemonset-pattern.html` - DaemonSet distribution
22. `upgrade-sequence.html` - Cluster upgrade sequence
23. `version-skew.html` - Version skew policy
24. `component-upgrade-order.html` - Component upgrade order
25. `etcd-backup-restore.html` - etcd backup and restore

### Reference (1 diagram)
26. `k8s-objects-reference.html` - Complete K8s objects reference (41 objects)

## 🔧 Technical Details

### No External Dependencies
- All CSS is embedded in `<style>` tags
- All JavaScript is embedded in `<script>` tags
- No external fonts, icons, or libraries
- No CDN links (no jQuery, Bootstrap, etc.)

### Browser APIs Used (All Standard)
- `document.getElementById()` - DOM access
- `document.querySelectorAll()` - DOM queries
- `element.classList` - CSS class manipulation
- `element.style` - Inline style manipulation
- `addEventListener()` - Event handling

### YAML Code Formatting
All YAML examples use:
```html
<pre style="white-space: pre;">
  [YAML content here]
</pre>
```
This preserves proper indentation and line breaks.

## 📝 Usage Notes

### Local Development
Open any HTML file directly in a browser:
```bash
# Windows
start k8s-architecture-interactive.html

# macOS
open k8s-architecture-interactive.html

# Linux
xdg-open k8s-architecture-interactive.html
```

### Linking from Markdown
To link from markdown files in the repository:
```markdown
[Interactive K8s Architecture](html/k8s-architecture-interactive.html)
```

### Embedding in Documentation
These files can be:
- Linked from README.md or index.md
- Embedded in iframe (if needed)
- Served as standalone pages
- Downloaded and used offline

## ✅ Tested Environments

- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+
- ✅ Mobile browsers (iOS Safari, Chrome Mobile)
- ✅ GitHub Pages with Jekyll
- ✅ Local file system (file:// protocol)

## 🐛 Known Issues

**None!** All files are:
- Self-contained
- No external dependencies
- No CORS issues
- No browser-specific code
- No Jekyll conflicts

## 📞 Support

For issues or questions about these diagrams, please open an issue in the GitHub repository.

---

**Last Updated:** March 2026
**Total Files:** 26 HTML diagrams
**Total Size:** ~700KB
