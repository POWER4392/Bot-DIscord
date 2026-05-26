import tkinter as tk
from tkinter import messagebox, filedialog
import json
import os
import subprocess
import shutil
import sqlite3
import requests as http_requests
import threading
import psutil
from PIL import Image, ImageTk, ImageDraw
import customtkinter as ctk

GUI_SETTINGS_FILE = "gui_settings.json"
bot_process = None

def load_gui_settings():
    if os.path.exists(GUI_SETTINGS_FILE):
        try:
            with open(GUI_SETTINGS_FILE, "r", encoding="utf-8") as f: return json.load(f)
        except: pass
    return {"remote_api_url": "", "api_secret": "BOT_SECRET_KEY_2026"}

gui_settings = load_gui_settings()

def _remote_request(action, extra_payload=None):
    try:
        url = entry_remote_url.get().strip().rstrip("/") + "/api"
        key = entry_remote_key.get().strip()
    except NameError:
        url = gui_settings.get("remote_api_url", "").strip().rstrip("/") + "/api"
        key = gui_settings.get("api_secret", "BOT_SECRET_KEY_2026").strip()
        
    if not url or "http" not in url: return None
    payload = {"action": action}
    if extra_payload: payload.update(extra_payload)
    try:
        resp = http_requests.post(url, json=payload, headers={"X-API-Key": key}, timeout=10)
        return resp.json()
    except: return None

def load_current_config():
    resp = _remote_request("GET_CONFIG")
    if resp and resp.get("ok"): return resp.get("data", {})
    return {}

def get_server_data():
    resp = _remote_request("GET_SERVER_DATA")
    if resp and resp.get("ok"): return resp.get("data", {})
    return {}

# --- QUẢN LÝ TIẾN TRÌNH BOT ---
def stop_bot():
    global bot_process
    if bot_process:
        try:
            parent = psutil.Process(bot_process.pid)
            for child in parent.children(recursive=True): child.kill()
            parent.kill()
        except Exception: pass
        bot_process = None
    current_dir = os.path.abspath(os.path.dirname(__file__))
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmd = proc.info.get('cmdline') or []
            if proc.info.get('name', '').lower().startswith('python') and 'main.py' in " ".join(cmd):
                if any(current_dir in arg for arg in cmd):
                    spider = psutil.Process(proc.info['pid'])
                    for child in spider.children(recursive=True): child.kill()
                    spider.kill()
        except: pass
    if 'lbl_status' in globals(): lbl_status.configure(text="TRẠNG THÁI: ĐÃ DỪNG", text_color="#DA373C")

def start_bot():
    global bot_process
    stop_bot()
    try:
        import sys
        bot_process = subprocess.Popen([sys.executable, "main.py"])
        if 'lbl_status' in globals(): lbl_status.configure(text="TRẠNG THÁI: ĐANG HOẠT ĐỘNG 🚀", text_color="#23A559")
    except Exception as e: messagebox.showerror("Lỗi", f"Không thể bật Bot: {e}")

def select_file(entry_widget, title, types):
    source_path = filedialog.askopenfilename(title=title, filetypes=types)
    if source_path:
        filename = os.path.basename(source_path)
        dest_path = os.path.join(os.getcwd(), filename)
        try:
            if os.path.abspath(source_path) != os.path.abspath(dest_path):
                shutil.copy2(source_path, dest_path)
            entry_widget.delete(0, tk.END); entry_widget.insert(0, filename)
        except Exception as e: messagebox.showerror("Lỗi Copy", str(e))

def preview_position():
    if not current_server_id: return messagebox.showerror("Lỗi", "Vui lòng Chọn Server ở mục TRẠM ĐIỀU KHIỂN trước khi căn chỉnh!")
    bg_file = entry_bg.get()
    if not os.path.exists(bg_file): return messagebox.showerror("Lỗi", "Không tìm thấy file ảnh nền! Vui lòng Upload lại.")
    
    editor = tk.Toplevel(root)
    bg_img = Image.open(bg_file).convert("RGBA")
    canvas = tk.Canvas(editor, width=bg_img.width, height=bg_img.height)
    canvas.pack()
    
    bg_tk = ImageTk.PhotoImage(bg_img)
    canvas.create_image(0, 0, image=bg_tk, anchor=tk.NW)
    editor.bg_tk = bg_tk
    
    try: curr_size = int(entry_size.get())
    except: curr_size = 200
    try: curr_x = int(entry_x.get()); curr_y = int(entry_y.get())
    except: curr_x, curr_y = 0, 0
        
    drag_data = {"x": 0, "y": 0, "item": None}
    def create_avg(size):
        img = Image.new("RGBA", (size, size), (0,0,0,0))
        ImageDraw.Draw(img).ellipse((0,0,size,size), fill=(255,0,0,180))
        return ImageTk.PhotoImage(img)
    
    av_tk = create_avg(curr_size)
    av_item = canvas.create_image(curr_x, curr_y, image=av_tk, anchor=tk.NW, tags="av")
    editor.av_tk = av_tk
    
    def on_drag_start(e): drag_data["item"] = av_item; drag_data["x"], drag_data["y"] = e.x, e.y
    def on_drag_motion(e):
        if drag_data["item"]:
            canvas.move(av_item, e.x - drag_data["x"], e.y - drag_data["y"])
            drag_data["x"], drag_data["y"] = e.x, e.y
    def on_drag_stop(e):
        if drag_data["item"]:
            c = canvas.coords(av_item)
            entry_x.delete(0, tk.END); entry_x.insert(0, str(int(c[0])))
            entry_y.delete(0, tk.END); entry_y.insert(0, str(int(c[1])))
            drag_data["item"] = None

    canvas.tag_bind("av", "<ButtonPress-1>", on_drag_start)
    canvas.tag_bind("av", "<B1-Motion>", on_drag_motion)
    canvas.tag_bind("av", "<ButtonRelease-1>", on_drag_stop)

    fc = tk.Frame(editor); fc.pack(fill=tk.X)
    sc = tk.Scale(fc, from_=50, to=800, orient=tk.HORIZONTAL)
    sc.set(curr_size); sc.pack(fill=tk.X)
    def update_size(v):
        ns = int(v); nat = create_avg(ns)
        canvas.itemconfig(av_item, image=nat); editor.av_tk = nat
        entry_size.delete(0, tk.END); entry_size.insert(0, str(ns))
    sc.config(command=update_size)
    editor.transient(root); editor.grab_set()

