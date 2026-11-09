#!/bin/bash
# OregonInformation Deploy Script

SSH_HOST="173.249.54.18"
SSH_USER="root"
SSH_PASS=$(jq -r '."linux server ssh".secrets.password.value' < /home/ubuntu/.config/abacusai_auth_secrets.json)
REMOTE_REPO="/root/repos/oregon-information"
COMMIT_MSG="Auto-publish: christmas-in-oregon"

echo "Syncing VPS to origin/main..."
sshpass -p "$SSH_PASS" ssh -o StrictHostKeyChecking=no root@$SSH_HOST "cd $REMOTE_REPO && git rebase --abort; git fetch origin main && git reset --hard origin/main"

echo "Syncing local site to VPS..."
sshpass -p "$SSH_PASS" rsync -az --delete --exclude=".git" /home/ubuntu/oi/ root@$SSH_HOST:$REMOTE_REPO/

echo "Performing git operations on VPS..."
sshpass -p "$SSH_PASS" ssh -o StrictHostKeyChecking=no root@$SSH_HOST "cd $REMOTE_REPO && git add . && git commit -m '$COMMIT_MSG' && git push origin main"

echo "Deploy complete."
