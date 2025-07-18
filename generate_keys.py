#!/usr/bin/env python3
"""
SDX Project Manager - Enterprise Security Key Generator
DENSO Innovation Team - Production-Grade Security Keys
Version: 2.5.0 | Updated: 2025-01-18
"""

import secrets
import string
import hashlib
import base64
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import argparse


class EnterpriseKeyGenerator:
    """Enterprise-grade security key generator for production environments"""

    def __init__(self):
        self.key_types = {
            "basic": 32,  # Standard keys
            "enhanced": 48,  # Production keys
            "critical": 64,  # High-security keys
            "jwt": 64,  # JWT signing keys
            "encryption": 32,  # AES-256 compatible
            "token": 43,  # URL-safe tokens
        }

    def generate_cryptographically_secure_key(
        self, length: int = 32, key_type: str = "urlsafe"
    ) -> str:
        """สร้าง cryptographically secure key"""
        if key_type == "urlsafe":
            return secrets.token_urlsafe(length)
        elif key_type == "hex":
            return secrets.token_hex(length)
        elif key_type == "bytes":
            return secrets.token_bytes(length)
        else:
            # Custom alphabet for maximum security
            alphabet = string.ascii_letters + string.digits + "-._~"
            return "".join(secrets.choice(alphabet) for _ in range(length))

    def generate_jwt_secret_pair(self) -> Dict[str, str]:
        """สร้าง JWT key pair สำหรับ access + refresh tokens"""
        return {
            "access_secret": self.generate_cryptographically_secure_key(64, "urlsafe"),
            "refresh_secret": self.generate_cryptographically_secure_key(64, "urlsafe"),
            "signing_key": self.generate_cryptographically_secure_key(48, "urlsafe"),
            "verification_key": self.generate_cryptographically_secure_key(
                48, "urlsafe"
            ),
        }

    def generate_encryption_key_set(self) -> Dict[str, str]:
        """สร้าง encryption keys สำหรับ data protection"""
        # Generate Fernet-compatible key
        fernet_key = Fernet.generate_key().decode("utf-8")

        return {
            "fernet_key": fernet_key,
            "data_encryption_key": self.generate_cryptographically_secure_key(
                32, "urlsafe"
            ),
            "field_encryption_key": self.generate_cryptographically_secure_key(
                32, "urlsafe"
            ),
            "file_encryption_key": self.generate_cryptographically_secure_key(
                32, "urlsafe"
            ),
            "backup_encryption_key": self.generate_cryptographically_secure_key(
                48, "urlsafe"
            ),
        }

    def generate_api_security_keys(self) -> Dict[str, str]:
        """สร้าง API security keys"""
        return {
            "api_key": f"sdx_{self.generate_cryptographically_secure_key(32, 'urlsafe')}",
            "api_secret": self.generate_cryptographically_secure_key(48, "urlsafe"),
            "webhook_secret": self.generate_cryptographically_secure_key(32, "urlsafe"),
            "csrf_token": self.generate_cryptographically_secure_key(24, "urlsafe"),
            "request_signing_key": self.generate_cryptographically_secure_key(
                32, "urlsafe"
            ),
        }

    def generate_session_security_keys(self) -> Dict[str, str]:
        """สร้าง session management keys"""
        return {
            "session_secret": self.generate_cryptographically_secure_key(48, "urlsafe"),
            "cookie_secret": self.generate_cryptographically_secure_key(32, "urlsafe"),
            "remember_me_key": self.generate_cryptographically_secure_key(
                32, "urlsafe"
            ),
            "csrf_protection_key": self.generate_cryptographically_secure_key(
                24, "urlsafe"
            ),
        }

    def generate_database_keys(self) -> Dict[str, str]:
        """สร้าง database security keys"""
        return {
            "db_encryption_key": self.generate_cryptographically_secure_key(
                32, "urlsafe"
            ),
            "backup_encryption_key": self.generate_cryptographically_secure_key(
                48, "urlsafe"
            ),
            "audit_signing_key": self.generate_cryptographically_secure_key(
                32, "urlsafe"
            ),
            "connection_secret": self.generate_cryptographically_secure_key(
                24, "urlsafe"
            ),
        }

    def generate_integration_keys(self) -> Dict[str, str]:
        """สร้าง third-party integration keys"""
        return {
            "oauth_client_secret": self.generate_cryptographically_secure_key(
                48, "urlsafe"
            ),
            "webhook_verification_key": self.generate_cryptographically_secure_key(
                32, "urlsafe"
            ),
            "api_rate_limit_key": self.generate_cryptographically_secure_key(
                24, "urlsafe"
            ),
            "external_service_key": self.generate_cryptographically_secure_key(
                32, "urlsafe"
            ),
        }

    def validate_key_strength(self, key: str) -> Dict[str, any]:
        """ตรวจสอบความแข็งแกร่งของ key"""
        validation = {
            "length_check": len(key) >= 24,
            "entropy_check": False,
            "character_diversity": False,
            "security_score": 0,
            "recommendations": [],
        }

        # ตรวจสอบ entropy
        unique_chars = len(set(key))
        entropy_ratio = unique_chars / len(key) if len(key) > 0 else 0
        validation["entropy_check"] = entropy_ratio > 0.6

        # ตรวจสอบความหลากหลายของตัวอักษร
        has_upper = any(c.isupper() for c in key)
        has_lower = any(c.islower() for c in key)
        has_digit = any(c.isdigit() for c in key)
        has_special = any(c in "-._~" for c in key)

        diversity_score = sum([has_upper, has_lower, has_digit, has_special])
        validation["character_diversity"] = diversity_score >= 3

        # คำนวณ security score
        length_score = min(len(key) / 32 * 40, 40)  # Max 40 points
        entropy_score = entropy_ratio * 30  # Max 30 points
        diversity_score = diversity_score * 7.5  # Max 30 points

        validation["security_score"] = int(
            length_score + entropy_score + diversity_score
        )

        # ข้อแนะนำ
        if validation["security_score"] < 70:
            validation["recommendations"].append("ใช้ key ที่ยาวกว่า 32 characters")
        if not validation["entropy_check"]:
            validation["recommendations"].append("เพิ่มความหลากหลายของตัวอักษร")
        if not validation["character_diversity"]:
            validation["recommendations"].append("ใช้ตัวอักษรพิมพ์ใหญ่ เล็ก ตัวเลข และสัญลักษณ์")

        return validation

    def generate_complete_key_set(
        self, environment: str = "production"
    ) -> Dict[str, any]:
        """สร้าง complete key set สำหรับ environment ที่กำหนด"""

        # กำหนด security level ตาม environment
        if environment == "production":
            base_length = 48
        elif environment == "staging":
            base_length = 32
        else:  # development
            base_length = 24

        key_set = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "environment": environment,
                "version": "2.5.0",
                "security_level": "enterprise-grade",
                "expires_at": (datetime.now() + timedelta(days=365)).isoformat(),
            },
            "application": {
                "secret_key": self.generate_cryptographically_secure_key(
                    base_length, "urlsafe"
                ),
                "app_id": f"sdx_{secrets.token_hex(8)}",
                "instance_id": f"inst_{secrets.token_hex(6)}",
            },
            "jwt": self.generate_jwt_secret_pair(),
            "encryption": self.generate_encryption_key_set(),
            "api": self.generate_api_security_keys(),
            "session": self.generate_session_security_keys(),
            "database": self.generate_database_keys(),
            "integration": self.generate_integration_keys(),
        }

        return key_set

    def export_secrets_toml(self, key_set: Dict[str, any]) -> str:
        """Export keys ในรูปแบบ .streamlit/secrets.toml"""

        toml_content = f"""# .streamlit/secrets.toml
# SDX Project Manager - Enterprise Security Configuration
# Generated: {key_set['metadata']['generated_at']}
# Environment: {key_set['metadata']['environment']}
# ⚠️ NEVER commit this file to version control!

# =============================================================================
# APPLICATION SECURITY
# =============================================================================

[app]
secret_key = "{key_set['application']['secret_key']}"
app_id = "{key_set['application']['app_id']}"
instance_id = "{key_set['application']['instance_id']}"
debug_mode = {"true" if key_set['metadata']['environment'] != 'production' else "false"}

# =============================================================================
# JWT AUTHENTICATION
# =============================================================================

[jwt]
access_secret = "{key_set['jwt']['access_secret']}"
refresh_secret = "{key_set['jwt']['refresh_secret']}"
signing_key = "{key_set['jwt']['signing_key']}"
verification_key = "{key_set['jwt']['verification_key']}"
algorithm = "HS256"
access_token_expires = 3600    # 1 hour
refresh_token_expires = 604800 # 7 days

# =============================================================================
# DATA ENCRYPTION
# =============================================================================

[encryption]
fernet_key = "{key_set['encryption']['fernet_key']}"
data_encryption_key = "{key_set['encryption']['data_encryption_key']}"
field_encryption_key = "{key_set['encryption']['field_encryption_key']}"
file_encryption_key = "{key_set['encryption']['file_encryption_key']}"
backup_encryption_key = "{key_set['encryption']['backup_encryption_key']}"

# =============================================================================
# API SECURITY
# =============================================================================

[api]
api_key = "{key_set['api']['api_key']}"
api_secret = "{key_set['api']['api_secret']}"
webhook_secret = "{key_set['api']['webhook_secret']}"
csrf_token = "{key_set['api']['csrf_token']}"
request_signing_key = "{key_set['api']['request_signing_key']}"
rate_limit_per_hour = 1000
rate_limit_burst = 100

# =============================================================================
# SESSION MANAGEMENT
# =============================================================================

[session]
session_secret = "{key_set['session']['session_secret']}"
cookie_secret = "{key_set['session']['cookie_secret']}"
remember_me_key = "{key_set['session']['remember_me_key']}"
csrf_protection_key = "{key_set['session']['csrf_protection_key']}"
session_timeout = 28800        # 8 hours
remember_me_duration = 604800  # 7 days

# =============================================================================
# DATABASE SECURITY
# =============================================================================

[database_security]
db_encryption_key = "{key_set['database']['db_encryption_key']}"
backup_encryption_key = "{key_set['database']['backup_encryption_key']}"
audit_signing_key = "{key_set['database']['audit_signing_key']}"
connection_secret = "{key_set['database']['connection_secret']}"

# =============================================================================
# INTEGRATION SECURITY
# =============================================================================

[integration]
oauth_client_secret = "{key_set['integration']['oauth_client_secret']}"
webhook_verification_key = "{key_set['integration']['webhook_verification_key']}"
api_rate_limit_key = "{key_set['integration']['api_rate_limit_key']}"
external_service_key = "{key_set['integration']['external_service_key']}"

# =============================================================================
# SECURITY POLICIES
# =============================================================================

[security_policy]
password_min_length = 8
password_require_uppercase = true
password_require_lowercase = true
password_require_numbers = true
password_require_special = true
password_history_count = 5
max_login_attempts = 5
lockout_duration = 1800        # 30 minutes
session_rolling = true
concurrent_sessions_limit = 3

# =============================================================================
# ENVIRONMENT CONFIGURATION
# =============================================================================

[environment]
name = "{key_set['metadata']['environment']}"
security_level = "{key_set['metadata']['security_level']}"
generated_at = "{key_set['metadata']['generated_at']}"
expires_at = "{key_set['metadata']['expires_at']}"
version = "{key_set['metadata']['version']}"
"""
        return toml_content

    def export_env_file(self, key_set: Dict[str, any]) -> str:
        """Export keys ในรูปแบบ .env file"""

        env_content = f"""# SDX Project Manager - Environment Variables
# Generated: {key_set['metadata']['generated_at']}
# Environment: {key_set['metadata']['environment']}

# Application
SDX_SECRET_KEY={key_set['application']['secret_key']}
SDX_APP_ID={key_set['application']['app_id']}
SDX_INSTANCE_ID={key_set['application']['instance_id']}

# JWT
SDX_JWT_ACCESS_SECRET={key_set['jwt']['access_secret']}
SDX_JWT_REFRESH_SECRET={key_set['jwt']['refresh_secret']}
SDX_JWT_SIGNING_KEY={key_set['jwt']['signing_key']}

# Encryption
SDX_FERNET_KEY={key_set['encryption']['fernet_key']}
SDX_DATA_ENCRYPTION_KEY={key_set['encryption']['data_encryption_key']}
SDX_FILE_ENCRYPTION_KEY={key_set['encryption']['file_encryption_key']}

# API Security
SDX_API_KEY={key_set['api']['api_key']}
SDX_API_SECRET={key_set['api']['api_secret']}
SDX_WEBHOOK_SECRET={key_set['api']['webhook_secret']}

# Session
SDX_SESSION_SECRET={key_set['session']['session_secret']}
SDX_COOKIE_SECRET={key_set['session']['cookie_secret']}
"""
        return env_content


