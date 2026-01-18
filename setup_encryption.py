#!/usr/bin/env python3
"""
Setup script for encryption and secure storage
Generates encryption key and provides configuration guidance
"""

import os
import sys
from pathlib import Path


def generate_encryption_key():
    """Generate a new Fernet encryption key"""
    from cryptography.fernet import Fernet
    key = Fernet.generate_key()
    return key.decode('utf-8')


def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import cryptography
        import boto3
        import sqlalchemy
        print("✅ All required dependencies installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("\nInstall dependencies with:")
        print("  pip install -r requirements.txt")
        return False


def create_env_file():
    """Create or update .env file with encryption configuration"""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    # Generate new encryption key
    encryption_key = generate_encryption_key()
    
    print("\n" + "="*60)
    print("🔐 ENCRYPTION KEY GENERATED")
    print("="*60)
    print(f"\nENCRYPTION_KEY={encryption_key}")
    print("\n⚠️  IMPORTANT: Save this key securely!")
    print("   - Add it to your .env file")
    print("   - Store a backup in a secure location")
    print("   - Never commit it to version control")
    print("   - Loss of this key means data cannot be decrypted")
    print("="*60)
    
    # Check if .env exists
    if env_file.exists():
        print(f"\n📝 .env file already exists at: {env_file}")
        response = input("Do you want to add the encryption key to it? (y/n): ")
        if response.lower() == 'y':
            with open(env_file, 'a') as f:
                f.write(f"\n# Encryption Configuration (Added {os.popen('date').read().strip()})\n")
                f.write(f"ENCRYPTION_KEY={encryption_key}\n")
            print("✅ Encryption key added to .env file")
    else:
        print(f"\n📝 Creating new .env file...")
        with open(env_file, 'w') as f:
            f.write("# MicroCFO Environment Configuration\n\n")
            f.write("# ========================================\n")
            f.write("# ENCRYPTION CONFIGURATION\n")
            f.write("# ========================================\n")
            f.write(f"ENCRYPTION_KEY={encryption_key}\n\n")
            f.write("# ========================================\n")
            f.write("# S3 STORAGE CONFIGURATION (Optional)\n")
            f.write("# ========================================\n")
            f.write("# AWS_ACCESS_KEY_ID=your-access-key\n")
            f.write("# AWS_SECRET_ACCESS_KEY=your-secret-key\n")
            f.write("# AWS_REGION=us-east-1\n")
            f.write("# S3_BUCKET_NAME=microcfo-invoices\n")
            f.write("# KMS_KEY_ID=your-kms-key-id  # Optional: for SSE-KMS\n\n")
            f.write("# ========================================\n")
            f.write("# LOCAL STORAGE FALLBACK\n")
            f.write("# ========================================\n")
            f.write("LOCAL_STORAGE_DIR=file_storage\n\n")
            f.write("# ========================================\n")
            f.write("# DATABASE CONFIGURATION\n")
            f.write("# ========================================\n")
            f.write("DATABASE_URL=postgresql://microcfo:changeme@localhost:5432/microcfo\n")
        print(f"✅ Created .env file at: {env_file}")


def test_encryption():
    """Test encryption functionality"""
    print("\n" + "="*60)
    print("🧪 TESTING ENCRYPTION")
    print("="*60)
    
    try:
        from encryption import test_encryption
        test_encryption()
        print("✅ Encryption tests passed")
        return True
    except Exception as e:
        print(f"❌ Encryption test failed: {e}")
        return False


def check_s3_configuration():
    """Check if S3 is configured"""
    print("\n" + "="*60)
    print("☁️  S3 STORAGE CONFIGURATION")
    print("="*60)
    
    s3_bucket = os.getenv('S3_BUCKET_NAME')
    
    if s3_bucket:
        print(f"✅ S3 bucket configured: {s3_bucket}")
        
        try:
            from s3_storage import get_s3_manager
            manager = get_s3_manager()
            print(f"✅ S3 manager initialized")
            print(f"   Region: {manager.region}")
            print(f"   Encryption: {manager.encryption_type}")
            return True
        except Exception as e:
            print(f"⚠️  S3 configuration error: {e}")
            print("   Files will be stored locally")
            return False
    else:
        print("⚠️  S3 not configured")
        print("   Files will be stored locally in: file_storage/")
        print("\nTo enable S3 storage, add to .env:")
        print("   S3_BUCKET_NAME=your-bucket-name")
        print("   AWS_ACCESS_KEY_ID=your-access-key")
        print("   AWS_SECRET_ACCESS_KEY=your-secret-key")
        print("   AWS_REGION=us-east-1")
        return False


def create_local_storage_dir():
    """Create local storage directory"""
    storage_dir = Path(os.getenv('LOCAL_STORAGE_DIR', 'file_storage'))
    storage_dir.mkdir(exist_ok=True, parents=True)
    print(f"\n✅ Local storage directory created: {storage_dir}")


def print_next_steps():
    """Print next steps for user"""
    print("\n" + "="*60)
    print("📋 NEXT STEPS")
    print("="*60)
    print("\n1. Review and secure your encryption key")
    print("   - Backup the key to a secure location")
    print("   - Consider using a secrets manager in production")
    print("\n2. Configure S3 storage (recommended for production)")
    print("   - Create S3 bucket with encryption enabled")
    print("   - Add S3 credentials to .env file")
    print("   - See ENCRYPTION_AND_STORAGE.md for details")
    print("\n3. Run database migration")
    print("   - Backup your database first!")
    print("   - Run: alembic upgrade head")
    print("\n4. Test the setup")
    print("   - Run: python test_encryption_setup.py")
    print("\n5. Start the server")
    print("   - Run: python integration_server.py")
    print("\n📚 Documentation: ENCRYPTION_AND_STORAGE.md")
    print("="*60)


def main():
    """Main setup function"""
    print("\n" + "="*60)
    print("🔐 MicroCFO Encryption & Storage Setup")
    print("="*60)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Create .env file with encryption key
    create_env_file()
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Test encryption
    if not test_encryption():
        print("\n⚠️  Encryption test failed. Please check your setup.")
    
    # Check S3 configuration
    check_s3_configuration()
    
    # Create local storage directory
    create_local_storage_dir()
    
    # Print next steps
    print_next_steps()
    
    print("\n✅ Setup complete!")


if __name__ == "__main__":
    main()
