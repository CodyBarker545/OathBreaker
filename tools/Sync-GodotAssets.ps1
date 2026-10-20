# Refresh runtime GLB copies while preserving editable sources and licences.
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$characterRoot = Join-Path $projectRoot 'SourceAssets\characters'
$runtimeRoot = Join-Path $projectRoot 'Assets'
$copies = @(
    @((Join-Path $characterRoot 'hooded_assassin\blendswap_assassin\assassin_refined.glb'), (Join-Path $runtimeRoot 'Characters\Assassin\Assassin.glb')),
    @((Join-Path $characterRoot 'ashveil\ashveil.glb'), (Join-Path $runtimeRoot 'Characters\Ashveil\Ashveil.glb')),
    @((Join-Path $characterRoot 'komodo_axe_warrior\komodo_axe_warrior.glb'), (Join-Path $runtimeRoot 'Characters\Komodo\Komodo.glb')),
    @((Join-Path $characterRoot 'forsaken_sister\forsaken_sister.glb'), (Join-Path $runtimeRoot 'Characters\ForsakenSister\ForsakenSister.glb')),
    @((Join-Path $characterRoot 'masked_ninja\masked_ninja.glb'), (Join-Path $runtimeRoot 'Characters\MaskedNinja\MaskedNinja.glb')),
    @((Join-Path $characterRoot 'broken_oath_knight\broken_oath_knight.glb'), (Join-Path $runtimeRoot 'Characters\BrokenOathKnight\BrokenOathKnight.glb')),
    @((Join-Path $characterRoot 'ash_scholar\ash_scholar.glb'), (Join-Path $runtimeRoot 'Characters\AshScholar\AshScholar.glb'))
)
foreach ($copy in $copies) {
    New-Item -ItemType Directory -Path (Split-Path -Parent $copy[1]) -Force | Out-Null
    Copy-Item -LiteralPath $copy[0] -Destination $copy[1] -Force
}
$levelDestination = Join-Path $runtimeRoot 'Levels'
New-Item -ItemType Directory -Path $levelDestination -Force | Out-Null
$levelModels = @(Get-ChildItem -LiteralPath (Join-Path $projectRoot 'SourceAssets\levels\models') -Filter '*.glb' -File)
foreach ($model in $levelModels) {
    Copy-Item -LiteralPath $model.FullName -Destination $levelDestination -Force
}
Write-Output "Synchronized $($copies.Count) character models and $($levelModels.Count) level models."
