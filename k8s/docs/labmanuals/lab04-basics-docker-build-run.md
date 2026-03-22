# Lab 08: Docker Build and Run - Multi-Version Application

## Overview
In this lab, you will learn how to build Docker images from Dockerfiles, tag them with versions, run containers, and manage multiple versions of the same application. You'll build and deploy two versions of an Apache web server to understand Docker's containerization workflow.

## Prerequisites
- Docker installed on your machine
- Basic understanding of containers
- Terminal/Command line access
- Text editor
- Basic understanding of HTML (helpful but not required)

## Learning Objectives
By the end of this lab, you will be able to:
- Understand Dockerfile structure and instructions
- Build Docker images from Dockerfiles
- Tag images with version labels
- Run containers from custom images
- Map container ports to host ports
- Manage multiple container versions
- Test containerized applications
- Stop, start, and remove containers
- Implement application versioning strategies

---

## What is Docker?

### Introduction
**Docker** is a platform for developing, shipping, and running applications in containers. Containers package an application with all its dependencies, ensuring it runs consistently across different environments.

### Key Concepts

| Concept | Description |
|---------|-------------|
| **Image** | Read-only template containing application code and dependencies |
| **Container** | Running instance of an image |
| **Dockerfile** | Text file with instructions to build an image |
| **Registry** | Storage for Docker images (e.g., Docker Hub) |
| **Tag** | Version label for images (e.g., `v1`, `v2`, `latest`) |

### Why Use Docker?

- **Consistency**: Same environment in development, testing, and production
- **Isolation**: Applications run in separate containers
- **Portability**: Run anywhere Docker is installed
- **Efficiency**: Lightweight compared to virtual machines
- **Versioning**: Easy rollback to previous versions

---

## Exercise 1: Environment Setup

### Step 1: Verify Docker Installation

Check if Docker is installed:

```bash
docker --version
```

Expected output:
```
Docker version 24.0.x, build xxxxx
```

Check Docker is running:

```bash
docker info
```

Should show system information without errors.

### Step 2: Navigate to Lab Directory

```bash
cd k8s/labs/docker_app/docker
```

Verify you're in the correct directory:

```bash
pwd
ls -la
```

Expected files:
```
Dockerfile.v1
Dockerfile.v2
index-v1.html
index-v2.html
```

---

## Exercise 2: Understanding the Application Structure

### Step 1: Review Version 1 Files

**View the Dockerfile for Version 1:**

```bash
cat Dockerfile.v1
```

Content:
```dockerfile
# Use an official Apache HTTP server image as the base
FROM httpd:2.4

# Copy the index.html file for version 1 into the Apache web server document root
COPY index-v1.html /usr/local/apache2/htdocs/index.html

# Expose the default HTTP port
EXPOSE 80
```

**Understanding the Dockerfile:**

| Instruction | Purpose |
|-------------|---------|
| `FROM httpd:2.4` | Base image - Apache HTTP Server version 2.4 |
| `COPY index-v1.html /usr/local/apache2/htdocs/index.html` | Copies HTML file into container |
| `EXPOSE 80` | Documents that container listens on port 80 |

**View the HTML file:**

```bash
cat index-v1.html
```

Content:
```html
<!DOCTYPE html>
<html>
<head>
    <title>Apache HTML Index - Version 1</title>
</head>
<body>
    <h1>Welcome to Apache HTML Index - Version 1</h1>
</body>
</html>
```

### Step 2: Review Version 2 Files

**View the Dockerfile for Version 2:**

```bash
cat Dockerfile.v2
```

Content:
```dockerfile
# Use an official Apache HTTP server image as the base
FROM httpd:2.4

# Copy the index.html file for version 2 into the Apache web server document root
COPY index-v2.html /usr/local/apache2/htdocs/index.html

# Expose the default HTTP port
EXPOSE 80
```

**View the HTML file:**

```bash
cat index-v2.html
```

Content:
```html
<!DOCTYPE html>
<html>
<head>
    <title>Apache HTML Index - Version 2</title>
</head>
<body>
    <h1>Welcome to Apache HTML Index - Version 2</h1>
</body>
</html>
```

**Key Difference**: Version 2 displays "Version 2" instead of "Version 1" in the HTML content.

---

## Exercise 3: Building Docker Images

### Step 1: Build Version 1 Image

