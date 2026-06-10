#!/usr/bin/env bash
set -euo pipefail

DEPLOY_ROOT="/var/www/jintianchisha"
BACKEND_DIR="${DEPLOY_ROOT}/backend"
FRONTEND_DIR="${DEPLOY_ROOT}/frontend"
SERVICE_NAME="jintianchisha"
LOG_PREFIX="[deploy]"

echo "${LOG_PREFIX} ========== 开始部署 $(date '+%Y-%m-%d %H:%M:%S') =========="

echo "${LOG_PREFIX} 1. 创建必要目录"
mkdir -p "${DEPLOY_ROOT}"
mkdir -p "${FRONTEND_DIR}/dist"
mkdir -p /var/lib/jintianchisha
chown -R www-data:www-data /var/lib/jintianchisha || true

echo "${LOG_PREFIX} 2. 检查 Python 版本"
if ! command -v python3.11 &> /dev/null; then
    if command -v python3 &> /dev/null; then
        PYTHON_BIN="python3"
    else
        echo "::error::未找到 Python 3，请先安装 Python 3.11+"
        exit 1
    fi
else
    PYTHON_BIN="python3.11"
fi
echo "${LOG_PREFIX} 使用 ${PYTHON_BIN}"

echo "${LOG_PREFIX} 3. 创建/更新后端虚拟环境"
cd "${BACKEND_DIR}"
if [ ! -d ".venv" ]; then
    ${PYTHON_BIN} -m venv .venv
fi
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

echo "${LOG_PREFIX} 4. 校验后端语法"
python -m compileall -q app

echo "${LOG_PREFIX} 5. 复制前端资源到 nginx 根目录"
mkdir -p "${FRONTEND_DIR}/dist"
# 前端文件已由 rsync 推送到 ${FRONTEND_DIR}/dist
chown -R www-data:www-data "${FRONTEND_DIR}" || true
chmod -R 755 "${FRONTEND_DIR}" || true

echo "${LOG_PREFIX} 6. 安装 systemd service 文件（如需要则复制）"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
if [ -f "${DEPLOY_ROOT}/deploy/config/${SERVICE_NAME}.service" ]; then
    cp "${DEPLOY_ROOT}/deploy/config/${SERVICE_NAME}.service" "${SERVICE_FILE}"
    systemctl daemon-reload
fi

echo "${LOG_PREFIX} 7. 重启后端服务"
systemctl restart "${SERVICE_NAME}.service"
sleep 2

echo "${LOG_PREFIX} 8. 检查服务状态"
systemctl status "${SERVICE_NAME}.service" --no-pager || true

echo "${LOG_PREFIX} 9. 健康检查"
sleep 2
if curl -s -f http://127.0.0.1:8000/health > /dev/null; then
    echo "${LOG_PREFIX} 服务健康检查通过"
else
    echo "${LOG_PREFIX} ::warning::服务健康检查失败，请手动查看日志 journalctl -u ${SERVICE_NAME}.service -n 50"
fi

echo "${LOG_PREFIX} ========== 部署完成 $(date '+%Y-%m-%d %H:%M:%S') =========="
