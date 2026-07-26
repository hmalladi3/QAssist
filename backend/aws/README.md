# AWS setup for QAssist

One-time setup in the AWS account that will run Bedrock for this project.
All of it can be done via the AWS CLI (`aws bedrock`, `aws iam`,
`aws budgets`) — no console clicking required, as long as `aws configure`
is already set up.

1. **Bedrock model access.** Claude 4.5 Haiku is invoked through a
   cross-region **inference profile**, not a bare model ID:
   `us.anthropic.claude-haiku-4-5-20251001-v1:0`. Check access with:

   ```bash
   aws bedrock get-foundation-model-availability --region us-east-1 \
     --model-id anthropic.claude-haiku-4-5-20251001-v1:0
   aws bedrock get-foundation-model-availability --region us-east-1 \
     --model-id amazon.titan-embed-text-v2:0
   ```

   If either isn't authorized, request access at Bedrock console → Model
   access (Anthropic models occasionally require accepting a EULA there
   that isn't exposed over the CLI).

   Separately, the *first* Claude Haiku invocation on a fresh account may
   fail with `Model use case details have not been submitted for this
   account` — this is Anthropic's Bedrock marketplace listing requiring a
   one-time intended-use form, also console-only (Bedrock console → Model
   access → the Anthropic row has a use-case-details prompt). Titan is
   unaffected. Retry a few minutes after submitting.

2. **Create an IAM user** (e.g. `qassist-backend`) with no console access,
   programmatic access only:

   ```bash
   aws iam create-user --user-name qassist-backend
   ```

3. **Attach `iam-policy.json`** (in this directory) as an inline policy —
   it grants `bedrock:InvokeModel`/`bedrock:Converse` on exactly the
   inference profile, its three underlying regional model ARNs (Bedrock
   checks both), and the Titan embedding model, nothing else. Fill in your
   account ID first (see docs/llds/deployment-infra.md, DEPLOY-IAM-001):

   ```bash
   aws iam put-user-policy --user-name qassist-backend \
     --policy-name qassist-bedrock-invoke \
     --policy-document file://iam-policy.json
   ```

4. **Generate an access key** and set `AWS_ACCESS_KEY_ID` /
   `AWS_SECRET_ACCESS_KEY` as Render environment variables — never commit
   them:

   ```bash
   aws iam create-access-key --user-name qassist-backend
   ```

5. **Set a budget alert** (tripwire, not a hard cap — Bedrock has no native
   spend cap; expected actual cost for this project is under $1-3):

   ```bash
   aws budgets create-budget --account-id <ACCOUNT_ID> --cli-input-json file://budget.json
   ```

   `budget.json` defines a $5/month budget with an email alert at 80% —
   **critically, scoped with `"CostFilters": {"Service": ["Amazon Bedrock"]}`**.
   If you skip that filter, AWS Budgets tracks your *entire account's*
   spend, not just this project's — if the AWS account also runs other
   infrastructure (EC2, etc.), you'll get alerted on total bill size, not
   QAssist's cost, and the alert becomes noise instead of a useful signal.
