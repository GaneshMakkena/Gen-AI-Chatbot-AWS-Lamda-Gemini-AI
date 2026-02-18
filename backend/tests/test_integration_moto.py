"""
Moto-based integration tests for MediBot DynamoDB operations.
Uses moto to mock AWS DynamoDB locally, testing real data flows
without hitting production AWS services.
"""

import os
import pytest
import time
import boto3
from decimal import Decimal
from unittest.mock import patch

# Must be set before any imports that touch boto3
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
os.environ["AWS_ACCESS_KEY_ID"] = "testing"
os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
os.environ["AWS_SECURITY_TOKEN"] = "testing"
os.environ["AWS_SESSION_TOKEN"] = "testing"

try:
    from moto import mock_aws
    HAS_MOTO = True
except ImportError:
    HAS_MOTO = False
    mock_aws = None

pytestmark = pytest.mark.skipif(
    not HAS_MOTO,
    reason="moto is not installed. Install with: pip install moto[dynamodb]"
)

# ---- Table names used in tests ----
CHAT_TABLE = "medibot-chats-test"
HEALTH_TABLE = "medibot-health-profiles-test"
AUDIT_TABLE = "medibot-audit-test"
GUEST_TABLE = "medibot-guest-sessions-test"
RATE_TABLE = "medibot-rate-limits-test"


