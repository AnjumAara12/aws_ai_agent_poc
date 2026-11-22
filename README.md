# AI Agent POC

A small end-to-end demo of a FastAPI service calling Amazon Bedrock and running
on EKS. It includes a Docker image, Terraform for the AWS resources, a Helm
chart, a GitHub Actions build/deploy workflow, IRSA for Bedrock access, and
basic logs/metrics.

The app writes logs to standard output and exposes health endpoints plus
Prometheus metrics at `/metrics`. EKS control-plane logs are sent to
CloudWatch. The API service is internal (`ClusterIP`); use `kubectl
port-forward` for a demo instead of exposing it publicly.

## Run locally

From the project directory in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Put the generated value in `.env` as `JWT_SECRET`. Configure AWS credentials
with the AWS CLI or SSO, then confirm the selected identity:

```powershell
aws sts get-caller-identity
```

The identity needs permission to invoke the selected Bedrock model, and model
access must be enabled in the selected region. Start the API:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` to try the API. Generate a development token
in a second terminal with
`.\.venv\Scripts\python.exe -m app.token --subject local-user`. Send it as a
bearer token to `POST /v1/chat`.

Run the automated API tests with
`.\.venv\Scripts\python.exe -m pytest -q`. They mock the Bedrock response, so
the tests do not require AWS credentials or make model calls.

## AWS and EKS setup

Terraform creates a VPC, EKS cluster with one small managed node, an ECR
repository, CloudWatch control-plane logs, a GitHub Actions OIDC role, and an
IRSA role limited to invoking the configured Bedrock model. **Applying
Terraform creates billable AWS resources.** Review the plan before applying
and run `terraform destroy` when the POC is finished.

1. Install Terraform, AWS CLI, `kubectl`, Docker, and Helm. Configure an AWS
   identity that is allowed to create the required VPC, EKS, IAM, ECR, and
   CloudWatch resources.
2. In PowerShell:

   ```powershell
   Set-Location .\terraform
   Copy-Item terraform.tfvars.example terraform.tfvars
   ```

3. Edit `terraform.tfvars`: set `github_repository` to `owner/repository` and
   set `cluster_public_access_cidrs` to the public IP of the machine that will
   run `kubectl` and the deploy workflow, using `/32` for a single IP. Do not
   use `0.0.0.0/0`. The included GitHub workflow deploy job uses a self-hosted
   Linux runner so its network address can be allow-listed.
4. Create the infrastructure:

   ```powershell
   terraform init
   terraform plan
   terraform apply
   ```

5. Configure local access and confirm the node is ready:

   ```powershell
   aws eks update-kubeconfig --region us-east-1 --name ai-agent-poc
   kubectl get nodes
   ```

   Use the region and cluster name from your Terraform values/outputs if you
   changed the defaults.

The EKS API is public but restricted to the CIDRs in `terraform.tfvars`.
Workers run in private subnets. A single NAT gateway is used to keep this
demo's networking simpler; NAT gateways and EKS incur ongoing charges.
The VPC CNI add-on is configured to enforce Kubernetes NetworkPolicies.

## GitHub Actions deployment

The workflow at `.github/workflows/deploy.yml` runs a Python syntax check on
pull requests. On pushes to `main`, it assumes the Terraform-created AWS role
through GitHub OIDC, builds and pushes an image to ECR, then deploys the Helm
chart.

Add these **repository Actions variables** in GitHub Settings:

| Variable | Value |
| --- | --- |
| `AWS_REGION` | Your Terraform AWS region |
| `AWS_ROLE_ARN` | Terraform output `github_actions_role_arn` |
| `ECR_REPOSITORY` | Terraform output `ecr_repository_name` |
| `EKS_CLUSTER_NAME` | Terraform output `cluster_name` |
| `BEDROCK_MODEL_ID` | Same model ID configured in Terraform |
| `BEDROCK_ROLE_ARN` | Terraform output `bedrock_irsa_role_arn` |

Add a repository **Actions secret** named `JWT_SECRET` with a random value of
at least 32 characters. Do not commit this value.

Register a self-hosted **Linux** GitHub Actions runner on a machine whose
public IP is included in `cluster_public_access_cidrs`. It needs Docker and
AWS CLI and `kubectl` installed. The workflow installs Helm and configures
`kubectl` for the EKS cluster.
The Terraform-created GitHub role is limited to pushing to this ECR repository,
describing this cluster, and editing resources in the Kubernetes `default`
namespace.

On deployment, the chart creates a non-root pod, applies a NetworkPolicy, and
uses the IRSA service account to call Bedrock without static AWS keys. To try
the API after the workflow completes:

```powershell
kubectl get services
kubectl port-forward service/ai-agent-api 8000:80
```

Then open `http://127.0.0.1:8000/docs`.

## Clean up

After demos and any needed log/image review, remove the AWS resources:

```powershell
Set-Location .\terraform
terraform destroy
```

Terraform state is local and ignored by Git. Keep it safe: Terraform needs it
to manage and destroy the resources it created. The ECR repository is configured
to delete its images when destroyed.

## POC limitations

- The API rate limit is per process; it is only a basic demo guard.
- The Helm chart disables public ingress by default. `kubectl port-forward` is
  intended for a local demo.
- Model IDs that refer to Bedrock inference profiles may need additional IAM
  resource ARNs in the Terraform Bedrock policy.
- This is a learning POC, not a production-ready deployment.
