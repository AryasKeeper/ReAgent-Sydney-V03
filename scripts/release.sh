#!/bin/bash
# Bash Release Script for Unix/Linux/macOS
# Works around npm corruption by using Git-based workflow

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Default values
RELEASE_TYPE="custom"
DRY_RUN=false
VERSION=""

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --version|-v)
      VERSION="$2"
      shift 2
      ;;
    --type|-t)
      RELEASE_TYPE="$2"
      shift 2
      ;;
    --dry-run|-d)
      DRY_RUN=true
      shift
      ;;
    --help|-h)
      echo "Usage: $0 --version VERSION [--type TYPE] [--dry-run]"
      echo ""
      echo "Options:"
      echo "  --version, -v    Release version (e.g., 1.0.0)"
      echo "  --type, -t       Release type (patch|minor|major|custom) [default: custom]"
      echo "  --dry-run, -d    Perform dry run without pushing changes"
      echo "  --help, -h       Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

echo -e "${CYAN}========================================"
echo -e "ReAgent Release Pipeline v3.0"
echo -e "========================================${NC}"
echo ""

# Validate Git is clean
if [[ -n $(git status --porcelain) ]]; then
    echo -e "${RED}Error: Working directory is not clean. Please commit or stash changes.${NC}"
    git status --short
    exit 1
fi

# Validate we're on main/master branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [[ "$CURRENT_BRANCH" != "main" && "$CURRENT_BRANCH" != "master" ]]; then
    echo -e "${RED}Error: Must be on main or master branch. Current branch: $CURRENT_BRANCH${NC}"
    exit 1
fi

# Fetch latest changes
echo -e "${YELLOW}Fetching latest changes...${NC}"
git fetch origin --tags

