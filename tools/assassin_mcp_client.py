import socket, json, sys
from pathlib import Path
code = Path(sys.argv[1]).read_text(encoding='utf-8')
with socket.create_connection(('localhost', 9876), timeout=600) as conn:
    conn.sendall(json.dumps({'type':'execute','code':code,'strict_json':False}).encode()+b'\0')
    data=b''
    while b'\0' not in data:
        chunk=conn.recv(65536)
        if not chunk: break
        data+=chunk
    print(data.rstrip(b'\0').decode())
