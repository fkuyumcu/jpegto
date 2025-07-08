#!/usr/bin/env python3
"""
JPEG Orientation Fixer & Rotator - macOS Optimize Edilmiş Versiyon
Bu script JPEG dosyalarının EXIF orientation bilgisini düzeltir ve gerektiğinde dosyaları döndürür.
Basit drag & drop arayüzü ile kolayca kullanılabilir.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import sys
import subprocess
import threading
from pathlib import Path
from PIL import Image
import piexif

class JPEGOrientationFixer:
    def __init__(self, root):
        self.root = root
        self.root.title("JPEG Orientation Fixer")
        self.root.geometry("800x650")
        self.root.configure(bg='#f0f0f0')
        
        # macOS için native görünüm
        if sys.platform == "darwin":
            try:
                # macOS'ta daha iyi görünüm için
                self.root.tk.call('set', 'tk::mac::CGAntialiasLimit', '0')
            except:
                pass
        
        self.setup_ui()
        self.check_exiftool()
        
    def setup_ui(self):
        # Ana frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Başlık
        title_label = ttk.Label(main_frame, text="JPEG Orientation Fixer", 
                               font=('SF Pro Display', 18, 'bold') if sys.platform == "darwin" else ('Arial', 18, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Açıklama
        desc_label = ttk.Label(main_frame, 
                              text="JPEG dosyalarını seçin ve orientation/döndürme işlemlerini uygulayın",
                              font=('SF Pro Display', 12) if sys.platform == "darwin" else ('Arial', 12))
        desc_label.grid(row=1, column=0, columnspan=2, pady=(0, 10))
        
        # Dosya seçme alanı
        self.drop_frame = tk.Frame(main_frame, bg='#e8e8e8', relief='solid', bd=1)
        self.drop_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        self.drop_frame.configure(height=150)
        
        # Dosya seçme label
        self.drop_label = tk.Label(self.drop_frame, 
                                  text="Aşağıdaki butonları kullanarak JPEG dosyalarını seçin",
                                  bg='#e8e8e8', font=('SF Pro Display', 14) if sys.platform == "darwin" else ('Arial', 14),
                                  fg='#666666')
        self.drop_label.place(relx=0.5, rely=0.5, anchor='center')
        
        # Butonlar frame'i
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=3, column=0, columnspan=2, pady=15)
        
        # Dosya seçme butonu
        self.select_files_btn = ttk.Button(buttons_frame, text="📁 Dosyaları Seç", 
                                          command=self.select_files, width=18)
        self.select_files_btn.grid(row=0, column=0, padx=8)
        
        # Klasör seçme butonu
        self.select_folder_btn = ttk.Button(buttons_frame, text="📂 Klasör Seç", 
                                           command=self.select_folder, width=18)
        self.select_folder_btn.grid(row=0, column=1, padx=8)
        
        # Seçenekler frame'i
        options_frame = ttk.LabelFrame(main_frame, text="İşlem Seçenekleri", padding="15")
        options_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=15)
        
        # EXIF orientation düzeltme
        self.fix_exif_var = tk.BooleanVar(value=True)
        fix_exif_check = ttk.Checkbutton(options_frame, text="✅ EXIF Orientation bilgisini düzelt (Orientation=1)", 
                                        variable=self.fix_exif_var)
        fix_exif_check.grid(row=0, column=0, sticky=tk.W, pady=3)
        
        # 90 derece döndürme
        self.rotate_var = tk.BooleanVar(value=False)
        rotate_check = ttk.Checkbutton(options_frame, text="🔄 Dosyaları 90° saat yönünde döndür", 
                                      variable=self.rotate_var)
        rotate_check.grid(row=1, column=0, sticky=tk.W, pady=3)
        
        # Orijinal dosyaları yedekle
        self.backup_var = tk.BooleanVar(value=True)
        backup_check = ttk.Checkbutton(options_frame, text="💾 Orijinal dosyaları yedekle (.backup uzantısı ile)", 
                                      variable=self.backup_var)
        backup_check.grid(row=2, column=0, sticky=tk.W, pady=3)
        
        # İşlem butonu
        self.process_btn = ttk.Button(main_frame, text="🚀 İşlemleri Başlat", 
                                     command=self.start_processing)
        self.process_btn.grid(row=5, column=0, columnspan=2, pady=20)
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='determinate')
        self.progress.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Log alanı
        log_frame = ttk.LabelFrame(main_frame, text="İşlem Detayları", padding="5")
        log_frame.grid(row=7, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        
        # Log text widget ve scrollbar
        log_container = ttk.Frame(log_frame)
        log_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.log_text = tk.Text(log_container, height=10, width=80, wrap=tk.WORD,
                               font=('Monaco', 10) if sys.platform == "darwin" else ('Consolas', 10))
        scrollbar = ttk.Scrollbar(log_container, orient="vertical", command=self.log_text.yview)
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
        log_container.columnconfigure(0, weight=1)
        log_container.rowconfigure(0, weight=1)
        
        self.selected_files = []
        
    def select_files(self):
        """Dosya seçme diyaloğu"""
        files = filedialog.askopenfilenames(
            title="JPEG dosyalarını seçin",
            filetypes=[
                ("JPEG files", "*.jpg *.jpeg *.JPG *.JPEG"), 
                ("All files", "*.*")
            ]
        )
        if files:
            self.selected_files = list(files)
            self.update_drop_label()
            self.log(f"📁 {len(files)} dosya seçildi")
    
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
                self.log(f"📂 {folder} klasöründe {len(jpeg_files)} JPEG dosyası bulundu")
            else:
                messagebox.showwarning("Uyarı", "Seçilen klasörde JPEG dosyası bulunamadı!")
    
    def update_drop_label(self):
        """Drop alanının etiketini güncelle"""
        if self.selected_files:
            count = len(self.selected_files)
            self.drop_label.configure(
                text=f"✅ {count} JPEG dosyası seçildi\n\nİşlemleri başlatmaya hazır!",
                fg='#2e7d32'
            )
        else:
            self.drop_label.configure(
                text="Aşağıdaki butonları kullanarak JPEG dosyalarını seçin",
                fg='#666666'
            )
    
    def check_exiftool(self):
        """exiftool'un yüklü olup olmadığını kontrol et"""
        try:
            result = subprocess.run(['exiftool', '-ver'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                version = result.stdout.strip()
                self.log(f"✅ exiftool bulundu (versiyon: {version})")
                return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        # exiftool yoksa uyarı göster
        self.log("⚠️  exiftool bulunamadı - EXIF işlemleri için gerekli")
        answer = messagebox.askyesno(
            "exiftool Gerekli", 
            "EXIF orientation düzeltme için exiftool gereklidir.\n\n"
            "Homebrew ile yüklemek ister misiniz?\n\n"
            "Terminal komutu: brew install exiftool"
        )
        if answer:
            self.install_exiftool()
        return False
    
    def install_exiftool(self):
        """exiftool'u Homebrew ile yükle"""
        def install():
            try:
                self.log("📦 exiftool yükleniyor...")
                result = subprocess.run(
                    ['brew', 'install', 'exiftool'], 
                    capture_output=True, text=True, timeout=300
                )
                if result.returncode == 0:
                    self.log("✅ exiftool başarıyla yüklendi!")
                else:
                    self.log(f"❌ exiftool yükleme hatası: {result.stderr}")
                    self.log("💡 Manuel yükleme: Terminal'de 'brew install exiftool' komutunu çalıştırın")
            except subprocess.TimeoutExpired:
                self.log("⏱️  Yükleme zaman aşımına uğradı")
            except Exception as e:
                self.log(f"❌ Yükleme hatası: {str(e)}")
                self.log("💡 Manuel yükleme: Terminal'de 'brew install exiftool' komutunu çalıştırın")
        
        threading.Thread(target=install, daemon=True).start()
    
    def start_processing(self):
        """İşlemleri başlat"""
        if not self.selected_files:
            messagebox.showwarning("Uyarı", "Lütfen önce dosyaları seçin!")
            return
        
        if not self.fix_exif_var.get() and not self.rotate_var.get():
            messagebox.showwarning("Uyarı", "Lütfen en az bir işlem seçin!")
            return
        
        # Onay diyaloğu
        message = f"{len(self.selected_files)} dosya üzerinde şu işlemler yapılacak:\n\n"
        if self.fix_exif_var.get():
            message += "✅ EXIF Orientation düzeltme\n"
        if self.rotate_var.get():
            message += "🔄 90° döndürme\n"
        if self.backup_var.get():
            message += "💾 Yedekleme\n"
        message += "\nDevam etmek istiyor musunuz?"
        
        if not messagebox.askyesno("İşlemi Onayla", message):
            return
        
        # İşlemi ayrı thread'de çalıştır
        self.process_btn.configure(state='disabled', text="⏳ İşleniyor...")
        self.log("🚀 İşlem başlatılıyor...")
        threading.Thread(target=self.process_files, daemon=True).start()
    
    def process_files(self):
        """Dosyaları işle"""
        total_files = len(self.selected_files)
        self.progress.configure(maximum=total_files, value=0)
        
        success_count = 0
        error_count = 0
        
        for i, file_path in enumerate(self.selected_files):
            try:
                filename = os.path.basename(file_path)
                self.log(f"🔄 İşleniyor: {filename}")
                
                # Yedek oluştur
                if self.backup_var.get():
                    backup_path = file_path + '.backup'
                    if not os.path.exists(backup_path):
                        subprocess.run(['cp', file_path, backup_path], check=True)
                        self.log(f"💾 Yedek oluşturuldu: {filename}.backup")
                
                # EXIF orientation düzelt
                if self.fix_exif_var.get():
                    self.fix_exif_orientation(file_path)
                    self.log(f"✅ EXIF orientation düzeltildi: {filename}")
                
                # Döndürme işlemi
                if self.rotate_var.get():
                    self.rotate_image(file_path)
                    self.log(f"🔄 90° döndürüldü: {filename}")
                
                success_count += 1
                self.log(f"✅ Tamamlandı: {filename}")
                
            except Exception as e:
                error_count += 1
                filename = os.path.basename(file_path)
                self.log(f"❌ Hata ({filename}): {str(e)}")
            
            # Progress bar güncelle
            self.root.after(0, lambda i=i: self.progress.configure(value=i+1))
        
        # İşlem tamamlandı
        self.root.after(0, self.processing_completed, success_count, error_count)
    
    def fix_exif_orientation(self, file_path):
        """EXIF orientation bilgisini düzelt"""
        try:
            # Önce exiftool ile deneme
            result = subprocess.run([
                'exiftool', '-Orientation=1', '-n', '-overwrite_original', file_path
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                raise subprocess.CalledProcessError(result.returncode, 'exiftool')
                
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            # exiftool çalışmazsa PIL ile deneme
            try:
                with Image.open(file_path) as img:
                    # Mevcut EXIF verilerini oku
                    exif_data = img.getexif()
                    
                    if exif_data:
                        # PIL için piexif kullan
                        exif_dict = piexif.load(img.info.get('exif', b''))
                        # Orientation değerini 1 yap (normal)
                        exif_dict['0th'][piexif.ImageIFD.Orientation] = 1
                        exif_bytes = piexif.dump(exif_dict)
                        
                        # Görüntüyü kaydet
                        img.save(file_path, exif=exif_bytes, quality=95, optimize=True)
                    else:
                        # EXIF verisi yoksa basit kaydetme
                        img.save(file_path, quality=95, optimize=True)
                        
            except Exception as pil_error:
                raise Exception(f"EXIF orientation düzeltilemedi: {str(pil_error)}")
    
    def rotate_image(self, file_path):
        """Görüntüyü 90 derece saat yönünde döndür"""
        try:
            # macOS'ta sips komutunu kullan (daha hızlı)
            result = subprocess.run([
                'sips', '-r', '90', file_path
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                raise subprocess.CalledProcessError(result.returncode, 'sips')
                
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            # sips çalışmazsa PIL kullan
            try:
                with Image.open(file_path) as img:
                    # 90 derece saat yönünde döndür
                    rotated = img.rotate(-90, expand=True)
                    
                    # EXIF verilerini koru
                    exif = img.info.get('exif')
                    if exif:
                        rotated.save(file_path, exif=exif, quality=95, optimize=True)
                    else:
                        rotated.save(file_path, quality=95, optimize=True)
                        
            except Exception as pil_error:
                raise Exception(f"Döndürme işlemi başarısız: {str(pil_error)}")
    
    def processing_completed(self, success_count, error_count):
        """İşlem tamamlandığında çağrılır"""
        self.process_btn.configure(state='normal', text="🚀 İşlemleri Başlat")
        self.progress.configure(value=0)
        
        if error_count == 0:
            icon = "🎉"
            title = "İşlem Başarıyla Tamamlandı!"
        else:
            icon = "⚠️"
            title = "İşlem Tamamlandı (Bazı Hatalar ile)"
        
        message = f"{icon} İşlem Sonuçları:\n\n"
        message += f"✅ Başarılı: {success_count} dosya\n"
        if error_count > 0:
            message += f"❌ Hatalı: {error_count} dosya\n\n"
            message += "Detaylar için işlem geçmişine bakın."
        
        messagebox.showinfo(title, message)
        self.log(f"\n🏁 İşlem tamamlandı: {success_count} başarılı, {error_count} hatalı\n" + "="*50)
    
    def log(self, message):
        """Log mesajı ekle"""
        def add_log():
            self.log_text.insert(tk.END, f"{message}\n")
            self.log_text.see(tk.END)
            self.root.update_idletasks()
        
        if threading.current_thread() == threading.main_thread():
            add_log()
        else:
            self.root.after(0, add_log)

def main():
    """Ana fonksiyon"""
    # macOS için uygulama ayarları
    if sys.platform == "darwin":
        os.environ['TK_SILENCE_DEPRECATION'] = '1'
    
    root = tk.Tk()
    
    # macOS için özel ayarlar
    if sys.platform == "darwin":
        try:
            # macOS'ta menü çubuğunu gizle
            root.createcommand('tk::mac::Quit', root.quit)
        except:
            pass
    
    app = JPEGOrientationFixer(root)
    
    # Başlangıç mesajı
    app.log("🔧 JPEG Orientation Fixer başlatıldı")
    app.log("📋 Kullanım: Dosyalarınızı seçin, işlem seçeneklerini belirleyin ve başlatın")
    
    def on_closing():
        """Uygulama kapanırken"""
        if messagebox.askokcancel("Çıkış", "Uygulamayı kapatmak istediğinizden emin misiniz?"):
            root.quit()
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        on_closing()

if __name__ == "__main__":
    main()
