import base64
import hashlib
# import mimetypes
import json
from pathlib import Path
from typing import Any, Callable, Collection
import tkinter as tk
from tkinter import ttk, filedialog
from tkinter.scrolledtext import ScrolledText
from time import time

# Constants
KEY_CANDIDATES = {"image", "bgImage", "backgroundImage", "rowBackgroundImage"}
CONFIG_FILE = "config.json"

# Utility functions

def get_hash(data: str) -> str:
    h = hashlib.sha256()
    h.update(data.encode('utf-8'))
    return h.hexdigest()

def neocities_abs_path(id:str, x:str) -> str:
    return f"https://{id.strip()}.neocities.org/{x.strip()}"

def save_base64_image(b64_string: str, folder_path: str) -> str:
    # Strip header if present
    if b64_string.startswith("data:"):
        header, b64_data = b64_string.split(",", 1)
        mime = header.split(";", 1)[0].split(":", 1)[1]
    else:
        b64_data = b64_string
        mime = None

    # ext = mimetypes.guess_extension(mime) if mime else None
    # if ext == ".jpe": ext = ".jpg"
    # ext = ext or ".webp"
    ext = ".webp"  # Default to webp for consistency

    filename = get_hash(b64_data) + ext
    out_path = Path(folder_path) / filename
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img_bytes = base64.b64decode(b64_data)
    out_path.write_bytes(img_bytes)
    return str(filename)


def apply_to_keys(obj: Any,
                  apply_function: Callable[[Any], Any],
                  keys: Collection[str] = KEY_CANDIDATES,
                  condition: Callable[[Any], bool] = lambda x: True) -> None:
    if isinstance(obj, dict):
        for k, v in list(obj.items()):
            if k in keys and condition(v):
                obj[k] = apply_function(v)
            else:
                apply_to_keys(v, apply_function, keys, condition)
    elif isinstance(obj, list):
        for item in obj:
            apply_to_keys(item, apply_function, keys, condition)


def load_config() -> dict:
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        default = {
            "folder_path": str(Path.cwd()),
            "img_folder": "iccup2",
            "id": "",
            "pw": "",
            "last_file": ""
        }
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(default, f, indent=2)
        return default


def save_config(cfg: dict) -> None:
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, indent=2)


