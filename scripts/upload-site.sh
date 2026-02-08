#!/bin/bash
# Upload frontend to S3 and invalidate CloudFront cache.
# Usage: ./scripts/upload-site.sh

set -euo pipefail

STACK_NAME="dc-permit-navigator"

echo "Getting stack outputs..."
BUCKET=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" \
    --query "Stacks[0].Outputs[?OutputKey=='SiteBucketName'].OutputValue" \
    --output text)
DIST_ID=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" \
    --query "Stacks[0].Outputs[?OutputKey=='DistributionId'].OutputValue" \
    --output text)

if [ -z "$BUCKET" ] || [ "$BUCKET" = "None" ]; then
    echo "Error: Could not find S3 bucket. Is the stack deployed?"
    exit 1
fi

echo "Uploading site to s3://$BUCKET..."

# Generate latest permit data JS
echo "Generating permits-data.js..."
python3 scripts/generate_site_data.py

# Sync site files
aws s3 sync site/ "s3://$BUCKET/" \
    --delete \
    --cache-control "public, max-age=3600" \
    --exclude "*.map"

# Set longer cache for static assets
aws s3 sync site/css/ "s3://$BUCKET/css/" \
    --cache-control "public, max-age=86400"
aws s3 sync site/js/ "s3://$BUCKET/js/" \
    --cache-control "public, max-age=86400"

# Set short cache for HTML
aws s3 cp "s3://$BUCKET/index.html" "s3://$BUCKET/index.html" \
    --cache-control "public, max-age=300" \
    --content-type "text/html" \
    --metadata-directive REPLACE

echo "Site uploaded."

# Invalidate CloudFront cache
if [ -n "$DIST_ID" ] && [ "$DIST_ID" != "None" ]; then
    echo "Invalidating CloudFront cache (distribution: $DIST_ID)..."
    aws cloudfront create-invalidation \
        --distribution-id "$DIST_ID" \
        --paths "/*" \
        --output text > /dev/null
    echo "Cache invalidation started."
fi

CF_URL=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" \
    --query "Stacks[0].Outputs[?OutputKey=='CloudFrontUrl'].OutputValue" \
    --output text)
echo ""
echo "Done! Site is live at: $CF_URL"
