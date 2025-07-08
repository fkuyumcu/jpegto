#!/bin/bash

# JPEG Orientation Fixer Launcher Script
# Bu script Python uygulamasını başlatır

# Script'in bulunduğu dizine geç
cd "$(dirname "$0")"

# tkinter desteği kontrolü
echo "🔍 tkinter desteği kontrol ediliyor..."
if ! python3 -c "import tkinter" 2>/dev/null; then
    echo "❌ tkinter bulunamadı!"
    echo "📦 Homebrew ile python-tk yükleniyor..."
    if command -v brew >/dev/null 2>&1; then
        brew install python-tk
    else
        echo "❌ Homebrew bulunamadı. Lütfen manuel olarak yükleyin:"
        echo "   brew install python-tk"
        exit 1
    fi
fi

# Python sanal ortamını etkinleştir
if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "✅ Python sanal ortamı etkinleştirildi"
    
    # Gerekli paketleri kontrol et
    if ! python -c "import PIL, piexif" 2>/dev/null; then
        echo "📦 Gerekli Python paketleri yükleniyor..."
        pip install Pillow piexif
    fi
else
    echo "⚠️  Sanal ortam bulunamadı, sistem Python kullanılacak"
    
    # Sistem Python ile gerekli paketleri kontrol et
    if ! python3 -c "import PIL, piexif" 2>/dev/null; then
        echo "❌ Gerekli Python paketleri bulunamadı!"
        echo "💡 Lütfen şu komutu çalıştırın: pip3 install Pillow piexif"
        exit 1
    fi
fi

# tkinter'ın çalıştığını doğrula
if ! python3 -c "import tkinter" 2>/dev/null; then
    echo "❌ tkinter hala çalışmıyor. Sistem yeniden başlatılması gerekebilir."
    exit 1
fi

# Python script'ini çalıştır
echo "🚀 JPEG Orientation Fixer başlatılıyor..."
python3 jpeg_fixer.py

echo "✅ Uygulama kapatıldı."
