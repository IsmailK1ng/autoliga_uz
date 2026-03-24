from pathlib import Path
p=Path('c:/Users/Администратор/Desktop/autoliga_uz/main/views.py')
raw=p.read_bytes()
print('len', len(raw), 'start', raw[:10])
print('bom', 'utf16le' if raw.startswith(b'\xff\xfe') else 'utf16be' if raw.startswith(b'\xfe\xff') else 'utf8bom' if raw.startswith(b'\xef\xbb\xbf') else 'nobom')
try:
    raw.decode('utf-8')
    print('utf8 ok')
except Exception as e:
    print('utf8 fail', repr(e))
try:
    raw.decode('utf-16')
    print('utf16 ok')
except Exception as e:
    print('utf16 fail', repr(e))