# --- LƯU CẤU HÌNH ---
def save_settings():
    try:
        cfg["token"] = entry_token.get()
        cfg["prefix"] = entry_prefix.get()
        cfg["cmd_play"] = entry_cmd_play.get()
        cfg["cmd_stop"] = entry_cmd_stop.get()
        cfg["cmd_skip"] = entry_cmd_skip.get()
        cfg["cmd_pause"] = entry_cmd_pause.get()
        cfg["cmd_resume"] = entry_cmd_resume.get()
        cfg["cmd_kick"] = entry_cmd_kick.get()
        cfg["cmd_ban"] = entry_cmd_ban.get()
        cfg["cmd_mute"] = entry_cmd_mute.get()
        cfg["cmd_clear"] = entry_cmd_clear.get()
        cfg["cmd_ping"] = entry_cmd_ping.get()
        cfg["cmd_addword"] = entry_cmd_addword.get()
        cfg["cmd_delword"] = entry_cmd_delword.get()
        cfg["cmd_warn"] = entry_cmd_warn.get()
        cfg["cmd_timed_role"] = entry_cmd_timed_role.get()

        cfg["cmd_profile"] = entry_cmd_profile.get()
        cfg["cmd_rank"] = entry_cmd_rank.get()
        cfg["cmd_setup_voice"] = entry_cmd_setup_voice.get()
        cfg["cmd_ticket_setup"] = entry_cmd_ticket_setup.get()
        
        if current_server_id:
            if "servers" not in cfg: cfg["servers"] = {}
            if current_server_id not in cfg["servers"]: cfg["servers"][current_server_id] = {}
            sc = cfg["servers"][current_server_id]
            
            sel_chan = combo_welcome_channel.get()
            sc["welcome_channel_id"] = next((str(c["id"]) for c in current_server_data.get("channels", []) if c["name"] == sel_chan), None)
            
            sel_am_chan = combo_automod_channel.get()
            sc["automod_channel_id"] = next((str(c["id"]) for c in current_server_data.get("channels", []) if c["name"] == sel_am_chan), None)
            
            sel_log_chan = combo_log_channel.get()
            sc["log_channel_id"] = next((str(c["id"]) for c in current_server_data.get("channels", []) if c["name"] == sel_log_chan), None)
            
            t_mute = entry_automod_mute_mins.get()
            sc["automod_mute_minutes"] = int(t_mute) if t_mute.isdigit() else 5
            
            sc["welcome_message"] = entry_welcome.get()
            sc["leave_message"] = entry_leave.get()
            sc["background_image"] = entry_bg.get()
            sc["font_file"] = entry_font.get()
            try:
                sc["avatar_x"] = int(entry_x.get())
                sc["avatar_y"] = int(entry_y.get())
                sc["avatar_size"] = int(entry_size.get())
            except: pass
            
            sel_auto = combo_auto_role.get()
            sc["auto_role_id"] = next((r["id"] for r in current_server_data.get("roles", []) if r["name"] == sel_auto), None)
            
            sel_voice_category = combo_voice_category.get()
            sc["voice_category_id"] = next((str(c["id"]) for c in current_server_data.get("categories", []) if c["name"] == sel_voice_category), None)

            # Xác minh thành viên
            sel_pending = combo_pending_role.get()
            sc["pending_role_id"] = next((r["id"] for r in current_server_data.get("roles", []) if r["name"] == sel_pending), None)
            sel_verify_ch = combo_verify_channel.get()
            sc["verify_channel_id"] = next((str(c["id"]) for c in current_server_data.get("channels", []) if c["name"] == sel_verify_ch), None)

            sc["mod_role_ids"] = [r["id"] for r in current_mod_roles]
            if "mod_role_id" in sc: del sc["mod_role_id"]

            sc["boost_channel_id"] = next((str(c["id"]) for c in current_server_data.get("channels", []) if c["name"] == combo_boost_channel.get()), None)
            sc["boost_message"] = entry_boost_msg.get().strip() or "🚀 **{mention}** vừa boost server! Cảm ơn vì sự ủng hộ của bạn! 💜"
            sel_booster_role = combo_booster_role.get()
            sc["booster_role_id"] = next((str(r["id"]) for r in current_server_data.get("roles", []) if r["name"] == sel_booster_role), None)
            
            sc["rr_channel_id"] = next((str(c["id"]) for c in current_server_data.get("channels", []) if c["name"] == combo_rr_channel.get()), None)
            sc["rr_title"] = entry_rr_title.get()
            sc["rr_roles_list"] = [r["id"] for r in current_rr_roles]

        resp = _remote_request("UPDATE_CONFIG", {"payload": cfg})
        if not resp or not resp.get("ok"):
            messagebox.showerror("Lỗi", "Không thể lưu cấu hình lên Bot: " + (resp.get("error") if resp else "Mất kết nối"))
            return False
        return True
    except Exception as e:
        messagebox.showerror("Lỗi", str(e))
        return False

def save_and_reset():
    if save_settings():
        start_bot()

# --- GIAO DIỆN CHÍNH ---
ctk.set_appearance_mode("dark")
root = ctk.CTk()
root.title("Quản Lý Bot Đa Server")
root.geometry("540x950")

cfg = load_current_config()
srv_data = get_server_data()
current_server_id = None
current_server_data = {}

tabview = ctk.CTkTabview(root)
tabview.pack(fill="both", expand=True, padx=5, pady=5)
tab_system = tabview.add("⚙️ HỆ THỐNG")
tab_cmds = tabview.add("📝 LỆNH TÙY BIẺN")
tab_server = tabview.add("🌐 QUẢN LÝ SERVER")
tab_social = tabview.add("📡 SOCIAL MEDIA")

sf_system = ctk.CTkScrollableFrame(tab_system, fg_color="transparent")
sf_system.pack(fill="both", expand=True)
sf_cmds = ctk.CTkScrollableFrame(tab_cmds, fg_color="transparent")
sf_cmds.pack(fill="both", expand=True)
sf_server = ctk.CTkScrollableFrame(tab_server, fg_color="transparent")
sf_server.pack(fill="both", expand=True)
sf_social = ctk.CTkScrollableFrame(tab_social, fg_color="transparent")
sf_social.pack(fill="both", expand=True)

# --- KHỐI TOÀN CẦU ---
fc = ctk.CTkFrame(sf_system, fg_color="#2B2D31", corner_radius=12); fc.pack(pady=10, fill="x")
ctk.CTkLabel(fc, text="⚙️ CẤU HÌNH BOT GLOBAL", font=("Segoe UI", 16, "bold")).pack(pady=10)
def mki(p, l, k, d=""):
    ctk.CTkLabel(p, text=l, font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=20)
    e = ctk.CTkEntry(p, width=420, height=30)
    e.insert(0, str(cfg.get(k, d)))
    e.pack(pady=(0,10), padx=20)
    return e
entry_token = mki(fc, "BOT TOKEN:", "token")
entry_prefix = mki(fc, "PREFIX (Dấu bắt đầu lệnh):", "prefix", "!")

# --- REMOTE MODE (Kết nối Discloud / VPS) ---
fr = ctk.CTkFrame(sf_system, fg_color="#1E2124", corner_radius=12, border_width=1, border_color="#F1C40F")
fr.pack(pady=10, fill="x", padx=5)
ctk.CTkLabel(fr, text="☁️ ĐIỀU KHIỂN BOT TỪ XA (DISCLOUD/VPS)", font=("Segoe UI", 15, "bold"), text_color="#F1C40F").pack(pady=10)
ctk.CTkLabel(fr, text="Nhập địa chỉ Bot API (ví dụ: http://12.34.56.78:8080)", font=("Segoe UI", 11), text_color="#B5BAC1").pack(anchor="w", padx=20)
entry_remote_url = ctk.CTkEntry(fr, width=420, height=32, placeholder_text="http://xxx.xxx.xxx.xxx:8080")
entry_remote_url.insert(0, gui_settings.get("remote_api_url", ""))
entry_remote_url.pack(pady=(2,8), padx=20)

ctk.CTkLabel(fr, text="API Secret Key:", font=("Segoe UI", 11), text_color="#B5BAC1").pack(anchor="w", padx=20)
entry_remote_key = ctk.CTkEntry(fr, width=420, height=32, show="*", placeholder_text="BOT_SECRET_KEY_2026")
entry_remote_key.insert(0, gui_settings.get("api_secret", "BOT_SECRET_KEY_2026"))
entry_remote_key.pack(pady=(2,8), padx=20)

