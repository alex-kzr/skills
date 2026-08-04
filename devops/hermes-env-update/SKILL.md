---
name: hermes-env-update
description: Обновление env переменных в контейнере Hermes с автоматическим пересозданием
tags: [docker, env, hermes, compose, restart]
---

# Навык: Обновление env переменных в контейнере Hermes

## Когда использовать
- Нужно добавить/обновить переменные окружения в контейнере hermes
- Изменили `.env` или `docker-compose.yml` в `/services/hermes/compose/`
- Добавили новые переменные в compose-конфигурацию

## Ключевой insight
`docker restart` **НЕ подтягивает** изменения из `docker-compose.yml` — он перезапускает контейнер с существующим env. Для применения новых переменных нужен **полный пересозд** контейнера.

## Процедура

### 1. Проверка текущих env
```bash
docker exec hermes env | grep AGENT_
```

### 2. Обновление docker-compose.yml
Добавить переменную в секцию `environment:` сервиса `hermes`:
```bash
docker exec hermes sed -i '/AGENT_GITHUB_PASS=${AGENT_GITHUB_PASS:-}/a\\      - AGENT_GITHUB_TOKEN=${AGENT_GITHUB_TOKEN:-}' /services/hermes/compose/docker-compose.yml
```

### 3. Проверка .env
```bash
docker exec hermes cat /services/hermes/compose/.env | grep AGENT_GITHUB_TOKEN
```

### 4. Пересоздание контейнера
Важно: использовать полный пересозд, а не docker restart

#### Вариант A: Через docker compose (если доступен)
```bash
cd /services/hermes/compose
docker compose down
docker compose up -d
```

#### Вариант B: Вручную (как было сделано на практике)
```bash
# Получить текущую конфигурацию
docker inspect hermes --format '{{range .Config.Env}}{{println .}}{{end}}' | sort
docker inspect hermes --format '{{json .Mounts}}' | jq

# Остановить и переименовать (для отката)
docker stop hermes
docker rename hermes hermes-old

# Создать новый контейнер с полным набором env
docker run -d \
  --name hermes \
  --restart unless-stopped \
  --network proxy \
  --group-add 988 \
  -e HERMES_HOME=/hermes \
  -e HERMES_DASHBOARD_BASE_URL=https://hermes.smartbits.pro \
  -e HERMES_TRUST_PROXY_HEADERS=1 \
  -e DOCKER_HOST=unix:///var/run/docker.sock \
  -e HERMES_SERVICES_ROOT=/services \
  -e AGENT_EMAIL=the.loop@smartbits.pro \
  -e AGENT_EMAIL_PASS=C9p2a7zaRWZsYNF \
  -e AGENT_EMAIL_HOST=mail.smartbits.pro \
  -e AGENT_GITHUB=the.loop@smartbits.pro \
  -e AGENT_GITHUB_PASS=3OpaU66LUca@9 \
  -e AGENT_GITHUB_TOKEN=*** \
  -v /root/services/hermes/data/hermes:/hermes \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /root/services:/services \
  --label traefik.enable=true \
  --label traefik.docker.network=proxy \
  --label 'traefik.http.routers.hermes.rule=Host(`hermes.smartbits.pro`)' \
  --label traefik.http.routers.hermes.entrypoints=websecure \
  --label traefik.http.routers.hermes.tls=true \
  --label traefik.http.routers.hermes.tls.certresolver=le \
  --label traefik.http.routers.hermes.middlewares=hermes-auth,hermes-secure-headers,hermes-proto-header \
  --label "traefik.http.middlewares.hermes-auth.basicauth.users=${HERMES_AUTH_USERS}" \
  --label traefik.http.services.hermes.loadbalancer.server.port=9119 \
  --label traefik.http.services.hermes.loadbalancer.passHostHeader=true \
  --label 'traefik.http.middlewares.hermes-proto-header.headers.customRequestHeaders.X-Forwarded-Proto=https' \
  --label 'traefik.http.middlewares.hermes-proto-header.headers.customRequestHeaders.X-Forwarded-Port=443' \
  --label traefik.http.middlewares.hermes-secure-headers.headers.contentSecurityPolicy=upgrade-insecure-requests \
  --label traefik.http.middlewares.hermes-secure-headers.headers.stsSeconds=31536000 \
  --label traefik.http.middlewares.hermes-secure-headers.headers.stsIncludeSubdomains=true \
  --label traefik.http.middlewares.hermes-secure-headers.headers.stsPreload=true \
  --label traefik.http.middlewares.hermes-secure-headers.headers.forceSTSHeader=true \
  hermes:latest
```

### 5. Проверка результата
```bash
# Статус контейнера
docker ps --filter name=hermes

# Проверка новых переменных
docker exec hermes env | grep AGENT_GITHUB_TOKEN

# Логи
docker logs hermes --tail 20
```

