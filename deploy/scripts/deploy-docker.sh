#!/usr/bin/env bash
set -euo pipefail

DEPLOY_ROOT="/opt/jintianchisha"
COMPOSE_FILE="${DEPLOY_ROOT}/docker-compose.yml"
LOG_PREFIX="[deploy]"

echo "${LOG_PREFIX} ========== 容器化部署 $(date '+%Y-%m-%d %H:%M:%S') =========="

echo "${LOG_PREFIX} 1. 检查 Docker"
docker --version
docker compose version

echo "${LOG_PREFIX} 2. 创建部署目录"
mkdir -p "${DEPLOY_ROOT}"

echo "${LOG_PREFIX} 3. 拉取最新镜像"
cd "${DEPLOY_ROOT}"
TAG="${1:-latest}"
export TAG
export GITHUB_REPOSITORY_OWNER="${2:-jiangdongshi}"
docker compose pull

echo "${LOG_PREFIX} 4. 启动 (或重启) 容器"
docker compose up -d

echo "${LOG_PREFIX} 5. 清理旧镜像"
docker image prune -f

echo "${LOG_PREFIX} 6. 等待健康检查"
for i in $(seq 1 15); do
    sleep 2
    if curl -s -f http://127.0.0.1:80/health > /dev/null 2>&1; then
        echo "${LOG_PREFIX} 健康检查通过 ✓"
        break
    fi
    echo "${LOG_PREFIX} 等待服务就绪... ($i/15)"
done

echo "${LOG_PREFIX} 7. 当前容器状态"
docker compose ps

echo "${LOG_PREFIX} ========== 完成 =========="
