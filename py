Essential Python Upgrade Steps (3.9.12 → 3.12)

  1. Pre-Upgrade Backup

  - Export current packages: pip3 freeze > packages_backup.txt
  - List virtual environments and their locations
  - Backup shell configs (.zshrc, .bashrc)

  2. Check Critical Breaking Changes

  - Python 3.10+: distutils removed (affects setup.py)
  - Python 3.11+: Major performance improvements but stricter typing
  - Python 3.12: No more deprecated unittest methods

  3. Install Python via pyenv (Recommended)

  brew install pyenv
  pyenv install 3.12.0
  pyenv global 3.12.0

  4. Recreate Virtual Environments

  - Never upgrade in-place - always recreate
  - Create new venv: python3.12 -m venv new_env
  - Install packages: pip install -r packages_backup.txt

  5. Update Critical Integrations

  - Update IDE Python interpreter paths
  - Fix any hardcoded Python paths in scripts
  - Update system services/cron jobs using Python

  6. Validate

  - Run test suites for all projects
  - Check compiled C extensions work
  - Verify system services are running

  7. Rollback Plan

  - Keep Python 3.9 available: pyenv install 3.9.12
  - Switch back if needed: pyenv global 3.9.12
  - Have environment backups ready
