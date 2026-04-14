# Infrastructure

## Cloud spend breakdown (monthly)
- Production environment: $2,400/mo
  - API servers (2x c5.xlarge): $500
  - Postgres RDS (db.r5.large): $400
  - Redis (cache.r5.large): $300
  - S3 + CloudFront: $200
  - Monitoring (Datadog): $600
  - Misc (DNS, load balancer, etc.): $400

- Staging environments: $1,800/mo
  - staging-1: Full production mirror - $800 (used daily)
  - staging-2: Created for billing migration testing - $500 (last deploy: Feb 10)
  - staging-3: Created for 'load testing' - $500 (last deploy: Jan 22, never actually used for load testing)

- Development: $900/mo
  - Dev database: db.r5.large (production-sized) - $400 (could be db.t3.medium: $60)
  - Dev Redis: cache.r5.large - $300 (could be cache.t3.small: $30)
  - Dev monitoring: Full Datadog agent - $200 (only need basic metrics)

- Logging pipeline: $1,200/mo
  - Elasticsearch cluster for log search - $800
  - Log retention: 90 days (team only ever searches last 7 days)
  - Could reduce to 14-day retention: ~$250/mo

## Total: $6,300/mo