def main():
    """Main function with CLI interface"""
    parser = argparse.ArgumentParser(
        description="SDX Project Manager - Enterprise Security Key Generator"
    )
    parser.add_argument(
        "--environment",
        "-e",
        choices=["development", "staging", "production"],
        default="production",
        help="Target environment (default: production)",
    )
    parser.add_argument(
        "--output",
        "-o",
        choices=["console", "file", "both"],
        default="both",
        help="Output format (default: both)",
    )
    parser.add_argument(
        "--validate", "-v", action="store_true", help="Validate generated keys"
    )

    args = parser.parse_args()

    # Initialize generator
    generator = EnterpriseKeyGenerator()

    print("🔐 SDX Project Manager - Enterprise Security Key Generator")
    print("=" * 65)
    print(f"🎯 Target Environment: {args.environment.upper()}")
    print(f"🕐 Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Generate complete key set
    print("🔄 Generating cryptographically secure keys...")
    key_set = generator.generate_complete_key_set(args.environment)

    # Validation
    if args.validate:
        print("🧪 Validating key strength...")
        sample_keys = [
            key_set["application"]["secret_key"],
            key_set["jwt"]["access_secret"],
            key_set["encryption"]["data_encryption_key"],
        ]

        for i, key in enumerate(sample_keys, 1):
            validation = generator.validate_key_strength(key)
            print(f"   Key {i}: Security Score {validation['security_score']}/100")

    # Export to console
    if args.output in ["console", "both"]:
        print("\n📋 Generated Configuration:")
        print("-" * 40)
        toml_content = generator.export_secrets_toml(key_set)
        print(toml_content[:1000] + "..." if len(toml_content) > 1000 else toml_content)

    # Export to files
    if args.output in ["file", "both"]:
        print("💾 Saving to files...")

        # Save secrets.toml
        os.makedirs(".streamlit", exist_ok=True)
        with open(".streamlit/secrets.toml", "w", encoding="utf-8") as f:
            f.write(generator.export_secrets_toml(key_set))
        print("   ✅ .streamlit/secrets.toml")

        # Save .env
        with open(".env", "w", encoding="utf-8") as f:
            f.write(generator.export_env_file(key_set))
        print("   ✅ .env")

        # Save key backup (JSON)
        backup_filename = f"key_backup_{args.environment}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(backup_filename, "w", encoding="utf-8") as f:
            json.dump(key_set, f, indent=2, ensure_ascii=False)
        print(f"   ✅ {backup_filename}")

    print("\n🛡️ Security Reminders:")
    print("• Never commit secrets.toml to version control")
    print("• Store key backups in secure, encrypted location")
    print("• Rotate keys regularly (every 6-12 months)")
    print("• Use different keys for each environment")
    print("• Monitor key usage and access patterns")
    print()

    print("🚀 Next Steps:")
    print("1. Update .gitignore to exclude secrets.toml")
    print("2. Configure environment variables in production")
    print("3. Test application with new keys")
    print("4. Set up key rotation schedule")
    print("5. Document key management procedures")
    print()

    print("✅ Key generation completed successfully!")


if __name__ == "__main__":
    main()
