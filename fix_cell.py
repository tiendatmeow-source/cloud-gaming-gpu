#@title 🩺 SỬA NHANH · Chẩn đoán + cài thiếu + khởi động lại toàn bộ server { display-mode: "form" }
# ══ Dùng khi: Cloud Gaming không có tunnel / Desktop đen / thiếu dịch vụ ══
# CÁCH DÙNG: ① Interrupt (■) ô Bước 2 đang chạy  →  ② chạy ô này  →  ③ dùng URL MỚI in ra dưới đây.
import os, sys, json, time, re, shutil, socket, subprocess, threading, secrets, pathlib
import importlib.util, platform, urllib.request, zipfile
from collections import deque

HOME = pathlib.Path.home()
GDIR, BDIR, LDIR = HOME / "gpu_server", HOME / "bots", HOME / "bot_logs"
for d in (GDIR, BDIR, LDIR):
    d.mkdir(parents=True, exist_ok=True)
LOCAL_BIN = str(HOME / ".local" / "bin")
pathlib.Path(LOCAL_BIN).mkdir(parents=True, exist_ok=True)
os.environ["PATH"] = LOCAL_BIN + os.pathsep + os.environ.get("PATH", "")
root = os.geteuid() == 0
SUDO = "" if (root or not shutil.which("sudo")) else "sudo -n "

PORT_DASH, PORT_NOVNC, PORT_TTYD, DISPLAY = 8080, 6080, 7681, ":1"
TUNNELS_FILE = pathlib.Path("/tmp/tunnels.json")
TUNNELS, PROCS = {}, []
TL = threading.Lock()

def sh(cmd, timeout=None):
    p = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    return p.returncode, ((p.stdout or "") + (p.stderr or ""))

def have(c): return shutil.which(c) is not None

def port_open(port, timeout=0.5):
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=timeout):
            return True
    except OSError:
        return False

def wait_port(port, timeout=25):
    t0 = time.time()
    while time.time() - t0 < timeout:
        if port_open(port):
            return True
        time.sleep(0.4)
    return False

def kill_matching(needles):
    me = os.getpid()
    for d in pathlib.Path("/proc").iterdir():
        if not d.name.isdigit() or int(d.name) == me:
            continue
        try:
            cmd = (d / "cmdline").read_bytes().decode("utf-8", "ignore").replace("\x00", " ")
        except Exception:
            continue
        if any(n in cmd for n in needles):
            try:
                os.kill(int(d.name), 15)
            except Exception:
                pass

def comp(label, ok, extra=""):
    print(f"  {'✅' if ok else '❌'} {label}" + (f" — {extra}" if extra else ""))

def spawn(args, name, gui=False, extra_env=None):
    env = dict(os.environ)
    if gui:
        env["DISPLAY"] = DISPLAY
    if extra_env:
        env.update(extra_env)
    logf = GDIR / f"{name}.log"
    lf = open(logf, "ab", buffering=0)
    lf.write(f"\n══════ ▶ {name} · {time.strftime('%H:%M:%S')} ══════\n".encode())
    p = subprocess.Popen([str(a) for a in args], stdout=lf, stderr=subprocess.STDOUT,
                         stdin=subprocess.DEVNULL, env=env, start_new_session=True)
    PROCS.append(p)
    print(f"  ▶ {name:<11} pid={p.pid:<6} log={logf}")
    return p

def save_tunnels():
    try:
        with TL:
            TUNNELS_FILE.write_text(json.dumps(TUNNELS))
    except Exception:
        pass

