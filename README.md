# 🎬 Telegram Kino Bot

Python 3.12+ · aiogram 3 · SQLite. Videolar Telegram `file_id` orqali saqlanadi (serverga yuklanmaydi).

## 1. Tayyorlash
1. **@BotFather** → `/newbot` → token oling.
2. Bosh admin `6222096713` kodga o‘rnatilgan (`config.py`). Boshqa bosh admin kerak bo‘lsa, ID sini **@userinfobot** orqali bilib `.env` ga yozing.
3. `.env.example` ni `.env` deb nusxalab, to‘ldiring:
   ```
   BOT_TOKEN=...            # BotFather tokeni
   ADMIN_IDS=               # ixtiyoriy: qo‘shimcha bosh adminlar (vergul bilan)
   DB_PATH=data/kino_bot.db # baza fayli
   ```

## 2. Lokal ishga tushirish
```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```
Botga `/start`, admin sifatida `/admin` yuboring.

## 3. Hostingga qo‘yish

> ⚠️ **Muhim:** barcha kinolar SQLite faylida (`DB_PATH`) saqlanadi. Hosting qayta ishga tushganda/yangilanganda
> bu fayl o‘chib ketmasligi uchun **doimiy disk (volume)** kerak. Disksiz bepul tariflarda (masalan Render Free)
> baza yo‘qolishi mumkin. Shuning uchun **VPS** yoki **doimiy diskli** tarifni tavsiya qilamiz.
> Zaxira: bot har kuni 00:00 va 12:00 da avtomatik zaxira olib, adminlarga yuboradi (pastdagi 4-bo‘limga qarang).
> Disksiz hostingda yuborilgan fayllarni saqlab qo‘ying va kerak bo‘lsa botdan tiklang.

### A) VPS (Ubuntu) — tavsiya etiladi
```bash
sudo apt update && sudo apt install -y python3.12 python3.12-venv git
sudo useradd -r -m botuser
sudo mkdir -p /opt/kino_bot && sudo chown botuser /opt/kino_bot
# loyiha fayllarini /opt/kino_bot ga yuklang (scp/git), so‘ng:
cd /opt/kino_bot
sudo -u botuser python3.12 -m venv .venv
sudo -u botuser .venv/bin/pip install -r requirements.txt
sudo -u botuser cp .env.example .env && sudo -u botuser nano .env
sudo cp kino-bot.service /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable --now kino-bot
sudo journalctl -u kino-bot -f        # jonli log
```

### B) Docker
```bash
docker build -t kino-bot .
docker run -d --name kino-bot --restart unless-stopped \
  --env-file .env \
  -v kino_data:/app/data -v kino_logs:/app/logs kino-bot   # zaxiralar ham /app/data/backups da
```

### C) Railway / Render / boshqa PaaS
- Start buyrug‘i: `python main.py` (yoki `Procfile` / `Dockerfile` ishlatiladi).
- Environment variables: `BOT_TOKEN`, `ADMIN_IDS`, `DB_PATH` (volume ulangan yo‘lga, masalan `/data/kino_bot.db`).
- Hosting `PORT` bersa, bot avtomatik `/health` sahifasini ochadi — uptime monitor (masalan UptimeRobot) shu manzilni
  har 5 daqiqada tekshirsa, bot uxlab qolmaydi.
- Volume (doimiy disk) ulashni unutmang.

## 4. Admin panel qo‘llanmasi (`/admin`)
- 🎬 **Kino qo‘shish** — kod → nom → poster → video → reyting → tasdiqlash. Kod takrorlanmaydi.
- ✏️ **Tahrirlash / 🗑 O‘chirish** — kino kodi bo‘yicha.
- 📋 **Ro‘yxat**, 📊 **Statistika**, 👥 **Foydalanuvchilar**.
- 📢 **Reklama** — istalgan xabar (matn/rasm/video) barcha foydalanuvchilarga yuboriladi.
- 📡 **Majburiy obuna** — kanal qo‘shing (@username, ID yoki kanaldan forward). **Bot kanalda admin bo‘lishi shart**;
  yopiq kanalda “taklif havolalari yaratish” huquqi ham kerak.
- 👮 **Adminlar** — ID orqali qo‘shish/o‘chirish (`.env` dagi asosiy adminlar o‘chmaydi).
- ⚙️ **Sozlamalar** — botni vaqtincha o‘chirish/yoqish, “Bizning kanal” havolasi.
- 💾 **Zaxira nusxalar**:
  - 📥 *Zaxira olish* — baza nusxasi tayyorlanib, sizga fayl sifatida yuboriladi.
  - ♻️ *Tiklash* — `.db` faylni yuborasiz, bot uni tekshiradi (buzilgan yoki boshqa bot bazasi rad etiladi),
    ichidagi foydalanuvchi/kino sonini ko‘rsatadi, tasdiqlasangiz joriy bazadan avtomatik zaxira olib, so‘ng tiklaydi.
  - 🗂 *Tarix* — so‘nggi 10 ta zaxira: yuklab olish yoki o‘chirish.
  - ⏰ *Avtomatik zaxira* — har kuni **00:00 va 12:00** (O‘zbekiston vaqti), `.env` dagi `ADMIN_IDS` adminlariga yuboriladi.
    Serverda `data/backups/` papkasida saqlanadi (avtomatiklaridan oxirgi 20 tasi qoladi, qo‘lda olinganlar o‘chmaydi).
    Fayl 50 MB dan katta bo‘lsa Telegram yubormaydi, lekin serverda saqlanadi.

## 5. Bilish kerak
- Kino kodini foydalanuvchi to‘g‘ridan-to‘g‘ri botga yozadi (alohida tugma yo‘q).
- Video **video ko‘rinishida** yuborilishi kerak (fayl/hujjat sifatida emas).
- “Bugun” hisoblari O‘zbekiston vaqti (UTC+5) bo‘yicha.
- Xatolar `logs/errors.log`, umumiy log `logs/bot.log` da.
- FSM holatlari xotirada saqlanadi: bot qayta ishga tushsa, jarayondagi admin amali (masalan yarim qo‘shilgan kino)
  bekor bo‘ladi, ma'lumotlar bazasiga tegmaydi.
