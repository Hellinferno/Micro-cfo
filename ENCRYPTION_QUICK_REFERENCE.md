# 🔐 Encryption Quick Reference

## Setup (One-Time)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run setup script
python setup_encryption.py

# 3. Backup database
pg_dump microcfo > backup.sql

# 4. Run migration
alembic upgrade head

# 5. Start server
python integration_server.py
```

## Environment Variables

```bash
# Required
ENCRYPTION_KEY=<generated-key>

# Optional (S3)
S3_BUCKET_NAME=microcfo-invoices
AWS_ACCESS_KEY_ID=<your-key>
AWS_SECRET_ACCESS_KEY=<your-secret>
AWS_REGION=us-east-1
```

## Using Encrypted Columns

```python
from models import Invoice
from encryption import EncryptedString, EncryptedNumeric

# Define model with encrypted fields
class Invoice(Base):
    vendor_name = Column(EncryptedString(255))  # Encrypted
    total_amount = Column(EncryptedNumeric(15, 2))  # Encrypted

# Use normally - encryption is automatic
invoice = Invoice(
    vendor_name="Acme Corp",  # Automatically encrypted
    total_amount=15000.00      # Automatically encrypted
)
db.add(invoice)

# Read normally - decryption is automatic
invoice = db.query(Invoice).first()
print(invoice.vendor_name)  # Automatically decrypted
```

## Using File Storage

```python
from storage_manager import get_storage_manager

storage = get_storage_manager()

# Upload file (uses S3 if configured, local otherwise)
result = storage.save_file(
    file_path=Path("invoice.pdf"),
    user_id="user-123"
)

# Get file
content = storage.get_file(result['storage_key'])

# Generate download URL
url = storage.generate_download_url(
    storage_key=result['storage_key'],
    expiration=3600  # 1 hour
)

# Delete file
storage.delete_file(result['storage_key'])
```

## Testing

```bash
# Test encryption
python encryption.py

# Test S3
python s3_storage.py

# Test storage manager
python storage_manager.py
```

## Troubleshooting

### "Invalid encryption key"
```bash
# Check key is set
echo $ENCRYPTION_KEY

# Regenerate if needed
python setup_encryption.py
```

### "S3 bucket not found"
```bash
# Check bucket exists
aws s3 ls s3://microcfo-invoices

# Create if needed
aws s3 mb s3://microcfo-invoices
```

### "Decryption failed"
- Wrong encryption key
- Data corrupted
- Restore from backup

## Security Checklist

- [ ] Encryption key generated and secured
- [ ] .env file not committed to git
- [ ] Database backup created
- [ ] S3 bucket encryption enabled
- [ ] S3 public access blocked
- [ ] IAM roles configured (production)
- [ ] SSL/TLS enabled for database
- [ ] Key backup stored securely

## Quick Commands

```bash
# Generate encryption key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Test encryption
python -c "from encryption import test_encryption; test_encryption()"

# Check S3 configuration
python -c "from s3_storage import is_s3_enabled; print('S3:', 'Enabled' if is_s3_enabled() else 'Disabled')"

# Backup database
pg_dump microcfo > backup_$(date +%Y%m%d_%H%M%S).sql
```

## Documentation

- **Full Guide**: ENCRYPTION_AND_STORAGE.md
- **Summary**: ENCRYPTION_IMPLEMENTATION_SUMMARY.md
- **This File**: ENCRYPTION_QUICK_REFERENCE.md