Build the first version of the application:

```bash
docker build -t my-apache-app:v1 -f Dockerfile.v1 .
```

Expected output:
```
[+] Building 5.2s (8/8) FINISHED
 => [internal] load build definition from Dockerfile.v1
 => => transferring dockerfile: 250B
 => [internal] load .dockerignore
 => => transferring context: 2B
 => [internal] load metadata for docker.io/library/httpd:2.4
 => [1/2] FROM docker.io/library/httpd:2.4@sha256:xxxxx
 => [internal] load build context
 => => transferring context: 230B
 => [2/2] COPY index-v1.html /usr/local/apache2/htdocs/index.html
 => exporting to image
 => => exporting layers
 => => writing image sha256:xxxxx
 => => naming to docker.io/library/my-apache-app:v1
```

**Understanding the command:**
- `docker build` - Command to build an image
- `-t my-apache-app:v1` - Tag (name and version) for the image
  - `my-apache-app` - Image name
  - `v1` - Version tag
- `-f Dockerfile.v1` - Specifies which Dockerfile to use
- `.` - Build context (current directory)

### Step 2: Build Version 2 Image

Build the second version:

```bash
docker build -t my-apache-app:v2 -f Dockerfile.v2 .
```

Expected output similar to v1 build.

### Step 3: Verify Images Were Created

List all Docker images:

```bash
docker images
```

Expected output:
```
REPOSITORY       TAG       IMAGE ID       CREATED          SIZE
my-apache-app    v2        abc123def456   10 seconds ago   145MB
my-apache-app    v1        xyz789ghi012   2 minutes ago    145MB
httpd            2.4       def456abc789   2 weeks ago      145MB
```

**Understanding the output:**
- **REPOSITORY**: Image name
- **TAG**: Version label
- **IMAGE ID**: Unique identifier (first 12 chars of SHA256)
- **CREATED**: When the image was built
- **SIZE**: Image size on disk

Filter to show only our application images:

```bash
docker images my-apache-app
```

---

## Exercise 4: Running Containers

### Step 1: Run Version 1 Container

Start a container from the v1 image:

```bash
docker run -d -p 8081:80 --name apache-v1 my-apache-app:v1
```

Expected output (container ID):
```
a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0
```

**Understanding the command:**
- `docker run` - Create and start a container
- `-d` - Detached mode (runs in background)
- `-p 8081:80` - Port mapping
  - `8081` - Host port (your machine)
  - `80` - Container port (Apache default)
- `--name apache-v1` - Custom container name
- `my-apache-app:v1` - Image to use

### Step 2: Run Version 2 Container

Start a container from the v2 image on a different port:

```bash
docker run -d -p 8082:80 --name apache-v2 my-apache-app:v2
```

**Why different port?**
- Two containers can't bind to the same host port
- v1 uses 8081, v2 uses 8082
- Both use port 80 internally (isolated from each other)

### Step 3: Verify Containers Are Running

List running containers:

```bash
docker ps
```

Expected output:
```
CONTAINER ID   IMAGE              COMMAND              CREATED          STATUS          PORTS                  NAMES
xyz789abc012   my-apache-app:v2   "httpd-foreground"   30 seconds ago   Up 29 seconds   0.0.0.0:8082->80/tcp   apache-v2
abc123def456   my-apache-app:v1   "httpd-foreground"   2 minutes ago    Up 2 minutes    0.0.0.0:8081->80/tcp   apache-v1
```

**Understanding the output:**
- **CONTAINER ID**: Unique container identifier
- **IMAGE**: Image used to create the container
- **COMMAND**: Command running inside container
- **CREATED**: When container was created
- **STATUS**: Current status (Up = running)
- **PORTS**: Port mappings (host:container)
- **NAMES**: Container name

---

## Exercise 5: Testing the Applications

### Step 1: Test Version 1 Application

**Using curl:**

```bash
curl http://localhost:8081
```

Expected output:
```html
<!DOCTYPE html>
<html>
<head>
    <title>Apache HTML Index - Version 1</title>
</head>
<body>
    <h1>Welcome to Apache HTML Index - Version 1</h1>
</body>
</html>
```

**Using a web browser:**
- Open: `http://localhost:8081`
- Should display: "Welcome to Apache HTML Index - Version 1"

### Step 2: Test Version 2 Application

**Using curl:**

