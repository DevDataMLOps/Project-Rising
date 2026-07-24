param(
    [string]$BaseUrl = "https://project-rising-api.onrender.com"
)

$ErrorActionPreference = "Stop"
$base = $BaseUrl.TrimEnd("/")
$results = [System.Collections.Generic.List[object]]::new()

function Test-Endpoint {
    param(
        [string]$Path,
        [string]$ExpectedContentType
    )

    $response = Invoke-WebRequest `
        -Uri "$base$Path" `
        -Method Get `
        -UseBasicParsing `
        -TimeoutSec 90

    if ($response.StatusCode -ne 200) {
        throw "$Path returned HTTP $($response.StatusCode)"
    }
    if ($ExpectedContentType -and $response.Headers["Content-Type"] -notmatch $ExpectedContentType) {
        throw "$Path returned unexpected Content-Type: $($response.Headers['Content-Type'])"
    }

    $results.Add([pscustomobject]@{
        Endpoint = $Path
        Status = $response.StatusCode
        ContentType = $response.Headers["Content-Type"]
    })
    return $response
}

$healthResponse = Test-Endpoint -Path "/health" -ExpectedContentType "application/json"
$health = $healthResponse.Content | ConvertFrom-Json
if ($health.status -ne "healthy") {
    throw "/health did not report status=healthy"
}

$readyResponse = Test-Endpoint -Path "/ready" -ExpectedContentType "application/json"
$ready = $readyResponse.Content | ConvertFrom-Json
if ($ready.status -ne "ready") {
    throw "/ready did not report status=ready"
}

$docsResponse = Test-Endpoint -Path "/docs" -ExpectedContentType "text/html"
if ($docsResponse.Content -notmatch "Swagger UI") {
    throw "/docs loaded, but the Swagger UI marker was not found"
}

$openApiResponse = Test-Endpoint -Path "/openapi.json" -ExpectedContentType "application/json"
$openApi = $openApiResponse.Content | ConvertFrom-Json
if ($openApi.info.title -ne "Project RISING") {
    throw "/openapi.json returned an unexpected API title: $($openApi.info.title)"
}

$healthDataResponse = Test-Endpoint -Path "/api/v1/health-indicators?limit=1" -ExpectedContentType "application/json"
$healthData = $healthDataResponse.Content | ConvertFrom-Json
if ($healthData.count -lt 1) {
    throw "Health indicator smoke test returned no records"
}

$riskResponse = Test-Endpoint -Path "/api/v1/disease-risk/sample" -ExpectedContentType "application/json"
$null = $riskResponse.Content | ConvertFrom-Json

$results | Format-Table -AutoSize
Write-Host "PASS: Project RISING live Render smoke test completed successfully." -ForegroundColor Green
