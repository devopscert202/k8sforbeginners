from pathlib import Path
from string import Template

BASE = Path(r"c:\Users\pkart\OneDrive\Documents\gitrepos\k8sforbeginners\k8s\docs\html")

PAGE_TEMPLATE = Template(
    """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>$title - Interactive Guide</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background: #f5f6fa;
            color: #1a1a2e;
            padding: 20px;
            line-height: 1.6;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        header {
            text-align: center;
            margin-bottom: 30px;
        }
        h1 {
            font-size: 2rem;
            font-weight: 700;
            color: #326CE5;
            margin-bottom: 8px;
        }
        .subtitle {
            font-size: 1rem;
            color: #64748b;
            font-weight: 400;
            max-width: 950px;
            margin: 0 auto;
        }
        .controls {
            display: flex;
            justify-content: center;
            gap: 12px;
            margin-bottom: 30px;
            flex-wrap: wrap;
        }
        .btn {
            padding: 10px 20px;
            border: 2px solid #326CE5;
            background: white;
            color: #326CE5;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            font-size: 0.9rem;
            transition: all 0.3s ease;
        }
        .btn:hover {
            background: #326CE5;
            color: white;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(50, 108, 229, 0.3);
        }
        .btn.active {
            background: #326CE5;
            color: white;
        }
        .diagram-container {
            background: white;
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            margin-bottom: 30px;
        }
        .view-section {
            display: none;
        }
        .view-section.active {
            display: block;
        }
        .section-title {
            text-align: center;
            font-size: 1.45rem;
            font-weight: 700;
            color: #1e293b;
            margin-bottom: 24px;
        }
        .lead-box {
            background: #f8fafc;
            border-left: 4px solid #326CE5;
            padding: 18px;
            border-radius: 10px;
            color: #475569;
            margin-bottom: 24px;
        }
        .concept-grid, .card-grid, .practice-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            gap: 18px;
        }
        .info-card, .practice-card {
            background: white;
            border: 2px solid #e2e8f0;
            border-radius: 10px;
            padding: 20px;
            transition: all 0.3s ease;
        }
        .info-card:hover, .practice-card:hover {
            border-color: #326CE5;
            box-shadow: 0 4px 12px rgba(50, 108, 229, 0.2);
            transform: translateY(-2px);
        }
        .info-card h3, .practice-card h3 {
            font-size: 1rem;
            color: #1e293b;
            margin-bottom: 8px;
        }
        .info-card p, .practice-card p {
            font-size: 0.9rem;
            color: #64748b;
        }
        .flow-step {
            display: flex;
            align-items: flex-start;
            background: #f8fafc;
            border-radius: 10px;
            padding: 16px;
            margin-bottom: 14px;
        }
        .step-number {
            background: #326CE5;
            color: white;
            width: 34px;
            height: 34px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            margin-right: 16px;
            flex-shrink: 0;
        }
        .step-title {
            font-weight: 700;
            color: #1e293b;
            margin-bottom: 4px;
        }
        .step-detail {
            font-size: 0.9rem;
            color: #64748b;
        }
        .yaml-section {
            margin-bottom: 24px;
        }
        .yaml-title {
            font-size: 1rem;
            font-weight: 700;
            color: #1e293b;
            margin-bottom: 10px;
        }
        .yaml-code {
            background: #1e293b;
            color: #e2e8f0;
            padding: 20px;
            border-radius: 8px;
            overflow-x: auto;
            font-family: 'Courier New', monospace;
            font-size: 0.85rem;
            line-height: 1.6;
            white-space: pre-wrap;
        }
        .compare-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }
        .compare-table th {
            background: #326CE5;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }
        .compare-table td {
            padding: 12px;
            border-bottom: 1px solid #e2e8f0;
            color: #475569;
        }
        .compare-table tr:hover {
            background: #f8fafc;
        }
        .highlight-box {
            background: #eff6ff;
            border-radius: 10px;
            padding: 18px;
            color: #1d4ed8;
            margin-top: 18px;
        }
        .highlight-box strong {
            color: #1e40af;
        }
        @media (max-width: 768px) {
            .diagram-container {
                padding: 20px;
            }
            h1 {
                font-size: 1.6rem;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>$title</h1>
            <p class="subtitle">$subtitle</p>
        </header>

        <div class="controls">
            <button class="btn active" onclick="showView('concept', this)">Concept</button>
            <button class="btn" onclick="showView('flow', this)">Flow</button>
            <button class="btn" onclick="showView('examples', this)">Examples</button>
            <button class="btn" onclick="showView('comparison', this)">Comparison</button>
            <button class="btn" onclick="showView('practice', this)">Practice</button>
        </div>

        <div id="concept-view" class="diagram-container view-section active">
            <h2 class="section-title">Core Concept</h2>
            <div class="lead-box">$lead</div>
            <div class="concept-grid">
$concept_cards
            </div>
        </div>

        <div id="flow-view" class="diagram-container view-section">
            <h2 class="section-title">$flow_title</h2>
$flow_steps
            <div class="highlight-box"><strong>Key Point:</strong> $flow_note</div>
        </div>

        <div id="examples-view" class="diagram-container view-section">
            <h2 class="section-title">Examples and Commands</h2>
$example_sections
        </div>

        <div id="comparison-view" class="diagram-container view-section">
            <h2 class="section-title">$comparison_title</h2>
            <table class="compare-table">
$comparison_table
            </table>
            <div class="highlight-box"><strong>Design Hint:</strong> $comparison_note</div>
        </div>

        <div id="practice-view" class="diagram-container view-section">
            <h2 class="section-title">How to Use It in Practice</h2>
            <div class="practice-grid">
$practice_cards
            </div>
        </div>
    </div>

    <script>
        function showView(view, button) {
            document.querySelectorAll('.view-section').forEach(section => section.classList.remove('active'));
            document.querySelectorAll('.btn').forEach(btn => btn.classList.remove('active'));
            document.getElementById(view + '-view').classList.add('active');
            button.classList.add('active');
        }
    </script>
</body>
</html>
"""
)


def card_html(items):
    return "\n".join(
        f'                <div class="info-card"><h3>{item["title"]}</h3><p>{item["text"]}</p></div>'
        for item in items
    )


def flow_html(items):
    out = []
    for i, item in enumerate(items, start=1):
        out.append(
            "            <div class=\"flow-step\">"
            f"<div class=\"step-number\">{i}</div>"
            "<div class=\"step-content\">"
            f"<div class=\"step-title\">{item['title']}</div>"
            f"<div class=\"step-detail\">{item['text']}</div>"
            "</div></div>"
        )
    return "\n".join(out)


def example_html(items):
    return "\n".join(
        f'            <div class="yaml-section"><div class="yaml-title">{item["title"]}</div><div class="yaml-code">{item["code"]}</div></div>'
        for item in items
    )


def comparison_html(rows):
    html = [
        "                <tr>" + "".join(f"<th>{cell}</th>" for cell in rows[0]) + "</tr>"
    ]
    for row in rows[1:]:
        html.append("                <tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>")
    return "\n".join(html)


def practice_html(items):
    return "\n".join(
        f'                <div class="practice-card"><h3>{item["title"]}</h3><p>{item["text"]}</p></div>'
        for item in items
    )