def create_chat_table(dynamodb):
    """Create the chat history DynamoDB table."""
    dynamodb.create_table(
        TableName=CHAT_TABLE,
        KeySchema=[
            {"AttributeName": "user_id", "KeyType": "HASH"},
            {"AttributeName": "chat_id", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "user_id", "AttributeType": "S"},
            {"AttributeName": "chat_id", "AttributeType": "S"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )


def create_health_table(dynamodb):
    """Create the health profile DynamoDB table."""
    dynamodb.create_table(
        TableName=HEALTH_TABLE,
        KeySchema=[
            {"AttributeName": "user_id", "KeyType": "HASH"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "user_id", "AttributeType": "S"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )


def create_audit_table(dynamodb):
    """Create the audit log DynamoDB table with GSI."""
    dynamodb.create_table(
        TableName=AUDIT_TABLE,
        KeySchema=[
            {"AttributeName": "event_id", "KeyType": "HASH"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "event_id", "AttributeType": "S"},
            {"AttributeName": "user_id", "AttributeType": "S"},
            {"AttributeName": "timestamp", "AttributeType": "N"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "user-id-index",
                "KeySchema": [
                    {"AttributeName": "user_id", "KeyType": "HASH"},
                    {"AttributeName": "timestamp", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            }
        ],
        BillingMode="PAY_PER_REQUEST",
    )


def create_guest_table(dynamodb):
    """Create the guest sessions DynamoDB table."""
    dynamodb.create_table(
        TableName=GUEST_TABLE,
        KeySchema=[
            {"AttributeName": "session_id", "KeyType": "HASH"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "session_id", "AttributeType": "S"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )


def create_rate_limit_table(dynamodb):
    """Create the rate limit DynamoDB table."""
    dynamodb.create_table(
        TableName=RATE_TABLE,
        KeySchema=[
            {"AttributeName": "user_id", "KeyType": "HASH"},
            {"AttributeName": "window", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "user_id", "AttributeType": "S"},
            {"AttributeName": "window", "AttributeType": "S"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )


# ---- Fixtures ----

@pytest.fixture
def dynamodb_resource():
    """Provide a moto-backed DynamoDB resource with all tables created."""
    if not HAS_MOTO:
        pytest.skip("moto not installed")

    with mock_aws():
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        create_chat_table(dynamodb)
        create_health_table(dynamodb)
        create_audit_table(dynamodb)
        create_guest_table(dynamodb)
        create_rate_limit_table(dynamodb)
        yield dynamodb


# ==========================
# Chat History Tests
# ==========================

class TestChatHistory:
    """Integration tests for chat history CRUD operations."""

    def test_save_and_retrieve_chat(self, dynamodb_resource):
        table = dynamodb_resource.Table(CHAT_TABLE)

        item = {
            "user_id": "user-001",
            "chat_id": "chat-abc",
            "query": "How to treat a headache?",
            "response": "Rest in a dark room and stay hydrated.",
            "topic": "Headache Treatment",
            "language": "English",
            "timestamp": Decimal(str(int(time.time()))),
            "images": [],
            "step_images": [],
        }
        table.put_item(Item=item)

        result = table.get_item(Key={"user_id": "user-001", "chat_id": "chat-abc"})
        assert "Item" in result
        assert result["Item"]["query"] == "How to treat a headache?"
        assert result["Item"]["topic"] == "Headache Treatment"

    def test_query_user_chats(self, dynamodb_resource):
        table = dynamodb_resource.Table(CHAT_TABLE)

        # Insert multiple chats for the same user
        for i in range(5):
            table.put_item(Item={
                "user_id": "user-002",
                "chat_id": f"chat-{i}",
                "query": f"Question {i}",
                "response": f"Answer {i}",
                "topic": f"Topic {i}",
                "language": "English",
                "timestamp": Decimal(str(int(time.time()) + i)),
            })

        response = table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key("user_id").eq("user-002")
        )
        assert response["Count"] == 5

    def test_delete_chat(self, dynamodb_resource):
        table = dynamodb_resource.Table(CHAT_TABLE)

        table.put_item(Item={
            "user_id": "user-003",
            "chat_id": "chat-del",
            "query": "Delete me",
            "response": "Deleted",
            "topic": "Test",
            "language": "English",
            "timestamp": Decimal(str(int(time.time()))),
        })

        table.delete_item(Key={"user_id": "user-003", "chat_id": "chat-del"})

        result = table.get_item(Key={"user_id": "user-003", "chat_id": "chat-del"})
        assert "Item" not in result


# ==========================
# Health Profile Tests
# ==========================

class TestHealthProfile:
    """Integration tests for health profile operations."""

    def test_create_and_read_profile(self, dynamodb_resource):
        table = dynamodb_resource.Table(HEALTH_TABLE)

        profile = {
            "user_id": "user-hp1",
            "conditions": [{"name": "Diabetes Type 2", "status": "active"}],
            "medications": [{"name": "Metformin", "dosage": "500mg"}],
            "allergies": [{"name": "Penicillin", "severity": "severe"}],
            "blood_type": "O+",
            "age": Decimal("45"),
            "gender": "Male",
            "key_facts": [],
            "report_summaries": [],
        }
        table.put_item(Item=profile)

        result = table.get_item(Key={"user_id": "user-hp1"})
        assert result["Item"]["blood_type"] == "O+"
        assert len(result["Item"]["conditions"]) == 1

    def test_update_profile_facts(self, dynamodb_resource):
        table = dynamodb_resource.Table(HEALTH_TABLE)

        table.put_item(Item={
            "user_id": "user-hp2",
            "key_facts": [],
        })

        table.update_item(
            Key={"user_id": "user-hp2"},
            UpdateExpression="SET key_facts = list_append(if_not_exists(key_facts, :empty), :facts)",
            ExpressionAttributeValues={
                ":facts": ["Patient has hypertension"],
                ":empty": [],
            },
        )

        result = table.get_item(Key={"user_id": "user-hp2"})
        assert "Patient has hypertension" in result["Item"]["key_facts"]


# ==========================
# Audit Log Tests (with GSI)
# ==========================

class TestAuditLog:
    """Integration tests for audit logging with GSI queries."""

    def test_log_event_and_query_by_user(self, dynamodb_resource):
        table = dynamodb_resource.Table(AUDIT_TABLE)

        now = Decimal(str(int(time.time())))
        events = [
            {"event_id": "evt-1", "user_id": "user-aud1", "event_type": "chat_query", "timestamp": now},
            {"event_id": "evt-2", "user_id": "user-aud1", "event_type": "profile_view", "timestamp": now + 1},
            {"event_id": "evt-3", "user_id": "user-aud2", "event_type": "chat_query", "timestamp": now},
        ]
        for event in events:
            table.put_item(Item=event)

        # Query using GSI — same pattern as our optimized get_user_audit_log
        response = table.query(
            IndexName="user-id-index",
            KeyConditionExpression=boto3.dynamodb.conditions.Key("user_id").eq("user-aud1"),
            ScanIndexForward=False,
        )
        assert response["Count"] == 2

    def test_audit_filter_by_event_type(self, dynamodb_resource):
        table = dynamodb_resource.Table(AUDIT_TABLE)

        now = Decimal(str(int(time.time())))
        for i in range(3):
            table.put_item(Item={
                "event_id": f"evt-filter-{i}",
                "user_id": "user-aud3",
                "event_type": "chat_query" if i < 2 else "profile_update",
                "timestamp": now + i,
            })

        response = table.query(
            IndexName="user-id-index",
            KeyConditionExpression=boto3.dynamodb.conditions.Key("user_id").eq("user-aud3"),
            FilterExpression=boto3.dynamodb.conditions.Attr("event_type").eq("chat_query"),
            ScanIndexForward=False,
        )
        assert response["Count"] == 2


# ==========================
# Guest Session Tests
# ==========================

class TestGuestSession:
    """Integration tests for guest session tracking."""

    def test_create_and_increment_guest_session(self, dynamodb_resource):
        table = dynamodb_resource.Table(GUEST_TABLE)

        table.put_item(Item={
            "session_id": "guest-abc",
            "query_count": Decimal("0"),
            "created_at": Decimal(str(int(time.time()))),
        })

        table.update_item(
            Key={"session_id": "guest-abc"},
            UpdateExpression="SET query_count = query_count + :inc",
            ExpressionAttributeValues={":inc": Decimal("1")},
        )

        result = table.get_item(Key={"session_id": "guest-abc"})
        assert result["Item"]["query_count"] == Decimal("1")


# ==========================
# Rate Limit Tests
# ==========================

class TestRateLimit:
    """Integration tests for rate limit tracking."""

    def test_record_and_check_rate_limit(self, dynamodb_resource):
        table = dynamodb_resource.Table(RATE_TABLE)

        window = "2024-01-01T00:00"  # Per-minute window
        table.put_item(Item={
            "user_id": "user-rl1",
            "window": window,
            "request_count": Decimal("1"),
            "ttl": Decimal(str(int(time.time()) + 120)),
        })

        # Increment
        table.update_item(
            Key={"user_id": "user-rl1", "window": window},
            UpdateExpression="SET request_count = request_count + :inc",
            ExpressionAttributeValues={":inc": Decimal("1")},
        )

        result = table.get_item(Key={"user_id": "user-rl1", "window": window})
        assert result["Item"]["request_count"] == Decimal("2")
