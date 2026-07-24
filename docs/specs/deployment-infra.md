# EARS: Deployment & Infra

Segment owner: [../llds/deployment-infra.md](../llds/deployment-infra.md)

- [ ] **DEPLOY-ENV-001**: The system shall read all secrets (AWS credentials, database URL) from environment variables, never from source-controlled files.
- [ ] **DEPLOY-HEALTH-001**: When `GET /health` is requested, the system shall report database connectivity and Bedrock configuration status.
- [ ] **DEPLOY-PING-001**: The system shall be pinged on a recurring schedule to prevent the free-tier backend from sleeping during expected demo hours.
- [ ] **DEPLOY-IAM-001**: The system's AWS credentials shall be scoped to only the Bedrock actions and model ARNs required by the generation agent.