lbl_remote_status = ctk.CTkLabel(fr, text="⬤ Chưa kết nối", font=("Segoe UI", 12, "bold"), text_color="#72767D")
lbl_remote_status.pack(pady=4)



def ping_remote():
    def task():
        result = _remote_request("STATUS")
        if result and result.get("ok"):
            info = f"🤖 {result.get('bot')}  |  {result.get('guilds')} server  |  {result.get('latency_ms')}ms"
            lbl_remote_status.configure(text=f"✅ Online — {info}", text_color="#23A559")
        elif result:
            lbl_remote_status.configure(text=f"❌ {result.get('error','Lỗi không xác định')}", text_color="#DA373C")
        else:
            lbl_remote_status.configure(text="❌ Mất kết nối", text_color="#DA373C")
    threading.Thread(target=task, daemon=True).start()

def push_config_remote():
    if not save_settings():
        return
    gui_settings["remote_api_url"] = entry_remote_url.get().strip()
    gui_settings["api_secret"] = entry_remote_key.get().strip()
    with open(GUI_SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(gui_settings, f, indent=4, ensure_ascii=False)
    
    global cfg, srv_data
    cfg = load_current_config()
    srv_data = get_server_data()
    combo_servers.configure(values=["Chọn Server"] + list(srv_data.keys()))
    if srv_data: combo_servers.set("Chọn Server")
    messagebox.showinfo("Thành công", "Đã lưu và tải cấu hình mới từ Bot!")

btn_row = ctk.CTkFrame(fr, fg_color="transparent")
btn_row.pack(pady=(4,14), padx=20, fill="x")
ctk.CTkButton(btn_row, text="📡 Ping Bot", width=130, fg_color="#2C2F33", hover_color="#3A3D42", command=ping_remote).pack(side="left", padx=4)
ctk.CTkButton(btn_row, text="⬆️ Đẩy Config & Reload", width=200, fg_color="#F1A000", hover_color="#D4900A", text_color="black", command=push_config_remote).pack(side="left", padx=4)

fcmd_music = ctk.CTkFrame(sf_cmds, fg_color="#2B2D31", corner_radius=12)
fcmd_music.pack(pady=10, fill="x", padx=10)
ctk.CTkLabel(fcmd_music, text="🎵 LỆNH ĐIỀU KHIỂN ÂM NHẠC", font=("Segoe UI", 15, "bold"), text_color="#5865F2").pack(pady=5)

fcmd_music_l = ctk.CTkFrame(fcmd_music, fg_color="transparent"); fcmd_music_l.pack(side="left", fill="both", expand=True)
fcmd_music_r = ctk.CTkFrame(fcmd_music, fg_color="transparent"); fcmd_music_r.pack(side="left", fill="both", expand=True)

fcmd_mod = ctk.CTkFrame(sf_cmds, fg_color="#2B2D31", corner_radius=12)
fcmd_mod.pack(pady=20, fill="x", padx=10)
ctk.CTkLabel(fcmd_mod, text="🛡️ LỆNH QUẢN TRỊ KÊNH", font=("Segoe UI", 15, "bold"), text_color="#ED4245").pack(pady=5)

fcmd_mod_l = ctk.CTkFrame(fcmd_mod, fg_color="transparent"); fcmd_mod_l.pack(side="left", fill="both", expand=True)
fcmd_mod_r = ctk.CTkFrame(fcmd_mod, fg_color="transparent"); fcmd_mod_r.pack(side="left", fill="both", expand=True)

def mki_grid(p, l, k, d=""):
    ctk.CTkLabel(p, text=l, font=("Segoe UI", 12)).pack(anchor="w", padx=10)
    e = ctk.CTkEntry(p, width=180, height=30)
    e.insert(0, str(cfg.get(k, d)))
    e.pack(pady=(0,10), padx=10)
    return e

# Music commands
entry_cmd_play = mki_grid(fcmd_music_l, "🎵 Play:", "cmd_play", "play")
entry_cmd_skip = mki_grid(fcmd_music_l, "⏭️ Skip:", "cmd_skip", "skip")
entry_cmd_resume = mki_grid(fcmd_music_l, "▶️ Resume:", "cmd_resume", "resume")
entry_cmd_ping = mki_grid(fcmd_music_l, "🏓 Ping:", "cmd_ping", "ping")

entry_cmd_stop = mki_grid(fcmd_music_r, "⏹️ Stop:", "cmd_stop", "stop")
entry_cmd_pause = mki_grid(fcmd_music_r, "⏸️ Pause:", "cmd_pause", "pause")

# Mod commands
entry_cmd_mute = mki_grid(fcmd_mod_l, "🔇 Mute:", "cmd_mute", "mute")
entry_cmd_clear = mki_grid(fcmd_mod_l, "🧹 Clear:", "cmd_clear", "clear")
entry_cmd_addword = mki_grid(fcmd_mod_l, "➕ Add Word:", "cmd_addword", "addword")
entry_cmd_warn = mki_grid(fcmd_mod_l, "⚠️ Warn:", "cmd_warn", "warn")

entry_cmd_kick = mki_grid(fcmd_mod_r, "🔨 Kick:", "cmd_kick", "kick")
entry_cmd_ban = mki_grid(fcmd_mod_r, "⛔ Ban:", "cmd_ban", "ban")
entry_cmd_delword = mki_grid(fcmd_mod_r, "🗑️ Del Word:", "cmd_delword", "delword")
entry_cmd_timed_role = mki_grid(fcmd_mod_r, "⏳ Timed Role:", "cmd_timed_role", "timed_role")

# XP & Utilities
fcmd_eco = ctk.CTkFrame(sf_cmds, fg_color="#2B2D31", corner_radius=12)
fcmd_eco.pack(pady=10, fill="x", padx=10)
ctk.CTkLabel(fcmd_eco, text="🏆 LỆNH XP & TIỆN ÍCH", font=("Segoe UI", 15, "bold"), text_color="#5865F2").pack(pady=5)

fcmd_eco_l = ctk.CTkFrame(fcmd_eco, fg_color="transparent"); fcmd_eco_l.pack(side="left", fill="both", expand=True)
fcmd_eco_r = ctk.CTkFrame(fcmd_eco, fg_color="transparent"); fcmd_eco_r.pack(side="left", fill="both", expand=True)

entry_cmd_profile = mki_grid(fcmd_eco_l, "🏆 Profile:", "cmd_profile", "profile")
entry_cmd_rank = mki_grid(fcmd_eco_l, "📊 Rank:", "cmd_rank", "rank")

entry_cmd_setup_voice = mki_grid(fcmd_eco_r, "🎙️ Setup Voice:", "cmd_setup_voice", "setup_voice")
entry_cmd_ticket_setup = mki_grid(fcmd_eco_r, "🎫 Setup Ticket:", "cmd_ticket_setup", "ticket_setup")


# --- KHỐI SERVER ---
fsrv = ctk.CTkFrame(sf_server, fg_color="#5865F2", corner_radius=12); fsrv.pack(pady=10, fill="x")
ctk.CTkLabel(fsrv, text="🌐 TRẠM ĐIỀU KHIỂN SERVER TÙY CHỈNH", font=("Segoe UI", 16, "bold"), text_color="white").pack(pady=(15,5))

combo_servers = ctk.CTkComboBox(fsrv, values=["Chọn Server bên dưới..."] + [v["name"] for v in srv_data.values()], width=420, height=40, font=("Segoe UI", 14, "bold"))
combo_servers.pack(pady=(0,15))

# SERVER SPECIFIC CONTROLS
fs_spec = ctk.CTkFrame(sf_server, fg_color="#2B2D31", corner_radius=12); fs_spec.pack(pady=10, fill="x")
ctk.CTkLabel(fs_spec, text="(Cài đặt sẽ chỉ lưu riêng cho Server được chọn)", text_color="#FEE75C").pack(pady=(10,0))

def load_sv_cf(k, d=""):
    return str(cfg.get("servers", {}).get(current_server_id, {}).get(k, d))

def ms(l): ctk.CTkLabel(fs_spec, text=l, font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=20)
def me():
    e = ctk.CTkEntry(fs_spec, width=420, height=30)
    e.pack(pady=(0,10), padx=20)
    return e

ms("KÊNH CHÀO MỪNG:"); combo_welcome_channel = ctk.CTkComboBox(fs_spec, values=["Không Yêu Cầu"], width=420); combo_welcome_channel.pack(pady=(0,10), padx=20)
ms("THÔNG ĐIỆP CHÀO:"); entry_welcome = me()
ms("THÔNG ĐIỆP TẠM BIỆT:"); entry_leave = me()

ms("QUẢN LÝ TỪ CẤM AUTOMOD (Mỗi từ 1 dòng):")
f_bl = ctk.CTkFrame(fs_spec, fg_color="transparent"); f_bl.pack(fill="x", padx=20, pady=(0,10))
textbox_banned_words = ctk.CTkTextbox(f_bl, width=320, height=100); textbox_banned_words.pack(side="left")

def btn_save_blacklist_click():
    if not current_server_id: return messagebox.showwarning("Cảnh báo", "Vui lòng chọn Server!")
    text_content = textbox_banned_words.get("1.0", tk.END).strip()
    words = [w.strip() for w in text_content.split('\n') if w.strip()]
    try:
        _remote_request("DB_QUERY", {"query": "DELETE FROM blacklists WHERE guild_id=?", "params": [str(current_server_id)]})
        for w in words:
            _remote_request("DB_QUERY", {"query": "INSERT INTO blacklists (guild_id, word) VALUES (?, ?)", "params": [str(current_server_id), w]})
        messagebox.showinfo("Thành công", f"Đã cập nhật {len(words)} từ cấm thành công lên DB cho Server!")
    except Exception as e: messagebox.showerror("Lỗi", str(e))

ctk.CTkButton(f_bl, text="Đồng Bộ File\nTừ Cấm", width=90, height=90, command=btn_save_blacklist_click, fg_color="#DA373C", hover_color="#A12828").pack(side="right")

ms("THỜI GIAN MUTE AUTOMOD (Phút):"); entry_automod_mute_mins = me()
ms("KÊNH BÁO CÁO AUTOMOD (Từ Cấm):"); combo_automod_channel = ctk.CTkComboBox(fs_spec, values=["Không Yêu Cầu"], width=420); combo_automod_channel.pack(pady=(0,10), padx=20)
ms("KÊNH NHẬT KÝ (Ghi Logs/Bảo Mật):"); combo_log_channel = ctk.CTkComboBox(fs_spec, values=["Không Yêu Cầu"], width=420); combo_log_channel.pack(pady=(0,10), padx=20)

ms("ẢNH NỀN (.png/.jpg):")
ff1 = ctk.CTkFrame(fs_spec, fg_color="transparent"); ff1.pack(fill="x", padx=20, pady=(0,10))
entry_bg = ctk.CTkEntry(ff1, width=320); entry_bg.pack(side="left")
ctk.CTkButton(ff1, text="Chọn Ảnh", width=80, command=lambda: select_file(entry_bg, "Ảnh Nền", [("Image", "*.png;*.jpg")])).pack(side="right")

ms("CHỮ NGHỆ THUẬT (.ttf):")
ff2 = ctk.CTkFrame(fs_spec, fg_color="transparent"); ff2.pack(fill="x", padx=20, pady=(0,10))
entry_font = ctk.CTkEntry(ff2, width=320); entry_font.pack(side="left")
ctk.CTkButton(ff2, text="Chọn Font", width=80, command=lambda: select_file(entry_font, "Font", [("Font", "*.ttf")])).pack(side="right")

f_coord = ctk.CTkFrame(fs_spec, fg_color="transparent"); f_coord.pack(fill="x", padx=20, pady=10)
ctk.CTkLabel(f_coord, text="X:").pack(side="left"); entry_x = ctk.CTkEntry(f_coord, width=60); entry_x.pack(side="left", padx=5)
ctk.CTkLabel(f_coord, text="  Y:").pack(side="left"); entry_y = ctk.CTkEntry(f_coord, width=60); entry_y.pack(side="left", padx=5)
ctk.CTkLabel(f_coord, text="  Size:").pack(side="left"); entry_size = ctk.CTkEntry(f_coord, width=60); entry_size.pack(side="left", padx=5)
ctk.CTkButton(fs_spec, text="👁 MỞ STUDIO KÉO THẢ AVATAR", fg_color="#5865F2", hover_color="#4752C4", command=preview_position).pack(pady=10)

ms("AUTO ROLE (Gán tự động — khi không có xác minh):"); combo_auto_role = ctk.CTkComboBox(fs_spec, values=["Không Yêu Cầu"], width=420); combo_auto_role.pack(pady=(0,10), padx=20)
ms("DANH MỤC LƯU PHÒNG THOẠI (Temp Voice):"); combo_voice_category = ctk.CTkComboBox(fs_spec, values=["Không Yêu Cầu (Tạo thư mục mặc định)"], width=420); combo_voice_category.pack(pady=(0,10), padx=20)

# ─── XÁC MINH THÀNH VIÊN ────────────────────────────────────────────────────
f_verify_section = ctk.CTkFrame(sf_server, fg_color="#1E2836", corner_radius=12, border_width=1, border_color="#5865F2")
f_verify_section.pack(pady=10, fill="x", padx=10)
ctk.CTkLabel(f_verify_section, text="🔒 HỆ THỐNG XÁC MINH THÀNH VIÊN",
             font=("Segoe UI", 16, "bold"), text_color="#5865F2").pack(pady=(12, 4))
ctk.CTkLabel(f_verify_section,
    text="Bật xác minh: thành viên mới nhận Pending Role → phải vượt CAPTCHA tại kênh Verify → mới nhận Auto Role.",
    font=("Segoe UI", 11), text_color="#B5BAC1", wraplength=460).pack(padx=20, pady=(0, 8))

def mv(l): ctk.CTkLabel(f_verify_section, text=l, font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=20)
mv("⏳ PENDING ROLE (Role tạm – chưa xác minh, để 'Không Bật' = tắt hẳn xác minh):")
combo_pending_role = ctk.CTkComboBox(f_verify_section, values=["Không Bật Xác Minh"], width=420)
combo_pending_role.pack(pady=(0, 10), padx=20)

mv("🔐 KÊNH XÁC MINH (Kênh chứa panel CAPTCHA nút bấm):")
combo_verify_channel = ctk.CTkComboBox(f_verify_section, values=["Không Yêu Cầu"], width=420)
combo_verify_channel.pack(pady=(0, 10), padx=20)

ctk.CTkLabel(f_verify_section,
    text="💡 Sau khi Lưu cấu hình, gõ lệnh  .setup_verify #kênh  trong Discord để tạo nút bấm xác minh.",
    font=("Segoe UI", 10), text_color="#FEE75C", wraplength=460).pack(padx=20, pady=(0, 12))

ms("MOD ROLES (Quyền Quản Trị):")
f_mod_roles_container = ctk.CTkScrollableFrame(fs_spec, height=100, fg_color="#1E1F22")
f_mod_roles_container.pack(fill="x", padx=20, pady=5)
f_mod_controls = ctk.CTkFrame(fs_spec, fg_color="transparent")
f_mod_controls.pack(fill="x", padx=20, pady=(5, 20))

combo_mod_add = ctk.CTkComboBox(f_mod_controls, values=["Không Yêu Cầu"], width=280)
combo_mod_add.pack(side="left", padx=(0,10))

current_mod_roles = []
current_rr_roles = []
ui_mod_tags = []

def refresh_mod_roles_ui():
    for t in ui_mod_tags:
        try: t.destroy()
        except: pass
    ui_mod_tags.clear()
    for mr in current_mod_roles:
        ft = ctk.CTkFrame(f_mod_roles_container, fg_color="#ED4245", corner_radius=6)
        ft.pack(fill="x", padx=5, pady=2)
        ctk.CTkLabel(ft, text=mr["name"], text_color="white", font=("Segoe UI", 12, "bold")).pack(side="left", padx=10, pady=2)
        btn_del = ctk.CTkButton(ft, text="X", width=20, fg_color="#DA373C", hover_color="#A12828", command=lambda r=mr["id"]: remove_mod_role(r))
        btn_del.pack(side="right", padx=5, pady=2)
        ui_mod_tags.append(ft)

def remove_mod_role(r_id):
    global current_mod_roles
    current_mod_roles = [r for r in current_mod_roles if r["id"] != r_id]
    refresh_mod_roles_ui()

def btn_add_mod_role():
    r_val = combo_mod_add.get()
    if r_val == "Không Yêu Cầu": return
    r_id = next((str(r["id"]) for r in current_server_data.get("roles", []) if r["name"] == r_val), None)
    if not r_id: return
    if any(r["id"] == str(r_id) for r in current_mod_roles):
        return messagebox.showwarning("Lỗi", "Role này đã được thêm rồi!")
    current_mod_roles.append({"id": str(r_id), "name": r_val})
    refresh_mod_roles_ui()

ctk.CTkButton(f_mod_controls, text="➕ Thêm Mod", width=90, fg_color="#ED4245", hover_color="#A12828", command=btn_add_mod_role).pack(side="left")

# ================= BOOST SERVER =================
f_boost = ctk.CTkFrame(sf_server, fg_color="#2B2D31", corner_radius=12); f_boost.pack(pady=10, fill="x", padx=10)
ctk.CTkLabel(f_boost, text="💜 BOOST SERVER", font=("Segoe UI", 16, "bold"), text_color="#FF73FA").pack(pady=10)

def mb(l): ctk.CTkLabel(f_boost, text=l, font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=20)
def me_b(): e = ctk.CTkEntry(f_boost, width=420, height=30); e.pack(pady=(0,10), padx=20); return e

mb("KÊNH THÔNG BÁO BOOST:")
combo_boost_channel = ctk.CTkComboBox(f_boost, values=["Không Yêu Cầu"], width=420); combo_boost_channel.pack(pady=(0,10), padx=20)
mb("ROLE TỰ ĐỘNG CẤP CHO BOOSTER:")
combo_booster_role = ctk.CTkComboBox(f_boost, values=["Không Yêu Cầu"], width=420); combo_booster_role.pack(pady=(0,10), padx=20)
mb("THÔNG ĐIỆP BOOST (Dùng {mention} cho mention, {name} cho tên):")
entry_boost_msg = me_b()

# ================= KHOẢNG BẢNG CHỌN VAI TRÒ =================
f_rr = ctk.CTkFrame(sf_server, fg_color="#2B2D31", corner_radius=12); f_rr.pack(pady=10, fill="x", padx=10)
ctk.CTkLabel(f_rr, text="🎛 BẢNG CHỌN VAI TRÒ (REACTION ROLES)", font=("Segoe UI", 16, "bold"), text_color="#F1C40F").pack(pady=10)

def mr(l): ctk.CTkLabel(f_rr, text=l, font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=20)
def me_rr(): e = ctk.CTkEntry(f_rr, width=420, height=30); e.pack(pady=(0,10), padx=20); return e

mr("Kênh Chứa Menu Role:")
combo_rr_channel = ctk.CTkComboBox(f_rr, values=["Không Yêu Cầu"], width=420); combo_rr_channel.pack(pady=(0,10), padx=20)

mr("Tiêu Đề Menu (Ví dụ: Hãy chọn Game bạn chơi):")
entry_rr_title = me_rr()
mr("Mô Tả Phụ (Hiển thị dưới tiêu đề, để trống để bỏ qua):")
entry_rr_desc = me_rr()

f_rr_roles_container = ctk.CTkScrollableFrame(f_rr, height=150, fg_color="#1E1F22")
f_rr_roles_container.pack(fill="x", padx=20, pady=5)

f_rr_controls = ctk.CTkFrame(f_rr, fg_color="transparent")
f_rr_controls.pack(fill="x", padx=20, pady=5)

combo_rr_add = ctk.CTkComboBox(f_rr_controls, values=["Không Yêu Cầu"], width=220)
combo_rr_add.pack(side="left", padx=(0,5))

current_rr_roles = []
ui_tags_list = []
def refresh_rr_roles_ui():
    for tag in ui_tags_list:
        try: tag.destroy()
        except: pass
    ui_tags_list.clear()
    for tr in current_rr_roles:
        f_tag = ctk.CTkFrame(f_rr_roles_container, fg_color="#3B3D44", corner_radius=8)
        f_tag.pack(fill="x", padx=5, pady=3)
        info_frame = ctk.CTkFrame(f_tag, fg_color="transparent")
        info_frame.pack(side="left", fill="x", expand=True, padx=8, pady=4)
        ctk.CTkLabel(info_frame, text=f"◆  {tr['name']}", text_color="#5865F2", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        desc_text = tr.get("desc", "")
        if desc_text:
            ctk.CTkLabel(info_frame, text=desc_text[:80], text_color="#B5BAC1", font=("Segoe UI", 10), wraplength=280, justify="left").pack(anchor="w")
        btn_del = ctk.CTkButton(f_tag, text="✕", width=26, height=26, fg_color="#DA373C", hover_color="#A12828", font=("Segoe UI", 11, "bold"), command=lambda r=tr["id"]: remove_rr_role(r))
        btn_del.pack(side="right", padx=6, pady=4)
        ui_tags_list.append(f_tag)

def remove_rr_role(r_id):
    global current_rr_roles
    current_rr_roles = [r for r in current_rr_roles if r["id"] != r_id]
    refresh_rr_roles_ui()

def btn_add_rr_role():
    r_val = combo_rr_add.get()
    if not r_val or r_val == "Không Yêu Cầu": return
    if len(current_rr_roles) >= 25: return messagebox.showwarning("Lỗi", "Tối đa 25 Role mỗi Menu!")
    r_id = next((str(r["id"]) for r in current_server_data.get("roles", []) if r["name"] == r_val), None)
    if not r_id: return
    if any(r["id"] == r_id for r in current_rr_roles): return messagebox.showwarning("Lỗi", "Role này đã được thêm rồi!")
    
    # Popup nhập mô tả
    desc_win = ctk.CTkToplevel(root)
    desc_win.title(f"Mô tả cho @{r_val}")
    desc_win.geometry("420x180")
    desc_win.grab_set()
    ctk.CTkLabel(desc_win, text=f"Nhập mô tả ngắn cho role  ◆  {r_val}:", font=("Segoe UI", 12, "bold")).pack(pady=(15,5), padx=20)
    entry_desc_input = ctk.CTkEntry(desc_win, width=380, height=32, placeholder_text="Ví dụ: Người chơi CS2, nhận thông báo sự kiện...")
    entry_desc_input.pack(padx=20, pady=5)
    def confirm_add():
        desc_val = entry_desc_input.get().strip()
        current_rr_roles.append({"id": r_id, "name": r_val, "desc": desc_val})
        refresh_rr_roles_ui()
        desc_win.destroy()
    ctk.CTkButton(desc_win, text="✅ Thêm Role", fg_color="#5865F2", command=confirm_add).pack(pady=10)
    desc_win.bind("<Return>", lambda e: confirm_add())

ctk.CTkButton(f_rr_controls, text="➕ Thêm Role", width=100, command=btn_add_rr_role).pack(side="left")

def btn_spawn_rr():
    if not current_server_id: return messagebox.showwarning("Lỗi", "Vui lòng chọn Server!")
    c_val = combo_rr_channel.get()
    if c_val == "Không Yêu Cầu": return messagebox.showerror("Lỗi", "Chưa chọn kênh để gửi Menu!")
    chan_id = next((str(c["id"]) for c in current_server_data.get("channels", []) if c["name"] == c_val), None)
    title = entry_rr_title.get().strip() or "Bảng Lựa Chọn Vai Trò"
    panel_desc = entry_rr_desc.get().strip()
    
    if not current_rr_roles: return messagebox.showerror("Lỗi", "Vui lòng thêm ít nhất 1 Role!")
    
    payload = json.dumps({"guild_id": current_server_id, "channel_id": chan_id, "title": title, "desc": panel_desc, "roles": current_rr_roles})
    
    try:
        resp = _remote_request("SPAWN_RR_PANEL", {"payload": json.loads(payload)})
        if resp and resp.get("ok"):
            messagebox.showinfo("Thành công", "Đã gửi lệnh cho Bot! Menu Role sẽ xuất hiện trên kênh chỉ sau 3 giây.")
        else:
            messagebox.showerror("Lỗi", "Bot không phản hồi lệnh SPAWN_RR_PANEL.")
    except Exception as e: messagebox.showerror("Lỗi API", str(e))

ctk.CTkButton(f_rr, text="▶ PHÁT BẢNG MÀU LÊN SERVER", fg_color="#23A559", font=("Segoe UI", 12, "bold"), command=btn_spawn_rr).pack(pady=15)

def on_server_select(choice):
    try:
        global current_server_id, current_server_data
        if "Chọn Server" in choice: return
        
        for sid, sdata in srv_data.items():
            if sdata["name"] == choice:
                current_server_id = sid
                current_server_data = sdata
                break
                
        c_names = ["Không Yêu Cầu"] + [c["name"] for c in current_server_data.get("channels", [])]
        r_names = ["Không Yêu Cầu"] + [r["name"] for r in current_server_data.get("roles", [])]
        cat_names = ["Không Yêu Cầu (Tạo thư mục mặc định)"] + [c["name"] for c in current_server_data.get("categories", [])]
        
        combo_welcome_channel.configure(values=c_names)
        combo_automod_channel.configure(values=c_names)
        combo_log_channel.configure(values=c_names)
        combo_rr_channel.configure(values=c_names)
        combo_boost_channel.configure(values=c_names)
        combo_verify_channel.configure(values=c_names)
        combo_auto_role.configure(values=r_names)
        combo_pending_role.configure(values=["Không Bật Xác Minh"] + r_names[1:])
        combo_mod_add.configure(values=r_names)
        combo_rr_add.configure(values=r_names)
        combo_booster_role.configure(values=r_names)
        combo_voice_category.configure(values=cat_names)
        
        scf = cfg.get("servers", {}).get(current_server_id, {})
        
        entry_welcome.delete(0, tk.END); entry_welcome.insert(0, str(scf.get("welcome_message", cfg.get("welcome_message", "🚀 Welcome {mention}!"))))
        entry_leave.delete(0, tk.END); entry_leave.insert(0, str(scf.get("leave_message", cfg.get("leave_message", "{name} đã rời đi."))))
        
        textbox_banned_words.delete("1.0", tk.END)
        resp = _remote_request("DB_QUERY", {"query": "SELECT word FROM blacklists WHERE guild_id=?", "params": [str(current_server_id)]})
        if resp and resp.get("ok"):
            words = [row.get("word", "") for row in resp.get("data", [])]
            textbox_banned_words.insert("1.0", "\n".join(words))
            
        entry_automod_mute_mins.delete(0, tk.END); entry_automod_mute_mins.insert(0, str(scf.get("automod_mute_minutes", cfg.get("automod_mute_minutes", 5))))
        entry_bg.delete(0, tk.END); entry_bg.insert(0, str(scf.get("background_image", cfg.get("background_image", ""))))
        entry_font.delete(0, tk.END); entry_font.insert(0, str(scf.get("font_file", cfg.get("font_file", ""))))
        entry_x.delete(0, tk.END); entry_x.insert(0, str(scf.get("avatar_x", cfg.get("avatar_x", 300))))
        entry_y.delete(0, tk.END); entry_y.insert(0, str(scf.get("avatar_y", cfg.get("avatar_y", 50))))
        entry_size.delete(0, tk.END); entry_size.insert(0, str(scf.get("avatar_size", cfg.get("avatar_size", 200))))
        
        cid = str(scf.get("welcome_channel_id", cfg.get("welcome_channel_id", "")))
        combo_welcome_channel.set(next((c["name"] for c in current_server_data.get("channels", []) if str(c["id"]) == cid), "Không Yêu Cầu"))
        
        am_cid = str(scf.get("automod_channel_id", cfg.get("automod_channel_id", "")))
        combo_automod_channel.set(next((c["name"] for c in current_server_data.get("channels", []) if str(c["id"]) == am_cid), "Không Yêu Cầu"))
        
        log_cid = str(scf.get("log_channel_id", cfg.get("log_channel_id", "")))
        combo_log_channel.set(next((c["name"] for c in current_server_data.get("channels", []) if str(c["id"]) == log_cid), "Không Yêu Cầu"))
        
        arid = scf.get("auto_role_id", cfg.get("auto_role_id"))
        combo_auto_role.set(next((r["name"] for r in current_server_data.get("roles", []) if r["id"] == arid), "Không Yêu Cầu"))
        
        vcat_id = str(scf.get("voice_category_id", ""))
        combo_voice_category.set(next((c["name"] for c in current_server_data.get("categories", []) if str(c["id"]) == vcat_id), "Không Yêu Cầu (Tạo thư mục mặc định)"))
        
        global current_mod_roles
        current_mod_roles = []
        mr_ids = scf.get("mod_role_ids", [])
        if not mr_ids and scf.get("mod_role_id"):
            mr_ids = [scf.get("mod_role_id")]
        for saved_id in mr_ids:
            r_name = next((r["name"] for r in current_server_data.get("roles", []) if str(r["id"]) == str(saved_id)), None)
            if r_name: current_mod_roles.append({"id": str(saved_id), "name": r_name})
        refresh_mod_roles_ui()

        # Boost settings
        boost_cid = str(scf.get("boost_channel_id", ""))
        combo_boost_channel.set(next((c["name"] for c in current_server_data.get("channels", []) if str(c["id"]) == boost_cid), "Không Yêu Cầu"))
        booster_rid = str(scf.get("booster_role_id", ""))
        combo_booster_role.set(next((r["name"] for r in current_server_data.get("roles", []) if str(r["id"]) == booster_rid), "Không Yêu Cầu"))
        entry_boost_msg.delete(0, "end"); entry_boost_msg.insert(0, str(scf.get("boost_message", "")))

        # Xác minh thành viên
        pending_rid = str(scf.get("pending_role_id", ""))
        combo_pending_role.set(next((r["name"] for r in current_server_data.get("roles", []) if str(r["id"]) == pending_rid), "Không Bật Xác Minh"))
        verify_cid = str(scf.get("verify_channel_id", ""))
        combo_verify_channel.set(next((c["name"] for c in current_server_data.get("channels", []) if str(c["id"]) == verify_cid), "Không Yêu Cầu"))

        rr_cid = str(scf.get("rr_channel_id", ""))
        combo_rr_channel.set(next((c["name"] for c in current_server_data.get("channels", []) if str(c["id"]) == rr_cid), "Không Yêu Cầu"))
        entry_rr_title.delete(0, 'end'); entry_rr_title.insert(0, str(scf.get("rr_title", "")))
        global current_rr_roles
        current_rr_roles = []
        saved_rrs = scf.get("rr_roles_list", [])
        for saved_id in saved_rrs:
            r_name = next((r["name"] for r in current_server_data.get("roles", []) if str(r["id"]) == saved_id), None)
            if r_name: current_rr_roles.append({"id": saved_id, "name": r_name})
        refresh_rr_roles_ui()

    except Exception as e:
        import traceback
        traceback.print_exc()
        messagebox.showerror("Lỗi khi chọn Server", str(e))

combo_servers.configure(command=on_server_select)

lbl_status = ctk.CTkLabel(root, text="TRẠNG THÁI: CHƯA HOẠT ĐỘNG", text_color="#FEE75C", font=("Segoe UI", 16, "bold")); lbl_status.pack()
bfr = ctk.CTkFrame(root, fg_color="transparent"); bfr.pack(pady=5)
ctk.CTkButton(bfr, text="▶ CHẠY BOT", height=40, font=("Segoe UI", 14, "bold"), fg_color="#23A559", command=start_bot).pack(side="left", padx=5)
ctk.CTkButton(bfr, text="⏹ NGỪNG", height=40, font=("Segoe UI", 14, "bold"), fg_color="#DA373C", command=stop_bot).pack(side="left", padx=5)
ctk.CTkButton(root, text="💾 LƯU CẤU HÌNH SERVER VÀ TÁI KHỞI ĐỘNG", height=40, font=("Segoe UI", 14, "bold"), fg_color="#5865F2", command=save_and_reset).pack(pady=(5,30))

def on_closing(): stop_bot(); root.destroy(); os._exit(0)
root.protocol("WM_DELETE_WINDOW", on_closing)

# TAB SOCIAL MEDIA
DB_PATH = os.path.join("databases", "bot_core.db")

def get_social_db():
    if not os.path.exists(DB_PATH): return []
    resp = _remote_request("DB_QUERY", {"query": "SELECT guild_id, platform, target_id, channel_id, ping_role FROM social_tracker"})
    if resp and resp.get("ok"):
        return [[r["guild_id"], r["platform"], r["target_id"], r["channel_id"], r["ping_role"]] for r in resp.get("data", [])]
    return []

def refresh_social_list():
    for w in social_list_frame.winfo_children(): w.destroy()
    rows = get_social_db()
    if not rows:
        ctk.CTkLabel(social_list_frame, text="Chưa có Ăng-ten nào. Thêm mới bên trên!",
                     text_color="#888", font=("Segoe UI", 12)).pack(pady=20)
        return

    PLATFORM_COLORS = {"youtube": "#FF0000", "reddit": "#FF4500", "tiktok": "#010101", "facebook": "#1877F2"}
    PLATFORM_ICONS  = {"youtube": "▶️", "reddit": "🟧", "tiktok": "🎵", "facebook": "🔵"}
    for row in rows:
        guild_id, plat, target_id, channel_id, ping_role = row
        color = PLATFORM_COLORS.get(plat, "#5865F2")
        icon  = PLATFORM_ICONS.get(plat, "🔗")

        row_frame = ctk.CTkFrame(social_list_frame, fg_color="#2B2D31", corner_radius=10)
        row_frame.pack(fill="x", padx=5, pady=4)

        left = ctk.CTkFrame(row_frame, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True, padx=10, pady=8)

        header = ctk.CTkLabel(left,
            text=f"{icon} {plat.upper()}",
            font=("Segoe UI", 13, "bold"), text_color=color)
        header.pack(anchor="w")

        ctk.CTkLabel(left, text=f"Target: {target_id[:60]}",
                     font=("Segoe UI", 11), text_color="#ccc").pack(anchor="w")
        ctk.CTkLabel(left, text=f"Channel ID: {channel_id}  |  Ping: {ping_role or 'None'}",
                     font=("Segoe UI", 10), text_color="#888").pack(anchor="w")

        def make_delete(g=guild_id, p=plat, t=target_id):
            def _del():
                try:
                    _remote_request("DB_QUERY", {"query": "DELETE FROM social_tracker WHERE guild_id=? AND platform=? AND target_id=?", "params": [g, p, t]})
                    refresh_social_list()
                except Exception as e:
                    messagebox.showerror("Lỗi", str(e))
            return _del

        ctk.CTkButton(row_frame, text="❌ Xóa", width=70, height=30,
                      fg_color="#DA373C", hover_color="#A12828",
                      command=make_delete()).pack(side="right", padx=10)

# Header card
fsc_header = ctk.CTkFrame(sf_social, fg_color="#5865F2", corner_radius=12)
fsc_header.pack(pady=10, fill="x", padx=5)
ctk.CTkLabel(fsc_header, text="📡 TRUNG TÂM QUẢN LÝ RADAR MẠNG XÃ HỘI",
             font=("Segoe UI", 15, "bold"), text_color="white").pack(pady=(12,4))
ctk.CTkLabel(fsc_header, text="Tự động cào tin tức từ YouTube / Reddit / TikTok / Facebook và thông báo vào kênh Discord!\n(Lưu ý: Bot phải đang chạy thì mậy mới lấy được danh sách Channel thực tế.)",
             font=("Segoe UI", 11), text_color="#ddd", justify="center").pack(pady=(0,12))

# Add form card
fsc_add = ctk.CTkFrame(sf_social, fg_color="#2B2D31", corner_radius=12)
fsc_add.pack(pady=5, fill="x", padx=5)
ctk.CTkLabel(fsc_add, text="➕ ĂNG-TEN SÓNG MỚI",
             font=("Segoe UI", 13, "bold"), text_color="#23A559").pack(pady=(12,5))

social_add_body = ctk.CTkFrame(fsc_add, fg_color="transparent")
social_add_body.pack(fill="x", padx=15, pady=5)

# Row 1: Platform + Server selector
row1 = ctk.CTkFrame(social_add_body, fg_color="transparent")
row1.pack(fill="x", pady=(0,8))

ctk.CTkLabel(row1, text="Nền Tảng:", font=("Segoe UI", 12, "bold"), width=110, anchor="w").pack(side="left")
combo_social_platform = ctk.CTkComboBox(row1, values=["youtube","reddit","tiktok","facebook"],
                                         width=140, height=32, font=("Segoe UI", 12))
combo_social_platform.set("youtube")
combo_social_platform.pack(side="left", padx=(0,15))

ctk.CTkLabel(row1, text="Server:", font=("Segoe UI", 12, "bold"), width=60, anchor="w").pack(side="left")
combo_social_server = ctk.CTkComboBox(row1,
    values=["(Nhấn F5 để tải Server)"] + list(srv_data.keys()),
    width=200, height=32, font=("Segoe UI", 11))
combo_social_server.pack(side="left")

# Row 2: Target URL/ID
row2 = ctk.CTkFrame(social_add_body, fg_color="transparent")
row2.pack(fill="x", pady=(0,8))
ctk.CTkLabel(row2, text="Link / ID / Tên:", font=("Segoe UI", 12, "bold"), width=110, anchor="w").pack(side="left")
entry_social_target = ctk.CTkEntry(row2, placeholder_text="VD: UCxxxx (YouTube) | programming (Reddit) | @mrwhosetheboss (TikTok) | https://rss.app/... (FB)",
                                    width=410, height=32, font=("Segoe UI", 11))
entry_social_target.pack(side="left")

# Row 3: Channel ID + optional ping
row3 = ctk.CTkFrame(social_add_body, fg_color="transparent")
row3.pack(fill="x", pady=(0,8))
ctk.CTkLabel(row3, text="Channel ID:", font=("Segoe UI", 12, "bold"), width=110, anchor="w").pack(side="left")
combo_social_channel = ctk.CTkComboBox(row3, values=["(Chọn server trước)"],
                                         width=220, height=32, font=("Segoe UI", 11))
combo_social_channel.pack(side="left", padx=(0,15))

ctk.CTkLabel(row3, text="Ping:", font=("Segoe UI", 12, "bold"), width=40, anchor="w").pack(side="left")
entry_social_ping = ctk.CTkEntry(row3, placeholder_text="@everyone hoặc để trống",
                                  width=140, height=32, font=("Segoe UI", 11))
entry_social_ping.pack(side="left")

def on_social_server_select(choice):
    """Load channels for selected server into the channel combobox."""
    try:
        # Find server id by name
        for sid, sdata in srv_data.items():
            if sdata.get("name") == choice or sid == choice:
                channels = [(c["name"], str(c["id"])) for c in sdata.get("channels", [])]
                combo_social_channel.configure(values=[f"{n} ({i})" for n, i in channels])
                if channels:
                    combo_social_channel.set(f"{channels[0][0]} ({channels[0][1]})")
                return
    except: pass

combo_social_server.configure(command=on_social_server_select)
# Populate with server names (not IDs)
combo_social_server.configure(values=[v.get("name", k) for k, v in srv_data.items()])

def btn_add_social_click():
    platform = combo_social_platform.get().lower().strip()
    target   = entry_social_target.get().strip()
    ping     = entry_social_ping.get().strip()
    chan_val  = combo_social_channel.get()

    if not platform or not target:
        return messagebox.showwarning("⚠️ Thiếu dữ liệu", "Vui lòng chọn Nền Tảng và nhập Link/ID.")
    if "(" not in chan_val:
        return messagebox.showwarning("⚠️ Thiếu kênh", "Vui lòng chọn Server và Kênh nhận thông báo.")

    # Extract channel ID from "channel-name (123456789)"
    channel_id = chan_val.rsplit("(", 1)[-1].rstrip(")")

    # Find guild_id for the selected server name
    sv_name = combo_social_server.get()
    guild_id = next((k for k, v in srv_data.items() if v.get("name") == sv_name), "")
    if not guild_id:
        return messagebox.showwarning("⚠️ Thiếu Server", "Không tìm thấy Server ID. Vui lòng chọn lại.")

    # Normalise target_id
    target_id = target
    if platform == "youtube":
        m = __import__("re").search(r'channel/(UC[\w-]+)', target)
        if m: target_id = m.group(1)
    elif platform == "reddit" and "reddit.com/r/" in target:
        target_id = target.split("reddit.com/r/")[1].split("/")[0]
    elif platform == "tiktok":
        target_id = target.lstrip("@").split("/")[-1].split("?")[0]
    # facebook: keep as-is (RSS url)

    try:
        _remote_request("DB_QUERY", {
            "query": "INSERT OR REPLACE INTO social_tracker (guild_id, platform, target_id, channel_id, ping_role, last_post_id) VALUES (?, ?, ?, ?, ?, ?)",
            "params": [guild_id, platform, target_id, channel_id, ping, "NO_POST_YET"]
        })
        entry_social_target.delete(0, tk.END)
        entry_social_ping.delete(0, tk.END)
        refresh_social_list()
        messagebox.showinfo("✅ Thành công!",
            f"Đã cắm Ăng-ten {platform.upper()} cho {target_id}\nBot sẽ bưng bài vào channel thông báo sau ≤ 5 phút.")
    except Exception as e:
        messagebox.showerror("❌ Lỗi DB", str(e))

ctk.CTkButton(fsc_add, text="➕ Cắm Ăng-ten Sóng", height=36, width=200,
              font=("Segoe UI", 13, "bold"),
              fg_color="#23A559", hover_color="#1A7A41",
              command=btn_add_social_click).pack(pady=(5,14))

# Help card
fsc_help = ctk.CTkFrame(sf_social, fg_color="#1e3a2f", corner_radius=10)
fsc_help.pack(pady=5, fill="x", padx=5)
help_text = ("""ℹ️ HƯỠNG DỬAẠ__SỨ DỤNG__

▶ YouTube — Dán Channel URL hoặc chỉ nhập Channel ID (bắt đầu bằng UC...)
🟧 Reddit  — Nhập tên subreddit (VD: worldnews, leagueoflegends)
🎵 TikTok — Nhập username (VD: @mrwhosetheboss hoặc chỉ mrwhosetheboss)
🔵 Facebook — Dán URL RSS được tạo từ rss.app hoặc rssbridge.org

Ping — Nhập @everyone, @here hoặc để trống nếu không muốn ping ai.""")
ctk.CTkLabel(fsc_help, text=help_text, font=("Segoe UI", 11),
             text_color="#a8f0c6", justify="left").pack(padx=15, pady=10, anchor="w")

# List card
fsc_list_header = ctk.CTkFrame(sf_social, fg_color="#2B2D31", corner_radius=12)
fsc_list_header.pack(pady=(10,0), fill="x", padx=5)
ctk.CTkLabel(fsc_list_header, text="📡 DANH SÁCH ĂNG-TEN ĐANG BẮT SÓNG",
             font=("Segoe UI", 13, "bold"), text_color="#00b4d8").pack(side="left", padx=15, pady=8)
ctk.CTkButton(fsc_list_header, text="🔄 Làm Mới", width=90, height=30,
              fg_color="#4752C4", hover_color="#3641a0",
              command=refresh_social_list).pack(side="right", padx=10)

social_list_frame = ctk.CTkScrollableFrame(sf_social, fg_color="transparent", height=280)
social_list_frame.pack(fill="x", padx=5, pady=(0,10))

refresh_social_list()


root.mainloop()