# **Lab Title**: Apache Container Version Testing with Docker

---

## **Objective**

1. Build Docker images for two versions of a simple Apache-based HTML app.
2. Run and expose the containers on different ports using `docker run`.
3. Verify the application version using `curl` and browser.
4. Understand version control and local testing before container registry or Kubernetes deployment.

---

## **Prerequisites**

- Docker installed and running.
- `curl` installed (optional for browser-based verification).

---

## **Step 1: Create Application Files**

### **1.1 HTML for Version 1**

Create a file named `index-v1.html` with this content:

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
````

### **1.2 HTML for Version 2**

Create a file named `index-v2.html`:

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

---

## **Step 2: Create Dockerfiles**

### **2.1 Dockerfile for Version 1**

Save as `Dockerfile-v1`:

```dockerfile
FROM httpd:2.4
COPY index-v1.html /usr/local/apache2/htdocs/index.html
EXPOSE 80
```

### **2.2 Dockerfile for Version 2**

Save as `Dockerfile-v2`:

```dockerfile
FROM httpd:2.4
COPY index-v2.html /usr/local/apache2/htdocs/index.html
EXPOSE 80
```

---

## **Step 3: Build Docker Images**

Run the following commands in the directory containing the Dockerfiles and HTML files:

```bash
docker build -t apache-html:v1 -f Dockerfile-v1 .
docker build -t apache-html:v2 -f Dockerfile-v2 .
```

Verify the images are built:

```bash
docker images | grep apache-html
```

---

## **Step 4: Run the Containers**

### **4.1 Run Version 1 on Port 8081**

```bash
docker run -d --name apache-v1 -p 8081:80 apache-html:v1
```

### **4.2 Run Version 2 on Port 8082**

```bash
docker run -d --name apache-v2 -p 8082:80 apache-html:v2
```

Check running containers:

```bash
docker ps
```

---

## **Step 5: Test with curl or Browser**

### **5.1 Test Version 1**

```bash
curl http://localhost:8081
```

**Expected Output:**

```html
<h1>Welcome to Apache HTML Index - Version 1</h1>
```

Or open in browser: [http://localhost:8081](http://localhost:8081)

---

### **5.2 Test Version 2**

```bash
curl http://localhost:8082
```

**Expected Output:**

```html
<h1>Welcome to Apache HTML Index - Version 2</h1>
```

Or open in browser: [http://localhost:8082](http://localhost:8082)

---

## **Step 6: Clean Up**

Stop and remove containers after testing:

```bash
docker stop apache-v1 apache-v2
docker rm apache-v1 apache-v2
```

Optionally, remove the images:

```bash
docker rmi apache-html:v1 apache-html:v2
```

---

## **Conclusion**

* Built two custom Docker images based on Apache with different HTML content.
* Used `docker run` to test both versions simultaneously on separate ports.
* Verified content using `curl` and browser for accurate local validation.
* This approach is ideal before pushing to a registry or using in Kubernetes.

```

