# 🎮 GPU Cloud Server — Cloud Gaming + Treo Bot trên Kaggle / Google Colab

<a href="https://colab.research.google.com/github/tiendatmeow-source/cloud-gaming-gpu/blob/main/cloud_gpu_server.ipynb"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/></a>
<a href="https://www.kaggle.com/kernels/welcome?src=https%3A%2F%2Fgithub.com%2Ftiendatmeow-source%2Fcloud-gaming-gpu%2Fblob%2Fmain%2Fcloud_gpu_server.ipynb"><img src="https://img.shields.io/badge/Open%20in%20Kaggle-20BEFF?logo=kaggle&logoColor=white" alt="Open In Kaggle"/></a>
<a href="https://tiendatmeow-source.github.io/cloud-gaming-gpu/"><img src="https://img.shields.io/badge/🌐_Landing_Page-8b5cf6?logo=githubpages&logoColor=white" alt="Landing Page"/></a>
<img src="https://img.shields.io/badge/Cloudflare_Tunnel-✔-f6821f?logo=cloudflare&logoColor=white"/>

Biến notebook Kaggle/Google Colab thành **máy chủ GPU đám mây hoàn chỉnh trong trình duyệt**:

- 🖥️ **Cloud Gaming / Cloud Desktop** — desktop XFCE ảo trên GPU VM, mở trong trình duyệt qua noVNC, cài Steam/Wine và chơi game ngay
- 🤖 **Treo bot** — upload script Python (Discord, Telegram, Twitter, …) + token env, Start/Stop, xem log realtime
- ⌨️ **Web Terminal** — bash đầy đủ trên VM qua ttyd
- 📊 **Dashboard realtime** — GPU / CPU / RAM / Disk / uptime, tự làm mới
- 📁 **File manager** — upload / download / xoá file trên VM
- ⚡ **Hành động nhanh** — 1 click cài Steam, Wine, Firefox, discord.py, …
- ☁️ **Cloudflare Tunnel** — URL public `https://xxx.trycloudflare.com`, không cần domain, không cần config

```
┌─────────────── Kaggle / Google Colab (GPU VM) ────────────────┐
│  Xvfb desktop → x11vnc → noVNC  :6080 ──┐                     │
│  ttyd web terminal              :7681 ──┼─► cloudflared ×3 ───┼──► https://xxx.trycloudflare.com
│  Dashboard aiohttp              :8080 ──┘    (3 tunnel riêng) │
└───────────────────────────────────────────────────────────────┘
```

## ⚡ Chạy ngay (2 ô code, ~3 phút)

1. **Mở notebook** — bấm badge *Open in Colab* / *Open in Kaggle* phía trên, hoặc tải `cloud_gpu_server.ipynb` rồi mở thủ công.
   - Colab: chọn **GPU runtime** (`Runtime → Change runtime type → GPU`)
   - Kaggle: bật **Internet** + chọn **Accelerator: GPU** trong Settings, rồi bấm *Save version* để chạy
2. **Chạy ô Bước 1** — auto-setup mọi thứ (apt + pip + cloudflared + ttyd).
3. **Chạy ô Bước 2** — khởi động server, đợi in ra 3 URL public. **Giữ ô này chạy!**
4. Mở **Dashboard URL** (kèm `?key=…`) trên máy bạn → chơi game, treo bot, dùng terminal…

> 📥 Tải notebook trực tiếp: [`cloud_gpu_server.ipynb`](https://raw.githubusercontent.com/tiendatmeow-source/cloud-gaming-gpu/main/cloud_gpu_server.ipynb)

## 🤖 Ví dụ treo bot

**Discord** — upload file này ở tab 🤖 Bots, điền Env `DISCORD_TOKEN=xxx` rồi Start:

```python
import os, discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print("✅ Đã đăng nhập:", bot.user)

@bot.command()
async def ping(ctx):
    await ctx.send("🏓 Pong! GPU server vẫn sống.")

bot.run(os.environ["DISCORD_TOKEN"])
```

**Telegram** — Env `TELEGRAM_TOKEN=xxx`:

```python
import os, telebot
bot = telebot.TeleBot(os.environ["TELEGRAM_TOKEN"])

@bot.message_handler(commands=["ping"])
def ping(m):
    bot.reply_to(m, "🏓 Pong từ GPU server!")

bot.infinity_polling()
```

*(cài thư viện bằng nút ⚡ "pip discord.py" / "pip telegram" ở tab Cloud Gaming, hoặc Web Terminal)*

## 🎮 Cloud Gaming — hướng dẫn

1. Tab **Cloud Gaming** → nút **🖥️ Mở Cloud Desktop** (mở noVNC trong tab mới)
2. Trong desktop: bấm nút **Cài Steam** trên dashboard (hoặc chạy `apt install steam`) → đăng nhập → chơi
3. Mẹo mượt: giảm độ phân giải desktop xuống 1280×720, chơi game nhẹ/emulator; noVNC truyền ảnh qua mạng nên game AAA sẽ lag — đây là cloud **desktop**, không phải cloud streaming độ trễ thấp kiểu Moonlight

## 🔐 Bảo mật

- Dashboard yêu cầu **Access Key** trong URL (`?key=…`), tự lưu cookie 7 ngày
- Desktop/Terminal là tunnel riêng không có key → **đừng chia sẻ URL công khai**
- Token bot nằm trong file `.env` cạnh script, không in ra log
- URL trycloudflare là tạm thời — mỗi phiên chạy có URL mới

## ⏱️ Giới hạn & ⚠️ Disclaimer

| Nền tảng | GPU | Giới hạn phiên |
|---|---|---|
| Google Colab (free) | T4 16GB | ~3–12h, ngắt khi idle |
| Kaggle | T4 x2 / P100 | ~9–12h/phiên, ~30h/tuần |

- Đây là dự án **giáo dục/thử nghiệm**. Chạy game, remote desktop và bot nền dài hạn **có thể vi phạm Terms of Service** của Google Colab và Kaggle — tài khoản của bạn tự chịu rủi ro. Hãy dùng có trách nhiệm.
- NoVNC không truyền âm thanh. Không passthrough GPU 3D thật vào desktop (render bằng LLVMpipe) — GPU dùng tốt nhất cho AI/compute; game 2D nhẹ chạy ổn.

## 🛠️ Troubleshooting

| Vấn đề | Cách xử lý |
|---|---|
| Ô Bước 1 báo Offline | Kaggle: Settings → Internet → ON rồi chạy lại |
| Không in ra URL tunnel | Đợi thêm ~30s; xem log `~/gpu_server/*.log`; trycloudflare đôi khi chậm |
| Desktop đen thui | Thử nút ↻ trong noVNC; kiểm tra `~/gpu_server/xfce4.log` |
| Bot start lập tức exit | Xem 📜 Logs — thường là thiếu token/env hoặc sai thư viện |
| Colab ngắt kết nối | Giữ tab mở, ô Bước 2 đang chạy; có thử nghiệm "auto-reconnect" của trình duyệt |

## 💻 Chạy ở local (không cần Colab)

```bash
pip install aiohttp
python dashboard.py            # mở http://localhost:8080
```

## 📄 License

MIT — xem [LICENSE](LICENSE).