class App(ttk.Frame):
    def __init__(self, root):
        super().__init__(root, padding=20)
        self.root = root
        self.root.title("ICC-UP 2.01 Offline")
        self.config = load_config()
        self.setup_style()
        self.build_ui()
        self.load_state()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.pack(fill='both', expand=True)

    def setup_style(self):
        s = ttk.Style()
        s.theme_use('clam')
        s.configure('TFrame', background='#f0f0f0')
        s.configure('TButton', font=('Segoe UI', 10), padding=6)
        s.configure('TLabel', background='#f0f0f0', font=('Segoe UI', 10))
        s.configure('TCheckbutton', background='#f0f0f0', font=('Segoe UI', 10))

    def build_ui(self):
        # File selection
        ff = ttk.Frame(self); ff.pack(fill='x', pady=5)
        ttk.Button(ff, text="JSON 파일을 선택하시오...", command=self.select_file).pack(side='left')
        self.file_label = ttk.Label(ff, text="선택하지 않으면 시작되지 않습니다.", width=40)
        self.file_label.pack(side='left', padx=10)

        # Message label
        self.message = tk.StringVar(value="준비 완료.")
        ttk.Label(self, textvariable=self.message).pack(fill='x', pady=5)

        # Image folder input
        mf = ttk.LabelFrame(self, text='기본설정', padding=10)
        mf.pack(fill='x', pady=5)
        ttk.Label(mf, text='이미지 폴더:').pack(side='left')
        self.img_folder_var = tk.StringVar()
        self.img_folder_message = tk.StringVar(value="")
        ttk.Entry(mf, textvariable=self.img_folder_var, width=20).pack(side='left', padx=5)
        ttk.Label(mf, textvariable=self.img_folder_message).pack(side='left', padx=(5, 0))

        # Credentials
        cf = ttk.LabelFrame(self, text='Neocities', padding=10); cf.pack(fill='x', pady=5)
        ttk.Label(cf, text='ID(절대경로 사용 시 필요):').pack(side='left')
        self.id_var = tk.StringVar(); ttk.Entry(cf, textvariable=self.id_var, width=15).pack(side='left', padx=5)
        
        # ttk.Label(cf, text='Password').pack(side='left', padx=(10,0))
        # self.pw_var = tk.StringVar(); ttk.Entry(cf, textvariable=self.pw_var, show='*', width=15).pack(side='left', padx=5)


        # Options
        of = ttk.LabelFrame(self, text='옵션', padding=10)
        of.pack(fill='x', pady=5)

        self.opt_json_abspath = tk.BooleanVar()
        checkbutton1 = ttk.Checkbutton(of, text='ICC UP 2 스타일(절대경로 사용 / 추천)', variable=self.opt_json_abspath)
        checkbutton1.pack(side='left', padx=5)

        ## Default to absolute path
        checkbutton1.state(["selected"])
        self.opt_json_abspath.set(True) 
        
        
        # self.opt2 = tk.BooleanVar();
        # ttk.Checkbutton(of, text='구현 예정', variable=self.opt2).pack(side='left', padx=5)
        ttk.Checkbutton(of, text='초경량화 (미구현)').pack(side='left', padx=5)
        ttk.Checkbutton(of, text='이미지 깜박임 해결 (미구현)').pack(side='left', padx=5)
        # ttk.Checkbutton(of, text='').pack(side='left', padx=5)


        # Buttons
        bf = ttk.Frame(self); bf.pack(fill='x', pady=10)
        ttk.Button(bf, text="추출", command=self.start_process).pack(side='left')
        ttk.Button(bf, text="업로드(미구현)").pack(side='left', padx=5)

        # Log area
        lf = ttk.LabelFrame(self, text='Log', padding=10); lf.pack(fill='both', expand=True, pady=5)
        self.log = ScrolledText(lf, wrap='word', state='disabled', height=12)
        self.log.pack(fill='both', expand=True)
        
        
        
        # OnChange event to update image folder message
        self.id_var.trace_add("write", self.update_img_folder_message)
        self.img_folder_var.trace_add("write", self.update_img_folder_message)
        self.opt_json_abspath.trace_add("write", self.update_img_folder_message)
        


    def load_state(self):
        # Restore saved state
        cfg = self.config
        self.id_var.set(cfg.get('id', ''))
        # self.pw_var.set(cfg.get('pw', ''))
        self.img_folder_var.set(cfg.get('img_folder', 'iccup2'))
        last = cfg.get('last_file', '')
        self.file_label.config(text=last if last else "고르라니까?")
        
        self.update_img_folder_message()

    # Update text when ID is changed (real-time)
    def update_img_folder_message(self, *args):
        img_folder = self.img_folder_var.get().strip() or 'iccup2'
        id_value = self.id_var.get().strip()
        
        use_abs_path = self.opt_json_abspath.get()

        if not use_abs_path:
            self.img_folder_message.set(f"json 대체값: {img_folder}/xxx.webp")
            return
        
        if id_value:
            self.img_folder_message.set("json 대체값: " + neocities_abs_path(id_value, img_folder) + '/xxx.webp')
        else:
            # If no ID is set, show a warning
            self.img_folder_message.set("경고: 절대경로 사용 시 ID가 필요합니다.")

    def save_state(self):
        # Save current state
        cfg = self.config
        cfg['id'] = self.id_var.get().strip()
        # cfg['pw'] = self.pw_var.get().strip()
        cfg['img_folder'] = self.img_folder_var.get().strip() or 'iccup2'
        save_config(cfg)

    def select_file(self):
        initial = self.config.get('folder_path', str(Path.cwd()))
        path = filedialog.askopenfilename(
            title="JSON 파일을 선택하세요.",
            filetypes=[('JSON', '*.json')],
            initialdir=initial
        )
        if path:
            self.file_label.config(text=path)
            self.config['folder_path'] = str(Path(path).parent)
            self.config['last_file'] = path
            self.save_state()
            self.log_message(f"Selected: {path}")
            self.message.set("준비 완료.")

    # def upload_file(self):
    #     if not self.file_label.cget('text').endswith('.json'):
    #         self.message.set("No JSON file selected.")
    #         return
    #     if not self.id_var.get() or not self.pw_var.get():
    #         self.message.set("Missing credentials.")
    #         return
    #     self.log_message("Upload simulated.")
    #     self.message.set("Upload done.")
    #     self.save_state()

    def start_process(self):
        fp = self.file_label.cget('text')
        if not fp.endswith('.json'):
            self.message.set("json 파일을 선택하세요.")
            return
        self.message.set("Processing...")
        self.log_message("Process start...")
        try:
            data = json.load(open(fp, 'r', encoding='utf-8'))
        except Exception as e:
            self.log_message(f"JSON load error: {e}")
            self.message.set("Failed to load JSON.")
            return

        # Determine output folder
        img_folder = self.img_folder_var.get().strip() or 'iccup2'
        out_folder = Path(fp).parent / img_folder
        n = 0

        ## Bake it
        self_optjsonabspath = self.opt_json_abspath.get()
        self_idvar = self.id_var.get().strip()

        print(self_optjsonabspath, self_idvar, out_folder)

        def k(x: str) -> str:
            nonlocal n
            n += 1
            self.log_message(f"Img {n}: {x[:10]}...")


            filename = save_base64_image(x, str(out_folder))
            
            # file path is img_folder/filename
            filepath = str(Path(img_folder) / filename)
            if self_optjsonabspath:
                # Use absolute path
                return neocities_abs_path(self_idvar, filepath)
            return filepath

        apply_to_keys(data, k, condition=lambda v: isinstance(v, str) and v.startswith('data:'))
        self.log_message(f"{n} 개의 이미지를 추출했습니다.")

        if n==0:
            pass
            # Alert user that this file already processed
            self.log_message("이미지 추출이 필요하지 않습니다. 이 파일은 이미 처리되었습니다.")
            self.message.set("No images to process.")
            return


        # Backup original
        js = Path(fp)
        bak = js.with_suffix(f'.json.{int(time())}backup')
        js.rename(bak)
        self.log_message(f"Backup: {bak.name}")

        # Save modified JSON
        with open(fp, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=None)
        self.log_message("수정된 JSON 저장 완료.")
        self.message.set("Done.")
        self.save_state()
        
        send_parse_event(
            image_count=n,
            total_image_size_MB=out_folder.stat().st_size / (1024 * 1024),  # Convert bytes to MB
            neocities_id=self_idvar
        )

    def log_message(self, msg: str):
        self.log.config(state='normal')
        self.log.insert('end', msg + '\n')
        self.log.see('end')
        self.log.config(state='disabled')

    def on_close(self):
        self.save_state()
        self.root.destroy()