```bash
curl http://localhost:8082
```

Expected output:
```html
<!DOCTYPE html>
<html>
<head>
    <title>Apache HTML Index - Version 2</title>
</head>
<body>
    <h1>Welcome to Apache HTML Index - Version 2</h1>
</body>
</html>
```

**Using a web browser:**
- Open: `http://localhost:8082`
- Should display: "Welcome to Apache HTML Index - Version 2"

### Step 3: Compare the Versions

Open both URLs in different browser tabs:
- `http://localhost:8081` - Version 1
- `http://localhost:8082` - Version 2

**Observation**: Two different versions of the same application running simultaneously!

---

## Exercise 6: Container Inspection and Logs

### Step 1: Inspect Container Details

View detailed information about a container:

```bash
docker inspect apache-v1
```

Returns JSON with comprehensive container information:
- Network settings
- Volume mounts
- Environment variables
- Resource limits
- Much more

Get specific information:

```bash
# Get container IP address
docker inspect -f '{{.NetworkSettings.IPAddress}}' apache-v1

# Get container state
docker inspect -f '{{.State.Status}}' apache-v1
```

### Step 2: View Container Logs

View logs from Version 1:

```bash
docker logs apache-v1
```

Expected output (Apache access logs):
```
[Mon Mar 16 18:30:00.123456 2026] [mpm_event:notice] [pid 1:tid 140xxxxx] AH00489: Apache/2.4.57 (Unix) configured -- resuming normal operations
[Mon Mar 16 18:30:00.123789 2026] [core:notice] [pid 1:tid 140xxxxx] AH00094: Command line: 'httpd -D FOREGROUND'
172.17.0.1 - - [16/Mar/2026:18:32:15 +0000] "GET / HTTP/1.1" 200 189
```

Follow logs in real-time:

```bash
docker logs -f apache-v1
```

(Press Ctrl+C to exit)

View last 10 log lines:

```bash
docker logs --tail 10 apache-v1
```

### Step 3: Execute Commands Inside Container

Open a shell inside the running container:

```bash
docker exec -it apache-v1 /bin/bash
```

You're now inside the container! Try these commands:

```bash
# List files in web root
ls -la /usr/local/apache2/htdocs/

# View the HTML file
cat /usr/local/apache2/htdocs/index.html

# Check Apache process
ps aux | grep httpd

# Exit the container
exit
```

Run a single command without interactive shell:

```bash
docker exec apache-v1 cat /usr/local/apache2/htdocs/index.html
```

---

## Exercise 7: Container Lifecycle Management

### Step 1: Stop Containers

Stop Version 1 container:

```bash
docker stop apache-v1
```

Expected output:
```
apache-v1
```

Verify it's stopped:

```bash
docker ps -a
```

The STATUS should show "Exited" for apache-v1.

Try accessing it:

```bash
curl http://localhost:8081
```

Should fail with connection refused.

### Step 2: Start Stopped Container

Restart the stopped container:

```bash
docker start apache-v1
```

Verify it's running:

```bash
docker ps
```

Test again:

```bash
curl http://localhost:8081
```

Should work again!

### Step 3: Restart Container

Restart (stop and start in one command):

```bash
docker restart apache-v1
```

### Step 4: Pause and Unpause

Pause container (freezes all processes):

```bash
docker pause apache-v1
```

Try accessing:

```bash
curl http://localhost:8081
```

Will hang (container is frozen).

Unpause:

```bash
docker unpause apache-v1
```

Now it works again.

---

## Exercise 8: Resource Monitoring

### Step 1: View Container Statistics

Real-time resource usage:

```bash
docker stats
```

Shows CPU, memory, network I/O for all running containers.

(Press Ctrl+C to exit)

View stats for specific container:

```bash
docker stats apache-v1 --no-stream
```

Expected output:
```
CONTAINER ID   NAME        CPU %     MEM USAGE / LIMIT    MEM %     NET I/O         BLOCK I/O   PIDS
abc123def456   apache-v1   0.01%     12.5MiB / 15.6GiB    0.08%     1.2kB / 856B    0B / 0B     82
```

### Step 2: View Running Processes

List processes inside container:

```bash
docker top apache-v1
```

