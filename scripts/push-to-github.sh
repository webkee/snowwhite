#!/bin/bash
# GitHub에 푸시하는 헬퍼 스크립트
# 사용법: ./scripts/push-to-github.sh https://github.com/YOUR_USERNAME/snowwhite.git

set -e
REPO_URL="${1:?Usage: $0 <repository-url>}"
cd "$(dirname "$0")/.."

if git remote get-url origin 2>/dev/null; then
  echo "이미 origin이 설정되어 있습니다. 업데이트합니다."
  git remote set-url origin "$REPO_URL"
else
  git remote add origin "$REPO_URL"
fi

git push -u origin main
echo "푸시 완료. Vercel에서 이 저장소를 import 하세요."
