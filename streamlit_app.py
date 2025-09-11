import tkinter as tk
from tkinter import filedialog, messagebox
import requests, base64, os, sys, json

# -------------------- Configuration --------------------
API_URL = "https://xmltools-g8vtzxnjbz7q3nuf3qj4y3.streamlit.app/?api=1"
EXE_TOKEN = "h3K7z9Pq2LxVbT8mR4sQ"  # must match Streamlit backend

# -------------------- Functions --------------------
def on_get():
    email = email_var.get().strip()
    serial = serial_var.get().strip()
    license_key = license_var.get().strip()
    xml_path = src_var.get().strip()

    if not email or not serial or not license_key or not xml_path:
        messagebox.showwarning("Missing Info", "⚠️ Please fill all fields and select XML file.")
        return

    try:
        with open(xml_path, "rb") as f:
            xml_content = f.read()
            xml_b64 = base64.b64encode(xml_content).decode()
    except Exception as e:
        messagebox.showerror("File Error", str(e))
        return

    payload = {
        "email": email,
        "serial": serial,
        "file_name": os.path.basename(xml_path),
        "file_content": xml_b64,
        "token": EXE_TOKEN,
        "license_key": license_key
    }

    try:
        r = requests.post(API_URL, json=payload, timeout=30)
        data = r.json()
    except Exception as e:
        messagebox.showerror("Server Error", str(e))
        return

    if data.get("status") != "success":
        messagebox.showerror("Error", data.get("message", "Unknown error"))
        return

    save_path = filedialog.asksaveasfilename(
        defaultextension=".xml",
        filetypes=[("XML files","*.xml"),("All files","*.*")],
        initialfile=f"xmlkey_{serial}.xml"
    )
    if not save_path:
        return

    key_xml = data.get("key_xml")  # Optional: backend can return XML content
    if key_xml:
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(key_xml)

    messagebox.showinfo("✅ Success", f"Request submitted successfully.\nSaved XML key to:\n{save_path}")

# -------------------- GUI --------------------
root = tk.Tk()
root.title("🔑 Secure XML Generator")
root.geometry("600x300")
root.configure(bg="#f8f9fa")
root.resizable(False, False)

font_label = ("Segoe UI", 11)
font_entry = ("Segoe UI", 11)
font_button = ("Segoe UI", 12, "bold")

# Row 1: Email
tk.Label(root, text="Your Email ID:", bg="#f8f9fa", font=font_label).grid(row=0, column=0, sticky="e", padx=15, pady=12)
email_var = tk.StringVar()
tk.Entry(root, textvariable=email_var, width=45, font=font_entry).grid(row=0, column=1, padx=5, pady=12, sticky="w")

# Row 2: Serial
tk.Label(root, text="Device Full Serial Number:", bg="#f8f9fa", font=font_label).grid(row=1, column=0, sticky="e", padx=15, pady=12)
serial_var = tk.StringVar()
tk.Entry(root, textvariable=serial_var, width=45, font=font_entry).grid(row=1, column=1, padx=5, pady=12, sticky="w")

# Row 3: License Key
tk.Label(root, text="Your License Key:", bg="#f8f9fa", font=font_label).grid(row=2, column=0, sticky="e", padx=15, pady=12)
license_var = tk.StringVar()
tk.Entry(root, textvariable=license_var, width=45, font=font_entry).grid(row=2, column=1, padx=5, pady=12, sticky="w")

# Row 4: XML File
tk.Label(root, text="Attach XML File:", bg="#f8f9fa", font=font_label).grid(row=3, column=0, sticky="e", padx=15, pady=12)
src_var = tk.StringVar()
tk.Entry(root, textvariable=src_var, width=38, font=font_entry).grid(row=3, column=1, padx=(5,0), pady=12, sticky="w")
def browse_file():
    p = filedialog.askopenfilename(filetypes=[("XML Files","*.xml"),("All files","*.*")])
    if p: src_var.set(p)
tk.Button(root, text="...", command=browse_file, width=4).grid(row=3, column=2, padx=5, pady=12)

# Row 5: Get Button
tk.Button(root, text="Get XML Key", command=on_get, bg="#0078d7", fg="white", font=font_button, width=14).grid(row=4, column=1, pady=20)

root.mainloop()
