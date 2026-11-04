# devops-2025S-demo

Class demo for the DevOps course: the **Campus Event Notifier**, a Django app for
listing campus events and registering for them.

This repository is a fork of
[pelino250/devops-2025S-demo](https://github.com/pelino250/devops-2025S-demo).
The sections below describe what I added.

---

## What changed in this fork

| Area | What | Where |
|---|---|---|
| CI | Linter workflow that runs `ruff check .` on every push | [.github/workflows/linter.yml](.github/workflows/linter.yml) |
| App | `/health/` endpoint returning `{"status": "ok"}` for health checks | [campus_notifier/urls.py](campus_notifier/urls.py) |
| Containers | `.dockerignore` to keep the image small and free of local files | [.dockerignore](.dockerignore) |
| Containers | Docker Compose setup: the app plus Postgres 16, with a healthcheck and a named volume | [docker-compose.yml](docker-compose.yml) |
| Containers | Published image on Docker Hub: `auwase/campus-event-notifier` (tags `v1`, `v2`) | [Docker Hub](https://hub.docker.com/r/auwase/campus-event-notifier) |
| Kubernetes | Deployment (with readiness and liveness probes) and a NodePort Service on port 8000 | [deployment.yaml](deployment.yaml), [service.yaml](service.yaml) |
| Terraform (pre-class) | Runs the app image as a local Docker container using the Docker provider | [preclass/local/](preclass/local/) |
| Terraform (AWS) | Two Ubuntu 24.04 EC2 servers (app + database), security groups, SSH key pair, state stored in HCP Terraform | [terraform/aws/](terraform/aws/) |
| Ansible | Inventory and playbook that configure both servers and deploy the app | [terraform/aws/inventory.ini](terraform/aws/inventory.ini), [terraform/aws/playbook.yml](terraform/aws/playbook.yml) |
| Security | `.gitignore` rules for Terraform state, `.tfvars`, and key files | [.gitignore](.gitignore) |

---

## Running the app locally with Docker Compose

Create a `.env` file in the project root (it is not committed):

```env
POSTGRES_DB=campus
POSTGRES_USER=campus
POSTGRES_PASSWORD=change-me
```

Then:

```bash
docker compose up --build
```

Compose waits for Postgres to pass its healthcheck, runs the migrations, and serves
the app at http://localhost:8000. Check it with:

```bash
curl http://localhost:8000/health/
```

---

## Running on Kubernetes

The manifests expect a local image named `campus-notifier:latest` (for example on
Docker Desktop's Kubernetes or minikube):

```bash
docker build -t campus-notifier:latest .
kubectl apply -f deployment.yaml -f service.yaml
kubectl get pods,svc
```

---

## Deploying to AWS with Terraform and Ansible

This is the main deliverable. Terraform builds two empty servers, and Ansible
configures them.

```
laptop (WSL Ubuntu)
  |-- Terraform --> AWS: app server + database server
  |-- Ansible ----> app server: Docker + Campus Event Notifier container
               \--> db server:  Postgres 16, campus user and database
```

### 1. Build the servers (Terraform)

Requirements: Terraform, AWS credentials (`aws configure`), an HCP Terraform
account (`terraform login`), and an SSH key at `~/.ssh/alu-devops`.

```bash
cd terraform/aws
export TF_CLOUD_ORGANIZATION=<your-hcp-organization>
export TF_WORKSPACE=campus-notifier-infra
echo "my_ip_cidr = \"$(curl -4 -s ifconfig.me)/32\"" > terraform.tfvars

terraform init
terraform apply
terraform output
```

The HCP workspace must use **Local** execution mode, because Terraform needs your
local AWS credentials and SSH key.

What gets built:

- **App server:** SSH and port 8000 are open to your IP only.
- **Database server:** SSH is open to your IP only. Postgres (5432) accepts
  connections **only from the app server's security group**, never from the internet.

The outputs are `instance_public_ip`, `instance_private_ip`, `ssh_user`,
`app_port`, `db_public_ip`, `db_private_ip` and `db_ssh_port`.

### 2. Configure the servers (Ansible)

Requirements: Ansible plus the `community.docker` and `community.postgresql`
collections.

Update [inventory.ini](terraform/aws/inventory.ini) with the public IPs from
`terraform output`, then:

```bash
ansible all -i inventory.ini -m ping             # expect "pong" from both servers
ansible-playbook -i inventory.ini playbook.yml
```

What the playbook does:

| Play | Hosts | Tasks |
|---|---|---|
| Gather facts | all | Collects facts (including private IPs) before any change is made |
| Database server | `db` | Installs Postgres, creates the `campus` user and database, sets `listen_addresses`, allows only the app server's private IP in `pg_hba.conf`, restarts Postgres through a handler |
| App server | `app` | Installs Docker (`apt`), starts and enables it (`service`), adds `ubuntu` to the `docker` group, runs the app with `community.docker.docker_container`, runs migrations, checks that `/health/` returns 200 |

The playbook only uses Ansible modules, never raw shell commands, so it is
**idempotent**. Running it a second time reports `changed=0`:

- Modules describe the desired state (`state: present` or `state: started`) and only act when the server differs from it.
- `docker_container` leaves the running container alone if its settings already match.
- `changed_when` on the migrate task reports a change only when there were migrations to apply.
- Postgres restarts only when one of its config files actually changed.

The private IPs come from the gathered facts (`hostvars`), so nothing in the
playbook needs editing after the servers are rebuilt.

### 3. Verify and clean up

```bash
curl http://<instance_public_ip>:8000/health/    # {"status": "ok"}

cd terraform/aws
terraform destroy                                # stop paying for the servers
```

---

## Notes

- The database password in `playbook.yml` is a throwaway value for a demo
  database that gets destroyed after class. A real project would store it in
  Ansible Vault.
- `terraform.tfvars`, Terraform state, and SSH keys are excluded by `.gitignore`.
