"""
Tests for aws_clients.py — Centralized AWS Client Factory.
"""

import pytest
from unittest.mock import patch, MagicMock


class TestGetDynamoDBResource:
    """Test DynamoDB resource singleton."""

    @patch("aws_clients.boto3")
    def test_returns_resource(self, mock_boto3):
        # Reset singleton
        import aws_clients
        aws_clients._dynamodb_resource = None

        mock_resource = MagicMock()
        mock_boto3.resource.return_value = mock_resource

        result = aws_clients.get_dynamodb_resource()
        assert result is mock_resource
        mock_boto3.resource.assert_called_once()

    @patch("aws_clients.boto3")
    def test_singleton_returns_same_instance(self, mock_boto3):
        import aws_clients
        aws_clients._dynamodb_resource = None

        mock_resource = MagicMock()
        mock_boto3.resource.return_value = mock_resource

        r1 = aws_clients.get_dynamodb_resource()
        r2 = aws_clients.get_dynamodb_resource()
        assert r1 is r2
        # Should only create once
        assert mock_boto3.resource.call_count == 1


class TestGetS3Client:
    """Test S3 client singleton."""

    @patch("aws_clients.boto3")
    def test_returns_client(self, mock_boto3):
        import aws_clients
        aws_clients._s3_client = None

        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client

        result = aws_clients.get_s3_client()
        assert result is mock_client
        mock_boto3.client.assert_called_once()

    @patch("aws_clients.boto3")
    def test_singleton_returns_same_instance(self, mock_boto3):
        import aws_clients
        aws_clients._s3_client = None

        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client

        c1 = aws_clients.get_s3_client()
        c2 = aws_clients.get_s3_client()
        assert c1 is c2
        assert mock_boto3.client.call_count == 1


class TestGetDynamoDBTable:
    """Test DynamoDB table helper."""

    @patch("aws_clients.boto3")
    def test_returns_table(self, mock_boto3):
        import aws_clients
        aws_clients._dynamodb_resource = None

        mock_resource = MagicMock()
        mock_table = MagicMock()
        mock_resource.Table.return_value = mock_table
        mock_boto3.resource.return_value = mock_resource

        result = aws_clients.get_dynamodb_table("test-table")
        assert result is mock_table
        mock_resource.Table.assert_called_once_with("test-table")


class TestConnectionPoolConfig:
    """Test that the config uses connection pooling settings."""

    def test_boto_config_has_keepalive(self):
        import aws_clients
        assert aws_clients._boto_config.tcp_keepalive is True

    def test_boto_config_has_pool_connections(self):
        import aws_clients
        assert aws_clients._boto_config.max_pool_connections == 25
