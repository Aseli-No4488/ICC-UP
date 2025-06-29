import base64
import hashlib
import mimetypes
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

    ext = mimetypes.guess_extension(mime) if mime else None
    if ext == ".jpe": ext = ".jpg"
    ext = ext or ".webp"

    filename = get_hash(b64_data) + ext
    out_path = Path(folder_path) / filename
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img_bytes = base64.b64decode(b64_data)
    out_path.write_bytes(img_bytes)
    rel_path = out_path.relative_to(Path(folder_path).parent)
    return str(rel_path)


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
        self.root.title("ICC-UP Offline")
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

    def load_state(self):
        # Restore saved state
        cfg = self.config
        self.id_var.set(cfg.get('id', ''))
        # self.pw_var.set(cfg.get('pw', ''))
        self.img_folder_var.set(cfg.get('img_folder', 'iccup2'))
        last = cfg.get('last_file', '')
        self.file_label.config(text=last if last else "고르라니까?")

        self.img_folder_message.set(neocities_abs_path(self.id_var.get(), self.img_folder_var.get() or 'iccup2') + '/xxx.webp')

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

            if self_optjsonabspath:
                # Use absolute path
                return neocities_abs_path(self_idvar, save_base64_image(x, str(out_folder)))
            return save_base64_image(x, str(out_folder))

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

    def log_message(self, msg: str):
        self.log.config(state='normal')
        self.log.insert('end', msg + '\n')
        self.log.see('end')
        self.log.config(state='disabled')

    def on_close(self):
        self.save_state()
        self.root.destroy()

if __name__ == '__main__':
    root = tk.Tk()
    root.geometry('680x620')
    App(root)
    root.mainloop()
