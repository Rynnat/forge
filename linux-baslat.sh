#!/usr/bin/env bash
# Forge / akademik-bosluk: Windows'tan Linux'a tek komutla geçiş.
# Tekrar tekrar çalıştırılabilir: depolar varsa günceller, hafızada yalnız daha yeni dosyaları kopyalar.
set -euo pipefail

WIN=/mnt/win
WINHOME="$WIN/Users/LENOVO"
PROJ="$HOME/Projeler"
REPOS=(akademik-bosluk forge forge-altin)

say() { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }

# 1) Windows diskini bağla (zaten bağlıysa atla)
if [ ! -d "$WINHOME/Projeler" ]; then
  say "Windows diski aranıyor"
  sudo mkdir -p "$WIN"
  for p in $(lsblk -rpno NAME,FSTYPE | awk '$2=="ntfs"{print $1}'); do
    if sudo mount -t ntfs3 "$p" "$WIN" 2>/dev/null; then
      [ -d "$WINHOME/Projeler" ] && { echo "bağlandı: $p"; break; }
      sudo umount "$WIN"
    fi
  done
  [ -d "$WINHOME/Projeler" ] || { echo "HATA: Windows diski bulunamadı ya da salt-okunur. Windows'tan 'Yeniden başlat' ile çıktın mı?"; exit 1; }
fi

# 2) Claude Code var mı?
if ! command -v claude >/dev/null 2>&1; then
  say "Claude Code kuruluyor"
  curl -fsSL https://claude.ai/install.sh | bash
  export PATH="$HOME/.local/bin:$PATH"
fi

# 3) Depolar: yoksa klonla, varsa Windows'taki son hâlini çek
mkdir -p "$PROJ"
for r in "${REPOS[@]}"; do
  if [ -d "$PROJ/$r/.git" ]; then
    say "$r güncelleniyor"
    git -C "$PROJ/$r" pull --ff-only "$WINHOME/Projeler/$r" HEAD || echo "UYARI: $r ileri sarılamadı (Linux'ta yeni commit var); elle birleştir."
  else
    say "$r klonlanıyor"
    git clone "$WINHOME/Projeler/$r" "$PROJ/$r"
  fi
  git -C "$PROJ/$r" remote get-url win >/dev/null 2>&1 || git -C "$PROJ/$r" remote add win "$WINHOME/Projeler/$r"
done

# 3b) Forge verisi: arXiv anlık görüntüsü (parquet, ~2,7 GB); sqlite dizini Linux'ta yeniden kurulur
if [ -d "$WINHOME/Projeler/forge-veri/arxiv" ]; then
  say "forge-veri/arxiv kopyalanıyor"
  mkdir -p "$PROJ/forge-veri/arxiv"
  cp -ru "$WINHOME/Projeler/forge-veri/arxiv/." "$PROJ/forge-veri/arxiv/"
fi

# 4) Hafıza ve özel ajanlar (yalnız daha yeni dosyalar)
SLUG=$(printf '%s' "$HOME" | sed 's#[^A-Za-z0-9]#-#g')
MEM="$HOME/.claude/projects/$SLUG/memory"
say "hafıza -> $MEM"
mkdir -p "$MEM" "$HOME/.claude/agents"
cp -ru "$WINHOME/.claude/projects/C--Users-LENOVO/memory/." "$MEM/"
cp -ru "$WINHOME/.claude/agents/." "$HOME/.claude/agents/" 2>/dev/null || true

# 5) "selam claude" yeterli olsun diye kullanıcı düzeyinde CLAUDE.md notu
CM="$HOME/.claude/CLAUDE.md"
touch "$CM"
if ! grep -q "FORGE-DEVAM" "$CM"; then
  cat >> "$CM" <<'EOF'

<!-- FORGE-DEVAM -->
## Linux devam kuralı
- Bu makinede projeler `~/Projeler/` altında. Hafızadaki `C:\Users\LENOVO\Projeler\X` yolları burada `~/Projeler/X` demektir.
- Oturumun başında `~/Projeler/akademik-bosluk/DEVAM-LINUX.md` dosyası varsa ve en üstünde "TAMAMLANDI" yazmıyorsa: onu oku, kullanıcıya 3 satırlık durum özeti ver ve "3. Yapılacak işler"den devam et.
- Forge için ayrıca `~/Projeler/forge/orkestra/DEVAM.md` sonundaki "LINUX'A GEÇİŞ" bölümünü oku ve oradan devam et.
- Linux'ta yapılan commit'leri Windows'a geri taşımak için: `git push win HEAD:linux`. Windows'ta da `git merge linux`.
EOF
fi

say "Hazır. Başlatmak için:  cd ~ && claude    sonra sadece:  selam claude"
