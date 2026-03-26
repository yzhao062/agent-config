# Let .gitattributes handle line endings; silence CRLF warnings on Windows
git config --global core.autocrlf false

New-Item -ItemType Directory -Force -Path .agent-config, .claude, .claude/commands | Out-Null
Invoke-WebRequest -UseBasicParsing -Uri https://raw.githubusercontent.com/yzhao062/agent-config/main/AGENTS.md -OutFile .agent-config/AGENTS.md
Copy-Item .agent-config/AGENTS.md AGENTS.md -Force
if (Test-Path .agent-config/repo/.git) {
  git -C .agent-config/repo pull --ff-only
} else {
  git clone --depth 1 --filter=blob:none --sparse https://github.com/yzhao062/agent-config.git .agent-config/repo
}
git -C .agent-config/repo sparse-checkout set skills .claude
if (Test-Path .agent-config/repo/.claude/commands) {
  Copy-Item .agent-config/repo/.claude/commands/*.md .claude/commands/ -Force
}
if (Test-Path .agent-config/repo/.claude/settings.json) {
  if (Test-Path .claude/settings.json) {
    function Merge-Json($base, $over) {
      foreach ($p in $over.PSObject.Properties) {
        $b = $base.PSObject.Properties[$p.Name]
        if ($b -and $b.Value -is [PSCustomObject] -and $p.Value -is [PSCustomObject]) {
          Merge-Json $b.Value $p.Value
        } elseif ($b -and $b.Value -is [Array] -and $p.Value -is [Array]) {
          $s = [System.Collections.Generic.HashSet[string]]::new()
          $m = @(); foreach ($i in $b.Value) { if ($s.Add($i)) { $m += $i } }
          foreach ($i in $p.Value) { if ($s.Add($i)) { $m += $i } }
          $base | Add-Member -NotePropertyName $p.Name -NotePropertyValue $m -Force
        } else {
          $base | Add-Member -NotePropertyName $p.Name -NotePropertyValue $p.Value -Force
        }
      }
    }
    $shared = Get-Content .agent-config/repo/.claude/settings.json -Raw | ConvertFrom-Json
    $project = Get-Content .claude/settings.json -Raw | ConvertFrom-Json
    Merge-Json $project $shared
    $project | ConvertTo-Json -Depth 10 | Set-Content .claude/settings.json
  } else {
    Copy-Item .agent-config/repo/.claude/settings.json .claude/settings.json -Force
  }
}
if (-not (Test-Path .gitignore) -or -not (Select-String -Quiet -Pattern '^\.agent-config/' .gitignore)) {
  Add-Content -Path .gitignore -Value "`n.agent-config/"
}