Expected output:
```
UID       PID     PPID    C   STIME   TTY   TIME      CMD
root      12345   12320   0   18:30   ?     00:00:00  httpd -DFOREGROUND
daemon    12380   12345   0   18:30   ?     00:00:00  httpd -DFOREGROUND
daemon    12381   12345   0   18:30   ?     00:00:00  httpd -DFOREGROUND
```

---

## Exercise 9: Cleanup

### Step 1: Stop All Containers

Stop both versions:

```bash
docker stop apache-v1 apache-v2
```

Verify they're stopped:

```bash
docker ps
```

Should show no containers.

View stopped containers:

```bash
docker ps -a
```

### Step 2: Remove Containers

Remove Version 1 container:

```bash
docker rm apache-v1
```

Remove Version 2 container:

```bash
docker rm apache-v2
```

Verify removal:

```bash
docker ps -a
```

Should show no apache-v1 or apache-v2 containers.

**Shortcut**: Stop and remove in one command:

```bash
# If containers were still running:
# docker rm -f apache-v1 apache-v2
```

### Step 3: Remove Images (Optional)

Remove the custom images:

```bash
docker rmi my-apache-app:v1
docker rmi my-apache-app:v2
```

Expected output:
```
Untagged: my-apache-app:v1
Deleted: sha256:abc123...
Deleted: sha256:def456...
```

Verify removal:

```bash
docker images my-apache-app
```

Should show no results.

---

## Exercise 10: Advanced Scenarios

### Scenario 1: Running Multiple Instances

Run multiple instances of the same version:

```bash
docker run -d -p 8083:80 --name apache-v1-instance1 my-apache-app:v1
docker run -d -p 8084:80 --name apache-v1-instance2 my-apache-app:v1
docker run -d -p 8085:80 --name apache-v1-instance3 my-apache-app:v1
```

All three serve the same content on different ports.

### Scenario 2: Rolling Update Simulation

Simulate a rolling update from v1 to v2:

```bash
# Start with v1
docker run -d -p 8080:80 --name app-prod my-apache-app:v1

# Stop v1
docker stop app-prod

# Start v2 with same name
docker rm app-prod
docker run -d -p 8080:80 --name app-prod my-apache-app:v2
```

### Scenario 3: Blue-Green Deployment

Run both versions simultaneously:

```bash
# Blue (current production)
docker run -d -p 8080:80 --name app-blue my-apache-app:v1

# Green (new version)
docker run -d -p 8081:80 --name app-green my-apache-app:v2

# Switch traffic by changing port mapping or load balancer config
# Then remove old version
docker stop app-blue
docker rm app-blue
```

---

## Key Takeaways

1. **Dockerfiles** define how to build images
2. **Images** are immutable templates
3. **Containers** are running instances of images
4. **Tags** enable version management
5. **Port mapping** allows external access
6. **Multiple versions** can run simultaneously
7. **Container lifecycle** includes create, start, stop, remove
8. **Logs and stats** help monitor applications
9. **Docker exec** allows debugging inside containers
10. **Versioning** enables safe deployments and rollbacks

---

## Docker Command Reference

### Image Management
```bash
# Build image
docker build -t <name>:<tag> -f <dockerfile> <context>

# List images
docker images

# Remove image
docker rmi <image>

# Tag image
docker tag <source> <target>

# Pull image from registry
docker pull <image>:<tag>

# Push image to registry
docker push <image>:<tag>
```

### Container Management
```bash
# Run container
docker run -d -p <host-port>:<container-port> --name <name> <image>

# List running containers
docker ps

# List all containers (including stopped)
docker ps -a

# Stop container
docker stop <container>

# Start stopped container
docker start <container>

# Restart container
docker restart <container>

# Remove container
docker rm <container>

# Force remove running container
docker rm -f <container>
```

### Container Interaction
```bash
# View logs
docker logs <container>

# Follow logs
docker logs -f <container>

# Execute command
docker exec <container> <command>

# Interactive shell
docker exec -it <container> /bin/bash

# Copy files to/from container
docker cp <container>:<path> <local-path>
docker cp <local-path> <container>:<path>

# Inspect container
docker inspect <container>

# View stats
docker stats <container>

# View processes
docker top <container>
```

### Cleanup
```bash
# Remove all stopped containers
docker container prune

# Remove all unused images
docker image prune

# Remove all unused resources (containers, images, networks, volumes)
docker system prune

# Remove everything with force
docker system prune -a --volumes
```

