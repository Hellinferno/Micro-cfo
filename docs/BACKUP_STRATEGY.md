# Backup Strategy for Micro-CFO

## Overview
This document outlines the comprehensive backup and data recovery strategy for the Micro-CFO platform to ensure business continuity and data protection.

## 1. Database Backup Strategy

### Automated PostgreSQL Backups

#### Daily Full Backups
```bash
# Automated via cron job (daily at 2:00 AM)
0 2 * * * /usr/local/bin/pg_backup.sh

# Script: /usr/local/bin/pg_backup.sh
#!/bin/bash
BACKUP_DIR="/var/backups/postgresql"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_NAME="microcfo"

# Create backup directory if not exists
mkdir -p $BACKUP_DIR

# Perform backup with compression
pg_dump -U postgres -d $DB_NAME | gzip > $BACKUP_DIR/microcfo_$TIMESTAMP.sql.gz

# Retain only last 30 days of backups
find $BACKUP_DIR -name "microcfo_*.sql.gz" -mtime +30 -delete

# Upload to S3
aws s3 cp $BACKUP_DIR/microcfo_$TIMESTAMP.sql.gz s3://microcfo-backups/database/
```

#### Hourly Incremental Backups (WAL Archiving)
```bash
# PostgreSQL configuration (postgresql.conf)
wal_level = replica
archive_mode = on
archive_command = 'aws s3 cp %p s3://microcfo-backups/wal/%f'
```

### Backup Retention Policy
- **Hourly WAL**: 7 days
- **Daily Full Backups**: 30 days
- **Weekly Backups**: 12 weeks (3 months)
- **Monthly Backups**: 12 months (1 year)

## 2. File Storage Backup

### S3 Versioning
```bash
# Enable versioning on S3 bucket
aws s3api put-bucket-versioning \
  --bucket microcfo-documents \
  --versioning-configuration Status=Enabled

# Enable lifecycle policy
aws s3api put-bucket-lifecycle-configuration \
  --bucket microcfo-documents \
  --lifecycle-configuration file://lifecycle.json
```

**lifecycle.json**:
```json
{
  "Rules": [
    {
      "Id": "ArchiveOldVersions",
      "Status": "Enabled",
      "NoncurrentVersionTransitions": [
        {
          "NoncurrentDays": 30,
          "StorageClass": "GLACIER"
        }
      ],
      "NoncurrentVersionExpiration": {
        "NoncurrentDays": 365
      }
    }
  ]
}
```

## 3. Vector Database Backup (ChromaDB)

### Automated ChromaDB Backup
```python
# Script: scripts/backup_chromadb.py
import shutil
from datetime import datetime
from pathlib import Path
import boto3

def backup_chromadb():
    """Backup ChromaDB collections"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Legal database backup
    legal_db = Path("legal_db")
    legal_backup = Path(f"/tmp/legal_db_backup_{timestamp}")
    shutil.copytree(legal_db, legal_backup)
    
    # Scheme database backup
    scheme_db = Path("scheme_db")
    scheme_backup = Path(f"/tmp/scheme_db_backup_{timestamp}")
    shutil.copytree(scheme_db, scheme_backup)
    
    # Compress and upload to S3
    s3 = boto3.client('s3')
    shutil.make_archive(legal_backup, 'gztar', legal_backup)
    shutil.make_archive(scheme_backup, 'gztar', scheme_backup)
    
    s3.upload_file(
        f"{legal_backup}.tar.gz",
        "microcfo-backups",
        f"chromadb/legal_db_{timestamp}.tar.gz"
    )
    s3.upload_file(
        f"{scheme_backup}.tar.gz",
        "microcfo-backups",
        f"chromadb/scheme_db_{timestamp}.tar.gz"
    )

if __name__ == "__main__":
    backup_chromadb()
```

**Cron Schedule**:
```bash
# Daily at 3:00 AM
0 3 * * * /usr/bin/python3 /opt/microcfo/scripts/backup_chromadb.py
```

## 4. Application Configuration Backup

### Environment Variables & Secrets
```bash
# Backup script: /usr/local/bin/backup_config.sh
#!/bin/bash
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Backup .env files (encrypted)
tar czf /tmp/config_$TIMESTAMP.tar.gz \
    /opt/microcfo/.env \
    /opt/microcfo/config/ \
    /opt/microcfo/alembic.ini

# Encrypt with GPG
gpg --encrypt --recipient admin@microcfo.com /tmp/config_$TIMESTAMP.tar.gz

# Upload to S3
aws s3 cp /tmp/config_$TIMESTAMP.tar.gz.gpg s3://microcfo-backups/config/

# Cleanup
rm /tmp/config_$TIMESTAMP.tar.gz*
```