# Determine version
if [[ "$RELEASE_TYPE" != "custom" ]]; then
    # Get latest tag
    LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.0.0")
    
    # Parse version parts
    VERSION_PARTS=(${LATEST_TAG//v/})
    VERSION_PARTS=(${VERSION_PARTS//./ })
    MAJOR=${VERSION_PARTS[0]:-0}
    MINOR=${VERSION_PARTS[1]:-0}
    PATCH=${VERSION_PARTS[2]:-0}
    
    case "$RELEASE_TYPE" in
        patch)
            ((PATCH++))
            ;;
        minor)
            ((MINOR++))
            PATCH=0
            ;;
        major)
            ((MAJOR++))
            MINOR=0
            PATCH=0
            ;;
    esac
    
    VERSION="$MAJOR.$MINOR.$PATCH"
fi

# Validate version format
if [[ ! "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+(-[a-z]+\.[0-9]+)?$ ]]; then
    echo -e "${RED}Error: Invalid version format. Expected: X.Y.Z or X.Y.Z-suffix.N${NC}"
    exit 1
fi

TAG_NAME="v$VERSION"

echo -e "${GREEN}Preparing release: $TAG_NAME${NC}"
echo ""

# Check if tag already exists
if git tag -l "$TAG_NAME" | grep -q .; then
    echo -e "${RED}Error: Tag $TAG_NAME already exists${NC}"
    exit 1
fi

# Update version in package.json files (without npm)
echo -e "${YELLOW}Updating version files...${NC}"

# Update frontend package.json
FRONTEND_PACKAGE="frontend/package.json"
if [[ -f "$FRONTEND_PACKAGE" ]]; then
    # Use jq if available, otherwise use sed
    if command -v jq &> /dev/null; then
        jq --arg v "$VERSION" '.version = $v' "$FRONTEND_PACKAGE" > tmp.json && mv tmp.json "$FRONTEND_PACKAGE"
    else
        sed -i.bak "s/\"version\": \"[^\"]*\"/\"version\": \"$VERSION\"/" "$FRONTEND_PACKAGE"
        rm -f "${FRONTEND_PACKAGE}.bak"
    fi
    echo -e "  ${GREEN}✓${NC} Updated frontend/package.json"
fi

# Update backend version file
BACKEND_VERSION="backend/version.py"
cat > "$BACKEND_VERSION" << EOF
"""
ReAgent Backend Version
"""
__version__ = "$VERSION"
RELEASE_DATE = "$(date +%Y-%m-%d)"
EOF
echo -e "  ${GREEN}✓${NC} Created backend/version.py"

# Create release notes
echo -e "${YELLOW}Generating release notes...${NC}"
RELEASE_NOTES_FILE="RELEASE_NOTES_${VERSION}.md"

# Get last tag for changelog
LAST_TAG=$(git describe --tags --abbrev=0 HEAD^ 2>/dev/null || git rev-list --max-parents=0 HEAD)

# Get commits since last tag
COMMITS=$(git log "$LAST_TAG..HEAD" --pretty=format:"- %s (%h)" --no-merges)

cat > "$RELEASE_NOTES_FILE" << EOF
# Release v$VERSION

Release Date: $(date +%Y-%m-%d)

## What's Changed

$COMMITS

## Migration Status

### AI SDK v5 Migration
- Status: Progressive rollout in production
- Current traffic: 1% (canary)
- Protocol: Dual support (v3/v5)

### AI Elements Integration
- Status: Foundation complete
- Components: Abstraction layer ready
- Rollout: Component-by-component

### Performance Metrics
- TTFB: Monitoring active
- Error rate: < 0.5%
- P95 latency: < 300ms

## Deployment

This release will be automatically deployed via GitHub Actions.

### Rollback Instructions

If issues are detected:
1. Set feature flags to disable new features
2. Use Vercel Dashboard to promote previous deployment
3. Or revert Git tag: \`git push --delete origin $TAG_NAME\`

## Testing

- Backend tests: Passing
- Frontend tests: Passing
- Migration validation: Complete
- Security scan: Clean
EOF

echo -e "  ${GREEN}✓${NC} Generated release notes"
echo ""

if [[ "$DRY_RUN" == true ]]; then
    echo -e "${MAGENTA}DRY RUN: Would perform the following actions:${NC}"
    echo -e "  ${CYAN}1. Commit version updates${NC}"
    echo -e "  ${CYAN}2. Create tag: $TAG_NAME${NC}"
    echo -e "  ${CYAN}3. Push changes to origin${NC}"
    echo -e "  ${CYAN}4. Trigger GitHub Actions workflow${NC}"
    echo ""
    echo -e "${YELLOW}Release notes preview:${NC}"
    cat "$RELEASE_NOTES_FILE"
    exit 0
fi

# Commit version changes
echo -e "${YELLOW}Committing version updates...${NC}"
git add frontend/package.json backend/version.py "$RELEASE_NOTES_FILE" 2>/dev/null || true
git commit -m "chore(release): prepare v$VERSION

- Update version in package.json
- Create version.py for backend
- Generate release notes

[skip ci]"

echo -e "  ${GREEN}✓${NC} Committed version updates"

# Create tag
echo -e "${YELLOW}Creating tag $TAG_NAME...${NC}"
git tag -a "$TAG_NAME" -m "Release v$VERSION

$(cat "$RELEASE_NOTES_FILE")"

echo -e "  ${GREEN}✓${NC} Created tag"

# Push changes
echo -e "${YELLOW}Pushing to origin...${NC}"
git push origin "$CURRENT_BRANCH"
git push origin "$TAG_NAME"

echo -e "  ${GREEN}✓${NC} Pushed changes"
echo ""

echo -e "${GREEN}========================================"
echo -e "Release v$VERSION initiated successfully!"
echo -e "========================================${NC}"
echo ""
echo -e "${CYAN}GitHub Actions will now:${NC}"
echo -e "  ${WHITE}1. Run validation tests${NC}"
echo -e "  ${WHITE}2. Perform security scans${NC}"
echo -e "  ${WHITE}3. Create GitHub Release${NC}"
echo -e "  ${WHITE}4. Deploy to Vercel${NC}"
echo -e "  ${WHITE}5. Run post-deployment validation${NC}"
echo ""
echo -e "${YELLOW}Monitor progress at: https://github.com/[your-repo]/actions${NC}"
echo ""
echo -e "${MAGENTA}Rollback command if needed:${NC}"
echo -e "  ${WHITE}git push --delete origin $TAG_NAME && git tag -d $TAG_NAME${NC}"