## Pitfalls

1. **docker restart НЕ работает** — контейнер перезапускается со старым env, изменения из docker-compose.yml игнорируются

2. **Потеря контейнера при пересоздании** — всегда переименовывайте старый контейнер (hermes-old) для возможности отката

3. **Неполный список env переменных** — при docker run обязательно переносите ВСЕ переменные из inspect, иначе что-то сломается

4. **Labels для Traefik** — не забудьте все labels, иначе контейнер не будет доступен через HTTPS

5. **Volumes** — обязательно подключайте все те же volumes, иначе потеряются данные

6. **Network** — контейнер должен быть в сети `proxy` для работы Traefik

7. **Group add** — параметр `--group-add 988` нужен для доступа к Docker socket изнутри контейнера

8. **GLM_BASE_URL обязателен для Z.AI** — без этой переменной Hermes запускает `detect_zai_endpoint()` на каждое сообщение: синхронный HTTP-проб до 4 endpoints × 4 модели × 8с таймаут. При падении Z.AI API (429) event loop зависает → Discord heartbeat blocked → s6-supervise SIGTERM → бесконечный restart loop. Всегда добавляйте:
   ```
   GLM_BASE_URL=https://api.z.ai/api/coding/paas/v4
   ```
   Подробности: `ag-hermes-deploy` skill → references/zai-endpoint-probe-restart-loop.md

## Откат в случае проблем

```bash
# Остановить новый контейнер
docker stop hermes
docker rm hermes

# Вернуть старый
docker rename hermes-old hermes
docker start hermes
```

## Автоматизация (скрипт)

Создайте скрипт `~/scripts/hermes-update-env.sh`:
```bash
#!/bin/bash
set -e

echo "=== 1. Проверка текущих env ==="
docker exec hermes env | grep AGENT_

echo "=== 2. Остановка и переименование ==="
docker stop hermes
docker rename hermes hermes-old

echo "=== 3. Создание нового контейнера ==="
docker run -d \
  --name hermes \
  --restart unless-stopped \
  --network proxy \
  --group-add 988 \
  -e HERMES_HOME=/hermes \
  -e HERMES_DASHBOARD_BASE_URL=https://hermes.smartbits.pro \
  -e HERMES_TRUST_PROXY_HEADERS=1 \
  -e DOCKER_HOST=unix:///var/run/docker.sock \
  -e HERMES_SERVICES_ROOT=/services \
  -e AGENT_EMAIL=the.loop@smartbits.pro \
  -e AGENT_EMAIL_PASS=C9p2a7zaRWZsYNF \
  -e AGENT_EMAIL_HOST=mail.smartbits.pro \
  -e AGENT_GITHUB=the.loop@smartbits.pro \
  -e AGENT_GITHUB_PASS=3OpaU66LUca@9 \
  -e AGENT_GITHUB_TOKEN=*** \
  -v /root/services/hermes/data/hermes:/hermes \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /root/services:/services \
  --label traefik.enable=true \
  --label traefik.docker.network=proxy \
  --label 'traefik.http.routers.hermes.rule=Host(`hermes.smartbits.pro`)' \
  --label traefik.http.routers.hermes.entrypoints=websecure \
  --label traefik.http.routers.hermes.tls=true \
  --label traefik.http.routers.hermes.tls.certresolver=le \
  --label traefik.http.routers.hermes.middlewares=hermes-auth,hermes-secure-headers,hermes-proto-header \
  --label "traefik.http.middlewares.hermes-auth.basicauth.users=${HERMES_AUTH_USERS}" \
  --label traefik.http.services.hermes.loadbalancer.server.port=9119 \
  --label traefik.http.services.hermes.loadbalancer.passHostHeader=true \
  --label 'traefik.http.middlewares.hermes-proto-header.headers.customRequestHeaders.X-Forwarded-Proto=https' \
  --label 'traefik.http.middlewares.hermes-proto-header.headers.customRequestHeaders.X-Forwarded-Port=443' \
  --label traefik.http.middlewares.hermes-secure-headers.headers.contentSecurityPolicy=upgrade-insecure-requests \
  --label traefik.http.middlewares.hermes-secure-headers.headers.stsSeconds=31536000 \
  --label traefik.http.middlewares.hermes-secure-headers.headers.stsIncludeSubdomains=true \
  --label traefik.http.middlewares.hermes-secure-headers.headers.stsPreload=true \
  --label traefik.http.middlewares.hermes-secure-headers.headers.forceSTSHeader=true \
  hermes:latest

echo "=== 4. Проверка ==="
sleep 5
docker ps --filter name=hermes
docker exec hermes env | grep AGENT_GITHUB_TOKEN

echo "=== Готово! ==="
echo "Старый контейнер: hermes-old"
echo "Для отката: docker stop hermes && docker rm hermes && docker rename hermes-old hermes && docker start hermes"
```