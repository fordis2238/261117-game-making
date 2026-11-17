from pathlib import Path
import subprocess,sys
root=Path(__file__).resolve().parent
mode=sys.argv[1] if len(sys.argv)>1 else 'onedir'
command=[sys.executable,'-m','PyInstaller','--noconfirm','--'+mode,'--windowed','--name','NemoGarden','--icon',str(root/'nemo.ico'),'--distpath',str(root/'portable-build'/mode),'--workpath',str(root/'portable-build'/('work-'+mode)),'--specpath',str(root/'portable-build'), '--add-data',str(root/'dist')+':dist','--add-data',str(root/'puzzle-seeds.json')+':.','--add-data',str(root/'puzzle-legacy.json')+':.','--add-data',str(root/'tools/cloudflared.exe')+':tools',str(root/'portable_launcher.py')]
raise SystemExit(subprocess.call(command))
