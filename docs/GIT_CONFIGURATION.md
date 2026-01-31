# Git Configuration Guide

## Windows-Specific Configuration

This project includes optimized Git configurations for Windows development to avoid common warnings and improve performance.

### Hardlink Warning Fix

**Issue**: `warning: Failed to hardlink files; falling back to full copy`

**Solution**: The repository is now configured to disable hardlinks, which prevents this warning on Windows systems.

```bash
git config core.hardlinks false
```

### Performance Optimizations

The following configurations are applied to improve Git performance on Windows:

#### File System Cache
Enables caching of file system operations:
```bash
git config core.fscache true
```

#### Index Preloading
Speeds up operations by preloading the index:
```bash
git config core.preloadindex true
```

#### Many Files Feature
Optimizes Git for repositories with many files:
```bash
git config feature.manyFiles true
```

## Configuration Status

Run this command to verify your current Git configuration:
```bash
git config --list --local
```

## Recommended Global Settings

For all your repositories, consider applying these settings globally:

```bash
# Disable hardlinks globally
git config --global core.hardlinks false

# Enable file system cache
git config --global core.fscache true

# Enable index preloading
git config --global core.preloadindex true

# Handle line endings
git config --global core.autocrlf true

# Disable symlinks on Windows
git config --global core.symlinks false
```

## Troubleshooting

### If warnings persist:
1. Check your file system permissions
2. Run Git as administrator (if necessary)
3. Ensure your Git version is up to date: `git --version`
4. Clear Git cache: `git rm -r --cached . && git add .`

### Performance issues:
1. Run garbage collection: `git gc --aggressive --prune=now`
2. Repack repository: `git repack -Ad`
3. Verify pack files: `git verify-pack -v .git/objects/pack/*.idx`

## References

- [Git Configuration Documentation](https://git-scm.com/docs/git-config)
- [Git on Windows Best Practices](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
- [Git Performance Tips](https://github.blog/2018-09-10-highlights-from-git-2-19/)

---

**Last Updated**: January 31, 2026  
**Applies To**: Windows development environments
