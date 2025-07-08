#!/usr/bin/env python3
"""
JPEG Orientation Fixer & Rotator
Bu script JPEG dosyalarının EXIF orientation bilgisini düzeltir ve gerektiğinde dosyaları döndürür.
Drag & drop arayüzü ile kolayca kullanılabilir.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import sys
import subprocess
import threading
from pathlib import Path
from PIL import Image, ImageTk
import piexif

class JPEGOrientationFixer:
    def __init__(self, root):
        self.root = root
        self.root.title("JPEG Orientation Fixer")
        self.root.geometry("800x600")
        self.root.configure(bg='#f0f0f0')
        
        # Stil ayarları
        style = ttk.Style()
        style.theme_use('clam')
        
        self.setup_ui()
        self.check_exiftool()
        
    def setup_ui(self):
        # Ana frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Başlık
        title_label = ttk.Label(main_frame, text="JPEG Orientation Fixer", 
                               font=('Arial', 18, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Açıklama
        desc_label = ttk.Label(main_frame, 
                              text="JPEG dosyalarını buraya sürükleyip bırakın veya klasör seçin",
                              font=('Arial', 12))
        desc_label.grid(row=1, column=0, columnspan=2, pady=(0, 10))
        
        # Drag & Drop alanı
        self.drop_frame = tk.Frame(main_frame, bg='#e8e8e8', relief='dashed', bd=2)
        self.drop_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        self.drop_frame.configure(height=200)
        
        # Drag & Drop label
        self.drop_label = tk.Label(self.drop_frame, 
                                  text="JPEG dosyalarını buraya sürükleyip bırakın\n\nveya aşağıdaki butonları kullanın",
                                  bg='#e8e8e8', font=('Arial', 14),
                                  fg='#666666')
        self.drop_label.place(relx=0.5, rely=0.5, anchor='center')
        
        # Butonlar frame'i
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=3, column=0, columnspan=2, pady=20)
        
        # Dosya seçme butonu
        self.select_files_btn = ttk.Button(buttons_frame, text="Dosyaları Seç", 
                                          command=self.select_files, width=15)
        self.select_files_btn.grid(row=0, column=0, padx=5)
        
        # Klasör seçme butonu
        self.select_folder_btn = ttk.Button(buttons_frame, text="Klasör Seç", 
                                           command=self.select_folder, width=15)
        self.select_folder_btn.grid(row=0, column=1, padx=5)
        
        # Seçenekler frame'i
        options_frame = ttk.LabelFrame(main_frame, text="Seçenekler", padding="10")
        options_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        # EXIF orientation düzeltme
        self.fix_exif_var = tk.BooleanVar(value=True)
        fix_exif_check = ttk.Checkbutton(options_frame, text="EXIF Orientation bilgisini düzelt (Orientation=1)", 
                                        variable=self.fix_exif_var)
        fix_exif_check.grid(row=0, column=0, sticky=tk.W, pady=2)
        
        # 90 derece döndürme
        self.rotate_var = tk.BooleanVar(value=False)
        rotate_check = ttk.Checkbutton(options_frame, text="Dosyaları 90° saat yönünde döndür", 
                                      variable=self.rotate_var)
        rotate_check.grid(row=1, column=0, sticky=tk.W, pady=2)
        
        # Orijinal dosyaları yedekle
        self.backup_var = tk.BooleanVar(value=True)
        backup_check = ttk.Checkbutton(options_frame, text="Orijinal dosyaları yedekle (önerilen)", 
                                      variable=self.backup_var)
        backup_check.grid(row=2, column=0, sticky=tk.W, pady=2)
        
        # İşlem butonu
        self.process_btn = ttk.Button(main_frame, text="İşlemleri Başlat", 
                                     command=self.start_processing, 
                                     style='Accent.TButton')
        self.process_btn.grid(row=5, column=0, columnspan=2, pady=20)
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='determinate')
        self.progress.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Log alanı
        log_frame = ttk.LabelFrame(main_frame, text="İşlem Geçmişi", padding="5")
        log_frame.grid(row=7, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        
        self.log_text = tk.Text(log_frame, height=8, width=80, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Grid weight ayarları
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(7, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        # Drag & Drop bağlamaları
        self.setup_drag_drop()
        
        self.selected_files = []
        
    def setup_drag_drop(self):
        """Drag & Drop işlevselliğini ayarla"""
        # macOS için drag & drop
        self.drop_frame.bind("<Button-1>", self.on_drop_click)
        self.drop_label.bind("<Button-1>", self.on_drop_click)
        
        # Drag olayları (macOS için sınırlı destek)
        try:
            self.root.tk.call('package', 'require', 'tkdnd')
            from tkdnd import DND_FILES
            self.drop_frame.drop_target_register(DND_FILES)
            self.drop_frame.dnd_bind('<<DropEnter>>', self.on_drop_enter)
            self.drop_frame.dnd_bind('<<DropLeave>>', self.on_drop_leave)
            self.drop_frame.dnd_bind('<<Drop>>', self.on_drop)
        except:
            # tkdnd mevcut değilse, click ile dosya seçme
            pass
    
    def on_drop_click(self, event):
        """Drop alanına tıklandığında dosya seçme diyaloğunu aç"""
        self.select_files()
    
    def on_drop_enter(self, event):
        self.drop_frame.configure(bg='#d0d0d0')
        self.drop_label.configure(bg='#d0d0d0')
        
    def on_drop_leave(self, event):
        self.drop_frame.configure(bg='#e8e8e8')
        self.drop_label.configure(bg='#e8e8e8')
        
    def on_drop(self, event):
        files = self.root.tk.splitlist(event.data)
        self.process_dropped_files(files)
        self.drop_frame.configure(bg='#e8e8e8')
        self.drop_label.configure(bg='#e8e8e8')
    
    def process_dropped_files(self, files):
        """Sürüklenen dosyaları işle"""
        jpeg_files = []
        for file_path in files:
            if os.path.isfile(file_path):
                if file_path.lower().endswith(('.jpg', '.jpeg')):
                    jpeg_files.append(file_path)
            elif os.path.isdir(file_path):
                # Klasördeki JPEG dosyalarını bul
                for root, dirs, files in os.walk(file_path):
                    for file in files:
                        if file.lower().endswith(('.jpg', '.jpeg')):
                            jpeg_files.append(os.path.join(root, file))
        
        if jpeg_files:
            self.selected_files = jpeg_files
            self.update_drop_label()
            self.log(f"{len(jpeg_files)} JPEG dosyası seçildi")
        else:
            messagebox.showwarning("Uyarı", "Seçilen dosyalar arasında JPEG dosyası bulunamadı!")
    
    def select_files(self):
        """Dosya seçme diyaloğu"""
        files = filedialog.askopenfilenames(
            title="JPEG dosyalarını seçin",
            filetypes=[("JPEG files", "*.jpg *.jpeg"), ("All files", "*.*")]
        )
        if files:
            self.selected_files = list(files)
            self.update_drop_label()
            self.log(f"{len(files)} dosya seçildi")
    
    def select_folder(self):
        """Klasör seçme diyaloğu"""
        folder = filedialog.askdirectory(title="JPEG dosyalarının bulunduğu klasörü seçin")
        if folder:
            jpeg_files = []
            for root, dirs, files in os.walk(folder):
                for file in files:
                    if file.lower().endswith(('.jpg', '.jpeg')):
                        jpeg_files.append(os.path.join(root, file))
            
            if jpeg_files:
                self.selected_files = jpeg_files
                self.update_drop_label()
                self.log(f"{folder} klasöründe {len(jpeg_files)} JPEG dosyası bulundu")
            else:
                messagebox.showwarning("Uyarı", "Seçilen klasörde JPEG dosyası bulunamadı!")
    
    def update_drop_label(self):
        """Drop alanının etiketini güncelle"""
        if self.selected_files:
            count = len(self.selected_files)
            self.drop_label.configure(text=f"{count} JPEG dosyası seçildi\n\nİşlemleri başlatmak için 'İşlemleri Başlat' butonuna tıklayın")
        else:
            self.drop_label.configure(text="JPEG dosyalarını buraya sürükleyip bırakın\n\nveya aşağıdaki butonları kullanın")
    
    def check_exiftool(self):
        """exiftool'un yüklü olup olmadığını kontrol et"""
        try:
            result = subprocess.run(['exiftool', '-ver'], capture_output=True, text=True)
            if result.returncode == 0:
                self.log(f"exiftool bulundu (versiyon: {result.stdout.strip()})")
                return True
        except FileNotFoundError:
            pass
        
        # exiftool yoksa Homebrew ile yüklemeyi öner
        answer = messagebox.askyesno("exiftool bulunamadı", 
                                   "EXIF orientation düzeltme için exiftool gerekli.\n\n"
                                   "Homebrew ile yüklemek ister misiniz?\n"
                                   "(Terminal: brew install exiftool)")
        if answer:
            self.install_exiftool()
        return False
    
    def install_exiftool(self):
        """exiftool'u Homebrew ile yükle"""
        def install():
            try:
                self.log("exiftool yükleniyor...")
                result = subprocess.run(['brew', 'install', 'exiftool'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    self.log("exiftool başarıyla yüklendi!")
                else:
                    self.log(f"exiftool yükleme hatası: {result.stderr}")
            except Exception as e:
                self.log(f"Yükleme hatası: {str(e)}")
        
        threading.Thread(target=install, daemon=True).start()
    
    def start_processing(self):
        """İşlemleri başlat"""
        if not self.selected_files:
            messagebox.showwarning("Uyarı", "Lütfen önce dosyaları seçin!")
            return
        
        if not self.fix_exif_var.get() and not self.rotate_var.get():
            messagebox.showwarning("Uyarı", "Lütfen en az bir işlem seçin!")
            return
        
        # İşlemi ayrı thread'de çalıştır
        self.process_btn.configure(state='disabled')
        threading.Thread(target=self.process_files, daemon=True).start()
    
    def process_files(self):
        """Dosyaları işle"""
        total_files = len(self.selected_files)
        self.progress.configure(maximum=total_files)
        
        success_count = 0
        error_count = 0
        
        for i, file_path in enumerate(self.selected_files):
            try:
                self.log(f"İşleniyor: {os.path.basename(file_path)}")
                
                # Yedek oluştur
                if self.backup_var.get():
                    backup_path = file_path + '.backup'
                    if not os.path.exists(backup_path):
                        subprocess.run(['cp', file_path, backup_path], check=True)
                
                # EXIF orientation düzelt
                if self.fix_exif_var.get():
                    self.fix_exif_orientation(file_path)
                
                # Döndürme işlemi
                if self.rotate_var.get():
                    self.rotate_image(file_path)
                
                success_count += 1
                self.log(f"✓ Tamamlandı: {os.path.basename(file_path)}")
                
            except Exception as e:
                error_count += 1
                self.log(f"✗ Hata ({os.path.basename(file_path)}): {str(e)}")
            
            # Progress bar güncelle
            self.root.after(0, lambda: self.progress.configure(value=i+1))
        
        # İşlem tamamlandı
        self.root.after(0, self.processing_completed, success_count, error_count)
    
    def fix_exif_orientation(self, file_path):
        """EXIF orientation bilgisini düzelt"""
        try:
            # exiftool ile orientation'ı 1 yap
            result = subprocess.run([
                'exiftool', '-Orientation=1', '-n', '-overwrite_original', file_path
            ], capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError as e:
            # exiftool yoksa PIL ile deneme
            try:
                with Image.open(file_path) as img:
                    # EXIF verilerini oku
                    exif_data = piexif.load(img.info.get('exif', b''))
                    
                    # Orientation değerini 1 yap
                    exif_data['0th'][piexif.ImageIFD.Orientation] = 1
                    
                    # EXIF verilerini geri yaz
                    exif_bytes = piexif.dump(exif_data)
                    img.save(file_path, exif=exif_bytes, quality=95)
            except Exception:
                raise Exception("EXIF orientation düzeltilemedi")
    
    def rotate_image(self, file_path):
        """Görüntüyü 90 derece döndür"""
        # macOS'ta sips komutunu kullan
        try:
            result = subprocess.run([
                'sips', '-r', '90', file_path
            ], capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError:
            # sips çalışmazsa PIL kullan
            with Image.open(file_path) as img:
                rotated = img.rotate(-90, expand=True)
                rotated.save(file_path, quality=95)
    
    def processing_completed(self, success_count, error_count):
        """İşlem tamamlandığında çağrılır"""
        self.process_btn.configure(state='normal')
        self.progress.configure(value=0)
        
        message = f"İşlem tamamlandı!\n\n"
        message += f"Başarılı: {success_count} dosya\n"
        if error_count > 0:
            message += f"Hatalı: {error_count} dosya"
        
        messagebox.showinfo("Tamamlandı", message)
        self.log(f"--- İşlem tamamlandı: {success_count} başarılı, {error_count} hatalı ---")
    
    def log(self, message):
        """Log mesajı ekle"""
        def add_log():
            self.log_text.insert(tk.END, f"{message}\n")
            self.log_text.see(tk.END)
        
        if threading.current_thread() == threading.main_thread():
            add_log()
        else:
            self.root.after(0, add_log)

def main():
    """Ana fonksiyon"""
    root = tk.Tk()
    app = JPEGOrientationFixer(root)
    
    # Uygulama kapanırken temizlik
    def on_closing():
        root.quit()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        on_closing()

if __name__ == "__main__":
    main()
