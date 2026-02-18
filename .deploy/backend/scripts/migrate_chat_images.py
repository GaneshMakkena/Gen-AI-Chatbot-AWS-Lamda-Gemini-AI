#!/usr/bin/env python3
"""
Migration Script: Fix old chat images by extracting S3 keys from URLs.

This script scans the chat history DynamoDB table and:
1. Finds chats with step_images that have image_url but no s3_key
2. Extracts the S3 key from the presigned URL
3. Updates the record with the s3_key for future URL regeneration

Usage:
    python migrate_chat_images.py [--dry-run] [--limit N]

Options:
    --dry-run   Show what would be updated without making changes
    --limit N   Process only N chats (default: all)
"""

import os

import boto3
import argparse
from urllib.parse import urlparse, unquote
from typing import Optional, Dict, Any, List

# Configuration from environment
CHAT_TABLE = os.getenv("CHAT_TABLE", "medibot-chats-production")
IMAGES_BUCKET = os.getenv("IMAGES_BUCKET", "")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

# Initialize clients
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
table = dynamodb.Table(CHAT_TABLE)


def extract_s3_key_from_url(url: str) -> Optional[str]:
    """
    Extract S3 key from a presigned URL.

    Presigned URLs look like:
    https://bucket.s3.region.amazonaws.com/steps/hash/image.png?X-Amz-...
    or
    https://s3.region.amazonaws.com/bucket/steps/hash/image.png?X-Amz-...
    """
    if not url or not url.startswith('http'):
        return None

    try:
        parsed = urlparse(url)
        path = unquote(parsed.path)

        # Remove leading slash
        if path.startswith('/'):
            path = path[1:]

        # Handle virtual-hosted style: bucket.s3.region.amazonaws.com/key
        if '.s3.' in parsed.netloc and 'amazonaws.com' in parsed.netloc:
            return path

        # Handle path style: s3.region.amazonaws.com/bucket/key
        if parsed.netloc.startswith('s3.') and 'amazonaws.com' in parsed.netloc:
            # First part of path is bucket name
            parts = path.split('/', 1)
            if len(parts) > 1:
                return parts[1]

        # Check if it looks like a valid S3 key pattern
        if path.startswith('steps/'):
            return path

        return None

    except Exception as e:
        print(f"  Error parsing URL: {e}")
        return None


def process_step_images(step_images: List[Dict[str, Any]]) -> tuple[List[Dict[str, Any]], int]:
    """
    Process step_images and add s3_key where missing.
    Returns (updated_images, count_of_fixes)
    """
    updated = []
    fixes = 0

    for img in step_images:
        img_copy = dict(img)

        # Skip if already has s3_key
        if img_copy.get('s3_key'):
            updated.append(img_copy)
            continue

        # Try to extract key from image_url
        image_url = img_copy.get('image_url')
        if image_url:
            s3_key = extract_s3_key_from_url(image_url)
            if s3_key:
                img_copy['s3_key'] = s3_key
                fixes += 1
                print(f"    Extracted key: {s3_key[:50]}...")

        updated.append(img_copy)

    return updated, fixes


def scan_and_fix_chats(dry_run: bool = True, limit: Optional[int] = None):
    """
    Scan all chats and fix missing s3_keys.
    """
    print(f"\n{'='*60}")
    print("Chat Image Migration Script")
    print(f"{'='*60}")
    print(f"Table: {CHAT_TABLE}")
    print(f"Region: {AWS_REGION}")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE UPDATE'}")
    if limit:
        print(f"Limit: {limit} chats")
    print(f"{'='*60}\n")

    total_scanned = 0
    total_fixed = 0
    total_images_fixed = 0

    # Scan parameters
    scan_kwargs = {
        'FilterExpression': 'attribute_exists(step_images)'
    }

    if limit:
        scan_kwargs['Limit'] = limit

    try:
        # Paginated scan
        last_key = None

        while True:
            if last_key:
                scan_kwargs['ExclusiveStartKey'] = last_key

            response = table.scan(**scan_kwargs)
            items = response.get('Items', [])

            for chat in items:
                total_scanned += 1

                step_images = chat.get('step_images', [])
                if not step_images:
                    continue

                # Check if any images need fixing
                needs_fix = any(
                    img.get('image_url') and not img.get('s3_key')
                    for img in step_images
                )

                if not needs_fix:
                    continue

                chat_id = chat.get('chat_id', 'unknown')
                user_id = chat.get('user_id', 'unknown')[:8]
                print(f"\nChat: {chat_id} (user: {user_id}...)")
                print(f"  Images: {len(step_images)}")

                # Process and fix images
                updated_images, image_fixes = process_step_images(step_images)

                if image_fixes > 0:
                    total_fixed += 1
                    total_images_fixed += image_fixes

                    if not dry_run:
                        # Update DynamoDB
                        table.update_item(
                            Key={
                                'user_id': chat['user_id'],
                                'chat_id': chat['chat_id']
                            },
                            UpdateExpression='SET step_images = :imgs',
                            ExpressionAttributeValues={
                                ':imgs': updated_images
                            }
                        )
                        print(f"  ✅ Updated {image_fixes} images")
                    else:
                        print(f"  📝 Would update {image_fixes} images")

                if limit and total_scanned >= limit:
                    break

            # Check for more pages
            last_key = response.get('LastEvaluatedKey')
            if not last_key or (limit and total_scanned >= limit):
                break

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Chats scanned: {total_scanned}")
    print(f"Chats needing fix: {total_fixed}")
    print(f"Images fixed: {total_images_fixed}")

    if dry_run and total_fixed > 0:
        print("\n⚠️  Run without --dry-run to apply changes")
    elif not dry_run and total_fixed > 0:
        print("\n✅ All changes applied!")
    else:
        print("\n✨ No changes needed")


def main():
    parser = argparse.ArgumentParser(description='Migrate chat images to include S3 keys')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be updated without making changes')
    parser.add_argument('--limit', type=int, default=None,
                        help='Process only N chats')

    args = parser.parse_args()

    # Safety: default to dry run
    if not args.dry_run:
        confirm = input("\n⚠️  This will modify your DynamoDB table. Continue? [y/N]: ")
        if confirm.lower() != 'y':
            print("Aborted.")
            return

    scan_and_fix_chats(dry_run=args.dry_run, limit=args.limit)


if __name__ == '__main__':
    main()
