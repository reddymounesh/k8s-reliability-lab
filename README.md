# Kubernetes Reliability Lab

A production-style Kubernetes deployment demonstrating SRE reliability practices — 
resource management, autoscaling, disruption protection, and systematic failure 
experimentation with documented evidence.

## Architecture




**Stack**: k3s, Helm, kube-prometheus-stack, Flask, Python

## Quick Start

```bash
git clone https://github.com/YOURUSERNAME/k8s-reliability-lab
cd k8s-reliability-lab
kubectl apply -f manifests/
helm install monitoring prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace
kubectl apply -f monitoring/servicemonitor.yaml
```

| Service | URL |
|---|---|
| Task API | http://localhost/tasks |
| Prometheus | http://localhost:30900 |
| Grafana | http://localhost:30300 (admin/admin123) |

## Kubernetes Objects and Why Each Exists

| Object | Purpose |
|---|---|
| Deployment (3 replicas) | Self-healing — auto-restarts crashed pods |
| Liveness probe (/health) | Restarts hung containers |
| Readiness probe (/ready) | Removes unready pods from traffic without restarting |
| HPA (2–8 replicas, 50% CPU) | Autoscales under load |
| PodDisruptionBudget (minAvailable:2) | Prevents >1 pod disrupted at once |
| ResourceQuota / LimitRange | Caps namespace resources, sets safe defaults |

## Experiments Run — With Evidence

| # | Experiment | Result | Evidence |
|---|---|---|---|
| 1 | Killed a running pod | New pod Running within ~8s | [test1](docs/evidence/test1-self-healing.txt) |
| 2 | Forced OOMKill (64Mi limit, 300MB alloc) | Exit code 137, confirmed kernel kill | [test2](docs/evidence/test2-oomkill.txt) |
| 3 | 200 req/s load spike | HPA scaled 3→6 replicas in ~45s | [test3](docs/evidence/test3-hpa-scaling.txt) |
| 4 | Node drain attempt | Blocked by PDB, protecting minAvailable:2 | [test4](docs/evidence/test4-pdb-drain.txt) |
| 5 | Bad image deploy | Old pods kept serving, rollback in <2min | [test5](docs/evidence/test5-rollback.txt) |

## Dashboards

![HPA Scaling](docs/screenshots/hpa-scaling-3to6-replicas.png)
![OOMKill Detection](docs/screenshots/oomkill-metric-spike.png)
![Prometheus Targets](docs/screenshots/prometheus-targets-all-up.png)

## Key Technical Finding

**OOMKill vs CPU throttling are fundamentally different mechanisms.** Exceeding a 
memory limit causes an instant kernel SIGKILL (exit code 137) — the container dies 
immediately with no warning. Exceeding a CPU limit causes gradual throttling via the 
kernel's CFS scheduler — the container keeps running, just slower. This distinction 
determines the correct fix: memory issues need higher limits or leak fixes; CPU 
throttling may be acceptable if latency SLOs are still met.

## Repository Structure

k8s-lab/
├── app/                  # Flask API source + Dockerfile
├── manifests/            # All Kubernetes YAML objects
├── monitoring/           # ServiceMonitor + Helm values
├── scripts/              # Load generator + validation scripts
└── docs/
├── evidence/         # Raw test output from all 5 experiments
├── screenshots/      # Grafana dashboard proof
├── observations/     # Written analysis per experiment
└── postmortems/      # Blameless post-mortem for OOMKill incident

