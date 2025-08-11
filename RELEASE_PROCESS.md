# ReAgent Release Process

## Overview

This document describes the release process for ReAgent Sydney V03, including the Git-based workflow that bypasses npm CLI issues and ensures safe, validated deployments.

## Release Pipeline Architecture

```
Developer → Git Tag → GitHub Actions → Validation → Vercel Deployment → Post-Deploy Validation
     ↓                                                                              ↓
 Local Script                                                               Rollback if needed
```

## Prerequisites

### Required Secrets (GitHub)
- `VERCEL_TOKEN`: Vercel authentication token
- `VERCEL_ORG_ID`: Vercel organization ID
- `VERCEL_PROJECT_ID`: Vercel project ID
- `OPENAI_API_KEY`: OpenAI API key for tests
- `BACKEND_URL`: Backend deployment URL
- `DEPLOYMENT_URL`: Frontend deployment URL

### Local Requirements
- Git configured with push access
- Clean working directory
- On main/master branch
- PowerShell (Windows) or Bash (Unix/Linux/macOS)

## Release Types

### Production Release
Full production deployment with all validations:
```bash
# Windows
./scripts/release.ps1 -Version 1.0.0

# Unix/Linux/macOS
./scripts/release.sh --version 1.0.0
```

### Staging Release
Deploy to staging environment for testing:
```bash
# Trigger via GitHub Actions UI with release_type: staging
```

### Canary Release
Limited rollout for testing:
```bash
# Windows
./scripts/release.ps1 -Version 1.0.0-canary.1

# Unix/Linux/macOS
./scripts/release.sh --version 1.0.0-canary.1
```

## Step-by-Step Release Process

### 1. Pre-Release Checklist

- [ ] All tests passing locally
- [ ] No uncommitted changes
- [ ] On main/master branch
- [ ] Feature flags configured for rollback
- [ ] Migration dashboards showing stable metrics

### 2. Determine Version

Use semantic versioning (MAJOR.MINOR.PATCH):
- **PATCH**: Bug fixes, minor updates (1.0.0 → 1.0.1)
- **MINOR**: New features, backward compatible (1.0.0 → 1.1.0)
- **MAJOR**: Breaking changes (1.0.0 → 2.0.0)

### 3. Run Release Script

#### Windows (PowerShell)
```powershell
# Dry run first
./scripts/release.ps1 -Version 1.0.0 -DryRun

# If everything looks good, run actual release
./scripts/release.ps1 -Version 1.0.0
```

#### Unix/Linux/macOS (Bash)
```bash
# Dry run first
./scripts/release.sh --version 1.0.0 --dry-run

# If everything looks good, run actual release
./scripts/release.sh --version 1.0.0
```

### 4. Monitor GitHub Actions

After pushing the tag, GitHub Actions will:
1. **Validation Phase**
   - Validate version format
   - Run backend tests
   - Run frontend tests
   - Check migration compatibility
   - Perform security scans

2. **Release Phase**
   - Create GitHub Release
   - Generate changelog
   - Tag Docker images (if applicable)

3. **Deployment Phase**
   - Deploy to Vercel
   - Run post-deployment validation
   - Check health endpoints
   - Verify streaming protocols

4. **Notification Phase**
   - Send success/failure notifications
   - Update monitoring dashboards

### 5. Post-Deployment Validation

Run manual validation:
```bash
# Run deployment validation script
node scripts/validate-deployment.js

# Check specific environments
DEPLOYMENT_URL=https://reagent-sydney.vercel.app \
BACKEND_URL=https://reagent-backend.herokuapp.com \
node scripts/validate-deployment.js
```

## Validation Criteria

### Critical Checks (Must Pass)
- Health endpoints returning 200
- SSE streaming functional
- Frontend accessible
- Error rate < 1%

### Performance Checks (Warnings)
- TTFB < 500ms
- TTFM < 1000ms
- P95 latency < 300ms

### Compatibility Checks
- v3 protocol support
- v5 protocol support
- Feature flags working
- Rollback capability verified

## Rollback Procedures

### Immediate Rollback (< 5 minutes)

1. **Via Feature Flags**:
```bash
# Disable v5 SDK
NEXT_PUBLIC_AI_SDK_V5_ENABLED=false

# Disable AI Elements
NEXT_PUBLIC_AI_ELEMENTS_ENABLED=false
```

2. **Via Vercel Dashboard**:
- Go to Vercel Dashboard
- Select previous deployment
- Click "Promote to Production"

### Git-Based Rollback

