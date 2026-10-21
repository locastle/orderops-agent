# Windows 环境脚本

这台机器上的两个 Docker 环境问题，以及对应的绕过方式。脚本放在仓库里是为了让"我为什么这么写"可追溯。

## 1. `docker-start.ps1` —— 清理残留 socket 再启动

**现象**：Docker Desktop 4.37.1 启动后自毁，弹出错误并触发"恢复出厂设置"，把 `docker-desktop` 发行版和镜像数据一起清掉。

**根因**：后端启动时会在 `%LOCALAPPDATA%\Docker\run` 删一个上次遗留的 `userAnalyticsOtlpHttp.sock`。这个 socket 是 Linux 侧创建的，Windows 无法识别（错误 1920），所以删除永远失败，后端随即退出。

**绕过**：Windows 删不掉，就从 WSL 侧删（`wsl --system -- /bin/rm`），再启动 Docker Desktop。

```powershell
powershell -ExecutionPolicy Bypass -File scripts/docker-start.ps1
```

## 2. `pull-images.ps1` —— 走镜像源拉基础镜像

**现象**：`docker pull pgvector/pgvector:pg16` 连接 `registry-1.docker.io` 超时。

**根因**：本机网络直连 Docker Hub 不通；而且 Docker Desktop 每次启动都会重写 `~/.docker/daemon.json`（日志里有 rename/restore 记录），所以在里面配 `registry-mirrors` 会被丢掉。

**绕过**：用镜像前缀拉取，再打回原始标签，Docker 就直接用本地镜像，不再访问 Docker Hub。

```powershell
powershell -ExecutionPolicy Bypass -File scripts/pull-images.ps1
```

实测可用镜像：`docker.m.daocloud.io`（`docker.1ms.run` 作为备选）。

## 3. 对项目的影响

- 代码里不写死镜像源，Dockerfile 仍用官方 `python:3.12-slim`，换网络环境时不用改代码。
- CI（GitHub Actions）有独立网络，不需要这些脚本。
