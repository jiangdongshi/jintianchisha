# 一键应用到 K8s 集群

```bash
# 1. 创建命名空间
kubectl apply -f namespace.yaml

# 2. 创建 GHCR 拉取密钥 (替换为你的 GitHub PAT)
kubectl create secret docker-registry ghcr-pull-secret \
  --namespace jintianchisha \
  --docker-server=ghcr.io \
  --docker-username=jiangdongshi \
  --docker-password=YOUR_GITHUB_PAT \
  --docker-email=your@email.com

# 3. 创建密钥 (替换为你的密钥)
# 编辑 k8s/backend.yaml 中的 stringData 后 apply
kubectl apply -f backend.yaml

# 4. 应用前端
kubectl apply -f frontend.yaml

# 5. 查看状态
kubectl get all -n jintianchisha
```
