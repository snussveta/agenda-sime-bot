#!/bin/bash
set -e

echo "=========================================="
echo "🚀 Agenda SIME MD - Deployment Script"
echo "=========================================="

# 1. Check Root / Sudo
if [ "$EUID" -ne 0 ]; then
  echo "⚠️ Пожалуйста, запустите скрипт с sudo:"
  echo "sudo bash deploy.sh"
  exit 1
fi

# 2. Check and Install Docker if missing
if ! command -v docker &> /dev/null; then
    echo "📦 Установка Docker и Docker Compose..."
    apt-get update
    apt-get install -y ca-certificates curl gnupg lsb-release
    mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    systemctl enable docker
    systemctl start docker
    echo "✅ Docker успешно установлен."
fi

# 3. Fix Oracle Cloud Firewall (iptables)
echo "🛡️ Настройка портов 80 и 443 для Oracle Cloud..."
if command -v iptables &> /dev/null; then
    iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT 2>/dev/null || iptables -A INPUT -p tcp --dport 80 -j ACCEPT
    iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT 2>/dev/null || iptables -A INPUT -p tcp --dport 443 -j ACCEPT
    
    # Save iptables if iptables-persistent exists
    if command -v netfilter-persistent &> /dev/null; then
        netfilter-persistent save
    fi
fi

if command -v ufw &> /dev/null; then
    ufw allow 80/tcp
    ufw allow 443/tcp
fi

# 4. Check .env file
if [ ! -f .env ]; then
    echo "⚠️ Файл .env не найден! Создаем из .env.example..."
    cp .env.example .env
    # Generate random secret key
    RAND_SECRET=$(openssl rand -hex 16 2>/dev/null || echo "random_secret_$(date +%s)")
    sed -i "s/generate_random_secret_string_here_32_chars/$RAND_SECRET/" .env
    echo "❗ ВНИМАНИЕ: Отредактируйте .env перед запуском:"
    echo "   nano .env"
    echo "   (Укажите ваш BOT_TOKEN и DOMAIN)"
    exit 0
fi

# 5. Create data folder
mkdir -p data

# 6. Build and Run Containers
echo "🐳 Запуск контейнеров через Docker Compose..."
docker compose pull || true
docker compose up -d --build

echo ""
echo "=========================================="
echo "✅ Приложение успешно развернуто и запущено!"
echo "=========================================="
echo "Проверить статус:   docker compose ps"
echo "Посмотреть логи:     docker compose logs -f"
echo "Остановить:          docker compose down"
echo "=========================================="
