# Men Mentor - Loyiha strukturasi yaratish

# Papkalar
$dirs = @(
    "app/api/v1",
    "app/core",
    "app/db",
    "app/models",
    "app/schemas",
    "app/services",
    "alembic/versions",
    "tests"
)

foreach ($dir in $dirs) {
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
}

# Fayllar
$files = @(
    "app/__init__.py",
    "app/main.py",
    "app/api/__init__.py",
    "app/api/deps.py",
    "app/api/v1/__init__.py",
    "app/api/v1/router.py",
    "app/api/v1/auth.py",
    "app/api/v1/users.py",
    "app/core/__init__.py",
    "app/core/config.py",
    "app/core/security.py",
    "app/core/exceptions.py",
    "app/db/__init__.py",
    "app/db/session.py",
    "app/db/base.py",
    "app/db/init_db.py",
    "app/models/__init__.py",
    "app/models/base_model.py",
    "app/models/user.py",
    "app/schemas/__init__.py",
    "app/schemas/base.py",
    "app/schemas/auth.py",
    "app/schemas/user.py",
    "app/services/__init__.py",
    "app/services/user_service.py",
    "app/services/auth_service.py",
    "alembic/env.py",
    "alembic/script.py.mako",
    "alembic/versions/.gitkeep",
    "tests/__init__.py",
    "tests/conftest.py",
    "tests/test_auth.py",
    "requirements.txt",
    "pyproject.toml",
    ".env.example",
    "alembic.ini",
    "Dockerfile",
    "docker-compose.yml",
    "README.md"
)

foreach ($file in $files) {
    New-Item -ItemType File -Force -Path $file | Out-Null
}

Write-Host "Struktura muvaffaqiyatli yaratildi!"
Get-ChildItem -Recurse | Where-Object { -not $_.PSIsContainer } | Select-Object -ExpandProperty FullName
