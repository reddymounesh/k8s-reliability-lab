import os, time, logging
from flask import Flask,request,jsonify
from prometheus_client import Counter ,Histogram,Gauge,generate_latest,CONTENT_TYPE_LATEST

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s')
log=logging.getLogger(__name__)
app=Flask(__name__)

REQUESTS=Counter('taskapi_requests_total','Total HTTP requests',['endpoint','status'])

DURATION=Histogram('taskapi_requests_duration_seconds','Request duration',['endpoint'])

TASK_COUNT=Gauge('taskapi_task_count','Current number of tasks')

tasks={}
next_id=1

def track(endpoint):
    """wraps a route to record metrics without repeating code."""
    def decorator(fn):
        def wrapper(*args,**kwargs):
            start=time.time()
            try:
                result=fn(*args,**kwargs)
                status=str(result[1]) if isinstance(result,tuple) else '200'
            except Exception as e:
                log.error("Error in %s: %s",endpoint,e)
                REQUESTS.labels(endpoint=endpoint,status='500').inc()
                DURATION.labels(endpoint=endpoint).observe(time.time()-start)
                return jsonify({'error': 'internal error'}),500
            REQUESTS.labels(endpoint=endpoint,status=status).inc()
            DURATION.labels(endpoint=endpoint).observe(time.time()-start)
            return result
        wrapper.__name__=fn.__name__
        return wrapper
    return decorator



@app.route('/tasks',methods=['GET'])
@track('/tasks')
def list_tasks():
    return jsonify({'tasks': list(tasks.values()),'count':len(tasks)}),200


@app.route('/tasks',methods=['POST'])
@track('/tracks')
def create_tasks():
    global next_id
    data = request.get_json()
    if not data or 'title' not in data:
        return jsonify({'error': 'title is required'}),400
    task = {'id': next_id,'title':data['title'],'done':False,'created':time.time()}
    
    tasks[next_id] = task
    next_id+=1
    TASK_COUNT.set(len(tasks))
    log.info("Created task: %s",task['title'])
    return jsonify(task),201


@app.route('/tasks/',methods=['PUT'])
@track('/tasks/:id')
def update_task(tid):
    if tid not in tasks:
        return jsonify({'error': 'not found'}),404
    data = request.get_json
    if 'done' in data:
        tasks[tid]['done'] = data['done']
    return jsonify(tasks[tid]),200

@app.route('/tasks/',methods=['DELETE'])
@track('/tasks/:id')
def delete_task(tid):
    if tid not in tasks:
        return jsonify({'error':'not found'}),404
    del tasks[tid]
    TASK_COUNT.set(len(tasks))
    return jsonify({'deleted':tid}),200

@app.route('/health')
def health():
    #liveness probe: is the process alive and not deadlocked?
    #Returns 200 as long as Flask is responding
    return jsonify({'status': 'ok','tasks':len(tasks)}),200

@app.route('/ready')
def ready():
    #readiness probe: is the pod ready to receive traffic?
    return jsonify({'ready': True}),200

@app.route('/metrics')
def metrics():
    return generate_latest(),200,{'Content-Type': CONTENT_TYPE_LATEST}

if __name__ == '__main__':
    log.info("Task API starting -- pod: %s",os.environ.get('HOSTNAME','local'))
    app.run(host='0.0.0.0',port=5000,debug=False)
    


    