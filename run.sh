#!/bin/bash
DIR="$( cd "$( dirname "$0" )" && pwd )"
if [ -e ~/.local/share/applications/venpy.desktop ]
then
  echo "Launcher is already in place, skipping installing of it."
else
  echo "Launcher is not in place, creating it."
  echo "Exec=""$DIR""/run.sh" >> venpy.desktop
  cp venpy.desktop ~/.local/share/applications/venpy.desktop
  cp icon.svg ~/.local/share/icons/hicolor/scalable/apps/venpy.svg
fi
python3 main.py