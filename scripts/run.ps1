param(
    [string]$DagId = "retize_social_elt",
    [int]$TimeoutMinutes = 20,
    [int]$PollSeconds = 5,
    [switch]$SkipBuild
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host "`n=== $Message ===" -ForegroundColor Cyan
}

function Assert-LastExitCode {
    param([string]$Context)
    if ($LASTEXITCODE -ne 0) {
        throw "Falha em: $Context (exit code: $LASTEXITCODE)"
    }
}

function Wait-ForContainerReady {
    param(
        [string]$ContainerName,
        [int]$TimeoutSeconds = 180
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)

    while ((Get-Date) -lt $deadline) {
        $state = & docker inspect -f '{{.State.Status}}|{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' $ContainerName 2>$null

        if ($LASTEXITCODE -eq 0 -and $state) {
            $parts = $state -split "\|"
            $status = $parts[0]
            $health = $parts[1]

            if ($status -eq "running" -and ($health -eq "healthy" -or $health -eq "none")) {
                Write-Host "[ok] ${ContainerName}: $status/$health"
                return
            }
        }

        Start-Sleep -Seconds 2
    }

    throw "Timeout aguardando container pronto: $ContainerName"
}

function Get-LatestDagRunId {
    param([string]$CurrentDagId)

    $runs = & docker exec airflow_scheduler airflow dags list-runs -d $CurrentDagId 2>$null
    if ($LASTEXITCODE -ne 0 -or -not $runs) {
        return $null
    }

    $runLines = $runs | Where-Object { $_ -match "\|" } | Select-Object -Skip 1
    if (-not $runLines) {
        return $null
    }

    $firstRun = $runLines | Select-Object -First 1
    $columns = $firstRun -split "\|"
    if ($columns.Count -lt 2) {
        return $null
    }

    return $columns[1].Trim()
}

function Get-DagRunState {
    param(
        [string]$CurrentDagId,
        [string]$RunId
    )

    $runs = & docker exec airflow_scheduler airflow dags list-runs -d $CurrentDagId 2>$null
    if ($LASTEXITCODE -ne 0 -or -not $runs) {
        return $null
    }

    $runLine = $runs | Where-Object { $_ -match [regex]::Escape($RunId) } | Select-Object -First 1
    if (-not $runLine) {
        return $null
    }

    $columns = $runLine -split "\|"
    if ($columns.Count -lt 3) {
        return $null
    }

    return $columns[2].Trim()
}

function Wait-ForDagRun {
    param(
        [string]$CurrentDagId,
        [int]$TimeoutSeconds = 120
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)

    while ((Get-Date) -lt $deadline) {
        $runId = Get-LatestDagRunId -CurrentDagId $CurrentDagId
        if ($runId) {
            return $runId
        }
        Start-Sleep -Seconds 3
    }

    return $null
}

function Reset-AndTriggerDag {
    param([string]$CurrentDagId)

    $runId = Get-LatestDagRunId -CurrentDagId $CurrentDagId
    if (-not $runId) {
        return $null
    }

    $state = Get-DagRunState -CurrentDagId $CurrentDagId -RunId $runId
    if ($state -in @("success", "failed")) {
        Write-Host "DAG ja possui run finalizado ($state). Limpando e disparando novo run..."
        $clearOut = & docker exec airflow_scheduler airflow tasks clear $CurrentDagId --yes 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw "Falha ao limpar DAG: $clearOut"
        }

        $newRunId = "manual__script_{0}" -f ([DateTime]::UtcNow.ToString("yyyyMMddHHmmss"))
        $triggerOut = & docker exec airflow_scheduler airflow dags trigger $CurrentDagId --run-id $newRunId 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw "Falha ao disparar DAG: $triggerOut"
        }

        Start-Sleep -Seconds 3
        return $newRunId
    }

    return $null
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Resolve-Path (Join-Path $scriptDir "..")

Push-Location $repoRoot
try {
    Write-Step "Subindo stack Docker"
    if ($SkipBuild) {
        & docker compose up -d
    }
    else {
        & docker compose up -d --build
    }
    Assert-LastExitCode "subir docker compose"

    Write-Step "Aguardando containers"
    Wait-ForContainerReady -ContainerName "retize_postgres" -TimeoutSeconds 180
    Wait-ForContainerReady -ContainerName "airflow_postgres" -TimeoutSeconds 180
    Wait-ForContainerReady -ContainerName "airflow_scheduler" -TimeoutSeconds 180
    Wait-ForContainerReady -ContainerName "airflow_webserver" -TimeoutSeconds 180
    Wait-ForContainerReady -ContainerName "retize_dashboard" -TimeoutSeconds 180

    Start-Sleep -Seconds 10

    Write-Step "Validando DAG no scheduler"
    $dagList = & docker exec airflow_scheduler airflow dags list
    Assert-LastExitCode "listar DAGs"

    if (-not ($dagList -match "(?m)^\s*$([regex]::Escape($DagId))\s+\|")) {
        throw "DAG nao encontrada no scheduler: $DagId"
    }
    Write-Host "[ok] DAG encontrada: $DagId"

    Write-Step "Verificando runs existentes"
    $triggeredRunId = Reset-AndTriggerDag -CurrentDagId $DagId
    if ($triggeredRunId) {
        Write-Host "Novo run disparado: $triggeredRunId"
        $runId = $triggeredRunId
    }
    else {
        Write-Host "Nenhum run finalizado encontrado. Aguardando run automatico (@once)..."
        $runId = Wait-ForDagRun -CurrentDagId $DagId -TimeoutSeconds 120
        if (-not $runId) {
            throw "Nenhum DAG run apareceu apos espera. Verifique os logs do scheduler."
        }
    }
    Write-Host "Run ID: $runId"

    Write-Step "Acompanhando execucao"
    $deadline = (Get-Date).AddMinutes($TimeoutMinutes)
    $state = $null

    while ((Get-Date) -lt $deadline) {
        $state = Get-DagRunState -CurrentDagId $DagId -RunId $runId
        if ($state) {
            Write-Host "Estado atual: $state"
            if ($state -in @("success", "failed")) {
                break
            }
        }
        Start-Sleep -Seconds $PollSeconds
    }

    if (-not $state) {
        throw "Timeout aguardando DAG finalizar. Estado atual: $state"
    }

    if ($state -notin @("success", "failed")) {
        throw "Timeout aguardando DAG finalizar. Estado atual: $state"
    }

    Write-Step "Estados das tasks"
    & docker exec airflow_scheduler airflow tasks states-for-dag-run $DagId $runId
    Assert-LastExitCode "listar estados das tasks"

    Write-Step "Resultado"
    if ($state -eq "success") {
        Write-Host "Pipeline finalizado com sucesso." -ForegroundColor Green
        Write-Host "Airflow UI: http://localhost:8080"
        Write-Host "Login: airflow / airflow"
    }
    else {
        Write-Host "Pipeline finalizado com falha." -ForegroundColor Red
        Write-Host "Consulte os logs no Airflow UI: http://localhost:8080"
        exit 1
    }
}
finally {
    Pop-Location
}
