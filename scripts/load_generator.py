"""
Usage:
python3 scripts/load_generator.py  # 10req/s forever
python3 scripts/load_generator.py --rps 100 #stress test for HPA
python3 scripts/load_generator.py --rps 5 --duration 60
"""

import argparse,requests,time,random,threading,signal,sys
from datetime import datetime

BASE = "http://localhost"
stats={"ok":0,"err":0,"total":0,"start":time.time()}
task_ids=[]
running=True

def seed():
    for i in range(5):
        try:
            r = requests.post(f"{BASE}/tasks",json={"title":f"seed task {i}"},timeout=3)
            if r.status_code == 201:
                task_ids.append(r.json()["id"])
        except: pass
        
        
def req():
    roll = random.random()
    try:
        if roll < 0.6 and task_ids:
            r = requests.get(f"{BASE}/tasks",timeout=3)
        
        elif roll< 0.85:
            r = requests.post(f"{BASE}/tasks",
                              json={"title":f"task-{random.randint(1,9999)}"},timeout=3)
            if r.status_code == 201:
                task_ids.append(r.json()["id"])
                
        else:
            r = requests.get(f"{BASE}/tasks/99999",timeout=3)
            
        stats["total"] += 1
        if r.status_code < 500: stats["ok"] +=1
        else: stats["err"] +=1
    
    except Exception as e:
        stats["total"] +=1; stats["err"]+=1
        if "Connection" in str(e): print("  [DOWN] Cannot connect", flush=True)
  
def printer():
    while running:
        time.sleep(10)
        elapsed = time.time() - stats["start"]
        rps = stats["total"] / max(elapsed,1)
        err_pct= stats["err"] / max(stats["total"],1)*100
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}]"
             f"RPS:{rps:.1f}  Total:{stats['total']} "
            f"Errors:{stats['err']} ({err_pct:.1f}%)", flush=True)
        
        

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rps", type=int, default=10)
    parser.add_argument("--duration", type=float, default=0)
    args = parser.parse_args()
    signal.signal(signal.SIGINT, lambda s,f: sys.exit(0))
    print(f"Load generator: {args.rps} req/s", flush=True)
    seed()
    threading.Thread(target=printer, daemon=True).start()
    interval = 1.0 / args.rps
    start = time.time()
    while running:
        if args.duration and time.time()-start > args.duration: break
        req(); time.sleep(interval)
        
if __name__ == "__main__":main()



            