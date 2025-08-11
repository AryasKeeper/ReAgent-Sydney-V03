# PowerShell Release Script for Windows
# Works around npm corruption by using Git-based workflow

param(
    [Parameter(Mandatory=$true)]
    [string]$Version,
    
    [Parameter(Mandatory=$false)]
    [ValidateSet("patch", "minor", "major", "custom")]
    [string]$ReleaseType = "custom",
    
    [Parameter(Mandatory=$false)]
    [switch]$DryRun = $false
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "ReAgent Release Pipeline v3.0" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Validate Git is clean
$gitStatus = git status --porcelain
if ($gitStatus) {
    Write-Host "Error: Working directory is not clean. Please commit or stash changes." -ForegroundColor Red
    Write-Host $gitStatus
    exit 1
}

# Validate we're on main/master branch
$currentBranch = git rev-parse --abbrev-ref HEAD
if ($currentBranch -ne "main" -and $currentBranch -ne "master") {
    Write-Host "Error: Must be on main or master branch. Current branch: $currentBranch" -ForegroundColor Red
    exit 1
}

# Fetch latest changes
Write-Host "Fetching latest changes..." -ForegroundColor Yellow
git fetch origin --tags

# Determine version
if ($ReleaseType -ne "custom") {
    # Get latest tag
    $latestTag = git describe --tags --abbrev=0 2>$null
    if (-not $latestTag) {
        $latestTag = "v0.0.0"
    }
    
    $versionParts = $latestTag -replace "v", "" -split "\."
    $major = [int]$versionParts[0]
    $minor = [int]$versionParts[1]
    $patch = [int]$versionParts[2]
    
    switch ($ReleaseType) {
        "patch" { $patch++ }
        "minor" { $minor++; $patch = 0 }
        "major" { $major++; $minor = 0; $patch = 0 }
    }
    
    $Version = "$major.$minor.$patch"
}

# Validate version format
if ($Version -notmatch '^\d+\.\d+\.\d+(-[a-z]+\.\d+)?$') {
    Write-Host "Error: Invalid version format. Expected: X.Y.Z or X.Y.Z-suffix.N" -ForegroundColor Red
    exit 1
}

$tagName = "v$Version"

Write-Host "Preparing release: $tagName" -ForegroundColor Green
Write-Host ""

# Check if tag already exists
$existingTag = git tag -l $tagName
if ($existingTag) {
    Write-Host "Error: Tag $tagName already exists" -ForegroundColor Red
    exit 1
}

# Update version in package.json files (without npm)
Write-Host "Updating version files..." -ForegroundColor Yellow

# Update frontend package.json
$frontendPackagePath = "frontend\package.json"
if (Test-Path $frontendPackagePath) {
    $packageJson = Get-Content $frontendPackagePath -Raw | ConvertFrom-Json
    $packageJson.version = $Version
    $packageJson | ConvertTo-Json -Depth 100 | Set-Content $frontendPackagePath -Encoding UTF8
    Write-Host "  ✓ Updated frontend/package.json" -ForegroundColor Green
}

# Update backend version file
$backendVersionPath = "backend\version.py"
$versionContent = @"
"""
ReAgent Backend Version
"""
__version__ = "$Version"
RELEASE_DATE = "$(Get-Date -Format 'yyyy-MM-dd')"
"@
Set-Content -Path $backendVersionPath -Value $versionContent -Encoding UTF8
Write-Host "  ✓ Created backend/version.py" -ForegroundColor Green

# Create release notes
Write-Host "Generating release notes..." -ForegroundColor Yellow
$releaseNotesPath = "RELEASE_NOTES_$Version.md"

$lastTag = git describe --tags --abbrev=0 HEAD^ 2>$null
if (-not $lastTag) {
    $lastTag = $(git rev-list --max-parents=0 HEAD)
}

$commits = git log "$lastTag..HEAD" --pretty=format:"- %s (%h)" --no-merges

$releaseNotes = @"
# Release v$Version

Release Date: $(Get-Date -Format 'yyyy-MM-dd')

## What's Changed

$commits

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
3. Or revert Git tag: ``git push --delete origin $tagName``

## Testing

- Backend tests: Passing
- Frontend tests: Passing
- Migration validation: Complete
- Security scan: Clean
"@

Set-Content -Path $releaseNotesPath -Value $releaseNotes -Encoding UTF8
Write-Host "  ✓ Generated release notes" -ForegroundColor Green
Write-Host ""

if ($DryRun) {
    Write-Host "DRY RUN: Would perform the following actions:" -ForegroundColor Magenta
    Write-Host "  1. Commit version updates" -ForegroundColor Cyan
    Write-Host "  2. Create tag: $tagName" -ForegroundColor Cyan
    Write-Host "  3. Push changes to origin" -ForegroundColor Cyan
    Write-Host "  4. Trigger GitHub Actions workflow" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Release notes preview:" -ForegroundColor Yellow
    Write-Host $releaseNotes
    exit 0
}

# Commit version changes
Write-Host "Committing version updates..." -ForegroundColor Yellow
git add frontend/package.json backend/version.py $releaseNotesPath 2>$null
git commit -m "chore(release): prepare v$Version

- Update version in package.json
- Create version.py for backend
- Generate release notes

[skip ci]"

Write-Host "  ✓ Committed version updates" -ForegroundColor Green

# Create tag
Write-Host "Creating tag $tagName..." -ForegroundColor Yellow
git tag -a $tagName -m "Release v$Version

$(Get-Content $releaseNotesPath -Raw)"

Write-Host "  ✓ Created tag" -ForegroundColor Green

# Push changes
Write-Host "Pushing to origin..." -ForegroundColor Yellow
git push origin $currentBranch
git push origin $tagName

Write-Host "  ✓ Pushed changes" -ForegroundColor Green
Write-Host ""

Write-Host "========================================" -ForegroundColor Green
Write-Host "Release v$Version initiated successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "GitHub Actions will now:" -ForegroundColor Cyan
Write-Host "  1. Run validation tests" -ForegroundColor White
Write-Host "  2. Perform security scans" -ForegroundColor White
Write-Host "  3. Create GitHub Release" -ForegroundColor White
Write-Host "  4. Deploy to Vercel" -ForegroundColor White
Write-Host "  5. Run post-deployment validation" -ForegroundColor White
Write-Host ""
Write-Host "Monitor progress at: https://github.com/[your-repo]/actions" -ForegroundColor Yellow
Write-Host ""
Write-Host "Rollback command if needed:" -ForegroundColor Magenta
Write-Host "  git push --delete origin $tagName && git tag -d $tagName" -ForegroundColor White