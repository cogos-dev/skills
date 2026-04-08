---
name: git-forensics
description: Deep knowledge of git internals - object model, content addressing, hash verification, and repository inspection. Use when debugging git issues or understanding repository state at the byte level.
---

# Git Forensics Skill

Deep inspection of git internals and content-addressable storage.

## Git Object Model

Git has exactly four object types:

### 1. Blob (File Content)

```
blob {size}\0{content}
hash = SHA-1(blob)
```

Blobs store file contents. No filename, no permissions--just bytes.

### 2. Tree (Directory)

```
tree {size}\0{entries}
entry = {mode} {name}\0{20-byte hash}
```

Trees map names to blobs (files) or other trees (subdirectories).

### 3. Commit

```
commit {size}\0{headers}\n\n{message}
headers: tree, parent(s), author, committer
```

Commits point to a tree (snapshot) and parent commit(s) (history).

### 4. Tag (Annotated)

```
tag {size}\0{headers}\n\n{message}
headers: object, type, tag, tagger
```

Tags name specific objects with optional metadata.

## Content Addressing

### The Core Principle

```
address = SHA-1(type + " " + size + "\0" + content)
```

Same content = same hash = stored once.

### Computing Hashes

```bash
# Hash a file as git would
git hash-object <file>

# Hash and store
git hash-object -w <file>

# See what type an object is
git cat-file -t <hash>

# See object content
git cat-file -p <hash>
```

### Manual Hash Computation

```python
import hashlib

def git_hash(obj_type: str, content: bytes) -> str:
    """Compute git-style SHA-1 hash."""
    header = f"{obj_type} {len(content)}\0".encode()
    return hashlib.sha1(header + content).hexdigest()
```

## Repository Inspection

### Object Database

```bash
# List all objects
find .git/objects -type f | head -20

# Objects are at .git/objects/XX/YYYYYY...
# XX = first two chars of hash
# YYY... = remaining chars

# Unpack an object
git cat-file -p <full-hash>
```

### Refs (Branches and Tags)

```bash
# Refs are just files containing hashes
cat .git/refs/heads/main  # -> commit hash

# Current HEAD
cat .git/HEAD  # -> ref: refs/heads/main (or detached hash)

# Symbolic refs
git symbolic-ref HEAD
```

### The Index (Staging Area)

```bash
# List staged files
git ls-files --stage

# Index is binary: .git/index
# Contains: mode, hash, stage, path for each entry
```

## Verification Commands

### Integrity Checks

```bash
# Verify all objects
git fsck --full

# Check connectivity
git fsck --connectivity-only

# Find dangling objects
git fsck --unreachable
```

### Hash Verification

```bash
# Verify a specific object
git cat-file -t <hash>  # Should return type
git cat-file -s <hash>  # Should return size

# Recompute and verify
git hash-object <file>  # Compare with stored hash
```

## Debugging Techniques

### Trace What Git Does

```bash
# See all git operations
GIT_TRACE=1 git <command>

# See pack operations
GIT_TRACE_PACK_ACCESS=1 git <command>

# See ref updates
GIT_TRACE_REFS=1 git <command>
```

### Object Archaeology

```bash
# When was this blob last modified?
git log --all --find-object=<hash>

# What commits contain this tree?
git log --all --find-object=<tree-hash>

# Who introduced this content?
git log -p -S "<search-string>" --all
```

### Recovery Operations

```bash
# Find lost commits
git reflog

# Recover deleted branch
git branch <name> <hash-from-reflog>

# Find dangling commits
git fsck --lost-found
# Creates .git/lost-found/commit/ and .git/lost-found/other/
```

## Merkle Tree Properties

```
        [Root = commit hash]
              |
          [tree hash]
         /    |     \
    [blob] [tree]  [blob]
              |
           [blob]
```

### Verification Principle

To verify any object:
1. Recompute its hash from content
2. Compare to claimed hash
3. Recursively verify children

```python
def verify_tree(repo, tree_hash):
    """Verify tree and all children."""
    tree = repo.get_object(tree_hash)
    computed = git_hash('tree', tree.raw)

    if computed != tree_hash:
        raise IntegrityError(f"Tree {tree_hash} corrupt")

    for entry in tree.entries:
        if entry.mode.is_tree():
            verify_tree(repo, entry.hash)
        else:
            verify_blob(repo, entry.hash)
```

## Pack Files

### When Objects Get Packed

```bash
# Manual pack
git gc

# Pack files live in .git/objects/pack/
ls .git/objects/pack/
# pack-<hash>.pack - compressed objects
# pack-<hash>.idx  - index for random access
```

### Inspecting Packs

```bash
# List pack contents
git verify-pack -v .git/objects/pack/pack-*.idx

# See object sizes and deltas
git verify-pack -v .git/objects/pack/*.idx | sort -k 3 -n | tail
```

## Common Issues

### Corrupt Objects

```bash
# Symptom: error: object file ... is empty
# Fix: fetch from remote or restore from backup
git fetch origin
git checkout origin/main -- <path>
```

### Detached HEAD

```bash
# Symptom: HEAD is not at a branch
cat .git/HEAD  # Shows hash, not ref

# Fix: create branch at current position
git checkout -b <branch-name>
```

### Large Repository

```bash
# Find large objects
git rev-list --objects --all | \
  git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' | \
  sort -k3 -n | tail -20

# Remove large file from history (destructive!)
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch <path>' HEAD
```

## Quick Reference

| Command | Purpose |
|---------|---------|
| `git cat-file -t <hash>` | Object type |
| `git cat-file -p <hash>` | Object content |
| `git cat-file -s <hash>` | Object size |
| `git hash-object <file>` | Compute hash |
| `git ls-files --stage` | Index contents |
| `git fsck` | Repository integrity |
| `git reflog` | Reference history |
| `git rev-parse HEAD` | Resolve ref to hash |
