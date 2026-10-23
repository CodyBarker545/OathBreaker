"""Install the user's 21 MPFB packs, preserving any replaced files."""
import zipfile, pathlib, hashlib, json, shutil
ROOT = pathlib.Path(r'D:\SoftwareEng\Game')
DEST = pathlib.Path(r'C:\Users\cody_\AppData\Roaming\Blender Foundation\Blender\5.2\extensions\.user\blender_org\mpfb\data')
NAMES = ['makehuman_system_poses_cc0.zip','suits02_cc0.zip','hair01_cc0.zip','suits03_cc-by.zip','shirts02_ccby.zip','pants02_ccby.zip','bodyparts03_cc-by.zip','haireditor.zip','suits01_cc0.zip','shoes01_cc0.zip','bodyparts02_cc-by.zip','bodyparts01_cc0.zip','skins02_cc0.zip','pants03_ccby.zip','hats03_cc-by.zip','pants01_cc0.zip','makehuman_system_assets_cc0.zip','gloves01_cc0.zip','shirts01_cc0.zip','shirts03_ccby.zip','hats02_cc0.zip']
backup=ROOT/'artifacts/mpfb_install_backup'
report=[]
for name in NAMES:
    with zipfile.ZipFile(pathlib.Path('D:/Downloads')/name) as z:
        assert any(n.startswith('packs/') and n.endswith('.json') for n in z.namelist()), name
        for info in z.infolist():
            path=(DEST/info.filename).resolve()
            assert path.is_relative_to(DEST.resolve()), info.filename
            assert not info.filename.startswith(('/', '\\'))
        files=0
        manifests=[]
        for info in z.infolist():
            path=DEST/info.filename
            if info.is_dir(): continue
            data=z.read(info)
            if path.exists() and path.read_bytes()!=data:
                saved=backup/name/path.relative_to(DEST)
                saved.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(path,saved)
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(data)
            assert hashlib.sha256(path.read_bytes()).digest()==hashlib.sha256(data).digest()
            files+=1
            if info.filename.startswith('packs/') and info.filename.endswith('.json'):
                manifests.append(json.loads(data))
        report.append({'archive':name,'verified_files':files,'manifests':manifests})
out=ROOT/'artifacts/mpfb_packages_installation.json'
out.write_text(json.dumps({'destination':str(DEST),'packages':report},indent=2),encoding='utf-8')
print(json.dumps({'installed_packages':len(report),'verified_files':sum(p['verified_files'] for p in report),'destination':str(DEST),'report':str(out)}))