---

## Best Practices

### Building Images
- ✅ Use official base images
- ✅ Specify exact image versions (not `latest`)
- ✅ Keep images small (minimize layers)
- ✅ Use `.dockerignore` to exclude unnecessary files
- ✅ Run as non-root user when possible
- ✅ Use multi-stage builds for production

### Tagging Strategy
- ✅ Use semantic versioning (`v1.0.0`, `v1.0.1`)
- ✅ Tag with git commit SHA for traceability
- ✅ Use meaningful tags (`stable`, `dev`, `prod`)
- ✅ Avoid overusing `latest` tag
- ✅ Tag images before pushing to registry

### Running Containers
- ✅ Always name your containers (`--name`)
- ✅ Use explicit port mappings
- ✅ Set resource limits (`--memory`, `--cpus`)
- ✅ Use volumes for persistent data
- ✅ Configure health checks
- ✅ Use environment variables for configuration

### Security
- ✅ Scan images for vulnerabilities
- ✅ Don't store secrets in images
- ✅ Use read-only file systems when possible
- ✅ Limit container capabilities
- ✅ Keep images updated
- ✅ Use trusted base images only

---

## Troubleshooting Guide

### Issue: Port already in use

**Error**: `Bind for 0.0.0.0:8080 failed: port is already allocated`

**Solution**:
```bash
# Find what's using the port
lsof -i :8080
# Or on Windows
netstat -ano | findstr :8080

# Use a different port
docker run -d -p 8090:80 --name apache-v1 my-apache-app:v1
```

### Issue: Container exits immediately

**Solution**:
```bash
# Check logs
docker logs <container-name>

# Check exit code
docker inspect <container-name> -f '{{.State.ExitCode}}'

# Common causes:
# - Application crashed
# - Wrong command
# - Missing dependencies
```

### Issue: Cannot connect to Docker daemon

**Error**: `Cannot connect to the Docker daemon at unix:///var/run/docker.sock`

**Solution**:
```bash
# Start Docker service (Linux)
sudo systemctl start docker

# On Windows/Mac, start Docker Desktop

# Check Docker is running
docker info
```

### Issue: Image not found

**Error**: `Unable to find image 'my-apache-app:v1' locally`

**Solution**:
```bash
# Verify image exists
docker images

# Rebuild if missing
docker build -t my-apache-app:v1 -f Dockerfile.v1 .
```

### Issue: Permission denied

**Error**: `Got permission denied while trying to connect`

**Solution**:
```bash
# Add user to docker group (Linux)
sudo usermod -aG docker $USER

# Logout and login again

# Or use sudo (not recommended for regular use)
sudo docker ps
```

---

## Real-World Applications

### CI/CD Pipeline
```bash
# Build
docker build -t myapp:${VERSION} .

# Test
docker run --rm myapp:${VERSION} npm test

# Push to registry
docker push myapp:${VERSION}
```

### Development Environment
```bash
# Run with volume mount for live code updates
docker run -d -p 8080:80 -v $(pwd):/app myapp:dev
```

### Microservices
```bash
# Run multiple services
docker run -d --name frontend -p 3000:3000 frontend:v1
docker run -d --name backend -p 5000:5000 backend:v1
docker run -d --name database -p 5432:5432 postgres:14
```

---

## Next Steps

After mastering Docker basics:
1. Learn **Docker Compose** for multi-container applications
2. Understand **Docker Networking** (bridge, host, overlay)
3. Explore **Docker Volumes** for data persistence
4. Study **Multi-stage builds** for optimized images
5. Learn **Docker Registry** for private image storage
6. Progress to **Kubernetes** for container orchestration

Proceed to [Lab 01: Creating Pods and Deployments](lab01-creating-pods.md) to deploy these Docker images on Kubernetes!

---

## Additional Reading

- [Docker Official Documentation](https://docs.docker.com/)
- [Dockerfile Best Practices](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)
- [Docker CLI Reference](https://docs.docker.com/engine/reference/commandline/cli/)
- [Docker Hub](https://hub.docker.com/)

---

**Lab Created**: March 2026
**Compatible with**: Docker 20.10+
**Based on**: labs/docker_app/docker/ files
**Tested on**: Docker Desktop (Windows/Mac), Docker Engine (Linux)
**Estimated Time**: 45-60 minutes
