apiVersion: v1
kind: Pod
metadata:
  name: hostpath-example
spec:
  containers:
  - name: myapp-container
    image: nginx
    volumeMounts:
    - mountPath: /usr/share/nginx/html
      name: hostpath-volume
  volumes:
  - name: hostpath-volume
    hostPath:
      path: /tmp/host-directory
      type: Directory
