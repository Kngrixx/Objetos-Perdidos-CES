# create_structure.ps1
# Misma estructura base de clase. En este proyecto ya está creada; se deja como referencia.

$folders = @(
    "app",
    "app\common",
    "app\controllers",
    "app\models",
    "app\routes",
    "app\services",
    "tests"
)

$files = @(
    "app\__init__.py",
    "app\extensions.py",
    "app\common\__init__.py",
    "app\controllers\__init__.py",
    "app\models\__init__.py",
    "app\routes\__init__.py",
    "app\services\__init__.py",
    "tests\__init__.py",
    ".env",
    ".env.example",
    ".gitignore",
    "config.py",
    "README.md",
    "run.py"
)

foreach ($folder in $folders) {
    New-Item -ItemType Directory -Force -Path $folder | Out-Null
}

foreach ($file in $files) {
    if (-not (Test-Path $file)) {
        New-Item -ItemType File -Path $file | Out-Null
    }
}

Write-Host "Estructura creada correctamente."
