#!/bin/bash
pip3 install -r requirements.txt

if [ ! -d ~/.config/ParaView ]; then
  mkdir -p ~/.config/ParaView;
fi
if [ ! -d ~/.config/ParaView/Macros ]; then
  mkdir -p ~/.config/ParaView/Macros;
fi

cp settings/ParaView-UserSettings.json ~/.config/ParaView/ParaView-UserSettings.json
cp -r macros/* ~/.config/ParaView/Macros/

my_path=$(python3 -c "import sys; print(sys.path)")

ed pyParaOcean.py << END
12d
12i
  PATH=$my_path
.
w
q
END