## 5. Backup Testing & Validation

### Monthly Restore Tests
```bash
# Script: /usr/local/bin/test_restore.sh
#!/bin/bash
TEST_DB="microcfo_restore_test"

# Download latest backup
LATEST_BACKUP=$(aws s3 ls s3://microcfo-backups/database/ | sort | tail -n 1 | awk '{print $4}')
aws s3 cp s3://microcfo-backups/database/$LATEST_BACKUP /tmp/

# Create test database
psql -U postgres -c "DROP DATABASE IF EXISTS $TEST_DB;"
psql -U postgres -c "CREATE DATABASE $TEST_DB;"

# Restore backup
gunzip -c /tmp/$LATEST_BACKUP | psql -U postgres -d $TEST_DB

# Verify data integrity
psql -U postgres -d $TEST_DB -c "SELECT COUNT(*) FROM users;"
psql -U postgres -d $TEST_DB -c "SELECT COUNT(*) FROM invoices;"

# Cleanup
psql -U postgres -c "DROP DATABASE $TEST_DB;"
rm /tmp/$LATEST_BACKUP
```

## 6. Monitoring & Alerting

### Backup Monitoring
```python
# Add to integration_server.py or monitoring service
import boto3
from datetime import datetime, timedelta

def check_backup_status():
    """Alert if backups are missing"""
    s3 = boto3.client('s3')
    bucket = 'microcfo-backups'
    
    # Check last database backup
    response = s3.list_objects_v2(
        Bucket=bucket,
        Prefix='database/',
        MaxKeys=1
    )
    
    if response['Contents']:
        last_backup = response['Contents'][0]['LastModified']
        age = datetime.now(last_backup.tzinfo) - last_backup
        
        if age > timedelta(hours=25):  # Should be daily
            # Send alert
            send_alert("Database backup is overdue!")
    else:
        send_alert("No database backups found!")
```

## 7. Recovery Time Objectives (RTO) & Recovery Point Objectives (RPO)

### Targets
- **RPO (Recovery Point Objective)**: 1 hour (via WAL)
- **RTO (Recovery Time Objective)**: 4 hours for full restore
- **Data Retention**: 1 year for critical data

### Recovery Procedures

#### Full Database Restore
```bash
# 1. Stop application
systemctl stop microcfo

# 2. Download backup
aws s3 cp s3://microcfo-backups/database/microcfo_YYYYMMDD.sql.gz /tmp/

# 3. Drop and recreate database
psql -U postgres -c "DROP DATABASE microcfo;"
psql -U postgres -c "CREATE DATABASE microcfo;"

# 4. Restore data
gunzip -c /tmp/microcfo_YYYYMMDD.sql.gz | psql -U postgres -d microcfo

# 5. Apply WAL files if needed
# (Restore from point-in-time)

# 6. Restart application
systemctl start microcfo
```

## 8. Security Considerations

### Backup Encryption
- All backups encrypted at rest (S3 SSE-KMS)
- Transfer encryption (TLS for S3 uploads)
- Config backups use GPG encryption

### Access Control
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::ACCOUNT:role/BackupRole"
      },
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::microcfo-backups",
        "arn:aws:s3:::microcfo-backups/*"
      ]
    }
  ]
}
```

## 9. Compliance

### Data Retention for Indian MSMEs
- **Financial Records**: 8 years (Companies Act 2013)
- **Tax Records**: 7 years (Income Tax Act)
- **User Data**: As per GDPR/DPDPA requirements

## 10. Backup Checklist

### Daily
- [ ] Verify database backup completed
- [ ] Check S3 upload success
- [ ] Review backup logs

### Weekly
- [ ] Verify WAL archiving
- [ ] Check backup storage usage
- [ ] Review retention policy compliance

### Monthly
- [ ] Perform restore test
- [ ] Audit backup access logs
- [ ] Update documentation if needed

### Quarterly
- [ ] Review and update backup strategy
- [ ] Test disaster recovery procedures
- [ ] Security audit of backup systems

---

**Document Version**: 1.0  
**Last Updated**: January 31, 2026  
**Owner**: DevOps Team
