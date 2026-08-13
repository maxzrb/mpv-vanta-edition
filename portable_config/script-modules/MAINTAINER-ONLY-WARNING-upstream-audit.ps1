# MAINTAINER ONLY: upstream audit/merge tool. End users must not run this script.
# Read-only by default. Only -ApplyReviewedChanges can write baselines or apply reviewed changes.
# 只读审计：powershell -File .\MAINTAINER-ONLY-WARNING-upstream-audit.ps1 -ConfigDir <portable_config>
# 审阅报告后应用：在同一命令末尾显式追加 -ApplyReviewedChanges
param(
    [Parameter(Mandatory = $true)]
    [string]$ConfigDir,

    [switch]$DryRun,

    [switch]$ApplyReviewedChanges,

    [string]$OnlySource = ''
)

if ($DryRun -and $ApplyReviewedChanges) {
    throw '-DryRun and -ApplyReviewedChanges cannot be used together.'
}
$DryRun = -not $ApplyReviewedChanges

$ErrorActionPreference = 'Stop'
$OutputEncoding = [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

function Invoke-Native {
    param(
        [Parameter(Mandatory = $true)]
        [string]$FilePath,

        [Parameter(Mandatory = $true)]
        [string[]]$Arguments,

        [switch]$AllowFailure
    )

    $previous_error_preference = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        $captured = @(& $FilePath @Arguments 2>&1)
        $exit_code = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $previous_error_preference
    }
    $output = ($captured | ForEach-Object { $_.ToString() }) -join [Environment]::NewLine

    $result = [PSCustomObject]@{
        ExitCode = $exit_code
        StdOut = $output
        StdErr = ''
    }

    if (-not $AllowFailure -and $result.ExitCode -ne 0) {
        $detail = $result.StdErr.Trim()
        if ([string]::IsNullOrWhiteSpace($detail)) {
            $detail = $result.StdOut.Trim()
        }
        throw "$FilePath failed with exit code $($result.ExitCode): $detail"
    }

    return $result
}

function Convert-LuaPatternPart {
    param([string]$Pattern)

    $builder = New-Object System.Text.StringBuilder
    for ($index = 0; $index -lt $Pattern.Length; $index++) {
        $character = $Pattern[$index]

        if ($character -eq '%' -and $index + 1 -lt $Pattern.Length) {
            $index++
            [void]$builder.Append([Regex]::Escape([string]$Pattern[$index]))
            continue
        }

        if ($character -eq '.') {
            [void]$builder.Append('.')
        }
        elseif ($character -eq '-') {
            [void]$builder.Append('*?')
        }
        elseif ($character -in @('*', '+', '?', '^', '$', '(', ')')) {
            [void]$builder.Append($character)
        }
        else {
            [void]$builder.Append([Regex]::Escape([string]$character))
        }
    }

    return $builder.ToString()
}

function Convert-LuaPatterns {
    param([string]$Patterns)

    if ([string]::IsNullOrWhiteSpace($Patterns)) {
        return ''
    }

    $converted = foreach ($part in $Patterns.ToLowerInvariant().Split('|')) {
        Convert-LuaPatternPart -Pattern $part
    }
    return ($converted -join '|')
}

function Get-OptionalProperty {
    param(
        [object]$Object,
        [string]$Name,
        $DefaultValue
    )

    $property = $Object.PSObject.Properties[$Name]
    if ($null -eq $property -or $null -eq $property.Value) {
        return $DefaultValue
    }
    return $property.Value
}

