# 27 · Security and secrets in production

**What you'll build:** a security check-up for an AI service. You scan a deliberately leaky project with **trivy** (old libraries, a pasted cloud key, a root container, a privileged pod), compare it with a hardened version that scans clean, create an **SBOM** (a list of every package inside an image), hand a secret to a container as a file, lock pods down with Kubernetes **NetworkPolicies**, and read a least-privilege IAM policy line by line.
**Like you're 5:** security is a school with good habits: everyone wears a name badge (identity), each badge opens only their own classroom (least privilege), the lunch money is in a locked box, not in your pocket (secrets), and the nurse checks everyone for germs before they come in (scanning).
**Time:** ~2 h · **Builds on:** [26 · Observability](../26-observability-logs-metrics-traces) and the kind cluster from [16](../../part-4-kubernetes/16-why-kubernetes-and-your-first-cluster) · **Needs:** Docker, trivy, and for part D a kind cluster with `kubectl`. No API key.

## Why this matters
AI apps hold valuable things: API keys that cost money when stolen, customer documents, and models that can be tricked into calling tools. Most real breaches are boring: a key committed to git, an old library with a known hole, a container running as root, a database reachable from anywhere, or one identity allowed to do everything. Enterprise customers will ask a forward deployed engineer exactly these questions in a security review, and a scan report plus an SBOM is often a requirement before your software is allowed into their network.

## What you'll learn
- **Least privilege**: every person and program gets only the permissions it needs, on only the resources it needs.
- **Secret management**: keys live in a secret manager or a mounted file, never in code, images, Git or plain YAML.
- **Vulnerability and misconfiguration scanning** with trivy: find known holes (**CVEs**) in packages, risky settings in Dockerfiles and Kubernetes YAML, and leaked keys.
- **SBOM** (software bill of materials): the ingredient list of an image, so you can answer "are we affected?" when the next big vulnerability is announced.
- **NetworkPolicies and dependency updates**: deny all traffic by default and allow only the paths you need; let Dependabot open pull requests when libraries need updating.

