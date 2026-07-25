# AWS setup for QAssist

One-time setup in the AWS account that will run Bedrock for this project.

1. **Enable Bedrock model access** (us-east-1) for exactly two models:
   Anthropic Claude 3.5 Haiku and Amazon Titan Embed Text v2. Bedrock
   console → Model access → request access to only these two.
2. **Create an IAM user** (e.g. `qassist-backend`) with no console access,
   programmatic access only.
3. **Attach `iam-policy.json`** (in this directory) as an inline policy on
   that user — it grants `bedrock:InvokeModel`/`bedrock:Converse` on exactly
   the two model ARNs above, nothing else (see docs/llds/deployment-infra.md,
   DEPLOY-IAM-001).
4. **Generate an access key** for the user and set `AWS_ACCESS_KEY_ID` /
   `AWS_SECRET_ACCESS_KEY` as Render environment variables — never commit
   them.
5. **Set a budget alert**: AWS Billing → Budgets → create a $5/month budget
   with an email alert. This is a tripwire, not a hard spend cap (Bedrock
   has no native hard cap) — expected actual spend for this project is
   under $1-3.
