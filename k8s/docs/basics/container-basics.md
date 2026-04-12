# Container basics for Kubernetes learners

Containers are **lightweight, portable units** that package an application with its libraries and configuration so it runs the same way in development, CI, and production. Kubernetes schedules and runs workloads as **Pods**, each of which uses a **container image** as its template.

---

## Images and layers

A **container image** is an immutable, layered filesystem snapshot plus metadata (entrypoint, environment defaults, exposed ports). Images are built from a **Dockerfile** (or another build spec) and tagged (for example `myapp:v1`, `myapp:v2`) so you can roll forward, roll back, and promote the same artifact through environments.

Typical image properties:

- **Base image** — e.g. `httpd:2.4` provides the runtime; your layers add app files.
- **`COPY` / `ADD`** — place application assets into the image.
- **`EXPOSE`** — documents intended ports (actual publishing happens at `docker run` or in Kubernetes `containerPort` / Service definitions).

Illustrative **Dockerfile** fragment (two variants of the same app, different static content):

```dockerfile
FROM httpd:2.4
COPY index-v1.html /usr/local/apache2/htdocs/index.html
EXPOSE 80
```

---

## Running containers locally (why it matters before Kubernetes)

Running a container on your machine with **Docker** (or a compatible runtime) lets you verify:

- the image builds and starts
- ports and HTTP responses match expectations
- you can run **multiple versions side by side** on different host ports for quick comparison

That validation is useful **before** you push to a registry or reference the image in a Pod spec. In Kubernetes, you do not run `docker run` on the node for normal workloads; the kubelet and container runtime create containers from the image reference in the Pod.

---

## Containers vs VMs (conceptual)

| Aspect | Containers | Traditional VMs |
|--------|------------|------------------|
| Isolation | Process + cgroup namespaces; shared kernel | Full guest OS per VM |
| Startup | Seconds | Often minutes |
| Density | Higher on same hardware | Lower |
| Use with K8s | Native workload unit | Nodes may be VMs or bare metal underneath |

---

## Relationship to Kubernetes

- Kubernetes **pulls** images (from a registry or pre-loaded in tools like Kind) and runs them as containers inside **Pods**.
- **Tags and digests** matter for reproducible deployments; many teams pin by digest in production.
- **Multi-stage builds** and minimal base images reduce attack surface and transfer size—relevant to security and policy topics elsewhere in this repo.

---

## Hands-On Labs

Practice these concepts with guided lab exercises:

| Lab | Description |
|-----|-------------|
| [Lab 04: Docker build and run](../../labmanuals/lab04-basics-docker-build-run.md) | Build images, run containers on different ports, and verify behavior before Kubernetes. |