```bash
# Delete remote tag
git push --delete origin v1.0.0

# Delete local tag
git tag -d v1.0.0

# Revert commits if needed
git revert HEAD
git push origin main
```

### Emergency Rollback

For critical issues:
1. Set `EMERGENCY_ROLLBACK=true` in Vercel environment
2. This disables all new features immediately
3. Investigate and fix issues
4. Re-release when stable

## Migration-Specific Considerations

### AI SDK v5 Migration
Monitor during release:
- A/B test allocation percentages
- Performance metrics (v3 vs v5)
- Error rates by SDK version
- TTFB/TTFM comparisons

Rollback triggers:
- Error rate > 5% for v5
- TTFM degradation > 50%
- User complaints about streaming

### AI Elements Migration
Monitor during release:
- Component render times
- Style consistency
- Interaction success rates
- Console errors

Rollback triggers:
- Visual regression detected
- Component errors > 1%
- Performance degradation > 20%

## Troubleshooting

### npm Corruption Issues
If npm commands fail with `ERR_INVALID_ARG_TYPE`:
- Use the Git-based release scripts
- Avoid `npm version` commands
- Update package.json manually or via scripts

### GitHub Actions Failures

1. **Validation Failed**:
   - Check test logs
   - Fix issues locally
   - Re-run workflow

2. **Deployment Failed**:
   - Check Vercel logs
   - Verify environment variables
   - Check API keys and secrets

3. **Post-Deployment Validation Failed**:
   - Review validation report
   - Check endpoint health
   - Consider rollback if critical

### Vercel Deployment Issues

1. **Build Failures**:
   - Check build logs
   - Verify dependencies
   - Check environment variables

2. **Runtime Errors**:
   - Check function logs
   - Review error tracking
   - Monitor performance metrics

## Release Schedule

### Regular Releases
- **Weekly**: Patch releases for bug fixes
- **Bi-weekly**: Minor releases for features
- **Monthly**: Major releases if needed

### Hotfix Releases
For critical issues:
1. Create hotfix branch from main
2. Fix issue with tests
3. Release as patch version
4. No waiting period required

## Monitoring Post-Release

### First Hour
- Monitor error rates closely
- Check performance dashboards
- Review user feedback channels
- Be ready for immediate rollback

### First 24 Hours
- Track migration metrics
- Monitor A/B test results
- Review performance trends
- Collect user feedback

### First Week
- Analyze complete metrics
- Plan next improvements
- Document lessons learned
- Update this guide if needed

## Best Practices

1. **Always Dry Run First**: Use `--dry-run` flag to preview changes
2. **Release Early in Week**: Avoid Friday deployments
3. **Communicate Releases**: Notify team before and after
4. **Document Changes**: Update CHANGELOG.md
5. **Monitor Actively**: Watch dashboards during rollout
6. **Have Rollback Plan**: Know how to revert quickly

## Contact & Support

### Release Issues
- Check GitHub Actions logs
- Review this documentation
- Contact DevOps team

### Emergency Contacts
- On-call engineer: [Contact info]
- Platform team: [Slack channel]
- Incident response: [PagerDuty]

## Appendix

### Environment Variables

#### Required for Release
```bash
VERCEL_TOKEN=xxx
VERCEL_ORG_ID=xxx
VERCEL_PROJECT_ID=xxx
GITHUB_TOKEN=xxx (auto-provided in Actions)
```

#### Feature Flags
```bash
# AI SDK v5
NEXT_PUBLIC_AI_SDK_V5_ENABLED=true|false
NEXT_PUBLIC_V5_TRAFFIC_PERCENTAGE=1-100

# AI Elements
NEXT_PUBLIC_AI_ELEMENTS_ENABLED=true|false
NEXT_PUBLIC_AI_ELEMENTS_[COMPONENT]=true|false

# Emergency
EMERGENCY_ROLLBACK=true|false
```

### Release Script Options

#### PowerShell (Windows)
```powershell
-Version        # Release version (required)
-ReleaseType    # patch|minor|major|custom
-DryRun         # Perform dry run
```

#### Bash (Unix/Linux/macOS)
```bash
--version, -v   # Release version (required)
--type, -t      # patch|minor|major|custom
--dry-run, -d   # Perform dry run
--help, -h      # Show help
```

### Validation Script

```javascript
// Environment variables
DEPLOYMENT_URL    // Frontend URL to test
BACKEND_URL       // Backend URL to test

// Exit codes
0 - All tests passed
1 - Some warnings, review needed
2 - Critical failures, rollback recommended
3 - Script error
```