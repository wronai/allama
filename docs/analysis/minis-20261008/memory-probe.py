"""Post-run AMD memory observation; inference benchmark must already be complete."""
import json, statistics, subprocess, time
from datetime import datetime, timezone
from pathlib import Path
import requests
from allama.benchmark import generate, payload

root=Path('/home/tom/.local/state/minis-allama-20261008/run-01')
report=json.loads((root/'results.json').read_text())
assert report['status']=='complete' and len(report['results'])==60
base='http://192.168.188.170:11434'
s=requests.Session();s.trust_env=False
assert not s.get(base+'/api/ps',timeout=20).json()['models'], 'Inference server must be idle'
remote='''import json,time
from pathlib import Path
p=Path('/sys/class/drm/card1/device')
assert (p/'vendor').read_text().strip()=='0x1002'
keys=['mem_info_vram_used','mem_info_vram_total','mem_info_gtt_used','mem_info_gtt_total']
print(json.dumps({'time':time.time(), **{k:int((p/k).read_text()) for k in keys}}))
'''
def sample():
 r=subprocess.run(['ssh','tom@192.168.188.170','python3','-'],input=remote,text=True,capture_output=True,timeout=15,check=True)
 return json.loads(r.stdout)
def samples():
 values=[]
 for _ in range(3):
  values.append(sample());time.sleep(.5)
 return values
before=samples()
try:
 warm=generate(s,base,payload('gemma4:12b','Odpowiedz OK.',False,8192,8))
 assert warm['completed'] and not warm['error'],warm
 after=samples()
 loaded=s.get(base+'/api/ps',timeout=20).json()['models']
 assert [m['name'] for m in loaded]==['gemma4:12b']
finally:
 response=s.post(base+'/api/generate',json={'model':'gemma4:12b','keep_alive':0},timeout=60)
 response.raise_for_status()
def used(row):return row['mem_info_vram_used']+row['mem_info_gtt_used']
delta=(statistics.median(map(used,after))-statistics.median(map(used,before)))/1024**3
result={'model':'gemma4:12b','at':datetime.now(timezone.utc).isoformat(),
 'method':'AMD sysfs incremental VRAM+GTT allocation: median of 3 readings after load minus median of 3 idle readings; not process peak or total host RAM',
 'device':'/sys/class/drm/card1/device','context':8192,'before':before,'after':after,
 'delta_gib':delta,'sample_delta_range_gib':[(min(map(used,after))-max(map(used,before)))/1024**3,(max(map(used,after))-min(map(used,before)))/1024**3],
 'ollama_loaded':loaded[0]}
(root/'driver-memory.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