## Before you start
1. Install **trivy** (official guide: https://trivy.dev/latest/getting-started/installation/):
   - Mac: `brew install trivy`
   - Ubuntu / WSL2: follow the "Debian/Ubuntu (Official)" steps on that page (it adds Aqua Security's apt repository), then `sudo apt install trivy`
   - Windows: use WSL2, or run it from Docker: `docker run --rm -v "${PWD}:/work" -w /work aquasec/trivy:latest fs insecure`
   Check it: `trivy --version`. The first scan downloads the vulnerability database (about 130 MB download, 1.5 GB on disk in `~/.cache/trivy`).
2. Docker running (for parts B and C).
3. For part D: the `ai-lab` kind cluster from lesson 16 (`kind get clusters` lists it) and `kubectl`.
4. `jq` (a JSON tool, used in part B): `sudo apt install jq`, `brew install jq` or `winget install jqlang.jq`.
5. Python 3.10+ for `make_leaky_config.py` (standard library only). No API key needed.

## Run it
Start in this lesson's folder (from the course folder `cloud-and-devops-for-ai`):
```bash
cd part-5-cloud-and-operations/27-security-and-secrets-in-production
```

### Part A: scan a leaky project and a hardened one
1. Create a file with FAKE cloud keys (made fresh each time, they open nothing; the file is git-ignored):
   ```bash
   python make_leaky_config.py
   ```
2. Scan the leaky folder for vulnerable packages, leaked secrets and risky settings, showing only the serious findings:
   ```bash
   trivy fs --scanners vuln,secret,misconfig --severity HIGH,CRITICAL insecure
   ```
   **Command, piece by piece**
   | Piece | Meaning |
   |---|---|
   | `trivy fs` | scan a folder on disk ("file system") |
   | `--scanners vuln,secret,misconfig` | look for three things: known vulnerabilities in packages, secrets such as keys, and misconfigurations in Dockerfiles / Kubernetes YAML / Terraform |
   | `--severity HIGH,CRITICAL` | show only the two most serious levels (the others are `UNKNOWN`, `LOW`, `MEDIUM`) |
   | `insecure` | the folder to scan |
3. Scan the fixed version the same way:
   ```bash
   trivy fs --scanners vuln,secret,misconfig --severity HIGH,CRITICAL secure
   ```
   Every column shows `0`.

### Part B: scan an image and make its SBOM
4. Scan the base image our Dockerfiles use:
   ```bash
   trivy image --severity HIGH,CRITICAL python:3.12-slim
   ```
5. Now hide the problems nobody can fix yet (no patched version exists):
   ```bash
   trivy image --severity HIGH,CRITICAL --ignore-unfixed python:3.12-slim
   ```
   | Piece | Meaning |
   |---|---|
   | `trivy image` | scan a container image (trivy pulls it if Docker does not have it) |
   | `--ignore-unfixed` | skip vulnerabilities that have no fixed version yet: you cannot act on them today, so they would only hide the ones you can fix |
6. Create the SBOM in the standard **CycloneDX** format, then look inside it:
   ```bash
   trivy image --format cyclonedx --output python-slim.cdx.json python:3.12-slim
   jq '.components | length' python-slim.cdx.json
   jq -r '.components[] | select(.name=="openssl" or .name=="pip") | "\(.name) \(.version)"' python-slim.cdx.json
   ```
   | Piece | Meaning |
   |---|---|
   | `--format cyclonedx` | write a CycloneDX SBOM (the other common standard is SPDX: `--format spdx-json`) |
   | `--output <file>` | save to a file instead of printing |
   | `jq '.components \| length'` | count the items in the `components` list |
   | `select(.name=="openssl" or ...)` | keep only components with these names |
   | `"\(.name) \(.version)"` | print name and version; `\( )` puts a value inside text |
7. Scan the SBOM itself (this is what you do months later, when a new CVE is announced, without rebuilding anything):
   ```bash
   trivy sbom python-slim.cdx.json
   ```
8. Build the hardened image and scan it:
   ```bash
   docker build -t secure-api:1.0.0 secure
   trivy image --severity HIGH,CRITICAL --ignore-unfixed secure-api:1.0.0
   ```

### Part C: give a container its secret as a file
9. Create the secret file (git-ignored; any text works for this demo):
   ```bash
   echo "sk-ant-this-is-not-a-real-key" > secrets/anthropic_api_key.txt
   ```
10. Start the hardened API with the secret mounted, and check it:
    ```bash
    docker compose -f secrets/compose.yaml up -d
    curl http://localhost:8000/health
    docker compose -f secrets/compose.yaml exec api ls -l /run/secrets/
    docker compose -f secrets/compose.yaml exec api id
    docker compose -f secrets/compose.yaml exec api sh -c 'env | grep -c ANTHROPIC'
    ```
    | Piece | Meaning |
    |---|---|
    | `-f secrets/compose.yaml` | use this compose file instead of `./compose.yaml` |
    | `exec api <command>` | run a command inside the running `api` container |
    | `id` | print the user the container runs as |
    | `sh -c '...'` | run the text as a shell command inside the container (so the `\|` pipe happens there) |
    | `grep -c ANTHROPIC` | count lines containing `ANTHROPIC` (here: in the environment variables) |
11. Stop it: `docker compose -f secrets/compose.yaml down`

### Part D: NetworkPolicies on kind
12. Make sure `kubectl` talks to your kind cluster: `kubectl config use-context kind-ai-lab`. Create the demo namespace with three pods and wait for them:
    ```bash
    kubectl apply -f k8s/demo-apps.yaml
    kubectl -n np-demo wait --for=condition=Ready pod --all --timeout=120s
    ```
    | Piece | Meaning |
    |---|---|
    | `-n np-demo` | work in the namespace `np-demo` |
    | `wait --for=condition=Ready pod --all` | wait until every pod in the namespace is ready |
    | `--timeout=120s` | give up after 120 seconds |
13. Both pods can call the llm service (no rules yet = everything allowed):
    ```bash
    kubectl -n np-demo exec gateway -- wget -qO- -T 3 http://llm:5678
    kubectl -n np-demo exec intruder -- wget -qO- -T 3 http://llm:5678
    ```
    | Piece | Meaning |
    |---|---|
    | `exec gateway --` | run what follows `--` inside the pod `gateway` |
    | `wget -qO-` | download quietly (`-q`) and print the page to the screen (`-O-`) |
    | `-T 3` | give up after 3 seconds |
    | `http://llm:5678` | the Service `llm` (Kubernetes DNS turns the name into its address), port 5678 |
14. Close every door, then try again: both calls now time out.
    ```bash
    kubectl apply -f k8s/deny-all-ingress.yaml
    kubectl -n np-demo exec gateway -- wget -qO- -T 3 http://llm:5678
    kubectl -n np-demo exec intruder -- wget -qO- -T 3 http://llm:5678
    ```
15. Open exactly one door (gateway → llm on port 5678) and test both again:
    ```bash
    kubectl apply -f k8s/allow-gateway-to-llm.yaml
    kubectl -n np-demo exec gateway -- wget -qO- -T 3 http://llm:5678
    kubectl -n np-demo exec intruder -- wget -qO- -T 3 http://llm:5678
    kubectl -n np-demo get networkpolicy
    ```
16. Clean up: `kubectl delete namespace np-demo`

### What you should see
Step 2 (real output, shortened; your fake key values differ):
```
Report Summary
┌──────────────────┬────────────┬─────────────────┬─────────┬───────────────────┐
│      Target      │    Type    │ Vulnerabilities │ Secrets │ Misconfigurations │
├──────────────────┼────────────┼─────────────────┼─────────┼───────────────────┤
│ requirements.txt │    pip     │       11        │    -    │         -         │
│ Dockerfile       │ dockerfile │        -        │    -    │         2         │
│ deployment.yaml  │ kubernetes │        -        │    -    │         3         │
│ config.py        │    text    │        -        │    2    │         -         │
└──────────────────┴────────────┴─────────────────┴─────────┴───────────────────┘
requirements.txt (pip)
Total: 11 (HIGH: 9, CRITICAL: 2)
│ pyyaml   │ CVE-2020-14343 │ CRITICAL │ fixed │ 5.3    │ 5.4    │ PyYAML: incomplete fix for CVE-2020-1747
│ requests │ CVE-2018-18074 │ HIGH     │       │ 2.19.0 │ 2.20.0 │ python-requests: Redirect from HTTPS to HTTP does not remove Authorization header
...
DS-0002 (HIGH): Specify at least 1 USER command in Dockerfile with non-root user as argument
DS-0031 (CRITICAL): Possible exposure of secret env "ANTHROPIC_API_KEY" in ENV
   8 [ ENV ANTHROPIC_API_KEY=put-your-real-key-here
KSV-0014 (HIGH): Container 'api' of Deployment 'leaky-api' should set 'securityContext.readOnlyRootFilesystem' to true
KSV-0017 (HIGH): Container 'api' of Deployment 'leaky-api' should set 'securityContext.privileged' to false
KSV-0118 (HIGH): deployment leaky-api in default namespace is using the default security context, which allows root privileges
CRITICAL: AWS (aws-access-key-id)
CRITICAL: AWS (aws-secret-access-key)
   2 [ AWS_ACCESS_KEY_ID = "********************"
```
Read the "Fixed Version" column: it tells you which version to upgrade to. Trivy hides the key itself with `*`, so the report does not leak it a second time.

Step 3 (real output):
```
│ requirements.txt │    pip     │        0        │    -    │         -         │
│ Dockerfile       │ dockerfile │        -        │    -    │         0         │
│ deployment.yaml  │ kubernetes │        -        │    -    │         0         │
```
Steps 4 and 5 (real output on the day this lesson was tested; the numbers change every week):
```
python:3.12-slim (debian 13.7)
Total: 44 (HIGH: 44, CRITICAL: 0)
...
with --ignore-unfixed:
│ python:3.12-slim (debian 13.7)  │   debian   │        0        │    -    │
```
All 44 were operating-system packages with no fix released yet. That is normal for any Linux image; what matters is that nothing *fixable* is left, and that you rebuild often so fixes arrive as soon as they exist.

Step 6 prints `89` (components in the image), then `openssl 3.5.7-1~deb13u3` and `pip 25.0.1`.

Step 10 (real output):
```
{"status":"ok","api_key_configured":true}
-rw-r--r-- 1 root root 30 Oct 23 00:04 anthropic_api_key
uid=10001(app) gid=10001(app) groups=10001(app)
0
```
The app found its key (`true`), it lives in a file, the app runs as user 10001 (not root), and the key is in **0** environment variables.

Steps 13 to 15:
```
hello from the llm service          <- gateway, no policies
hello from the llm service          <- intruder, no policies
wget: download timed out            <- gateway, after deny-all
wget: download timed out            <- intruder, after deny-all
hello from the llm service          <- gateway, after allow-gateway-to-llm
wget: download timed out            <- intruder, still blocked
NAME                   POD-SELECTOR   AGE
allow-gateway-to-llm   app=llm        5s
deny-all-ingress       <none>         20s
```

## How it works
```mermaid
flowchart LR
    Code["Your code<br/>+ requirements.txt"] --> Scan1{"trivy fs<br/>vulns, secrets, misconfig"}
    Scan1 -->|"clean"| Build["docker build"]
    Build --> Scan2{"trivy image<br/>+ SBOM"}
    Scan2 -->|"clean"| Registry["Image registry"]
    Registry --> Cluster["Kubernetes"]
    SM[("Secret manager")] -->|"key as a file / env at run time"| Cluster
    Cluster --> NP["NetworkPolicies:<br/>deny all, allow only what is needed"]
    Dep["Dependabot PRs"] --> Code
```
Security is layers: each layer catches what the one before missed. You will wire the two scan steps into GitHub Actions in lesson 28.

### 1. Least privilege (`iam/`)
Open [`iam/too-broad-policy.json`](iam/too-broad-policy.json): `"Action": "*"` and `"Resource": "*"` mean "do anything to anything". If the AI app's key leaks, the attacker owns your whole account.

Now [`iam/least-privilege-policy.json`](iam/least-privilege-policy.json), an AWS IAM policy for the same app:
| Line | Meaning |
|---|---|
| `"Version": "2012-10-17"` | the policy language version (always this date; it is not "today") |
| `"Statement": [ ... ]` | a list of rules |
| `"Sid"` | a name for the rule, for humans |
| `"Effect": "Allow"` | this rule grants permission (everything not allowed is denied by default) |
| `"Action": ["bedrock:InvokeModel", ...]` | exactly which API calls: call a model, with or without streaming. Not "create models", not "change settings" |
| `"Resource": "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-*"` | on exactly which things. An **ARN** (Amazon Resource Name) is the full address of a thing; `*` at the end = any Claude model in that region |
| `s3:GetObject` on `acme-ai-docs/customer-docs/*` | read files, only inside that one folder of that one bucket; no writing, no deleting |
| `s3:ListBucket` with `"Condition": {"StringLike": {"s3:prefix": "customer-docs/*"}}` | list file names, but only inside that folder |
| `secretsmanager:GetSecretValue` on `...secret:prod/ai-app/anthropic-api-key-*` | read one secret. The `-*` matches the random ending AWS adds to every secret's ARN |

Google Cloud and Azure use the same idea with different words: grant a narrow **role** (for example `roles/aiplatform.user`, `roles/storage.objectViewer`) to a **service account** or **managed identity**, on the smallest scope (one bucket, one project or one resource group), instead of "Owner" on everything.

### 2. Secrets
- **Never** in code, Dockerfiles (`ENV`, `ARG`), Git, or YAML in plain text. Image layers and Git history keep them forever, even after you "delete" them. If a key ever leaks: **revoke and replace it first**, then clean up.
- `secure/main.py` checks for `/run/secrets/anthropic_api_key` first and an environment variable second. A file is safer: it does not appear in `docker inspect`, crash reports or child processes, and it can be updated without restarting the container (Kubernetes refreshes mounted Secret files).
- `secrets/compose.yaml`: the top-level `secrets:` block says where the secret comes from (`file: ./anthropic_api_key.txt`); the service's `secrets: - anthropic_api_key` mounts it read-only at `/run/secrets/anthropic_api_key`.
- In Kubernetes, `secure/deployment.yaml` reads the key with `valueFrom.secretKeyRef` (name `anthropic`, key `api-key`) instead of writing it in the file. Remember from lesson 19 that a Kubernetes Secret is only **base64-encoded**, not encrypted: limit who can read Secrets with RBAC, and ask for **encryption at rest** on managed clusters (EKS, GKE and AKS support it).
- In production, the real key lives in a **secret manager** (AWS Secrets Manager, Google Secret Manager, Azure Key Vault, HashiCorp Vault). [`secrets/external-secret.yaml`](secrets/external-secret.yaml) shows the **External Secrets Operator**: it copies the cloud secret into a Kubernetes Secret and refreshes it every hour, so rotating a key in the cloud reaches the pods without anybody touching YAML.

### 3. Scanning with trivy
- **Vulnerabilities**: trivy reads `requirements.txt` (and the packages inside an image), looks each version up in its database of **CVEs** (Common Vulnerabilities and Exposures, the public list of known security holes) and reports the fixed version.
- **Secrets**: pattern rules recognise keys (AWS, GitHub, Slack, private keys...). `make_leaky_config.py` generates random fake AWS keys at run time, so no key-shaped text ever sits in this repository.
- **Misconfigurations**: rules like `DS-0002` (Dockerfile has no `USER`), `DS-0031` (secret in `ENV`), `KSV-0017` (privileged container), `KSV-0014` (writable root file system). Each finding has a link explaining why it matters.
- What changed in `secure/`: pinned slim base, `USER 10001`, `COPY` instead of `ADD`, no secrets, a `HEALTHCHECK`, current library versions; and in the Deployment: `runAsNonRoot`, `allowPrivilegeEscalation: false`, `readOnlyRootFilesystem: true` (with a small writable `/tmp`), `capabilities: drop: ["ALL"]`, `seccompProfile: RuntimeDefault`, resource requests and limits, an exact image tag, and `automountServiceAccountToken: false` (the app never calls the Kubernetes API, so it gets no token to steal).

### 4. SBOM
An SBOM is an ingredient list: every OS package and library, with versions. When the next famous vulnerability is announced, you run `trivy sbom` (or search the SBOM files) across all your images in seconds instead of rebuilding them. Many companies and governments now ask suppliers for an SBOM with every release.

### 5. NetworkPolicies
By default every pod in a Kubernetes cluster can talk to every other pod. If an attacker gets into one pod (for example through a prompt-injected tool call), they can reach your LLM service, your database and your Redis. A **NetworkPolicy** is a firewall rule for pods, chosen by labels:
| Key (in `k8s/allow-gateway-to-llm.yaml`) | Meaning |
|---|---|
| `kind: NetworkPolicy` | a pod firewall rule |
| `spec.podSelector.matchLabels: {app: llm}` | which pods this rule protects. In `deny-all-ingress.yaml`, `podSelector: {}` means every pod in the namespace |
| `policyTypes: [Ingress]` | this policy is about incoming traffic. (`Egress` would control outgoing traffic) |
| `ingress: - from: - podSelector: {app: gateway}` | who may come in: pods with the label `app=gateway` |
| `ports: - protocol: TCP, port: 5678` | and only on this port |
Policies **add up**: deny-all closes everything, each allow policy opens one more door. A network plugin must enforce them; kind's default plugin does, and so do the ones on EKS, GKE and AKS (sometimes you switch it on).

### 6. Keeping dependencies fresh
A library that is safe today will have a CVE next month. [`.github/dependabot.yml`](.github/dependabot.yml) tells GitHub to check every week for new versions of pip packages, Docker base images and GitHub Actions, and to open a pull request for each. Your CI (lesson 04, lesson 28) runs the tests on that pull request, so updating is a review-and-merge job. The file only works at the root of a repository (`.github/dependabot.yml`), so copy it there and adjust `directory`.

## If something goes wrong
- **`trivy: command not found`** → install it (Before you start) or use the Docker command shown there.
- **The first scan hangs on `Downloading vulnerability DB`** → it downloads about 130 MB once; wait. Behind a company proxy, set `HTTPS_PROXY`. `--skip-db-update` reuses the database you already have.
- **`no space left on device`** during scans → the trivy cache needs about 1.5 GB. Free space with `docker system prune`, or delete old caches with `trivy clean --all`.
- **`Bind for 0.0.0.0:8000 failed: port is already allocated`** in part C → stop the other lesson's containers (`docker ps` to find them).
- **Part D: the intruder still gets an answer after deny-all** → your network plugin does not enforce NetworkPolicies. kind's default plugin does since kind v0.24; check `kind version` and recreate the cluster with a newer kind.
- **`kubectl exec ... wget: bad address 'llm'`** → the pods are not ready or the Service is missing: `kubectl -n np-demo get pods,svc`.

## Try this
1. `trivy fs --scanners misconfig secure` (all severities) still shows 2 LOW findings. Fix both in `secure/deployment.yaml` and scan again until it shows 0.
2. Update `insecure/requirements.txt` to versions with no HIGH or CRITICAL findings, using the "Fixed Version" column. Re-scan until the `pip` row shows 0.
3. Add a second allow policy so a new pod `app=monitoring` may also reach `llm` on port 5678 (as Prometheus would). Prove it with a `monitoring` busybox pod, while `intruder` stays blocked.

<details><summary>Hints and solutions</summary>

1. The findings are `KSV-0021` (set `runAsGroup` above 10000) and `KSV-0110` (don't use the `default` namespace). Add `runAsGroup: 10001` next to `runAsUser: 10001`, and `namespace: ai-app` under `metadata:`. Then `trivy fs --scanners misconfig secure` shows `Failures: 0`.
2. For example:
   ```
   requests==2.34.2
   urllib3==2.8.0
   jinja2==3.1.6
   pyyaml==6.0.3
   ```
   These were clean on the day this lesson was tested. New CVEs appear all the time: if trivy lists one, raise that package to the "Fixed Version" it shows. In real projects, let Dependabot propose these bumps and let your tests prove nothing broke.
3. Save as `k8s/allow-monitoring-to-llm.yaml`:
   ```yaml
   apiVersion: networking.k8s.io/v1
   kind: NetworkPolicy
   metadata:
     name: allow-monitoring-to-llm
     namespace: np-demo
   spec:
     podSelector:
       matchLabels:
         app: llm
     policyTypes:
       - Ingress
     ingress:
       - from:
           - podSelector:
               matchLabels:
                 app: monitoring
         ports:
           - protocol: TCP
             port: 5678
   ```
   Then:
   ```bash
   kubectl apply -f k8s/allow-monitoring-to-llm.yaml
   kubectl -n np-demo run monitoring --image=busybox:1.37 --labels=app=monitoring -- sleep infinity
   kubectl -n np-demo wait --for=condition=Ready pod/monitoring
   kubectl -n np-demo exec monitoring -- wget -qO- -T 3 http://llm:5678
   ```
   It answers; `intruder` still times out.
</details>

## Check yourself
1. A teammate committed an API key to GitHub and deleted it in the next commit. Is the problem solved? What do you do first?
2. Trivy reports 44 HIGH vulnerabilities in your base image and 0 with `--ignore-unfixed`. What does that mean, and what should you do?
3. Why is `podSelector: {}` with no `ingress:` rules a good first policy in a namespace?
4. Your app only needs to read files from one S3 folder and call one Claude model. Which two parts of an IAM statement make it "least privilege"?

<details><summary>Answers</summary>

1. No: the key is still in Git history, and bots scan GitHub for keys within minutes. First **revoke the key** (Anthropic Console, cloud console) and create a new one, store the new one in a secret manager, then clean the history if needed and add secret scanning (trivy, GitHub push protection) to CI.
2. All 44 have no fixed version yet, so you cannot fix them today. Keep the base image small, rebuild regularly (weekly, and when fixes appear), and watch for the ones that get a fix.
3. It denies all incoming traffic to every pod, so any new pod or path is closed until someone deliberately opens it with an allow policy. Forgetting a rule then breaks something visibly instead of silently leaving a door open.
4. `Action` (only the exact calls needed, such as `s3:GetObject`, `bedrock:InvokeModel`) and `Resource` (only the exact folder ARN and model ARN), plus conditions when they narrow it further.
</details>

## Learn more (optional)
**Read the official docs**
- Trivy documentation: https://trivy.dev/latest/docs/
- Kubernetes: Network Policies: https://kubernetes.io/docs/concepts/services-networking/network-policies/
- Kubernetes: Secrets (and good practices): https://kubernetes.io/docs/concepts/configuration/secret/
- Kubernetes: Pod Security Standards: https://kubernetes.io/docs/concepts/security/pod-security-standards/
- Kubernetes: Configure a security context for a pod: https://kubernetes.io/docs/tasks/configure-pod-container/security-context/
- AWS IAM: security best practices: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html
- AWS Secrets Manager: https://docs.aws.amazon.com/secretsmanager/latest/userguide/intro.html
- Google Cloud Secret Manager: https://cloud.google.com/secret-manager/docs
- Azure Key Vault: https://learn.microsoft.com/azure/key-vault/general/overview
- External Secrets Operator: https://external-secrets.io/latest/
- Docker Compose secrets: https://docs.docker.com/compose/how-tos/use-secrets/
- GitHub Dependabot version updates: https://docs.github.com/code-security/dependabot/dependabot-version-updates
- CycloneDX (SBOM standard): https://cyclonedx.org/
- OWASP Top 10 for LLM applications: https://genai.owasp.org/

**Watch**
- TechWorld with Nana, Kubernetes security best practices: https://www.youtube.com/results?search_query=techworld+with+nana+kubernetes+security+best+practices
- freeCodeCamp, DevSecOps course: https://www.youtube.com/results?search_query=freecodecamp+devsecops+course
- Fireship, "how hackers steal API keys" / secrets management: https://www.youtube.com/results?search_query=fireship+api+keys+secrets
- Search: "trivy container scanning tutorial": https://www.youtube.com/results?search_query=trivy+container+scanning+tutorial
- Search: "kubernetes network policy explained": https://www.youtube.com/results?search_query=kubernetes+network+policy+explained

## Next
→ [28 · Capstone: ship an AI platform end to end](../28-capstone-ship-an-ai-platform-end-to-end)
