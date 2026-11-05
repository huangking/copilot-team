---
name: '基础设施与流水线规则'
description: 'infra/、.github/workflows/、deploy/ 下的安全与变更规则'
applyTo: '{infra/**,.github/workflows/**,deploy/**,Dockerfile*,docker-compose*}'
---

# 基础设施与流水线规则

- 所有 action / 镜像 / 模块固定版本（禁止 `@latest`、浮动 tag）。
- 权限最小化：workflow 顶层只给 `contents: read`，需要时按 job 提升。
- 密钥只从 secrets / OIDC 取；不回显、不写文件、不进日志。
- 生产变更必须先有 `plan` / `diff` / staging 验证结果。
- 每个部署步骤都要有对应回滚步骤。
- 一次 PR 只做一类基础设施变更；数据库迁移与应用发布分开。
- 变更后更新 `docs/releases/<id>.md` 的影响面与观测项。