def start_tunnel(label, port, attempts=2):
    cf = shutil.which("cloudflared")
    if not cf:
        print(f"  ⚠️ [{label}] thiếu cloudflared")
        return
    tail = deque(maxlen=10)
    for attempt in range(1, attempts + 1):
        found = threading.Event()
        p = subprocess.Popen([cf, "tunnel", "--url", f"http://localhost:{port}",
                              "--no-autoupdate", "--protocol", "http2"],
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             text=True, bufsize=1, start_new_session=True)
        PROCS.append(p)
        def reader(p=p, found=found, tail=tail):
            for line in p.stdout:
                tail.append(line.rstrip())
                m = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", line)
                if m:
                    with TL:
                        TUNNELS[label] = m.group(0)
                    save_tunnels()
                    found.set()
        threading.Thread(target=reader, daemon=True).start()
        if found.wait(25) and TUNNELS.get(label):
            print(f"  🌐 [{label}] {TUNNELS[label]}")
            return
        try:
            p.terminate()
        except Exception:
            pass
        if attempt < attempts:
            print(f"  ⚠️ [{label}] lần {attempt} chưa tạo được URL — thử lại…")
            time.sleep(2)
    print(f"  ❌ [{label}] không tạo được tunnel sau {attempts} lần. Log cuối:")
    for l in list(tail)[-6:]:
        print("      " + l[:150])

TOKEN = None
try:
    TOKEN = json.loads((GDIR / "server_info.json").read_text()).get("token")
except Exception:
    pass
TOKEN = TOKEN or secrets.token_hex(8)

# ═══════════ 1. CHẨN ĐOÁN ═══════════
print("🔍 CHẨN ĐOÁN THÀNH PHẦN")
WS_BIN = have("websockify")
WS_MOD = importlib.util.find_spec("websockify") is not None
NOVNC_WEB = ("/usr/share/novnc" if os.path.isdir("/usr/share/novnc")
             else (str(HOME / "novnc") if (HOME / "novnc").is_dir() else None))
ok_xvfb, ok_vnc = have("Xvfb"), have("x11vnc")
ok_gui = have("startxfce4") or have("xterm")
comp("Xvfb (desktop ảo)", ok_xvfb)
comp("x11vnc (VNC server)", ok_vnc)
comp("websockify (VNC → web)", WS_BIN or WS_MOD,
     "" if WS_BIN else ("module pip (không có binary)" if WS_MOD else "thiếu hoàn toàn"))
comp("noVNC (web client)", NOVNC_WEB is not None, NOVNC_WEB or "")
comp("XFCE / xterm", ok_gui)
comp("ttyd (web terminal)", have("ttyd"))
comp("cloudflared (tunnel)", have("cloudflared"))

# ═══════════ 2. CÀI THIẾU ═══════════
need_apt = not (ok_xvfb and ok_vnc and ok_gui and NOVNC_WEB and (WS_BIN or WS_MOD))
if need_apt and have("apt-get"):
    pkgs = [n for n, ok in [("xvfb", ok_xvfb), ("x11vnc", ok_vnc), ("novnc", NOVNC_WEB is None),
                            ("websockify", not (WS_BIN or WS_MOD)),
                            ("dbus-x11", not have("dbus-run-session")),
                            ("x11-xserver-utils", not have("xsetroot")),
                            ("xterm", not have("xterm")), ("xfce4", not have("startxfce4")),
                            ("xfce4-terminal", not have("xfce4-terminal"))] if not ok]
    print(f"\n📦 apt cài: {' '.join(pkgs)} (có thể mất vài phút)")
    rc, out = sh(f"{SUDO}DEBIAN_FRONTEND=noninteractive apt-get update -y", timeout=300)
    if rc != 0:
        print("  ⚠️ apt-get update lỗi (log cuối):\n" +
              "\n".join("    " + l for l in out.strip().splitlines()[-8:]))
    rc, out = sh(f"{SUDO}DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends {' '.join(pkgs)}",
                 timeout=1500)
    if rc != 0:
        print("  ⚠️ Cài cả list bị lỗi — thử từng gói để tìm thủ phạm:")
        for pkg in pkgs:
            rc2, out2 = sh(f"{SUDO}DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends {pkg}",
                           timeout=600)
            print(f"    {'✅' if rc2 == 0 else '❌'} {pkg}")
            if rc2 != 0:
                print("\n".join("       " + l for l in out2.strip().splitlines()[-5:]))

if not have("websockify") and not WS_MOD:
    print("\n🐍 pip fallback: websockify")
    sh(f"{sys.executable} -m pip install -q websockify", timeout=300)
    WS_MOD = importlib.util.find_spec("websockify") is not None
    print(f"  {'✅' if WS_MOD else '❌'} websockify module pip")