function Get-SafeChildPath {
    param(
        [string]$Root,
        [string]$RelativePath
    )

    $clean_relative = $RelativePath.Replace('/', [IO.Path]::DirectorySeparatorChar)
    if ([IO.Path]::IsPathRooted($clean_relative)) {
        throw "Absolute target paths are not allowed: $RelativePath"
    }

    $root_full = [IO.Path]::GetFullPath($Root).TrimEnd('\', '/')
    $candidate = [IO.Path]::GetFullPath((Join-Path $root_full $clean_relative))
    $prefix = $root_full + [IO.Path]::DirectorySeparatorChar
    if (-not $candidate.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Target path escapes its destination root: $RelativePath"
    }
    return $candidate
}

function Get-RelativePath {
    param(
        [string]$Root,
        [string]$Path
    )

    $root_full = [IO.Path]::GetFullPath($Root).TrimEnd('\', '/') + [IO.Path]::DirectorySeparatorChar
    $path_full = [IO.Path]::GetFullPath($Path)
    $root_uri = New-Object System.Uri($root_full)
    $path_uri = New-Object System.Uri($path_full)
    return [Uri]::UnescapeDataString($root_uri.MakeRelativeUri($path_uri).ToString()).Replace('/', '\')
}

function Get-FileSha256 {
    param([string]$Path)
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Get-GitBlobSha {
    param([string]$Path)
    $result = Invoke-Native -FilePath 'git.exe' -Arguments @('hash-object', '--no-filters', '--', $Path)
    return $result.StdOut.Trim().ToLowerInvariant()
}

function Get-UpstreamFile {
    param(
        [object]$SelectedFile,
        [string]$StagingRoot,
        [string]$SourceName
    )

    if (-not [string]::IsNullOrWhiteSpace([string]$SelectedFile.FilePath)) {
        return [string]$SelectedFile.FilePath
    }

    $download_file = Get-SafeChildPath -Root $StagingRoot -RelativePath (
        "downloads/$SourceName/$([string]$SelectedFile.Relative)"
    )
    if (-not (Test-Path -LiteralPath $download_file -PathType Leaf)) {
        Ensure-ParentDirectory -Path $download_file
        if (-not [string]::IsNullOrWhiteSpace([string]$SelectedFile.RepoPath)) {
            $start_info = New-Object System.Diagnostics.ProcessStartInfo
            $start_info.FileName = 'git.exe'
            $escaped_repo = ([string]$SelectedFile.RepoPath).Replace('"', '\"')
            $start_info.Arguments = "-C `"$escaped_repo`" cat-file blob $([string]$SelectedFile.BlobSha)"
            $start_info.UseShellExecute = $false
            $start_info.CreateNoWindow = $true
            $start_info.RedirectStandardOutput = $true
            $start_info.RedirectStandardError = $true

            $process = New-Object System.Diagnostics.Process
            $process.StartInfo = $start_info
            [void]$process.Start()
            $destination_stream = [IO.File]::Open(
                $download_file,
                [IO.FileMode]::Create,
                [IO.FileAccess]::Write,
                [IO.FileShare]::None
            )
            try {
                $process.StandardOutput.BaseStream.CopyTo($destination_stream)
            }
            finally {
                $destination_stream.Dispose()
            }
            $stderr = $process.StandardError.ReadToEnd()
            $process.WaitForExit()
            if ($process.ExitCode -ne 0) {
                throw "Unable to materialize Git blob $([string]$SelectedFile.BlobSha): $stderr"
            }
        }
        else {
            throw 'No local Git object source is available for this upstream file'
        }
    }
    return $download_file
}

function Test-TextFile {
    param([string]$Path)

    $text_extensions = @(
        '.lua', '.conf', '.json', '.md', '.txt', '.glsl', '.vpy',
        '.ps1', '.xml', '.html', '.css', '.js', '.toml', '.yml', '.yaml'
    )
    return $text_extensions -contains ([IO.Path]::GetExtension($Path).ToLowerInvariant())
}

function Ensure-ParentDirectory {
    param([string]$Path)
    $parent = Split-Path -Parent $Path
    if (-not (Test-Path -LiteralPath $parent)) {
        [void](New-Item -ItemType Directory -Path $parent -Force)
    }
}

function Copy-WithParent {
    param(
        [string]$Source,
        [string]$Destination
    )

    Ensure-ParentDirectory -Path $Destination
    Copy-Item -LiteralPath $Source -Destination $Destination -Force
}

function Get-CommonDirectoryPrefix {
    param([string[]]$Paths)

    if ($Paths.Count -eq 0) {
        return ''
    }

    $directories = New-Object System.Collections.Generic.List[object]
    foreach ($path in $Paths) {
        $normalized = $path.Replace('\', '/')
        $last_slash = $normalized.LastIndexOf('/')
        if ($last_slash -lt 0) {
            [void]$directories.Add([string[]]@())
        }
        else {
            $segments = [string[]]($normalized.Substring(0, $last_slash).Split('/'))
            [void]$directories.Add($segments)
        }
    }

    if ($directories.Count -eq 0) {
        return ''
    }

    $prefix = New-Object System.Collections.Generic.List[string]
    $position = 0
    while ($true) {
        $candidate = $null
        foreach ($segments in $directories) {
            if ($position -ge $segments.Count) {
                return ($prefix -join '/')
            }
            if ($null -eq $candidate) {
                $candidate = $segments[$position]
            }
            elseif ($candidate -cne $segments[$position]) {
                return ($prefix -join '/')
            }
        }
        [void]$prefix.Add($candidate)
        $position++
    }
}

function Get-SourceName {
    param(
        [object]$Source,
        [int]$Index
    )

    $configured_name = Get-OptionalProperty -Object $Source -Name 'name' -DefaultValue ''
    if (-not [string]::IsNullOrWhiteSpace($configured_name)) {
        $base_name = [string]$configured_name
    }
    else {
        $git_url = [string](Get-OptionalProperty -Object $Source -Name 'git' -DefaultValue "source-$Index")
        $base_name = [IO.Path]::GetFileNameWithoutExtension($git_url.TrimEnd('/'))
    }

    $safe_name = $base_name -replace '[^A-Za-z0-9._-]', '_'
    return ('{0:d2}-{1}' -f $Index, $safe_name)
}

function Add-Report {
    param(
        [string]$Kind,
        [string]$Message
    )

    $script:counts[$Kind] = [int]$script:counts[$Kind] + 1
    [void]$script:report_lines.Add("[$Kind] $Message")
}

$config_root = [IO.Path]::GetFullPath($ConfigDir).TrimEnd('\', '/')
$manager_file = Join-Path $config_root 'MAINTAINER-ONLY-WARNING-upstream-sources.json'
if (-not (Test-Path -LiteralPath $manager_file -PathType Leaf)) {
    throw "Update source configuration not found: $manager_file"
}

$cache_root = Join-Path $config_root 'cache\MAINTAINER-ONLY-upstream-audit'
$state_file = Join-Path $cache_root 'state.json'
$bases_root = Join-Path $cache_root 'bases'
$reports_root = Join-Path $cache_root 'reports'
$conflicts_root = Join-Path $cache_root 'conflicts'
$backups_root = Join-Path $cache_root 'backups'
$run_stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$run_id = "$run_stamp-$([Guid]::NewGuid().ToString('N').Substring(0, 8))"
$staging_root = Join-Path $cache_root "staging\$run_id"
$run_report = Join-Path $reports_root "$run_id.txt"
$last_report = Join-Path $cache_root 'last-report.txt'

if (-not $DryRun) {
    foreach ($directory in @($cache_root, $bases_root, $reports_root, $conflicts_root, $backups_root)) {
        if (-not (Test-Path -LiteralPath $directory)) {
            [void](New-Item -ItemType Directory -Path $directory -Force)
        }
    }
}
if (-not (Test-Path -LiteralPath $staging_root)) {
    [void](New-Item -ItemType Directory -Path $staging_root -Force)
}

$sources = Get-Content -LiteralPath $manager_file -Raw -Encoding UTF8 | ConvertFrom-Json
$state_map = @{}
if (Test-Path -LiteralPath $state_file -PathType Leaf) {
    $loaded_state = Get-Content -LiteralPath $state_file -Raw -Encoding UTF8 | ConvertFrom-Json
    $loaded_files = $loaded_state.files
    foreach ($entry in $loaded_files) {
        $state_map[[string]$entry.key] = $entry
    }
}

$counts = @{
    UNCHANGED = 0
    INSTALLED = 0
    UPDATED = 0
    MERGED = 0
    PROTECTED = 0
    SKIPPED = 0
    REMOVED = 0
    DISABLED = 0
    ERROR = 0
}
$report_lines = New-Object System.Collections.Generic.List[string]
[void]$report_lines.Add("MAINTAINER ONLY - MPV upstream audit report")
[void]$report_lines.Add("Run time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
[void]$report_lines.Add("Config directory: $config_root")
[void]$report_lines.Add("Mode: $(if ($DryRun) { 'dry run' } else { 'safe update' })")
[void]$report_lines.Add('')

$seen_keys = @{}
$processed_sources = @{}
$source_index = 0

foreach ($source in $sources) {
    $source_index++
    $source_name = Get-SourceName -Source $source -Index $source_index
    $configured_source_name = [string](Get-OptionalProperty -Object $source -Name 'name' -DefaultValue '')
    if (-not [string]::IsNullOrWhiteSpace($OnlySource) -and $configured_source_name -ne $OnlySource) {
        continue
    }
    $enabled = [bool](Get-OptionalProperty -Object $source -Name 'enabled' -DefaultValue $true)

    if (-not $enabled) {
        Add-Report -Kind 'DISABLED' -Message "$source_name is disabled"
        continue
    }
    $processed_sources[$source_name] = $true

    try {
        $destination_setting = [string](Get-OptionalProperty -Object $source -Name 'dest' -DefaultValue '~~/scripts')
        if ($destination_setting.StartsWith('~~/')) {
            $destination_relative = $destination_setting.Substring(3)
            $destination_root = Get-SafeChildPath -Root $config_root -RelativePath $destination_relative
        }
        else {
            $destination_root = [IO.Path]::GetFullPath($destination_setting)
        }

        $whitelist = Convert-LuaPatterns -Patterns ([string](Get-OptionalProperty -Object $source -Name 'whitelist' -DefaultValue ''))
        $blacklist = Convert-LuaPatterns -Patterns ([string](Get-OptionalProperty -Object $source -Name 'blacklist' -DefaultValue ''))
        $github_tree = [string](Get-OptionalProperty -Object $source -Name 'github_tree' -DefaultValue '')
        $configured_git = [string](Get-OptionalProperty -Object $source -Name 'git' -DefaultValue '')
        $configured_local_repo = [string](Get-OptionalProperty -Object $source -Name 'local_repo' -DefaultValue '')
        $default_git_tree = $configured_git -match '^https?://github\.com/'
        $git_tree = [bool](Get-OptionalProperty -Object $source -Name 'git_tree' -DefaultValue $default_git_tree)
        $selected = New-Object System.Collections.Generic.List[object]

        if (-not [string]::IsNullOrWhiteSpace($github_tree)) {
            $branch = [string](Get-OptionalProperty -Object $source -Name 'branch' -DefaultValue 'main')
            $api_uri = "https://api.github.com/repos/$github_tree/git/trees/$branch`?recursive=1"
            $tree_response = Invoke-RestMethod -Uri $api_uri -Headers @{
                'User-Agent' = 'mpv-safe-manager'
                'Accept' = 'application/vnd.github+json'
            }
            if ([bool]$tree_response.truncated) {
                throw 'GitHub tree response was truncated'
            }

            $source_commit = [string]$tree_response.sha
            foreach ($entry in $tree_response.tree) {
                if ([string]$entry.type -ne 'blob') {
                    continue
                }
                $repo_relative = ([string]$entry.path).Replace('\', '/')
                $lower_relative = $repo_relative.ToLowerInvariant()
                if ($whitelist -ne '' -and -not [Regex]::IsMatch($lower_relative, $whitelist)) {
                    continue
                }
                if ($blacklist -ne '' -and [Regex]::IsMatch($lower_relative, $blacklist)) {
                    continue
                }

                $encoded_path = (($repo_relative.Split('/') | ForEach-Object {
                    [Uri]::EscapeDataString($_)
                }) -join '/')
                [void]$selected.Add([PSCustomObject]@{
                    FilePath = ''
                    Relative = $repo_relative
                    BlobSha = ([string]$entry.sha).ToLowerInvariant()
                    DownloadUrl = "https://raw.githubusercontent.com/$github_tree/$branch/$encoded_path"
                    RepoPath = ''
                })
            }
        }
        elseif ($git_tree) {
            if ([string]::IsNullOrWhiteSpace($configured_git)) {
                throw 'git_tree requires a git URL'
            }
            $branch = [string](Get-OptionalProperty -Object $source -Name 'branch' -DefaultValue 'main')
            $repo_root = Join-Path $staging_root "$source_name.git"
            [void](Invoke-Native -FilePath 'git.exe' -Arguments @(
                '-c', 'core.autocrlf=false',
                'clone', '--bare', '--depth', '1', '--single-branch',
                '--filter=blob:none', '--branch', $branch,
                $configured_git, $repo_root
            ))
            $source_commit = (
                Invoke-Native -FilePath 'git.exe' -Arguments @('-C', $repo_root, 'rev-parse', 'HEAD')
            ).StdOut.Trim()
            $tree_lines = (
                Invoke-Native -FilePath 'git.exe' -Arguments @('-C', $repo_root, 'ls-tree', '-r', 'HEAD')
            ).StdOut -split '[\r\n]+'
            foreach ($tree_line in $tree_lines) {
                if ($tree_line -notmatch '^\d+\s+blob\s+(?<sha>[0-9a-f]+)\t(?<path>.+)$') {
                    continue
                }
                $repo_relative = $Matches.path.Replace('\', '/')
                $lower_relative = $repo_relative.ToLowerInvariant()
                if ($whitelist -ne '' -and -not [Regex]::IsMatch($lower_relative, $whitelist)) {
                    continue
                }
                if ($blacklist -ne '' -and [Regex]::IsMatch($lower_relative, $blacklist)) {
                    continue
                }
                [void]$selected.Add([PSCustomObject]@{
                    FilePath = ''
                    Relative = $repo_relative
                    BlobSha = $Matches.sha.ToLowerInvariant()
                    DownloadUrl = ''
                    RepoPath = $repo_root
                })
            }
        }
        else {
            $local_repo = $configured_local_repo
            if (-not [string]::IsNullOrWhiteSpace($local_repo)) {
                if ($local_repo.StartsWith('~~/')) {
                    $repo_root = Get-SafeChildPath -Root $config_root -RelativePath $local_repo.Substring(3)
                }
                else {
                    $repo_root = [IO.Path]::GetFullPath($local_repo)
                }
                if (-not (Test-Path -LiteralPath $repo_root -PathType Container)) {
                    throw "Local source does not exist: $repo_root"
                }
            }
            else {
                $git_url = $configured_git
                if ([string]::IsNullOrWhiteSpace($git_url)) {
                    throw 'Missing git, local_repo, or github_tree'
                }

                $repo_root = Join-Path $staging_root $source_name
                $clone_arguments = @('-c', 'core.autocrlf=false', 'clone', '--depth', '1', '--single-branch', '--filter=blob:none')
                $branch = [string](Get-OptionalProperty -Object $source -Name 'branch' -DefaultValue '')
                if (-not [string]::IsNullOrWhiteSpace($branch)) {
                    $clone_arguments += @('--branch', $branch)
                }
                $clone_arguments += @($git_url, $repo_root)
                [void](Invoke-Native -FilePath 'git.exe' -Arguments $clone_arguments)
            }

            $commit_result = Invoke-Native -FilePath 'git.exe' -Arguments @('-C', $repo_root, 'rev-parse', 'HEAD') -AllowFailure
            $source_commit = $commit_result.StdOut.Trim()
            if ($commit_result.ExitCode -ne 0) {
                $source_commit = 'local'
            }

            foreach ($file in Get-ChildItem -LiteralPath $repo_root -Recurse -File) {
                if ($file.FullName.StartsWith((Join-Path $repo_root '.git'), [StringComparison]::OrdinalIgnoreCase)) {
                    continue
                }

                $repo_relative = (Get-RelativePath -Root $repo_root -Path $file.FullName).Replace('\', '/')
                $lower_relative = $repo_relative.ToLowerInvariant()
                if ($whitelist -ne '' -and -not [Regex]::IsMatch($lower_relative, $whitelist)) {
                    continue
                }
                if ($blacklist -ne '' -and [Regex]::IsMatch($lower_relative, $blacklist)) {
                    continue
                }
                [void]$selected.Add([PSCustomObject]@{
                    FilePath = $file.FullName
                    Relative = $repo_relative
                    BlobSha = ''
                    DownloadUrl = ''
                    RepoPath = ''
                })
            }
        }

        if ($selected.Count -eq 0) {
            throw 'No files matched whitelist/blacklist'
        }

        $strip_prefix = [string](Get-OptionalProperty -Object $source -Name 'strip_prefix' -DefaultValue '')
        $strip_prefix = $strip_prefix.Replace('\', '/').Trim('/')
        if ($strip_prefix -eq '') {
            $strip_prefix = Get-CommonDirectoryPrefix -Paths @($selected | ForEach-Object { $_.Relative })
        }
        if ($strip_prefix -ne '') {
            $strip_prefix += '/'
        }

        $flatten_folders = [bool](Get-OptionalProperty -Object $source -Name 'flatten_folders' -DefaultValue $false)
        $install_missing = [bool](Get-OptionalProperty -Object $source -Name 'install_missing' -DefaultValue $false)
        $download_candidates = [bool](Get-OptionalProperty -Object $source -Name 'download_candidates' -DefaultValue $true)
        $renames = Get-OptionalProperty -Object $source -Name 'renames' -DefaultValue $null

        foreach ($selected_file in $selected) {
            $repo_relative = [string]$selected_file.Relative
            if ($strip_prefix -ne '' -and -not $repo_relative.StartsWith($strip_prefix, [StringComparison]::OrdinalIgnoreCase)) {
                continue
            }

            if ($strip_prefix -eq '') {
                $target_relative = $repo_relative
            }
            else {
                $target_relative = $repo_relative.Substring($strip_prefix.Length)
            }
            if ($flatten_folders) {
                $target_relative = [IO.Path]::GetFileName($target_relative)
            }

            if ($null -ne $renames) {
                $rename_property = $renames.PSObject.Properties[$target_relative]
                if ($null -ne $rename_property) {
                    $target_relative = [string]$rename_property.Value
                }
            }

            $destination_file = Get-SafeChildPath -Root $destination_root -RelativePath $target_relative
            $destination_key = (Get-RelativePath -Root $config_root -Path $destination_file).Replace('\', '/')
            $state_key = "$source_name|$destination_key"
            $seen_keys[$state_key] = $true

            $upstream_file = [string]$selected_file.FilePath
            if (-not [string]::IsNullOrWhiteSpace([string]$selected_file.BlobSha)) {
                $upstream_sha = [string]$selected_file.BlobSha
            }
            else {
                $upstream_sha = Get-FileSha256 -Path $upstream_file
            }
            $base_file = Get-SafeChildPath -Root $bases_root -RelativePath "$source_name/$target_relative"
            $previous = $state_map[$state_key]
            $exists = Test-Path -LiteralPath $destination_file -PathType Leaf
            $local_matches_upstream = $false
            $skip_upstream_materialization = $false

            if (-not $exists) {
                if ($install_missing) {
                    Add-Report -Kind 'INSTALLED' -Message "$destination_key <- $source_name"
                    if (-not $DryRun) {
                        $upstream_file = Get-UpstreamFile -SelectedFile $selected_file -StagingRoot $staging_root -SourceName $source_name
                        Copy-WithParent -Source $upstream_file -Destination $destination_file
                    }
                }
                else {
                    Add-Report -Kind 'SKIPPED' -Message "$destination_key is absent and install_missing is disabled"
                }
            }
            else {
                if (-not [string]::IsNullOrWhiteSpace([string]$selected_file.BlobSha)) {
                    $local_sha = Get-GitBlobSha -Path $destination_file
                }
                else {
                    $local_sha = Get-FileSha256 -Path $destination_file
                }
                if ($local_sha -eq $upstream_sha) {
                    $local_matches_upstream = $true
                    Add-Report -Kind 'UNCHANGED' -Message $destination_key
                }
                elseif ($null -eq $previous) {
                    Add-Report -Kind 'PROTECTED' -Message "$destination_key differs on first baseline; kept local file"
                    if (-not $DryRun -and $download_candidates) {
                        $upstream_file = Get-UpstreamFile -SelectedFile $selected_file -StagingRoot $staging_root -SourceName $source_name
                        $conflict_file = Get-SafeChildPath -Root $conflicts_root -RelativePath "$run_id/$source_name/$target_relative.upstream"
                        Copy-WithParent -Source $upstream_file -Destination $conflict_file
                    }
                    elseif (-not $download_candidates) {
                        $skip_upstream_materialization = $true
                    }
                }
                elseif ([string]$previous.upstream_sha -eq $upstream_sha) {
                    Add-Report -Kind 'PROTECTED' -Message "$destination_key has local-only changes; kept local file"
                }
                elseif ($local_sha -eq [string]$previous.upstream_sha) {
                    Add-Report -Kind 'UPDATED' -Message "$destination_key fast-forwarded to new upstream"
                    if (-not $DryRun) {
                        $upstream_file = Get-UpstreamFile -SelectedFile $selected_file -StagingRoot $staging_root -SourceName $source_name
                        $backup_file = Get-SafeChildPath -Root $backups_root -RelativePath "$run_id/$source_name/$target_relative"
                        Copy-WithParent -Source $destination_file -Destination $backup_file
                        Copy-WithParent -Source $upstream_file -Destination $destination_file
                    }
                }
                elseif ((Test-TextFile -Path $destination_file) -and (Test-Path -LiteralPath $base_file -PathType Leaf)) {
                    $upstream_file = Get-UpstreamFile -SelectedFile $selected_file -StagingRoot $staging_root -SourceName $source_name
                    $merge_candidate = Get-SafeChildPath -Root $staging_root -RelativePath "merge/$source_name/$target_relative"
                    Copy-WithParent -Source $destination_file -Destination $merge_candidate
                    $merge_result = Invoke-Native -FilePath 'git.exe' -Arguments @(
                        '-c', 'core.autocrlf=false',
                        'merge-file',
                        '-L', 'local-custom-version',
                        '-L', 'previous-upstream-base',
                        '-L', 'new-upstream-version',
                        $merge_candidate,
                        $base_file,
                        $upstream_file
                    ) -AllowFailure

                    if ($merge_result.ExitCode -eq 0) {
                        Add-Report -Kind 'MERGED' -Message "$destination_key was merged with the new upstream"
                        if (-not $DryRun) {
                            $backup_file = Get-SafeChildPath -Root $backups_root -RelativePath "$run_id/$source_name/$target_relative"
                            Copy-WithParent -Source $destination_file -Destination $backup_file
                            Copy-WithParent -Source $merge_candidate -Destination $destination_file
                        }
                    }
                    else {
                        Add-Report -Kind 'PROTECTED' -Message "$destination_key has overlapping changes; kept local and saved merge candidate"
                        if (-not $DryRun) {
                            $conflict_file = Get-SafeChildPath -Root $conflicts_root -RelativePath "$run_id/$source_name/$target_relative.merge"
                            Copy-WithParent -Source $merge_candidate -Destination $conflict_file
                        }
                    }
                }
                else {
                    Add-Report -Kind 'PROTECTED' -Message "$destination_key cannot be merged safely; kept local file"
                    if (-not $DryRun) {
                        $upstream_file = Get-UpstreamFile -SelectedFile $selected_file -StagingRoot $staging_root -SourceName $source_name
                        $conflict_file = Get-SafeChildPath -Root $conflicts_root -RelativePath "$run_id/$source_name/$target_relative.upstream"
                        Copy-WithParent -Source $upstream_file -Destination $conflict_file
                    }
                }
            }

            if (-not $DryRun) {
                if ($local_matches_upstream) {
                    Copy-WithParent -Source $destination_file -Destination $base_file
                }
                elseif ((-not $exists -and -not $install_missing) -or $skip_upstream_materialization) {
                }
                else {
                    $upstream_file = Get-UpstreamFile -SelectedFile $selected_file -StagingRoot $staging_root -SourceName $source_name
                    Copy-WithParent -Source $upstream_file -Destination $base_file
                }
                $state_map[$state_key] = [PSCustomObject]@{
                    key = $state_key
                    upstream_sha = $upstream_sha
                    source_commit = $source_commit
                    checked_at = (Get-Date).ToString('o')
                }
            }
        }
    }
    catch {
        Add-Report -Kind 'ERROR' -Message "$source_name`: $($_.Exception.Message)"
    }
}

foreach ($state_key in @($state_map.Keys)) {
    $state_source = ($state_key -split '\|', 2)[0]
    if (-not $processed_sources.ContainsKey($state_source)) {
        continue
    }
    if (-not $seen_keys.ContainsKey($state_key)) {
        Add-Report -Kind 'REMOVED' -Message "$state_key is no longer provided upstream; local file was not deleted"
        if (-not $DryRun) {
            [void]$state_map.Remove($state_key)
        }
    }
}

[void]$report_lines.Add('')
[void]$report_lines.Add('Summary:')
foreach ($kind in @('UNCHANGED', 'INSTALLED', 'UPDATED', 'MERGED', 'PROTECTED', 'SKIPPED', 'REMOVED', 'DISABLED', 'ERROR')) {
    [void]$report_lines.Add("  $kind=$($counts[$kind])")
}
[void]$report_lines.Add('')
[void]$report_lines.Add("Backup directory: $(Join-Path $backups_root $run_id)")
[void]$report_lines.Add("Conflict candidates: $(Join-Path $conflicts_root $run_id)")

if (-not $DryRun) {
    $state_object = [PSCustomObject]@{
        version = 1
        updated_at = (Get-Date).ToString('o')
        files = @($state_map.Values | Sort-Object key)
    }
    $utf8_no_bom = New-Object System.Text.UTF8Encoding($false)
    [IO.File]::WriteAllText($state_file, ($state_object | ConvertTo-Json -Depth 8), $utf8_no_bom)
    Ensure-ParentDirectory -Path $run_report
    [IO.File]::WriteAllLines($run_report, $report_lines, $utf8_no_bom)
    [IO.File]::WriteAllLines($last_report, $report_lines, $utf8_no_bom)
}

try {
    $staging_full = [IO.Path]::GetFullPath($staging_root)
    $cache_full = [IO.Path]::GetFullPath($cache_root).TrimEnd('\', '/') + [IO.Path]::DirectorySeparatorChar
    if ($staging_full.StartsWith($cache_full, [StringComparison]::OrdinalIgnoreCase) -and (Test-Path -LiteralPath $staging_full)) {
        Remove-Item -LiteralPath $staging_full -Recurse -Force
    }
}
catch {
    Write-Warning "Failed to clean staging directory: $($_.Exception.Message)"
}

$summary = "Maintainer upstream audit complete: installed $($counts.INSTALLED), updated $($counts.UPDATED), merged $($counts.MERGED), protected $($counts.PROTECTED), errors $($counts.ERROR)"
Write-Output $summary
$important_lines = @($report_lines | Where-Object {
    $_ -match '^\[(INSTALLED|UPDATED|MERGED|PROTECTED|REMOVED|ERROR)\]'
})
if ($important_lines.Count -gt 0) {
    Write-Output ($important_lines -join [Environment]::NewLine)
}
if (-not $DryRun) {
    Write-Output "Report: $last_report"
}

if ($counts.ERROR -gt 0) {
    exit 2
}

if ($DryRun -and (Test-Path -LiteralPath $cache_root -PathType Container)) {
    $staging_parent = Split-Path -Parent $staging_root
    if (Test-Path -LiteralPath $staging_parent -PathType Container) {
        $staging_entries = @(Get-ChildItem -LiteralPath $staging_parent -Force)
        if ($staging_entries.Count -eq 0) {
            Remove-Item -LiteralPath $staging_parent -Force
        }
    }
    $cache_entries = @(Get-ChildItem -LiteralPath $cache_root -Force)
    if ($cache_entries.Count -eq 0) {
        Remove-Item -LiteralPath $cache_root -Force
    }
}
exit 0
