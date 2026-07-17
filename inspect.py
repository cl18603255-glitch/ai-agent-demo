import subprocess, time, requests, sys, os, re

env = os.environ.copy()
env['PORT'] = '18082'
proc = subprocess.Popen([sys.executable, 'app.py'], cwd=r'C:\Users\曹雷\Documents\学习AI Agent\ai-agent-demo', env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
time.sleep(5)

if proc.poll() is None:
    base = 'http://127.0.0.1:18082'
    r = requests.get(base + '/', timeout=5)
    text = r.text
    
    oncalls = re.findall(r'onclick="([^"]+)"', text)
    print('=== onclick handlers ===')
    for oc in oncalls:
        print(' ', oc)
    print()
    
    modal_refs = re.findall(r'showModal\((\w+)\)', text)
    print('=== showModal refs ===')
    for m in sorted(set(modal_refs)):
        print(' ', m)
    print()
    
    modal_ids = re.findall(r'id="modal-(\w+)"', text)
    print('=== actual modal IDs ===')
    for m in modal_ids:
        print(' ', m)
    
    proc.terminate()
else:
    out, err = proc.communicate()
    print('ERROR:', err.decode('utf-8', errors='replace')[:500])