### About the GA(logging) ###
import uuid
import requests
import os
from dotenv import load_dotenv

load_dotenv()  # .env 파일에서 환경 변수 로드
MEASUREMENT_ID = os.getenv("GA_MEASUREMENT_ID") 
API_SECRET     = os.getenv("GA_API_SECRET")

def send_event(name: str, params: dict | None = None, client_id: str | None = None):
    endpoint = (
        f"https://www.google-analytics.com/mp/collect"
        f"?measurement_id={MEASUREMENT_ID}&api_secret={API_SECRET}"
    )
    payload = {
        "client_id": client_id or str(uuid.uuid4()),
        "events": [
            {
                "name": name,
                "params": params or {
                    "engagement_time_msec": "1",
                },
            }
        ],
    }
    try:
        debug_resp = requests.post(endpoint.replace("/mp/", "/debug/mp/"), json=payload, timeout=3)
        live_resp = requests.post(endpoint, json=payload, timeout=3)
        live_resp.raise_for_status()
        return live_resp.status_code
    except:
        # Looks like offline, so just ignore the error
        print(f"Failed to send event {name}. This is expected in offline mode.")
        return 200



def send_parse_event(image_count:int, total_image_size_MB:float, neocities_id:str = ""):
    try:
        user_ip = requests.get('https://api.ipify.org').text
        ip_hash = hashlib.sha256(user_ip.encode('utf-8')).hexdigest()[:16]  # Shorten for privacy
        
    except requests.RequestException:
        print("Failed to get public IP address. Using 'unknown'.")
        ip_hash = "unknown"
    
    return send_event(
        name="main",
        client_id=ip_hash,  # Use hashed IP as client_id for privacy
        params={
            "method": "cli",
            "non_personalized_ads": True,
            "image_count": image_count,
            "total_image_size_MB": total_image_size_MB,
            "neocities_id": neocities_id,
        },
    )

if __name__ == '__main__':
    root = tk.Tk()
    root.geometry('680x620')
    App(root)
    root.mainloop()