if not os.path.isdir("/usr/share/novnc") and not (HOME / "novnc").is_dir():
    print("\n⬇️ Fallback: tải noVNC từ GitHub → ~/novnc")
    for zurl in ("https://github.com/novnc/noVNC/archive/refs/tags/v1.5.0.zip",
                 "https://github.com/novnc/noVNC/archive/refs/heads/master.zip"):
        try:
            ztmp = pathlib.Path("/tmp/novnc.zip")
            urllib.request.urlretrieve(zurl, ztmp)
            with zipfile.ZipFile(ztmp) as z:
                z.extractall("/tmp/_novnc_extract")
            src = next(pathlib.Path("/tmp/_novnc_extract").iterdir())
            dst = HOME / "novnc"
            if dst.exists():
                shutil.rmtree(dst)
            shutil.move(str(src), str(dst))
            NOVNC_WEB = str(dst)
            print(f"  ✅ {NOVNC_WEB}")
            break
        except Exception as e:
            print(f"  ⚠️ {zurl} → {e}")

if not have("ttyd"):
    arch = {"x86_64": "x86_64", "aarch64": "aarch64"}.get(platform.machine())
    if arch:
        dst = pathlib.Path(LOCAL_BIN) / "ttyd"
        try:
            urllib.request.urlretrieve(
                f"https://github.com/tsl0922/ttyd/releases/download/1.7.7/ttyd.{arch}", dst)
            os.chmod(dst, 0o755)
            print(f"\n✅ ttyd binary → {dst}")
        except Exception as e:
            print("\n❌ tải ttyd:", e)
if not have("cloudflared"):
    arch = {"x86_64": "amd64", "aarch64": "arm64"}.get(platform.machine(), "amd64")
    dst = "/usr/local/bin/cloudflared" if root else pathlib.Path(LOCAL_BIN) / "cloudflared"
    try:
        urllib.request.urlretrieve(
            f"https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-{arch}", dst)
        os.chmod(dst, 0o755)
        print(f"\n✅ cloudflared → {dst}")
    except Exception as e:
        print("\n❌ tải cloudflared:", e)

# tổng kết sau cài đặt
WS_CMD = ["websockify"] if have("websockify") else (
    [sys.executable, "-m", "websockify"] if WS_MOD else None)
NOVNC_WEB = ("/usr/share/novnc" if os.path.isdir("/usr/share/novnc")
             else (str(HOME / "novnc") if (HOME / "novnc").is_dir() else None))
DESKTOP_OK = (have("Xvfb") and have("x11vnc") and bool(WS_CMD) and bool(NOVNC_WEB)
              and (have("startxfce4") or have("xterm")))
print("\n🧩 KẾT QUẢ:", "Desktop sẵn sàng ✅" if DESKTOP_OK
      else "Desktop vẫn thiếu ⚠️ — xem ❌ ở trên (Dashboard/Bots/Terminal vẫn chạy)")

# ═══════════ 3. DỌN + KHỞI ĐỘNG LẠI ═══════════
print("\n🧹 Dọn tiến trình cũ…")
kill_matching(["Xvfb", "x11vnc", "websockify", "ttyd", "cloudflared", "dashboard.py"])
time.sleep(2)
TUNNELS_FILE.write_text("{}")

print("🎬 Khởi động lại toàn bộ…")
if DESKTOP_OK:
    spawn(["Xvfb", DISPLAY, "-screen", "0", "1600x900x24", "-nolisten", "tcp"], "xvfb")
    for _ in range(20):
        if os.path.exists("/tmp/.X11-unix/X1"):
            break
        time.sleep(0.5)
    if have("xsetroot"):
        spawn(["xsetroot", "-solid", "#131022"], "xsetroot", gui=True)
    if have("dbus-run-session") and have("startxfce4"):
        spawn(["dbus-run-session", "--", "startxfce4"], "xfce4", gui=True)
    elif have("xterm"):
        spawn(["xterm", "-maximized"], "xterm", gui=True)
    spawn(["x11vnc", "-display", DISPLAY, "-rfbport", "5901", "-forever", "-shared",
           "-nopw", "-noxrecord", "-noxfixes", "-noxdamage"], "x11vnc")
    spawn(WS_CMD + ["--web", NOVNC_WEB, PORT_NOVNC, "localhost:5901"], "websockify")