PAGES = []
PAGES.extend([
    {
        "file": "configmaps-patterns.html",
        "title": "ConfigMaps in Kubernetes",
        "subtitle": "Interactive guide to storing non-sensitive configuration outside images and consuming it through environment variables or mounted files.",
        "lead": "ConfigMaps separate runtime configuration from application images. The key design question is not whether to use ConfigMaps, but how the container should consume the data.",
        "concept": [
            {"title": "Decouple configuration", "text": "The same image can run in dev, test, and prod with different configuration values."},
            {"title": "Not for secrets", "text": "ConfigMaps are for non-confidential data. Sensitive values should use Secrets."},
            {"title": "Three consumption paths", "text": "Use all keys as env vars, selected keys as env vars, or project data as files in a volume."},
        ],
        "flow_title": "Configuration Delivery Flow",
        "flow": [
            {"title": "Create ConfigMap", "text": "Store key-value data in a ConfigMap resource instead of baking it into the image."},
            {"title": "Reference it in a Pod", "text": "The Pod spec consumes the ConfigMap through envFrom, valueFrom, or a mounted volume."},
            {"title": "Kubernetes injects data", "text": "At runtime, the data becomes environment variables or files inside the container."},
            {"title": "Application starts with the right settings", "text": "The same container image behaves differently based on externalized config."},
        ],
        "flow_note": "The biggest practical choice is whether the application expects configuration as environment variables or as files.",
        "examples": [
            {"title": "ConfigMap YAML", "code": "apiVersion: v1\nkind: ConfigMap\nmetadata:\n  name: example-configmap\ndata:\n  database: mongodb\n  database_uri: mongodb://localhost:27017"},
            {"title": "Consume All Keys as Environment Variables", "code": "envFrom:\n- configMapRef:\n    name: example-configmap"},
            {"title": "Mount ConfigMap as Files", "code": "volumes:\n- name: config-volume\n  configMap:\n    name: example-configmap\nvolumeMounts:\n- name: config-volume\n  mountPath: /config"},
        ],
        "comparison_title": "ConfigMap Consumption Patterns",
        "comparison": [
            ["Pattern", "How it works", "Best fit"],
            ["envFrom", "Loads every key as an environment variable", "Simple apps that want all config at once"],
            ["valueFrom", "Maps one specific key to one variable", "Explicit control over naming and scope"],
            ["Volume mount", "Creates files from ConfigMap keys", "Apps that expect config files"],
        ],
        "comparison_note": "Most teams standardize on one or two consumption patterns per application type to keep operations predictable.",
        "practice": [
            {"title": "Application settings", "text": "Move database URLs, feature flags, and environment names out of the image."},
            {"title": "Config file projection", "text": "Mount web server configs, properties files, or startup scripts from ConfigMaps."},
            {"title": "Reusable config", "text": "Share a common non-secret configuration source across multiple Pods."},
        ],
    },
    {
        "file": "jobs-batch-processing.html",
        "title": "Jobs and Batch Processing",
        "subtitle": "Interactive guide to run-to-completion workloads, retries, completions, and parallel batch execution in Kubernetes.",
        "lead": "A Job is about successful completion, not continuous availability. That changes how Kubernetes measures success, handles retries, and cleans up Pods.",
        "concept": [
            {"title": "Run to completion", "text": "Jobs are the right workload for migrations, reports, calculations, and one-time administrative tasks."},
            {"title": "Retry-aware", "text": "A failed Pod can be retried until backoffLimit is reached."},
            {"title": "Parallel capable", "text": "Jobs can run one Pod or many Pods in parallel depending on the task."},
        ],
        "flow_title": "Job Controller Lifecycle",
        "flow": [
            {"title": "Create Job", "text": "The Job declares a Pod template plus success and retry settings."},
            {"title": "Launch Pods", "text": "The Job controller creates Pods to execute the batch task."},
            {"title": "Track success", "text": "Completed Pods count toward the desired number of successful completions."},
            {"title": "Retry failures", "text": "Failed runs may be retried depending on restartPolicy and backoffLimit."},
            {"title": "Finish and retain state", "text": "The Job reaches a completed or failed state once its criteria are met."},
        ],
        "flow_note": "Jobs are controller-driven just like Deployments, but the success metric is completions rather than continuously running replicas.",
        "examples": [
            {"title": "Basic Job", "code": "apiVersion: batch/v1\nkind: Job\nmetadata:\n  name: pi\nspec:\n  template:\n    spec:\n      containers:\n      - name: pi\n        image: perl\n        command: [\"perl\", \"-Mbignum=bpi\", \"-wle\", \"print bpi(2000)\"]\n      restartPolicy: Never\n  backoffLimit: 4"},
            {"title": "Useful Commands", "code": "kubectl get jobs\nkubectl describe job pi\nkubectl get pods -l job-name=pi\nkubectl logs -l job-name=pi"},
        ],
        "comparison_title": "Job vs Deployment",
        "comparison": [
            ["Feature", "Job", "Deployment"],
            ["Purpose", "Run to completion", "Keep application running"],
            ["Lifecycle", "Ends when work finishes", "Runs indefinitely"],
            ["Success criteria", "Completion count reached", "Desired replicas remain available"],
            ["Restart policy", "Never or OnFailure", "Controller keeps Pods replaced continuously"],
        ],
        "comparison_note": "If the workload should stop when the work is done, it should usually be a Job rather than a Deployment.",
        "practice": [
            {"title": "Database migrations", "text": "Run schema changes before or during rollout in a controlled way."},
            {"title": "Batch reports", "text": "Generate output files, analytics, or long-running calculations without long-lived Pods."},
            {"title": "Administrative automation", "text": "Backups, repair tasks, and one-time system operations fit naturally into Jobs."},
        ],
    },
    {
        "file": "cronjobs-scheduling.html",
        "title": "CronJobs in Kubernetes",
        "subtitle": "Interactive guide to recurring Jobs, cron schedules, history retention, and recurring workload behavior.",
        "lead": "CronJobs do not replace Jobs; they create Jobs on a schedule. The scheduling layer and the execution layer are separate and that distinction matters.",
        "concept": [
            {"title": "Recurring work", "text": "CronJobs are the right fit for backups, reports, cleanup, and periodic synchronization tasks."},
            {"title": "History retention", "text": "You can control how many successful and failed Jobs are retained for inspection."},
            {"title": "Idempotent design", "text": "Scheduled tasks should tolerate repeat runs because retries and overlaps can happen."},
        ],
        "flow_title": "CronJob Scheduling Flow",
        "flow": [
            {"title": "Define schedule", "text": "A cron expression specifies when Kubernetes should create a new Job."},
            {"title": "Controller checks time", "text": "The CronJob controller evaluates due schedules."},
            {"title": "Create Job", "text": "A new Job is generated from the jobTemplate when the time matches."},
            {"title": "Run Pods", "text": "The Job launches Pods and tracks completion as usual."},
            {"title": "Retain or clean history", "text": "Older Jobs are kept or removed according to retention limits."},
        ],
        "flow_note": "The CronJob owns time-based creation. The generated Job owns actual execution and completion tracking.",
        "examples": [
            {"title": "Basic CronJob", "code": "apiVersion: batch/v1\nkind: CronJob\nmetadata:\n  name: hello-cronjob\nspec:\n  schedule: \"*/5 * * * *\"\n  successfulJobsHistoryLimit: 3\n  failedJobsHistoryLimit: 1"},
            {"title": "Useful Commands", "code": "kubectl get cronjob\nkubectl describe cronjob hello-cronjob\nkubectl get jobs"},
        ],
        "comparison_title": "CronJob vs Job",
        "comparison": [
            ["Feature", "CronJob", "Job"],
            ["Trigger", "Time-based schedule", "Manual creation or external trigger"],
            ["Creates", "Jobs", "Pods"],
            ["Use case", "Recurring tasks", "One-off batch work"],
            ["State to monitor", "Schedule plus history", "Completion and failure state"],
        ],
        "comparison_note": "When debugging CronJobs, inspect both the CronJob itself and the Jobs it creates.",
        "practice": [
            {"title": "Backups", "text": "Run scheduled database or file backups at fixed times."},
            {"title": "Cleanup", "text": "Delete stale files, temporary data, or expired records periodically."},
            {"title": "Reporting", "text": "Trigger summary reports or email digests at regular intervals."},
        ],
    },
    {
        "file": "hpa-autoscaling.html",
        "title": "Horizontal Pod Autoscaling",
        "subtitle": "Interactive guide to metrics-driven scaling, target utilization, and how HPA changes replica counts automatically.",
        "lead": "Horizontal Pod Autoscaling is a control loop that reacts to observed metrics. It depends on a metrics pipeline and on realistic workload resource settings.",
        "concept": [
            {"title": "Automatic scaling", "text": "HPA adjusts replica counts in response to changing resource usage or other supported metrics."},
            {"title": "Metrics-dependent", "text": "Built-in autoscaling typically depends on Metrics Server for CPU and memory metrics."},
            {"title": "Request-aware", "text": "CPU utilization targets are meaningful only when resource requests are set sensibly."},
        ],
        "flow_title": "Autoscaling Control Loop",
        "flow": [
            {"title": "Collect metrics", "text": "Pod CPU or memory usage is gathered from the cluster metrics pipeline."},
            {"title": "Compare to target", "text": "Observed values are compared to the HPA target threshold."},
            {"title": "Calculate desired replicas", "text": "The controller determines whether more or fewer Pods are needed."},
            {"title": "Update workload", "text": "Replica count is changed on the target Deployment, ReplicaSet, or StatefulSet."},
            {"title": "Stabilize behavior", "text": "Scaling policies and timing prevent rapid oscillation in many setups."},
        ],
        "flow_note": "HPA is not a one-time action. It continuously re-evaluates the workload against the current metrics picture.",
        "examples": [
            {"title": "Basic HPA", "code": "apiVersion: autoscaling/v2\nkind: HorizontalPodAutoscaler\nmetadata:\n  name: php-apache\nspec:\n  minReplicas: 1\n  maxReplicas: 10\n  scaleTargetRef:\n    apiVersion: apps/v1\n    kind: Deployment\n    name: php-apache"},
            {"title": "Observe Scaling", "code": "kubectl get hpa\nkubectl top pods\nkubectl describe hpa php-apache"},
        ],
        "comparison_title": "Horizontal vs Vertical Scaling",
        "comparison": [
            ["Feature", "Horizontal Scaling", "Vertical Scaling"],
            ["Method", "Add or remove Pods", "Change CPU or memory size"],
            ["Downtime profile", "Usually none", "May require restart depending on approach"],
            ["Best fit", "Stateless workloads", "Right-sizing resource envelopes"],
            ["Typical tool", "HPA", "VPA"],
        ],
        "comparison_note": "Horizontal scaling changes the number of workload copies; vertical scaling changes the size of each copy.",
        "practice": [
            {"title": "Traffic spikes", "text": "Scale web or API workloads up during demand peaks and down later."},
            {"title": "Resource efficiency", "text": "Avoid keeping excess replicas running during low traffic periods."},
            {"title": "Autoscaling labs", "text": "Use generated load to observe how replica counts respond over time."},
        ],
    },
])
PAGES.extend([
    {
        "file": "workloads-pod-concepts.html",
        "title": "Workloads and Pod Concepts",
        "subtitle": "Interactive overview of the main workload controllers and the Pod-centric concepts they build upon.",
        "lead": "Pods are the runtime unit, and controllers exist to manage Pods for specific workload patterns. This page gives the big-picture map that ties those concepts together.",
        "concept": [
            {"title": "Pod is the runtime unit", "text": "Nearly every workload eventually becomes Pods scheduled and run on nodes."},
            {"title": "Controllers add behavior", "text": "Deployments, Jobs, StatefulSets, and DaemonSets each manage Pods differently."},
            {"title": "Supporting concepts shape behavior", "text": "Services, init containers, probes, and resource settings all influence Pod behavior."},
        ],
        "flow_title": "Workload Mental Model",
        "flow": [
            {"title": "Choose workload type", "text": "Pick the controller that matches the application’s lifecycle needs."},
            {"title": "Controller creates Pods", "text": "The workload abstraction turns desired state into running Pods."},
            {"title": "Expose and observe", "text": "Services, probes, and metrics make Pods reachable and manageable."},
            {"title": "Operate through controllers", "text": "Scaling, updates, and policy are applied through the controller layer."},
        ],
        "flow_note": "A strong mental model starts with Pods, but daily operations usually happen through controllers and supporting abstractions.",
        "examples": [
            {"title": "Core Workload Types", "code": "Pod\nDeployment\nStatefulSet\nDaemonSet\nJob\nCronJob"},
            {"title": "Supporting Concepts", "code": "Services\nInit Containers\nProbes\nRequests and Limits"},
        ],
        "comparison_title": "Workload Categories",
        "comparison": [
            ["Workload", "Primary goal", "Best fit"],
            ["Deployment", "Replicated stateless workloads", "Web apps and APIs"],
            ["StatefulSet", "Stable identity and ordered behavior", "Databases and clustered stateful apps"],
            ["DaemonSet", "One Pod per eligible node", "Node agents and platform services"],
            ["Job / CronJob", "Completion-based work", "Batch and scheduled processing"],
        ],
        "comparison_note": "Once you know the workload goal, picking the right controller becomes much easier.",
        "practice": [
            {"title": "Team onboarding", "text": "Use this as a concept map before diving into specific workload explainers."},
            {"title": "Exam revision", "text": "Connect object purpose to expected behavior and management model."},
            {"title": "Architecture reviews", "text": "Ask whether the chosen controller matches the real workload lifecycle."},
        ],
    },
    {
        "file": "multi-port-services.html",
        "title": "Multi-Port Services",
        "subtitle": "Interactive guide to named ports, service port mapping, and exposing multi-port applications clearly.",
        "lead": "Many applications expose more than one interface: app traffic, admin endpoints, metrics, or health ports. Multi-port Services organize those interfaces cleanly.",
        "concept": [
            {"title": "Multiple app interfaces", "text": "Applications often need more than one exposed port for different responsibilities."},
            {"title": "Named ports required", "text": "When a Service exposes multiple ports, each one needs a unique name."},
            {"title": "Clear service mapping", "text": "Port naming makes Service-to-Pod relationships easier to reason about and debug."},
        ],
        "flow_title": "Multi-Port Mapping Flow",
        "flow": [
            {"title": "Pod defines ports", "text": "Container ports are declared, often with names like http or metrics."},
            {"title": "Service selects backend Pods", "text": "Labels and selectors identify the application Pods."},
            {"title": "Service maps each port", "text": "Each service port is mapped to the correct targetPort."},
            {"title": "Clients reach the right interface", "text": "Traffic on each named port reaches the intended backend function."},
        ],
        "flow_note": "Port names are not cosmetic in multi-port Services; they are part of making the model understandable and valid.",
        "examples": [
            {"title": "Multi-Port Service Example", "code": "ports:\n- name: http\n  port: 8080\n  targetPort: 8080\n- name: custom\n  port: 9090\n  targetPort: 9090"},
            {"title": "Useful Commands", "code": "kubectl get svc multi-port-service\nkubectl describe svc multi-port-service"},
        ],
        "comparison_title": "Single-Port vs Multi-Port Service",
        "comparison": [
            ["Aspect", "Single-port Service", "Multi-port Service"],
            ["Port entries", "One", "Many"],
            ["Need for naming", "Optional in simple cases", "Required and important for clarity"],
            ["Typical app fit", "Simple web or API service", "Apps with metrics, admin, HTTPS, or multiple interfaces"],
        ],
        "comparison_note": "If your application exposes multiple interfaces, make those interfaces explicit in the Service instead of hiding them in assumptions.",
        "practice": [
            {"title": "App plus metrics", "text": "Expose user traffic and Prometheus metrics on distinct ports."},
            {"title": "Protocol separation", "text": "Use separate ports for web, HTTPS, or admin APIs."},
            {"title": "Troubleshooting clarity", "text": "Named ports make service descriptions and debugging output much easier to understand."},
        ],
    },
    {
        "file": "pod-security-standards.html",
        "title": "Pod Security Standards",
        "subtitle": "Interactive guide to Privileged, Baseline, Restricted profiles and enforce, audit, warn modes in Pod Security Admission.",
        "lead": "Pod Security Admission replaced PodSecurityPolicy with a simpler namespace-label model. The real learning goal is understanding profile levels and enforcement modes together.",
        "concept": [
            {"title": "Three profiles", "text": "Privileged, Baseline, and Restricted define increasing levels of hardening."},
            {"title": "Namespace-level labels", "text": "Pod Security Admission uses namespace labels to set desired policy behavior."},
            {"title": "Three modes", "text": "enforce rejects, audit records, and warn notifies without blocking."},
        ],
        "flow_title": "Namespace Policy Enforcement Flow",
        "flow": [
            {"title": "Label namespace", "text": "Set enforce, audit, and warn levels through namespace labels."},
            {"title": "Submit Pod or workload", "text": "A user creates a Pod or a controller creates one on the namespace’s behalf."},
            {"title": "Admission checks profile", "text": "Kubernetes compares the workload against the selected security profile."},
            {"title": "Allow, warn, or reject", "text": "The request outcome depends on which mode is configured."},
        ],
        "flow_note": "The most useful migration path is often to start with warn or audit before moving to strict enforce mode.",
        "examples": [
            {"title": "Namespace Labels", "code": "pod-security.kubernetes.io/enforce=restricted\npod-security.kubernetes.io/audit=baseline\npod-security.kubernetes.io/warn=baseline"},
            {"title": "Useful Commands", "code": "kubectl label namespace pss-restricted pod-security.kubernetes.io/enforce=restricted\nkubectl get ns --show-labels"},
        ],
        "comparison_title": "Profile Comparison",
        "comparison": [
            ["Profile", "Security posture", "Typical use"],
            ["Privileged", "Minimal restriction", "Trusted system workloads"],
            ["Baseline", "Blocks common privilege escalation risks", "General application workloads"],
            ["Restricted", "Strong hardening expectations", "Security-sensitive namespaces"],
        ],
        "comparison_note": "Restricted is the most secure profile, but Baseline is often the practical stepping stone for many existing workloads.",
        "practice": [
            {"title": "Namespace hardening", "text": "Set different security levels for dev, shared, and critical namespaces."},
            {"title": "Migration planning", "text": "Use warn and audit to discover what would break before enforcing."},
            {"title": "Security review", "text": "Combine PSA with container security context design for better results."},
        ],
    },
    {
        "file": "kubectl-essentials.html",
        "title": "kubectl Essentials",
        "subtitle": "Interactive guide to the everyday create, inspect, expose, scale, debug, and cleanup workflow with kubectl.",
        "lead": "kubectl is not just a collection of commands. It supports a repeatable operational loop: create, inspect, expose, change, debug, and clean up.",
        "concept": [
            {"title": "Imperative creation", "text": "Fast for learning, testing, and one-off actions."},
            {"title": "Inspection is central", "text": "get, describe, logs, and events reveal what the cluster is really doing."},
            {"title": "Declarative bridge", "text": "dry-run and YAML output help users move from imperative commands to versioned manifests."},
        ],
        "flow_title": "Daily kubectl Workflow",
        "flow": [
            {"title": "Create", "text": "Use kubectl create or apply to introduce resources."},
            {"title": "Inspect", "text": "Check objects, status, events, and runtime state."},
            {"title": "Expose or modify", "text": "Create Services, edit resources, or scale workloads."},
            {"title": "Debug and clean up", "text": "Use logs, describe output, and delete commands to resolve issues and remove test objects."},
        ],
        "flow_note": "Most kubectl fluency comes from understanding which command category to reach for at each stage of that operator loop.",
        "examples": [
            {"title": "Core Commands", "code": "kubectl create deployment myapp1 --image=docker.io/openshift/hello-openshift\nkubectl get pods\nkubectl describe deployment myapp1\nkubectl scale deployment myapp1 --replicas=3"},
            {"title": "Generate YAML", "code": "kubectl create deployment myhttpd --image=docker.io/httpd --dry-run=client -o yaml > myapp1.yaml"},
        ],
        "comparison_title": "Imperative vs Declarative Use",
        "comparison": [
            ["Mode", "Strength", "Typical use"],
            ["Imperative", "Fast and direct", "Learning, quick tests, ad hoc changes"],
            ["Declarative", "Repeatable and versionable", "Team workflows, Git-based operations, long-term management"],
        ],
        "comparison_note": "Strong operators usually know both styles and switch between them intentionally.",
        "practice": [
            {"title": "Fast lab work", "text": "Use imperative commands to move quickly while learning."},
            {"title": "Better debugging", "text": "Use describe, logs, and events together to form a full picture."},
            {"title": "Manifest generation", "text": "Use dry-run YAML output as a starting point for cleaner manifests."},
        ],
    },
    {
        "file": "cluster-administration.html",
        "title": "Cluster Administration with kubeadm",
        "subtitle": "Interactive guide to join tokens, certificate management, cluster configuration, and routine cluster health operations.",
        "lead": "Cluster administration is about the lifecycle of trust, control plane health, and safe cluster maintenance, not just application resources.",
        "concept": [
            {"title": "Join tokens", "text": "Secure and time-limited credentials let worker nodes join the cluster."},
            {"title": "Certificate health", "text": "TLS certificate expiry and renewal are core operational responsibilities."},
            {"title": "Cluster configuration", "text": "kubeadm and kubeconfig state influence how admins access and manage the cluster."},
        ],
        "flow_title": "Administrative Control Flow",
        "flow": [
            {"title": "Manage trust", "text": "Create, inspect, distribute, or revoke join tokens as needed."},
            {"title": "Check certificates", "text": "Review certificate expiration and plan renewals before failures occur."},
            {"title": "Inspect config and access", "text": "Validate kubeconfig and kubeadm-derived cluster configuration."},
            {"title": "Maintain cluster health", "text": "Use node, API, and certificate insight to keep the cluster healthy."},
        ],
        "flow_note": "The thread connecting these tasks is trust and continuity: cluster admins keep the platform joinable, secure, and operational.",
        "examples": [
            {"title": "Token Commands", "code": "kubeadm token list\nkubeadm token create --ttl 2h --print-join-command"},
            {"title": "Certificate Commands", "code": "sudo kubeadm certs check-expiration"},
        ],
        "comparison_title": "Admin Task Categories",
        "comparison": [
            ["Category", "Goal", "Example tools"],
            ["Node join management", "Control cluster membership", "kubeadm token commands"],
            ["Certificate management", "Maintain secure component communication", "kubeadm certs"],
            ["Health and access", "Keep cluster usable and observable", "kubectl, kubeconfig, API checks"],
        ],
        "comparison_note": "Many cluster issues are really trust or certificate issues disguised as application or connectivity problems.",
        "practice": [
            {"title": "Worker onboarding", "text": "Generate and rotate join commands safely."},
            {"title": "Certificate planning", "text": "Prevent outages by monitoring expiration and renewal windows."},
            {"title": "Operational review", "text": "Use kubeadm and kubectl together to understand cluster control-plane state."},
        ],
    },
    {
        "file": "kubernetes-installation.html",
        "title": "Kubernetes Installation",
        "subtitle": "Interactive guide to the kubeadm installation path from system preparation to control plane bootstrap and worker joins.",
        "lead": "Cluster installation is a dependency chain: operating system preparation, container runtime setup, Kubernetes tooling, control plane initialization, networking, and finally worker onboarding.",
        "concept": [
            {"title": "System preparation", "text": "Swap, kernel modules, and sysctl settings must be aligned before Kubernetes can behave correctly."},
            {"title": "Runtime and tools", "text": "containerd, kubelet, kubeadm, and kubectl form the local execution and bootstrap toolchain."},
            {"title": "Bootstrap then join", "text": "The control plane is initialized first, networking is added, and only then should workers join."},
        ],
        "flow_title": "Cluster Installation Sequence",
        "flow": [
            {"title": "Prepare all nodes", "text": "Update packages, disable swap, load modules, and configure kernel parameters."},
            {"title": "Install container runtime", "text": "Set up and configure containerd for kubelet."},
            {"title": "Install kubeadm toolchain", "text": "Install kubeadm, kubelet, and kubectl."},
            {"title": "Initialize control plane", "text": "Run kubeadm init and configure kubectl access."},
            {"title": "Install CNI", "text": "Apply a network plugin such as Calico so Pods can communicate."},
            {"title": "Join workers and verify", "text": "Run kubeadm join on workers, then confirm node and Pod health."},
        ],
        "flow_note": "CNI installation is the transition point between a bootstrapped control plane and a functional cluster that can run networked workloads cleanly.",
        "examples": [
            {"title": "High-Level Installation Steps", "code": "1. Disable swap\n2. Install containerd\n3. Install kubeadm, kubelet, kubectl\n4. kubeadm init\n5. Apply CNI\n6. kubeadm join workers"},
            {"title": "Verification Commands", "code": "kubectl get nodes\nkubectl get pods -A"},
        ],
        "comparison_title": "Installation Stages and Purpose",
        "comparison": [
            ["Stage", "Purpose", "Why it matters"],
            ["System prep", "Align OS and kernel expectations", "Prevents kubelet and networking failures"],
            ["Runtime setup", "Provide container execution engine", "Pods need a supported runtime"],
            ["Control plane bootstrap", "Create the cluster brain", "Establish API server and control components"],
            ["CNI install", "Enable Pod networking", "Without it, nodes or Pods may stay NotReady"],
            ["Worker join", "Add cluster capacity", "Turns isolated machines into participating nodes"],
        ],
        "comparison_note": "Many installation errors happen because a prerequisite stage was skipped or only partially completed.",
        "practice": [
            {"title": "Bootstrap from scratch", "text": "Use the sequence to build a cluster cleanly and predictably."},
            {"title": "Troubleshooting installs", "text": "Map failures back to the phase they belong to: OS, runtime, bootstrap, CNI, or join."},
            {"title": "Admin training", "text": "Understand the dependency order before touching production-like clusters."},
        ],
    },
])

