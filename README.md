# 📱 Agenda SIME MD — Telegram Bot & Mini App

Полнофункциональный Telegram-бот и интерактивный Telegram Mini App для электронного дневника Молдовы [agenda.sime.md](https://agenda.sime.md).

## ✨ Возможности
* 🔐 **Простой вход:** пользователь отправляет логин и пароль прямо в диалог с ботом. Сообщение с паролем автоматически удаляется из чата, а пароль шифруется в базе данных (AES-256).
* 📱 **Интерактивный Mini App:**
  * 📊 Вкладка **Оценки** с автоматическим расчетом среднего балла по каждому предмету и общему баллу.
  * 📝 Вкладка **Домашка** с удобными чекбоксами выполненных заданий.
  * 📅 Вкладка **Расписание** с кабинетами, временем и преподавателями.
  * 👤 Вкладка **Профиль** со статистикой посещаемости и уважительных/неуважительных пропусков.
* 🔔 **Умные Push-уведомления:** бот в фоновом режиме отслеживает появление новых оценок и домашних заданий и мгновенно присылает сообщение в Telegram.
* ⚡️ **Оптимизация и безопасность:** кэширование запросов, чтобы не создавать лишнюю нагрузку на сервер `agenda.sime.md` и предотвратить блокировку IP.

---

## 🛠️ Стек технологий
* **Backend:** Python 3.12, FastAPI, Aiogram 3 (Telegram Bot), aiohttp, BeautifulSoup4, SQLite (WAL-mode), Cryptography.
* **Frontend:** React 18, Vite, Tailwind CSS, Lucide Icons, Telegram WebApp SDK.
* **DevOps / Proxy:** Docker, Docker Compose, Caddy (автоматический бесплатный SSL Let's Encrypt).

---

## 🚀 Быстрое развертывание на сервере Oracle Cloud (Ubuntu / Oracle Linux)

### Шаг 1: Создание инстанса в Oracle Cloud Always Free
1. В консоли Oracle Cloud перейдите в **Compute -> Instances -> Create Instance**.
2. Выберите образ **Ubuntu 22.04 / 24.04** (или Oracle Linux).
3. Форм-фактор: подойдет как **VM.Standard.E2.1.Micro** (AMD), так и **VM.Standard.A1.Flex** (ARM Ampere).
4. Обязательно сохраните свой SSH-ключ.

### Шаг 2: Открытие портов 80 и 443 в панели Oracle Cloud
1. В деталях инстанса нажмите на вашу подсеть (**Subnet**).
2. Перейдите в **Default Security List for...**.
3. В **Ingress Rules** добавьте 2 правила:
   * **Source CIDR:** `0.0.0.0/0`
   * **IP Protocol:** `TCP`
   * **Destination Port Range:** `80`
   * Второе правило для порта `443`.

---

### Шаг 3: Настройка Telegram-бота
1. В Telegram перейдите к [@BotFather](https://t.me/BotFather) и создайте бота командой `/newbot`.
2. Скопируйте полученный **Bot Token**.
3. Настройте кнопку WebApp в меню бота:
   * В `@BotFather` вызовите команду `/mybots` -> выберите вашего бота -> **Bot Settings** -> **Menu Button** -> **Configure menu button**.
   * Введите URL вашего приложения: `https://your-domain.com/app` (или через команду `/newapp`).

---

### Шаг 4: Клонирование репозитория и запуск на сервере
Подключитесь к вашему серверу по SSH и выполните команды:

```bash
# 1. Клонируйте ваш репозиторий
git clone <URL_ВАШЕГО_РЕПОЗИТОРИЯ> agenda-bot
cd agenda-bot

# 2. Создайте файл настроек .env
cp .env.example .env
nano .env
```

Заполните три главные переменные в `.env`:
```env
BOT_TOKEN=123456789:ABCDefGhIJKlmNoPQRsTUVwxyZ
DOMAIN=sime.yourdomain.com
MINI_APP_URL=https://sime.yourdomain.com/app
```

> **Совет, если у вас нет своего домена:**
> Вы можете использовать бесплатный DNS от [DuckDNS](https://www.duckdns.org) или `nip.io` (например, `123.45.67.89.nip.io`, где вместо цифр — публичный IP вашего сервера Oracle). Caddy автоматически выпустит бесплатный SSL-сертификат!

### Шаг 5: Запуск в 1 команду
```bash
sudo bash deploy.sh
```
Скрипт сам:
* Установит Docker и Docker Compose (если они еще не установлены).
* Настроит системный фаервол `iptables` и `ufw` под Oracle Cloud.
* Соберет и запустит контейнеры приложения и Caddy.

---

## 🔧 Полезные команды управления
```bash
# Проверить статус контейнеров
docker compose ps

# Посмотреть живые логи бота
docker compose logs -f app

# Перезапустить проект
docker compose restart

# Остановить
docker compose down
```

---

## 🧪 Локальное тестирование без сервера
Вы можете протестировать вход в SIME прямо на своем компьютере:
```bash
python test_local_auth.py
```
Скрипт запросит логин и пароль и покажет выгруженные оценки и расписание.
