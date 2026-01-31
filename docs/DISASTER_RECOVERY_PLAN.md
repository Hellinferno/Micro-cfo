# Disaster Recovery Plan for Micro-CFO

## Executive Summary
This Disaster Recovery Plan (DRP) ensures the Micro-CFO platform can recover from catastrophic failures with minimal data loss and downtime, protecting critical financial data for Indian MSMEs.

## 1. Disaster Scenarios & Response

### Critical Scenarios

#### Scenario 1: Complete Data Center Failure
**Impact**: Total service outage  
**RPO**: 1 hour  
**RTO**: 6 hours  
**Recovery Steps**: See Section 3.1

#### Scenario 2: Database Corruption
**Impact**: Data integrity compromised  
**RPO**: 1 hour (via WAL)  
**RTO**: 2 hours  
**Recovery Steps**: See Section 3.2

#### Scenario 3: Ransomware Attack
**Impact**: Encrypted production data  
**RPO**: 24 hours (last clean backup)  
**RTO**: 8 hours  
**Recovery Steps**: See Section 3.3

#### Scenario 4: Regional AWS Outage
**Impact**: Service unavailable in primary region  
**RPO**: 15 minutes (cross-region replication)  
**RTO**: 30 minutes (failover)  
**Recovery Steps**: See Section 3.4

#### Scenario 5: Critical Bug in Production
**Impact**: Service degradation or data corruption  
**RPO**: 5 minutes  
**RTO**: 15 minutes (rollback)  
**Recovery Steps**: See Section 3.5

## 2. Infrastructure Architecture for DR

### Multi-Region Setup

```
Primary Region: ap-south-1 (Mumbai)
└── Availability Zones: ap-south-1a, ap-south-1b

Secondary Region: ap-southeast-1 (Singapore)
└── Availability Zones: ap-southeast-1a, ap-southeast-1b

Backup Storage: Multi-region S3 with versioning
```

### Component Redundancy

| Component | Primary | Secondary | Failover Time |
|-----------|---------|-----------|---------------|
| Application Servers | 3x instances | 2x instances (standby) | < 5 minutes |
| Database | PostgreSQL Primary | Read Replica + Standby | < 2 minutes |
| Redis Cache | Cluster mode | Backup cluster | < 1 minute |
| Load Balancer | ALB Multi-AZ | Route53 health checks | Automatic |
| File Storage | S3 (primary bucket) | S3 Cross-region replication | Automatic |

## 3. Recovery Procedures

### 3.1 Complete Data Center Failure

**Trigger**: Primary region unavailable for >15 minutes

**Steps**:

1. **Activate Emergency Response Team** (0-5 minutes)
   ```bash
   # Alert team via PagerDuty
   curl -X POST https://events.pagerduty.com/v2/enqueue \
     -H 'Authorization: Token token=YOUR_KEY' \
     -d '{"event_action":"trigger","routing_key":"DR_KEY"}'
   ```

2. **Verify Backup Region Status** (5-10 minutes)
   ```bash
   # Check secondary region health
   aws ec2 describe-instances --region ap-southeast-1 \
     --filters "Name=tag:Environment,Values=production-dr"
   
   # Verify database replica
   psql -h dr-db.microcfo.com -U postgres -c "SELECT pg_is_in_recovery();"
   ```

3. **Promote Database Replica** (10-15 minutes)
   ```bash
   # Promote read replica to primary
   aws rds promote-read-replica \
     --db-instance-identifier microcfo-db-replica-sg \
     --backup-retention-period 7 \
     --region ap-southeast-1
   ```

4. **Update DNS Records** (15-20 minutes)
   ```bash
   # Switch Route53 to secondary region
   aws route53 change-resource-record-sets \
     --hosted-zone-id Z1234567890ABC \
     --change-batch file://failover-recordset.json
   ```

   **failover-recordset.json**:
   ```json
   {
     "Changes": [{
       "Action": "UPSERT",
       "ResourceRecordSet": {
         "Name": "api.microcfo.com",
         "Type": "A",
         "AliasTarget": {
           "HostedZoneId": "Z3VA4XTPXXX",
           "DNSName": "dr-alb-singapore.amazonaws.com",
           "EvaluateTargetHealth": true
         }
       }
     }]
   }
   ```

5. **Scale Up DR Environment** (20-40 minutes)
   ```bash
   # Increase instance count
   aws autoscaling set-desired-capacity \
     --auto-scaling-group-name microcfo-dr-asg \
     --desired-capacity 5 \
     --region ap-southeast-1
   ```

