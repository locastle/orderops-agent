<#
.SYNOPSIS
    Pull the base images through a registry mirror and retag them locally.

.DESCRIPTION
    Docker Hub is not reachable from this network. Docker Desktop rewrites
    ~/.docker/daemon.json on every start, so "registry-mirrors" cannot be
    configured there and the setting is silently dropped.

    The reliable workaround is to pull through a mirror prefix and tag the
    result under the original name. Docker then resolves the local image and
    never contacts Docker Hub.

    Override the mirror with $env:DOCKER_MIRROR if needed.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts/pull-images.ps1
#>
$ErrorActionPreference = 'Stop'

$mirror = if ($env:DOCKER_MIRROR) { $env:DOCKER_MIRROR } else { 'docker.m.daocloud.io' }

$images = @(
    @{ src = "$mirror/library/python:3.12-slim"; dst = 'python:3.12-slim' }
    @{ src = "$mirror/pgvector/pgvector:pg16"; dst = 'pgvector/pgvector:pg16' }
)

foreach ($image in $images) {
    Write-Host "Pulling $($image.src)..."
    docker pull $image.src
    if ($LASTEXITCODE -ne 0) {
        Write-Error "pull failed: $($image.src)"
        exit 1
    }
    docker tag $image.src $image.dst
    Write-Host "  tagged as $($image.dst)"
}

Write-Host 'All base images are available locally.'
