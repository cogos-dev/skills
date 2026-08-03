# macOS Storage Knowledge Base

## Sparse Files and Virtual Disks

macOS uses sparse files for several applications. `ls -l` reports logical size while `du -sh` or `stat -f %b` reports actual disk blocks used.

Common sparse files:
- **Docker.raw** (`~/Library/Containers/com.docker.docker/Data/vms/0/data/Docker.raw`) — Often shows 1TB+ logical but only 20-50GB actual. Use `du -sh` not `ls -lh`.
- **Parallels VM disks** (`~/Parallels/*.pvm/harddisk.hdd/*.hds`) — Sparse; actual usage is smaller than logical.
- **APFS sparse files** — macOS APFS natively supports sparse files.

To check actual vs logical: `ls -ls <file>` (first column = 512-byte blocks on disk).

## Google Drive / Cloud Storage Streaming

Google Drive for Desktop in streaming mode mounts at `~/Library/CloudStorage/GoogleDrive-*/`. Files appear with full `st_size` but `st_blocks = 0` (not actually on disk). The `du` command correctly reports near-zero usage. Tools using `st_size` (including many scanners) will overreport.

To check if a cloud file is actually downloaded: `ls -ls <file>` — if first column is 0, it's cloud-only.

iCloud Drive files work similarly — `brctl download` forces download, `brctl evict` removes local copy.

## macOS System Storage Locations

### Safe to clean (regenerable caches)
| Location | Description |
|----------|-------------|
| `~/Library/Caches/` | App caches (browser, Spotify, Discord, etc.) |
| `~/Library/Caches/Homebrew/downloads/` | Downloaded bottles |
| `~/.cache/` | XDG user cache |
| `~/Library/Logs/` | App logs |
| `/private/var/folders/` | System temp (needs sudo) |
| `~/Library/Developer/Xcode/DerivedData/` | Xcode build cache |
| `~/Library/Developer/CoreSimulator/` | iOS Simulator data |

### Caution — check before cleaning
| Location | Description |
|----------|-------------|
| `~/Library/Application Support/` | App data (some is config, some is cache) |
| `~/Library/Containers/` | Sandboxed app data |
| `~/Library/Group Containers/` | Shared app data |
| `~/Library/Developer/Xcode/Archives/` | Build archives (may want to keep recent) |

### Never auto-clean
| Location | Description |
|----------|-------------|
| `~/Library/Keychains/` | Login credentials |
| `~/Library/Preferences/` | App settings |
| `~/Library/CloudStorage/` | Cloud file placeholders |

## Developer Artifact Cleanup

### node_modules
- Fully regenerable from `package.json` + lockfile
- `rm -rf node_modules` then `npm install` / `yarn` / `bun install`
- Tool: `npx npkill` (interactive finder/killer)
- Tool: `kondo` (finds all project types)

### Rust target/
- Fully regenerable: `cargo clean` in project dir
- Or `rm -rf target/` directly
- `target/debug/` is usually 2-5x larger than `target/release/`
- Tool: `kondo` or `cargo-clean-all`

### Python virtualenvs (.venv, venv)
- Fully regenerable from requirements.txt / pyproject.toml
- `rm -rf .venv` then recreate

### Go module cache
- `go clean -modcache` clears `~/go/pkg/mod/`
- `go clean -cache` clears build cache

### Homebrew
- `brew cleanup` removes old versions and downloads
- `brew autoremove` removes unused dependencies

### Docker
- `docker system prune -a` removes unused images, containers, networks
- `docker builder prune` clears build cache
- To reclaim Docker.raw space after pruning: restart Docker Desktop

## Package Manager Caches

| Cache | Location | Clean command |
|-------|----------|---------------|
| npm | `~/.npm/_cacache/` | `npm cache clean --force` |
| yarn | `~/.yarn/berry/cache/` | `yarn cache clean` |
| pnpm | `~/.local/share/pnpm/store/` | `pnpm store prune` |
| bun | `~/.bun/install/cache/` | `rm -rf ~/.bun/install/cache` |
| pip | `~/Library/Caches/pip/` | `pip cache purge` |
| cargo | `~/.cargo/registry/` | `cargo cache --autoclean` |
| go | `~/go/pkg/mod/cache/` | `go clean -modcache` |
| Homebrew | `~/Library/Caches/Homebrew/` | `brew cleanup` |
| CocoaPods | `~/Library/Caches/CocoaPods/` | `pod cache clean --all` |

## ML/AI Model Caches

| Cache | Location | Notes |
|-------|----------|-------|
| HuggingFace | `~/.cache/huggingface/hub/` | Can be multi-GB per model |
| MLX | `~/.cache/mlx-models/` | Apple Silicon ML models |
| LM Studio | `~/.lmstudio/` | Models + multiple backend versions |
| Ollama | `~/.ollama/models/` | LLM models |

## Useful One-Liners

```bash
# Actual disk usage summary (handles sparse files)
du -sh ~/Library ~/Documents ~/Downloads ~/Workspaces ~/Parallels 2>/dev/null | sort -rh

# Find large files (excluding cloud storage)
find ~ -type f -not -path '*/Library/CloudStorage/*' -size +500M 2>/dev/null -exec du -sh {} \; | sort -rh | head -20

# Find all node_modules with sizes
find ~ -name node_modules -type d -maxdepth 5 -not -path '*/node_modules/*/node_modules' 2>/dev/null -exec du -sh {} \; | sort -rh

# Find Rust target directories
find ~ -name target -type d -maxdepth 6 2>/dev/null | while read d; do [ -f "$d/../Cargo.toml" ] && du -sh "$d"; done | sort -rh

# Check if Docker.raw is sparse
ls -ls ~/Library/Containers/com.docker.docker/Data/vms/0/data/Docker.raw 2>/dev/null

# macOS storage breakdown (system view)
diskutil apfs list 2>/dev/null | head -30

# Empty trash from CLI
rm -rf ~/.Trash/* 2>/dev/null
```