6. **Validate Service** (40-60 minutes)
   ```bash
   # Run health checks
   curl https://api.microcfo.com/health
   
   # Test critical endpoints
   python tests/smoke_tests.py --env=production
   ```

7. **Notify Stakeholders** (60+ minutes)
   ```python
   # Send notifications
   from notifications import send_sms, send_email
   
   send_email(
       to=["cto@microcfo.com", "team@microcfo.com"],
       subject="DR Activated: Service Running in Singapore Region",
       body="Primary region failed. Service restored in secondary region."
   )
   ```

### 3.2 Database Corruption Recovery

**Trigger**: Database integrity check failures or corrupted data detected

**Steps**:

1. **Isolate Corrupted Database** (0-5 minutes)
   ```bash
   # Stop application connections
   psql -U postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='microcfo';"
   
   # Rename corrupted database
   psql -U postgres -c "ALTER DATABASE microcfo RENAME TO microcfo_corrupted;"
   ```

2. **Identify Last Good Backup** (5-10 minutes)
   ```bash
   # List recent backups
   aws s3 ls s3://microcfo-backups/database/ --recursive | sort | tail -20
   
   # Check backup integrity
   aws s3 cp s3://microcfo-backups/database/microcfo_20260131_020000.sql.gz /tmp/
   gunzip -t /tmp/microcfo_20260131_020000.sql.gz
   ```

3. **Restore from Backup** (10-40 minutes)
   ```bash
   # Create new database
   psql -U postgres -c "CREATE DATABASE microcfo;"
   
   # Restore backup
   gunzip -c /tmp/microcfo_20260131_020000.sql.gz | psql -U postgres -d microcfo
   
   # Apply WAL files for point-in-time recovery
   restore_command = 'aws s3 cp s3://microcfo-backups/wal/%f %p'
   ```

4. **Verify Data Integrity** (40-50 minutes)
   ```sql
   -- Check record counts
   SELECT 'users' as table_name, COUNT(*) FROM users
   UNION ALL
   SELECT 'invoices', COUNT(*) FROM invoices
   UNION ALL
   SELECT 'user_profiles', COUNT(*) FROM user_profiles;
   
   -- Verify key constraints
   SELECT conname, contype FROM pg_constraint WHERE connamespace = 'public'::regnamespace;
   ```

5. **Restart Application** (50-60 minutes)
   ```bash
   systemctl start microcfo
   ```

### 3.3 Ransomware Attack Response

**Trigger**: Encrypted files detected or ransom demand received

**Steps**:

1. **IMMEDIATE: Isolate Systems** (0-2 minutes)
   ```bash
   # Disconnect from network
   sudo iptables -P INPUT DROP
   sudo iptables -P OUTPUT DROP
   
   # Preserve evidence
   sudo dd if=/dev/sda of=/mnt/forensics/disk_image.img bs=4M
   ```

2. **Alert Security Team** (2-5 minutes)
   ```bash
   # Emergency alert
   # Contact: security@microcfo.com
   # Incident Response Team Lead: +91-XXXXXXXXXX
   ```

3. **Identify Infection Vector** (5-30 minutes)
   - Review application logs
   - Check system access logs
   - Analyze network traffic

4. **Assess Damage** (30-60 minutes)
   ```bash
   # Check encrypted files
   find /var/lib/postgresql -name "*.encrypted" -o -name "*.locked"
   
   # Verify backup integrity
   aws s3 ls s3://microcfo-backups/database/ | grep $(date -d "2 days ago" +%Y%m%d)
   ```

5. **Clean Recovery Environment** (60-90 minutes)
   ```bash
   # Spin up new clean instances
   aws ec2 run-instances --image-id ami-clean-backup \
     --count 3 --instance-type t3.medium
   ```

6. **Restore from Clean Backup** (90-240 minutes)
   - Use backup from before infection date
   - Follow procedures in Section 3.2
   - Verify no malware in backups

7. **Implement Security Patches** (240-300 minutes)
   ```bash
   # Update all systems
   apt-get update && apt-get upgrade -y
   
   # Apply security hardening
   bash scripts/security_hardening.sh
   ```

8. **Post-Incident Review** (Next 48 hours)
   - Root cause analysis
   - Update security policies
   - Enhance monitoring

### 3.4 Regional AWS Outage

**Trigger**: AWS status page shows region-wide outage