for page in PAGES:
    html = PAGE_TEMPLATE.substitute(
        title=page["title"],
        subtitle=page["subtitle"],
        lead=page["lead"],
        concept_cards=card_html(page["concept"]),
        flow_title=page["flow_title"],
        flow_steps=flow_html(page["flow"]),
        flow_note=page["flow_note"],
        example_sections=example_html(page["examples"]),
        comparison_title=page["comparison_title"],
        comparison_table=comparison_html(page["comparison"]),
        comparison_note=page["comparison_note"],
        practice_cards=practice_html(page["practice"]),
    )
    (BASE / page["file"]).write_text(html, encoding="utf-8")
PAGES.extend([
    {
        "file": "pods-vs-deployments.html",
        "title": "Pods vs Deployments",
        "subtitle": "Interactive guide for the beginner transition from manually created Pods to controller-managed Deployments and ReplicaSets.",
        "lead": "The core lesson is that Pods teach the runtime unit, but Deployments teach the controller model that Kubernetes uses for real application management.",
        "concept": [
            {"title": "Pod", "text": "The smallest runnable unit. Useful for learning, debugging, and simple direct execution."},
            {"title": "Deployment", "text": "A higher-level controller that manages ReplicaSets and Pods declaratively."},
            {"title": "Labels matter", "text": "Labels connect Pods to Services and controllers later in the workflow."},
        ],
        "flow_title": "Lab 01 Learning Progression",
        "flow": [
            {"title": "Create a Pod", "text": "Run apache1 directly from YAML and observe Pod state."},
            {"title": "Create another Pod", "text": "Notice that managing multiple Pods directly becomes manual and repetitive."},
            {"title": "Create a Deployment", "text": "Let Kubernetes manage replicated Pods through a controller."},
            {"title": "Scale declaratively", "text": "Change desired replicas instead of hand-creating or hand-deleting Pods."},
        ],
        "flow_note": "The real mindset shift is from manual Pod management to desired-state controller management.",
        "examples": [
            {"title": "Pod Example", "code": "apiVersion: v1\nkind: Pod\nmetadata:\n  name: apache1"},
            {"title": "Deployment Example", "code": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: myapp1"},
        ],
        "comparison_title": "Pod vs Deployment",
        "comparison": [
            ["Feature", "Pod", "Deployment"],
            ["Purpose", "Run one Pod directly", "Manage replicated Pods declaratively"],
            ["Scaling", "Manual", "Built-in replica management"],
            ["Self-healing", "No owning controller", "Controller recreates missing Pods"],
            ["Typical use", "Learning, debugging, special cases", "Normal stateless application management"],
        ],
        "comparison_note": "A Deployment is not a replacement runtime unit; it is a management layer on top of Pods.",
        "practice": [
            {"title": "Learn the basics", "text": "Start with Pods to understand container execution inside Kubernetes."},
            {"title": "Run stateless apps properly", "text": "Use Deployments for most normal web and API workloads."},
            {"title": "Understand controller ownership", "text": "This concept unlocks rollouts, rollback, scaling, and self-healing."},
        ],
    },
    {
        "file": "services-networking-deep-dive.html",
        "title": "Services Deep Dive",
        "subtitle": "Interactive guide to selectors, stable service identities, endpoint membership, and NodePort / LoadBalancer exposure.",
        "lead": "Services solve the problem of ephemeral Pod IPs by giving clients a stable network abstraction over a changing set of Pods.",
        "concept": [
            {"title": "Stable IP and DNS", "text": "Clients use a stable Service identity instead of talking directly to Pod IPs."},
            {"title": "Selector-based membership", "text": "Labels and selectors determine which Pods sit behind the Service."},
            {"title": "Port mapping", "text": "Service port, targetPort, and optional nodePort each have different roles."},
        ],
        "flow_title": "Service Routing Flow",
        "flow": [
            {"title": "Pods get labels", "text": "Backends are labeled so the Service can discover them."},
            {"title": "Service selector matches", "text": "The Service identifies which Pods belong to it."},
            {"title": "Endpoints are built", "text": "Kubernetes maintains the active backend endpoint list."},
            {"title": "Traffic enters Service", "text": "Clients use ClusterIP, NodePort, or LoadBalancer exposure."},
            {"title": "Requests reach Pods", "text": "Traffic is distributed across the matching backend Pods."},
        ],
        "flow_note": "Labels are the real control surface. If the selector does not match, the Service has no effective backends.",
        "examples": [
            {"title": "NodePort Service Example", "code": "kind: Service\nspec:\n  selector:\n    mycka: k8slearning\n  ports:\n  - port: 8081\n    targetPort: 80\n  type: NodePort"},
            {"title": "Useful Commands", "code": "kubectl get service myservice\nkubectl describe service myservice\nkubectl get endpoints"},
        ],
        "comparison_title": "Service Types",
        "comparison": [
            ["Type", "Main use", "Scope"],
            ["ClusterIP", "Internal service access", "Inside the cluster"],
            ["NodePort", "Expose through node ports", "Lab, dev, simple external access"],
            ["LoadBalancer", "Cloud-integrated external access", "Production-style external exposure"],
            ["ExternalName", "DNS alias to an external name", "Integration with external services"],
        ],
        "comparison_note": "The Service abstraction stays the same; the exposure model is what changes across Service types.",
        "practice": [
            {"title": "Internal app communication", "text": "Use ClusterIP Services and DNS names between in-cluster workloads."},
            {"title": "Lab access patterns", "text": "Use NodePort when learning or testing external access."},
            {"title": "Selector troubleshooting", "text": "When traffic fails, always confirm the Service selector and endpoint membership first."},
        ],
    },
    {
        "file": "deployment-strategies.html",
        "title": "Deployment Strategies",
        "subtitle": "Interactive guide to recreate, rolling update, blue-green, and canary release strategies.",
        "lead": "Release strategy is about balancing simplicity, user impact, rollback speed, and operational risk.",
        "concept": [
            {"title": "Recreate", "text": "Stop old Pods, then start new ones. Simple, but causes downtime."},
            {"title": "Rolling update", "text": "Gradually replace old Pods with new Pods while keeping the app available."},
            {"title": "Blue-green and canary", "text": "Traffic-control strategies that provide stronger safety for risky changes."},
        ],
        "flow_title": "Release Strategy Thinking",
        "flow": [
            {"title": "Assess workload needs", "text": "Decide how much downtime, risk, and duplicate capacity you can tolerate."},
            {"title": "Pick a strategy", "text": "Choose recreate, rolling, blue-green, or canary."},
            {"title": "Deploy the change", "text": "Update Pods or switch traffic using the selected approach."},
            {"title": "Observe and react", "text": "Validate health, metrics, and user impact before completing the rollout."},
        ],
        "flow_note": "There is no universally best strategy. The right choice depends on cost, risk, traffic patterns, and rollback needs.",
        "examples": [
            {"title": "RollingUpdate Strategy", "code": "strategy:\n  type: RollingUpdate"},
            {"title": "Blue-Green Idea", "code": "Blue environment + Green environment + traffic switch"},
        ],
        "comparison_title": "Strategy Comparison",
        "comparison": [
            ["Strategy", "Strength", "Tradeoff"],
            ["Recreate", "Very simple", "Downtime during switch"],
            ["RollingUpdate", "Good availability during rollout", "Rollback is controlled but not instant"],
            ["Blue-Green", "Fast cutover and rollback", "Requires duplicate environment capacity"],
            ["Canary", "Limits blast radius of risky changes", "Needs more routing and observability maturity"],
        ],
        "comparison_note": "Rolling updates are the default for a reason, but blue-green and canary are often better when release risk is high.",
        "practice": [
            {"title": "General web apps", "text": "Rolling updates are usually the most practical starting point."},
            {"title": "High-risk releases", "text": "Use canary to expose only a portion of users first."},
            {"title": "Fast rollback needs", "text": "Blue-green works well when you need instant cutover reversal."},
        ],
    },
    {
        "file": "multi-container-pod-patterns.html",
        "title": "Multi-Container Pod Patterns",
        "subtitle": "Interactive guide to sidecar, ambassador, adapter patterns and container lifecycle hooks within a Pod.",
        "lead": "Multi-container Pods work because containers inside the same Pod share a network namespace and can also share storage. The Pod boundary defines their close coupling.",
        "concept": [
            {"title": "Sidecar pattern", "text": "A helper container runs continuously alongside the app and supports it."},
            {"title": "Ambassador pattern", "text": "A proxy container manages communication to external or remote services."},
            {"title": "Adapter pattern", "text": "A helper container transforms app output into a standardized format."},
        ],
        "flow_title": "Multi-Container Pod Collaboration Flow",
        "flow": [
            {"title": "Pod starts", "text": "Multiple tightly related containers start inside one Pod."},
            {"title": "Hooks may run", "text": "postStart and preStop hooks can coordinate setup and graceful shutdown."},
            {"title": "Containers share localhost", "text": "They communicate through the same Pod network namespace."},
            {"title": "Support behavior runs continuously", "text": "Helper containers provide proxying, adaptation, or sidecar support to the main app."},
        ],
        "flow_note": "A multi-container Pod makes sense only when the containers are truly operationally coupled and benefit from sharing the same Pod boundary.",
        "examples": [
            {"title": "Pattern Summary", "code": "sidecar -> support service\nambassador -> local proxy\nadapter -> format transformer"},
            {"title": "Lifecycle Hooks", "code": "postStart\npreStop"},
        ],
        "comparison_title": "Pattern Comparison",
        "comparison": [
            ["Pattern", "Purpose", "Typical example"],
            ["Sidecar", "Support app continuously", "Log shipper, metrics agent"],
            ["Ambassador", "Proxy traffic for the app", "Database or service proxy"],
            ["Adapter", "Transform app output", "Custom metrics to standard metrics format"],
        ],
        "comparison_note": "The right pattern depends on whether the helper container is supporting behavior, proxying traffic, or translating output.",
        "practice": [
            {"title": "Logging sidecars", "text": "Ship logs without modifying the main application binary."},
            {"title": "Local traffic mediation", "text": "Proxy external services through an in-Pod ambassador container."},
            {"title": "Observability adaptation", "text": "Standardize app output so existing tooling can consume it easily."},
        ],
    },
])
PAGES.extend([
    {
        "file": "resource-quotas-limits.html",
        "title": "Resource Quotas and Limits",
        "subtitle": "Interactive guide to requests, limits, namespace quotas, and how Kubernetes enforces resource fairness in shared clusters.",
        "lead": "Requests, limits, and namespace ResourceQuota solve different but connected problems: scheduling guarantees, runtime protection, and namespace-level governance.",
        "concept": [
            {"title": "Requests", "text": "Requests define the minimum resources the scheduler must reserve for a container."},
            {"title": "Limits", "text": "Limits cap how much CPU or memory the container may consume at runtime."},
            {"title": "ResourceQuota", "text": "ResourceQuota restricts aggregate consumption across a namespace."},
        ],
        "flow_title": "Admission and Enforcement Flow",
        "flow": [
            {"title": "Define namespace quota", "text": "Administrators assign a resource budget to a namespace."},
            {"title": "Submit workload", "text": "A Pod or controller specifies resource requests and limits."},
            {"title": "Validate against quota", "text": "Admission checks whether enough quota remains."},
            {"title": "Admit or reject", "text": "The workload is accepted only if namespace constraints are satisfied."},
        ],
        "flow_note": "Requests influence scheduling, limits influence runtime behavior, and quotas influence namespace admission decisions.",
        "examples": [
            {"title": "ResourceQuota Example", "code": "apiVersion: v1\nkind: ResourceQuota\nmetadata:\n  name: mem-cpu-demo\n  namespace: quotaz\nspec:\n  hard:\n    requests.cpu: \"1\"\n    requests.memory: 1Gi\n    limits.cpu: \"2\"\n    limits.memory: 2Gi"},
            {"title": "Useful Commands", "code": "kubectl get resourcequota -n quotaz\nkubectl describe resourcequota mem-cpu-demo -n quotaz"},
        ],
        "comparison_title": "Requests, Limits, and Quotas",
        "comparison": [
            ["Layer", "Scope", "Purpose"],
            ["Request", "Container", "Guarantee minimum resources for scheduling"],
            ["Limit", "Container", "Prevent a container from exceeding allowed resources"],
            ["ResourceQuota", "Namespace", "Control total resource consumption across workloads"],
        ],
        "comparison_note": "Most confusion disappears when you remember that requests are about placement, limits are about runtime, and quotas are about aggregate namespace policy.",
        "practice": [
            {"title": "Multi-tenant governance", "text": "Keep one namespace or team from consuming the whole cluster."},
            {"title": "Cost boundaries", "text": "Enforce budget-oriented ceilings in development or shared environments."},
            {"title": "Stability protection", "text": "Prevent runaway workloads from destabilizing other workloads."},
        ],
    },
    {
        "file": "static-pods.html",
        "title": "Static Pods",
        "subtitle": "Interactive guide to kubelet-managed Pods, mirror Pods, and the node-local manifest model used by control plane components.",
        "lead": "Static Pods are created directly by the kubelet from files on a node, not from normal API-driven controller workflows. That makes them useful for critical node-local components.",
        "concept": [
            {"title": "Node-local manifests", "text": "Static Pods are declared as files in the kubelet static pod path."},
            {"title": "Kubelet-managed lifecycle", "text": "The kubelet is the primary manager that creates and restarts the Pod."},
            {"title": "Mirror Pod visibility", "text": "A read-only mirror object appears in the API server so operators can inspect status."},
        ],
        "flow_title": "Static Pod Lifecycle",
        "flow": [
            {"title": "Manifest placed on node", "text": "A YAML file is added to the static pod manifest directory."},
            {"title": "Kubelet detects file", "text": "The kubelet notices the manifest and creates the Pod locally."},
            {"title": "Mirror Pod appears", "text": "The API server shows a mirror Pod for visibility and inspection."},
            {"title": "Kubelet maintains the Pod", "text": "If the Pod fails, kubelet restarts it as long as the manifest exists."},
        ],
        "flow_note": "The API server shows status, but the kubelet remains the authoritative lifecycle manager for the Static Pod itself.",
        "examples": [
            {"title": "Typical Static Pod Path", "code": "/etc/kubernetes/manifests/"},
            {"title": "Useful Commands", "code": "kubectl get pods -n kube-system\nls -la /etc/kubernetes/manifests/\ncat /var/lib/kubelet/config.yaml | grep staticPodPath"},
        ],
        "comparison_title": "Static Pods vs Regular Pods",
        "comparison": [
            ["Feature", "Static Pods", "Regular Pods"],
            ["Managed by", "Kubelet on one node", "API server plus controllers"],
            ["Created from", "Manifest file on node", "API requests and controller objects"],
            ["Scheduling", "Node-specific", "Scheduler-controlled"],
            ["Visibility", "Mirror Pod in API", "Normal API object"],
        ],
        "comparison_note": "Static Pods are best understood as node-local kubelet behavior with API visibility added on top.",
        "practice": [
            {"title": "Control plane understanding", "text": "Learn why kubeadm-based control plane components often run as Static Pods."},
            {"title": "Node-local recovery thinking", "text": "Understand how critical components can boot from node configuration directly."},
            {"title": "Operational inspection", "text": "Use mirror Pods and manifest paths to debug kubelet-managed components."},
        ],
    },
    {
        "file": "custom-resource-definitions.html",
        "title": "Custom Resource Definitions",
        "subtitle": "Interactive guide to extending the Kubernetes API with custom types, schema validation, and operator-driven reconciliation.",
        "lead": "CRDs teach Kubernetes new resource types. They become truly useful when users create custom resources and optional controllers or operators act on those resources.",
        "concept": [
            {"title": "CRD defines a type", "text": "A CRD adds a new resource kind, names, version, and schema to the Kubernetes API."},
            {"title": "CR is an instance", "text": "A Custom Resource is an actual object created from that new type."},
            {"title": "Operator pattern", "text": "Controllers can watch custom resources and turn their desired state into action."},
        ],
        "flow_title": "API Extension Flow",
        "flow": [
            {"title": "Create CRD", "text": "Define names, versions, scope, and schema validation."},
            {"title": "Register with API server", "text": "The Kubernetes API now understands the new kind."},
            {"title": "Create custom resources", "text": "Users apply CR instances just like built-in objects."},
            {"title": "Validate object structure", "text": "OpenAPI schema checks whether the custom resource is valid."},
            {"title": "Optional controller reconciles", "text": "An operator or controller watches CRs and implements behavior."},
        ],
        "flow_note": "A CRD alone extends the API. A controller is what turns that custom type into an active platform feature.",
        "examples": [
            {"title": "CRD Skeleton", "code": "apiVersion: apiextensions.k8s.io/v1\nkind: CustomResourceDefinition\nmetadata:\n  name: websites.example.com"},
            {"title": "Useful Commands", "code": "kubectl get crds\nkubectl api-resources\nkubectl describe crd <name>"},
        ],
        "comparison_title": "CRD vs ConfigMap",
        "comparison": [
            ["Feature", "CRD", "ConfigMap"],
            ["Purpose", "Define a new API resource type", "Store non-secret configuration data"],
            ["Validation", "Schema-driven validation", "Limited built-in structure"],
            ["Versioning", "Supports API versioning", "Single core object type"],
            ["Typical use", "Operators and platform APIs", "Application configuration"],
        ],
        "comparison_note": "Use a CRD when you want a new platform concept with API semantics, not just a bag of configuration values.",
        "practice": [
            {"title": "Platform APIs", "text": "Define higher-level abstractions like Website, Application, or Database resources."},
            {"title": "Operator learning", "text": "Understand the foundation behind tools such as Prometheus Operator or ArgoCD."},
            {"title": "Schema enforcement", "text": "Use OpenAPI validation to make custom resources safer and more predictable."},
        ],
    },
    {
        "file": "opa-gatekeeper-policy.html",
        "title": "OPA Gatekeeper",
        "subtitle": "Interactive guide to policy enforcement with ConstraintTemplates, Constraints, validating admission, and audit mode.",
        "lead": "Gatekeeper adds policy-as-code controls to admission. It is most useful when you clearly separate reusable policy logic from the concrete policy instances that enforce it.",
        "concept": [
            {"title": "ConstraintTemplate", "text": "Defines reusable policy logic and schema for constraints."},
            {"title": "Constraint", "text": "Applies a specific policy instance to a set of resources."},
            {"title": "Admission plus audit", "text": "Gatekeeper can both block non-compliant resources and audit the cluster for drift."},
        ],
        "flow_title": "Admission Control Flow",
        "flow": [
            {"title": "Submit resource", "text": "A user or controller sends a request to the API server."},
            {"title": "Validating webhook runs", "text": "Gatekeeper intercepts the admission request."},
            {"title": "Policy evaluates", "text": "ConstraintTemplates and Constraints are used to check compliance."},
            {"title": "Allow or deny", "text": "The resource is accepted or rejected based on policy outcome."},
            {"title": "Audit existing resources", "text": "Gatekeeper also scans resources already in the cluster for violations."},
        ],
        "flow_note": "Gatekeeper is strongest when used both proactively at admission time and retrospectively through audit.",
        "examples": [
            {"title": "Policy Building Blocks", "code": "ConstraintTemplate + Constraint + Admission Webhook"},
            {"title": "Useful Commands", "code": "kubectl get constrainttemplates\nkubectl get constraints\nkubectl describe <constraint>"},
        ],
        "comparison_title": "Template vs Constraint",
        "comparison": [
            ["Component", "Role", "Analogy"],
            ["ConstraintTemplate", "Reusable policy definition", "Blueprint"],
            ["Constraint", "Concrete policy instance with scope", "Applied policy rule"],
        ],
        "comparison_note": "Think of ConstraintTemplate as the policy class and Constraint as the configured instance of that policy.",
        "practice": [
            {"title": "Security enforcement", "text": "Reject privileged containers, unsafe host access, or missing required settings."},
            {"title": "Organizational standards", "text": "Enforce labels, naming conventions, or namespace rules."},
            {"title": "Compliance visibility", "text": "Use audit mode to identify policy drift without immediately blocking workloads."},
        ],
    },
])
PAGES.extend([
    {
        "file": "health-probes.html",
        "title": "Health Probes",
        "subtitle": "Interactive guide to liveness, readiness, startup probes, and the different actions Kubernetes takes when checks fail.",
        "lead": "All probes answer different questions. The most important learning point is not how to configure them, but what Kubernetes does after each probe type fails.",
        "concept": [
            {"title": "Liveness probe", "text": "Checks whether the container is still alive. Failure leads to a restart."},
            {"title": "Readiness probe", "text": "Checks whether the container is ready to serve traffic. Failure removes the Pod from Service endpoints."},
            {"title": "Startup probe", "text": "Protects slow-starting applications by delaying liveness and readiness behavior until startup succeeds."},
        ],
        "flow_title": "Probe Decision Flow",
        "flow": [
            {"title": "Run probe", "text": "Kubelet executes exec, HTTP, TCP, or gRPC health checks."},
            {"title": "Evaluate result", "text": "Probe success or failure is recorded repeatedly over time."},
            {"title": "Reach threshold", "text": "Configured failure thresholds determine when action is taken."},
            {"title": "Apply action", "text": "Kubernetes restarts the container, removes it from endpoints, or continues startup isolation."},
        ],
        "flow_note": "Readiness affects traffic. Liveness affects process restart. Startup protects slow boot sequences from false liveness failure.",
        "examples": [
            {"title": "Liveness and Readiness Example", "code": "livenessProbe:\n  httpGet:\n    path: /healthz\n    port: 8080\nreadinessProbe:\n  tcpSocket:\n    port: 5432"},
            {"title": "Observe Probe Behavior", "code": "kubectl get pod -w\nkubectl describe pod <pod-name>"},
        ],
        "comparison_title": "Probe Types and Outcomes",
        "comparison": [
            ["Probe", "Question", "Action on failure"],
            ["Liveness", "Is the process alive?", "Restart the container"],
            ["Readiness", "Can this Pod receive traffic?", "Remove Pod from Service endpoints"],
            ["Startup", "Has startup finished successfully?", "Delay liveness/readiness reactions until successful"],
        ],
        "comparison_note": "A readiness failure does not mean the Pod is dead; it only means traffic should stop going there for now.",
        "practice": [
            {"title": "Hung processes", "text": "Use liveness probes to detect deadlocks or processes that stopped responding."},
            {"title": "Safe traffic management", "text": "Use readiness probes to keep warming or degraded Pods out of client traffic."},
            {"title": "Slow boots", "text": "Use startup probes for heavy applications that need extra warm-up time."},
        ],
    },
    {
        "file": "metrics-server-architecture.html",
        "title": "Metrics Server",
        "subtitle": "Interactive guide to the resource metrics pipeline behind kubectl top and Horizontal Pod Autoscaling.",
        "lead": "Metrics Server is the lightweight short-term resource metrics path for Kubernetes autoscaling and quick inspection. It is not a full observability stack.",
        "concept": [
            {"title": "Cluster-wide aggregator", "text": "Metrics Server gathers CPU and memory usage across nodes in the cluster."},
            {"title": "Metrics API provider", "text": "It exposes those metrics through the Kubernetes Metrics API."},
            {"title": "Autoscaling foundation", "text": "HPA and kubectl top depend on this pipeline."},
        ],
        "flow_title": "Metrics Collection Path",
        "flow": [
            {"title": "Kubelets expose metrics", "text": "Each node provides resource usage data for the Pods running there."},
            {"title": "Metrics Server scrapes", "text": "The service collects resource usage from kubelets."},
            {"title": "API aggregation layer serves results", "text": "Metrics become available through the Kubernetes API server."},
            {"title": "kubectl top and HPA consume data", "text": "Humans and controllers query the same aggregated metrics path."},
            {"title": "Observation and scaling happen", "text": "Operators inspect usage and autoscalers act on thresholds."},
        ],
        "flow_note": "Metrics Server provides current operational resource data, not long historical monitoring data.",
        "examples": [
            {"title": "Install Metrics Server", "code": "kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml"},
            {"title": "Inspect Metrics", "code": "kubectl top nodes\nkubectl top pods -A"},
        ],
        "comparison_title": "Metrics Server vs Full Monitoring",
        "comparison": [
            ["Tool", "Primary purpose", "Retention"],
            ["Metrics Server", "Autoscaling and quick resource visibility", "Short-term in-memory"],
            ["Prometheus / Grafana", "Monitoring, alerting, dashboards, history", "Long-term configurable retention"],
        ],
        "comparison_note": "Metrics Server is intentionally narrow and lightweight; it complements rather than replaces full monitoring systems.",
        "practice": [
            {"title": "Autoscaling enablement", "text": "Install Metrics Server first when building labs around HPA."},
            {"title": "Quick node insight", "text": "Use kubectl top to see immediate resource consumption."},
            {"title": "Resource troubleshooting", "text": "Confirm whether high CPU or memory usage is driving scaling or instability."},
        ],
    },
    {
        "file": "ingress-endpointslices.html",
        "title": "Ingress and EndpointSlices",
        "subtitle": "Interactive guide to HTTP routing through Ingress and how EndpointSlices help Kubernetes manage backend endpoints efficiently.",
        "lead": "Ingress handles HTTP and HTTPS routing decisions at the edge, while EndpointSlices help Kubernetes track backend Service membership efficiently at scale.",
        "concept": [
            {"title": "Ingress adds Layer 7 routing", "text": "Host-based and path-based routing turn one entry point into many application routes."},
            {"title": "Ingress Controller required", "text": "An Ingress resource needs a controller like NGINX or Traefik to become active."},
            {"title": "EndpointSlices scale endpoint tracking", "text": "They improve how Kubernetes stores and manages backend endpoint membership."},
        ],
        "flow_title": "Traffic Path from Client to Pod",
        "flow": [
            {"title": "Client sends request", "text": "Traffic arrives with a host, path, and optionally TLS."},
            {"title": "Ingress Controller receives traffic", "text": "The controller handles the network edge and interprets the request."},
            {"title": "Ingress rules match", "text": "Host and path rules choose the target Service."},
            {"title": "Service resolves backend set", "text": "The Service points to a set of eligible backend endpoints."},
            {"title": "EndpointSlices provide Pod addresses", "text": "Traffic is routed to the correct Pods behind the Service."},
        ],
        "flow_note": "Ingress decides where traffic should go. EndpointSlices help Kubernetes know which Pod addresses actually belong to that backend.",
        "examples": [
            {"title": "Basic Ingress Pattern", "code": "kind: Ingress\nspec:\n  rules:\n  - host: app.example.local"},
            {"title": "Useful Inspection Commands", "code": "kubectl get ingress\nkubectl get endpointslices\nkubectl describe ingress <name>"},
        ],
        "comparison_title": "Service vs Ingress",
        "comparison": [
            ["Feature", "Service", "Ingress"],
            ["Routing layer", "Layer 4", "Layer 7"],
            ["Routing style", "IP and port", "Host and path"],
            ["TLS termination", "Usually app-specific", "Can terminate at the edge"],
            ["Primary use", "Stable access to Pods", "HTTP/HTTPS application entry routing"],
        ],
        "comparison_note": "A Service is still part of the path even when Ingress is used; Ingress does not replace Services internally.",
        "practice": [
            {"title": "One entry point for many apps", "text": "Use Ingress to expose multiple web apps behind one edge endpoint."},
            {"title": "TLS at the edge", "text": "Centralize HTTPS handling instead of configuring certificates in every app."},
            {"title": "Scalable backend tracking", "text": "Use EndpointSlices to support larger backend sets cleanly."},
        ],
    },
    {
        "file": "gateway-api-routing.html",
        "title": "Gateway API",
        "subtitle": "Interactive guide to GatewayClass, Gateway, and HTTPRoute with a focus on portable routing and traffic policy composition.",
        "lead": "Gateway API evolves the ingress model by separating infrastructure ownership from routing ownership and by providing richer, more portable network APIs.",
        "concept": [
            {"title": "GatewayClass", "text": "Selects the implementation or controller that will realize the Gateway behavior."},
            {"title": "Gateway", "text": "Represents listeners and the network entry point into the cluster."},
            {"title": "HTTPRoute", "text": "Declares host, path, match, filter, and backend routing rules that attach to a Gateway."},
        ],
        "flow_title": "Gateway API Resource Flow",
        "flow": [
            {"title": "Choose GatewayClass", "text": "A specific controller implementation is selected."},
            {"title": "Create Gateway", "text": "Listeners declare ports, protocols, and attachment points."},
            {"title": "Attach HTTPRoute", "text": "Routes bind to the Gateway and express request matching rules."},
            {"title": "Select Services", "text": "Matched traffic is directed to backend Services."},
            {"title": "Apply richer routing policy", "text": "Advanced host routing, path routing, and traffic splitting become easier to express."},
        ],
        "flow_note": "Gateway API is not just an alternative syntax; it is a stronger separation of concerns between platform and app routing configuration.",
        "examples": [
            {"title": "Resource Chain", "code": "GatewayClass -> Gateway -> HTTPRoute -> Service"},
            {"title": "Useful Commands", "code": "kubectl get gatewayclass\nkubectl get gateways\nkubectl get httproutes"},
        ],
        "comparison_title": "Ingress vs Gateway API",
        "comparison": [
            ["Topic", "Ingress", "Gateway API"],
            ["Model", "Single ingress object", "Role-oriented resource model"],
            ["Expressiveness", "More limited", "Richer routing and policy structure"],
            ["Ownership split", "Less explicit", "Clearer platform/app separation"],
            ["Portability", "Often annotation-heavy", "Designed for stronger portable semantics"],
        ],
        "comparison_note": "Gateway API shines when teams want a cleaner contract between platform networking and application routing configuration.",
        "practice": [
            {"title": "Canary routing", "text": "Traffic splitting and richer routing policies fit naturally into Gateway API."},
            {"title": "Shared platform ownership", "text": "Platform teams can own Gateways while app teams own HTTPRoutes."},
            {"title": "Modern HTTP routing labs", "text": "Use it when teaching the next generation of ingress-style control."},
        ],
    },
])