else:
    print("  ⚠️ bỏ qua Desktop")
if have("ttyd"):
    spawn(["ttyd", "-W", "-p", PORT_TTYD, "bash", "-l"], "ttyd")
dash_py = next((c for c in [pathlib.Path.cwd() / "dashboard.py", HOME / "dashboard.py",
                            GDIR / "dashboard.py"] if c.exists()), None)
if dash_py:
    spawn([sys.executable, str(dash_py)], "dashboard",
          extra_env={"DASH_PORT": str(PORT_DASH), "DASH_TOKEN": TOKEN,
                     "TUNNELS_FILE": str(TUNNELS_FILE), "PYTHONUNBUFFERED": "1"})
else:
    print("  ⚠️ không tìm thấy dashboard.py — chạy lại ô %%writefile dashboard.py rồi chạy ô này")

if wait_port(PORT_DASH, 25):
    start_tunnel("dashboard", PORT_DASH)
else:
    print(f"  ❌ Dashboard không mở cổng {PORT_DASH} — xem {GDIR}/dashboard.log")
if DESKTOP_OK:
    if wait_port(PORT_NOVNC, 25):
        start_tunnel("desktop", PORT_NOVNC)
    else:
        print(f"  ❌ noVNC không mở cổng {PORT_NOVNC} — xem {GDIR}/websockify.log, x11vnc.log, xfce4.log")
if have("ttyd"):
    if wait_port(PORT_TTYD, 15):
        start_tunnel("terminal", PORT_TTYD)
    else:
        print(f"  ❌ ttyd không mở cổng {PORT_TTYD} — xem {GDIR}/ttyd.log")

demo = BDIR / "demo_bot.py"
if not demo.exists():
    demo.write_text("""import time
print("🤖 Demo bot đã khởi động!", flush=True)
while True:
    print(f"💓 demo bot alive · {time.strftime('%H:%M:%S')}", flush=True)
    time.sleep(60)
""")

for _ in range(45):
    if TUNNELS.get("dashboard") and (TUNNELS.get("desktop") or not DESKTOP_OK):
        break
    time.sleep(1)

dash = TUNNELS.get("dashboard")
desk = TUNNELS.get("desktop")
term = TUNNELS.get("terminal")
dash_url = f"{dash}/?key={TOKEN}" if dash else "(thất bại — chạy lại ô này)"
desk_url = f"{desk}/vnc.html?autoconnect=1&resize=scale&reconnect=1" if desk else "(thất bại — xem log bên trên)"
term_url = term or "(thất bại — xem log bên trên)"

(GDIR / "server_info.json").write_text(json.dumps(
    {"token": TOKEN, "tunnels": dict(TUNNELS),
     "ports": {"dashboard": PORT_DASH, "desktop": PORT_NOVNC, "terminal": PORT_TTYD}}, indent=2))

print()
print("═" * 66)
print("   🩺  SỬA XONG — GIỮ Ô NÀY CHẠY LIÊN TỤC (thay cho ô Bước 2)!")
print("═" * 66)
print(f"   📊 Dashboard     {dash_url}")
print(f"   🖥️  Cloud Desktop  {desk_url}")
print(f"   ⌨️  Web Terminal   {term_url}")
print(f"   🔑 Access Key     {TOKEN}")
print("═" * 66)
print("   ⚠️ URL MỚI khác URL cũ — mở link Dashboard mới này, đừng dùng link cũ!")
print("   💡 Xem trạng thái dịch vụ: Dashboard → Tổng quan → ⚙️ Dịch vụ nền")

n = 0
try:
    while True:
        time.sleep(30)
        n += 1
        if n % 40 == 0:
            print(f"💓 [{time.strftime('%H:%M:%S')}] server vẫn đang chạy — {dash_url}")
except KeyboardInterrupt:
    print("🛑 Đang dừng toàn bộ dịch vụ…")
    for p in PROCS:
        try:
            p.terminate()
        except Exception:
            pass
