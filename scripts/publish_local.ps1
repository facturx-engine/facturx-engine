# publish_local.ps1
$VERSION = "1.0.0"
$IMAGE_NAME = "facturx-engine"

Write-Host "[INFO] Building ${IMAGE_NAME}:${VERSION}..." -ForegroundColor Cyan

# Build Pro Version
docker build --target pro -t "${IMAGE_NAME}:latest" -t "${IMAGE_NAME}:${VERSION}" .

if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] Build Success!" -ForegroundColor Green
    
    $ARCHIVE_NAME = "${IMAGE_NAME}-pro-v${VERSION}.tar"
    Write-Host "[INFO] Exporting to $ARCHIVE_NAME..." -ForegroundColor Cyan
    docker save -o $ARCHIVE_NAME "${IMAGE_NAME}:${VERSION}"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Archive Created: $ARCHIVE_NAME" -ForegroundColor Green
        Write-Host "Ready for distribution!"
    }
    else {
        Write-Host "[ERROR] Export Failed" -ForegroundColor Red
        exit 1
    }
}
else {
    Write-Host "[ERROR] Build Failed" -ForegroundColor Red
    exit 1
}
