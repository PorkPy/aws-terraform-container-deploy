# Custom ML Model Productionisation

**Live demo:** [diy-llm-v2.streamlit.app](https://diy-llm-v2.streamlit.app)

A full-stack machine learning deployment project demonstrating production-grade MLOps engineering. The focus is not on building the best language model — it is on showing that a custom-trained model can be taken from raw PyTorch code to a live, monitored, serverless production system using the same tooling and patterns used in real-world ML engineering teams.

---

## What This Project Demonstrates

Most ML portfolios stop at the notebook. This project starts where the notebook ends.

The model at the centre is a **custom transformer language model built from scratch in PyTorch**, trained exclusively on Jane Austen's *Pride and Prejudice*. It is deliberately simple and deliberately limited — a small vocabulary, a narrow corpus, a model that generates Austen-flavoured text rather than anything useful. That limitation is the point. By keeping the model simple and explainable, the complexity budget goes entirely into the deployment infrastructure, which mirrors what a production ML system actually looks like.

**The full stack this project covers:**

- Building a transformer architecture from first principles (attention mechanisms, positional encoding, multi-head attention, layer normalisation)
- Containerising a PyTorch model in Docker and pushing to Amazon ECR
- Serving inference via AWS Lambda with cold start handling and warm-up strategies
- Exposing endpoints through API Gateway with REST routing
- Managing all infrastructure as code with Terraform
- Automating the entire build, test, and deploy cycle with GitHub Actions CI/CD
- Storing model artefacts and static assets in S3
- Surfacing real-time CloudWatch data (latency, cost, error rates, invocation counts) directly in the Streamlit app as a live monitoring dashboard
- Presenting everything through a Streamlit front-end with attention visualisations

---

## How It Works End to End

1. A developer pushes code to the `main` branch
2. GitHub Actions triggers: installs dependencies, runs tests, builds Docker image
3. The image is pushed to Amazon ECR
4. The trained model artefact is uploaded to S3
5. Terraform provisions or updates Lambda functions, API Gateway routes, IAM roles, and CloudWatch alarms
6. The Streamlit app calls the live Lambda endpoints for inference
7. CloudWatch captures latency, invocation counts, errors, and cost in real time

---

## Architecture

### Full System Overview
![System Architecture](https://transformer-model-artifacts-q3ukv7.s3.eu-west-2.amazonaws.com/static-assets/arch_aws_full_system_overview.png)

The system has two distinct layers. The **runtime pipeline** handles live inference — a user submits text to the Streamlit app, which calls API Gateway, which routes to one of two Lambda functions: one for text generation, one for attention visualisation. Both functions pull the model from S3 on cold start and cache it in memory for warm requests. CloudWatch monitors every invocation.

The **deployment pipeline** is fully automated. A push to the main branch triggers GitHub Actions, which builds the Docker image, runs tests, pushes to ECR, uploads the model artefact to S3, and runs Terraform to provision or update infrastructure. A full deployment completes in under an hour with zero manual steps.

### CI/CD Pipeline
![CI/CD Pipeline](https://transformer-model-artifacts-q3ukv7.s3.eu-west-2.amazonaws.com/static-assets/cicd_deployment_pipeline.png)

### Transformer Architecture
![Transformer Architecture](https://transformer-model-artifacts-q3ukv7.s3.eu-west-2.amazonaws.com/static-assets/model_transformer_architecture.png)

### Attention Mechanism
![Attention Mechanism](https://transformer-model-artifacts-q3ukv7.s3.eu-west-2.amazonaws.com/static-assets/model_attention_mechanism.png)

---

## Monitoring Dashboard

The Streamlit app doubles as a live operations dashboard, pulling real metrics directly from CloudWatch. This is not mocked data — it reflects the actual state of the deployed system.

The dashboard covers four areas:

**Performance metrics** — end-to-end latency per request, Lambda execution duration, and token generation speed broken down by invocation.

**System health** — Lambda cold start frequency, warm vs cold invocation ratio, memory utilisation, and API Gateway error rates.

**Cost analysis** — real-time AWS billing data showing cost per request, projected monthly spend based on current usage patterns, and a breakdown by service (Lambda compute, API Gateway calls, S3 storage and transfer).

**Error logging** — recent CloudWatch log events surfaced directly in the UI, so failures are visible without needing to open the AWS console.

This demonstrates that ML deployment is not just about getting the model running — it is about maintaining visibility over a live system and being able to diagnose issues without leaving the application.

---

## The Model

The language model is a **4-layer encoder-only transformer** with the following specification:

| Parameter | Value |
|---|---|
| Architecture | Encoder-only transformer |
| Layers | 4 |
| Attention heads | 8 |
| Embedding dimension | 256 |
| Feed-forward dimension | 1024 |
| Training corpus | Pride and Prejudice (~122,000 words) |
| Vocabulary size | ~5,400 tokens |
| Framework | PyTorch (built from scratch) |

The model is intentionally left in a raw, interpretable state. No pre-trained weights, no fine-tuning, no external dependencies beyond PyTorch. Every component — the attention mechanism, the positional encoding, the training loop — is written from scratch. This makes the architecture fully transparent and easy to explain, which is a deliberate design choice for a demo project where explainability matters more than benchmark performance.

The attention visualisation feature in the Streamlit app lets you see exactly which tokens the model attends to at each layer and head, making the mechanics of the transformer directly observable.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Model | PyTorch (custom transformer, built from scratch) |
| Containerisation | Docker |
| Container registry | Amazon ECR |
| Inference | AWS Lambda (containerised) |
| API | Amazon API Gateway |
| Storage | Amazon S3 |
| Monitoring | Amazon CloudWatch |
| Infrastructure as Code | Terraform |
| CI/CD | GitHub Actions |
| Front-end & Monitoring | Streamlit (text generation, attention visualisation, and live monitoring dashboard) |
| Deployment target | Streamlit Cloud |

---

## Why This Approach

Swapping out the Pride and Prejudice model for a production-grade LLM would require changing one file. The deployment infrastructure, the CI/CD pipeline, the monitoring, the IaC — none of it changes. That is the point of this project: to show that the hard engineering work of getting a model into production is model-agnostic, and that doing it properly from the start means scaling up is just a matter of upgrading what goes in the box.

---

## What I Would Do Differently

- **Model quality**: With more training data and compute, the same architecture would produce significantly better outputs. The current model is a demo vehicle, not a production model.
- **Authentication**: The API endpoints are currently open. A production system would add API key validation at the Gateway level.
- **Async inference**: Lambda is synchronous here. For longer generation tasks, an SQS queue with async Lambda invocation would be more appropriate.
- **Model versioning**: S3 holds a single model artefact. A proper MLflow or SageMaker Model Registry integration would enable versioned rollbacks.

---

## Repository Structure

transformer-aws-deployment/\
├── terraform/\
│   ├── main.tf              # Main Terraform configuration\
│   ├── variables.tf         # Input variables\
│   ├── outputs.tf           # Output values\
│   ├── api_gateway.tf       # API Gateway configuration\
│   ├── lambda.tf            # Lambda functions\
│   ├── s3.tf                # S3 buckets for model storage\
│   ├── iam.tf               # IAM roles and policies\
│   ├── cloudwatch.tf        # Monitoring and alerts\
│   └── providers.tf         # AWS provider configuration\
├── src/\
│   ├── model/               # Your transformer model code\
│   ├── lambda_functions/\
│   │   ├── generate_text/   # Text generation Lambda\
│   │   │   ├── main.py\
│   │   │   └── requirements.txt\
│   │   └── visualize_attention/ # Visualization Lambda\
│   │       ├── main.py\
│   │       └── requirements.txt\
│   └── streamlit/           # Streamlit app code\
├── scripts/\
│   ├── package_lambdas.sh   # Script to package Lambda functions\
│   ├── upload_model.sh      # Script to upload model to S3\
│   └── deploy.sh            # Main deployment script\
├── .github/\
│   └── workflows/\
│       └── deploy.yml       # GitHub Actions workflow (optional)\
└── README.md\

---

## Author

Dom McKean — Data Scientist  
[GitHub](https://github.com/PorkPy)
