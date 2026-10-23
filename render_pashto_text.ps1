param([Parameter(Mandatory=$true)][string]$SceneDataPath)
Add-Type -AssemblyName System.Drawing
$sceneData = @(Get-Content -LiteralPath $SceneDataPath -Raw | ConvertFrom-Json)
$fmt = New-Object System.Drawing.StringFormat
$fmt.Alignment = [System.Drawing.StringAlignment]::Center
$fmt.LineAlignment = [System.Drawing.StringAlignment]::Center
$fmt.FormatFlags = [System.Drawing.StringFormatFlags]::DirectionRightToLeft
function Draw-Pashto($g,$s,$y,$size,$color) {
    $font = New-Object System.Drawing.Font('Arial',$size,[System.Drawing.FontStyle]::Regular,[System.Drawing.GraphicsUnit]::Pixel)
    $brush = New-Object System.Drawing.SolidBrush([System.Drawing.ColorTranslator]::FromHtml($color))
    $rect = New-Object System.Drawing.RectangleF(55,($y-65),970,130)
    $g.DrawString($s,$font,$brush,$rect,$fmt)
    $brush.Dispose(); $font.Dispose()
}
for ($i=0; $i -lt $sceneData.Count; $i++) {
    $p = Join-Path $PSScriptRoot ('video-pilot-output/scene-'+($i+1)+'.png')
    $source = [System.Drawing.Image]::FromFile($p)
    $bmp = New-Object System.Drawing.Bitmap($source)
    $source.Dispose()
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit
    Draw-Pashto $g $sceneData[$i].Title 360 72 '#f4f9ff'
    for ($j=0; $j -lt $sceneData[$i].Lines.Count; $j++) {
        Draw-Pashto $g $sceneData[$i].Lines[$j] (1390+$j*105) 49 '#f4f9ff'
    }
    Draw-Pashto $g 'تشریحي انځور' 1630 29 '#9cb7cf'
    $g.Dispose(); $bmp.Save($p,[System.Drawing.Imaging.ImageFormat]::Png); $bmp.Dispose()
}
$fmt.Dispose()