**Steps** (Largely automated via Route53 health checks):

1. **Automatic Failover** (0-2 minutes)
   - Route53 detects unhealthy endpoints
   - Automatically routes to secondary region

2. **Monitor Failover** (2-10 minutes)
   ```bash
   # Watch DNS propagation
   watch -n 5 'dig api.microcfo.com +short'
   
   # Monitor secondary region load
   aws cloudwatch get-metric-statistics --region ap-southeast-1 \
     --metric-name CPUUtilization --namespace AWS/EC2
   ```

3. **Scale if Needed** (10-30 minutes)
   ```bash
   # Auto-scaling should handle, but manual override if needed
   aws autoscaling set-desired-capacity \
     --auto-scaling-group-name microcfo-dr-asg \
     --desired-capacity 10
   ```

4. **Communicate Status** (Ongoing)
   - Update status page: status.microcfo.com
   - Send notifications to users
   - Post updates on social media

### 3.5 Critical Bug Rollback

**Trigger**: Severe bug detected in production

**Steps**:

1. **Immediate Rollback** (0-5 minutes)
   ```bash
   # Rollback to previous Docker image
   kubectl set image deployment/microcfo-api \
     microcfo=microcfo:stable-previous
   
   # Or via Git
   git revert HEAD
   git push origin main
   ```

2. **Verify Rollback** (5-10 minutes)
   ```bash
   # Check deployment status
   kubectl rollout status deployment/microcfo-api
   
   # Run smoke tests
   python tests/smoke_tests.py
   ```

3. **Database Rollback** (if needed) (10-30 minutes)
   ```bash
   # Downgrade migrations
   alembic downgrade -1
   ```

## 4. Communication Plan

### Stakeholder Contact List

| Role | Name | Contact | Escalation Time |
|------|------|---------|-----------------|
| CTO | [Name] | +91-XXX, cto@microcfo.com | Immediate |
| DevOps Lead | [Name] | +91-XXX, devops@microcfo.com | Immediate |
| Security Lead | [Name] | +91-XXX, security@microcfo.com | < 5 min |
| CEO | [Name] | +91-XXX, ceo@microcfo.com | < 15 min |
| Customer Support | Team | support@microcfo.com | < 10 min |

### Communication Templates

#### Internal Alert
```
PRIORITY: URGENT
INCIDENT: [Type]
STATUS: [Active/Resolved]
IMPACT: [Description]
ETA: [Recovery time]
ACTIONS: [What we're doing]
```

#### Customer Notification
```
Subject: Service Update - Micro-CFO

Dear Valued Customer,

We are currently experiencing [issue]. Our team is actively working to resolve this.

Current Status: [Description]
Expected Resolution: [Time]
Impact: [What features are affected]

We apologize for any inconvenience. Updates will be posted at status.microcfo.com

Thank you for your patience.
- Micro-CFO Team
```

## 5. Testing & Validation

### Quarterly DR Drills

**Schedule**:
- Q1: Database failover test
- Q2: Full region failover
- Q3: Ransomware scenario
- Q4: Complete DR exercise

**Metrics to Track**:
- Actual RTO vs. target
- Actual RPO vs. target
- Team response time
- Issues encountered
- Lessons learned

### Monthly Backup Validation
```bash
# Automated restore test
#!/bin/bash
# Run on 1st of each month

# Restore to test environment
./scripts/test_restore.sh

# Run integration tests
pytest tests/integration/ --env=restore-test

# Generate report
python scripts/generate_dr_report.py
```

## 6. Post-Incident Procedures

### Within 24 Hours
1. Document incident timeline
2. Preliminary root cause analysis
3. Immediate fixes/patches

### Within 1 Week
1. Complete incident report
2. Update DR procedures
3. Implement preventive measures
4. Team retrospective

### Within 1 Month
1. Security audit
2. Architecture review
3. Update monitoring/alerting
4. Training for team

## 7. Annual DR Plan Review

### Checklist
- [ ] Review and update contact information
- [ ] Verify backup/restore procedures
- [ ] Test all DR scenarios
- [ ] Update documentation
- [ ] Review and adjust RTO/RPO targets
- [ ] Audit access controls
- [ ] Update incident response playbooks
- [ ] Review insurance coverage
- [ ] Assess new threats/risks

---

**Document Version**: 1.0  
**Last Reviewed**: January 31, 2026  
**Next Review**: July 31, 2026  
**Owner**: CTO / DevOps Lead  
**Approval**: CEO
