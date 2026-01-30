# VHS Demo Recording for Claude Mountaineering Skills
# Run: cd scripts && vhs demo.tape

Output ../skills/route-researcher/assets/demo.gif

# Terminal settings - wide enough to fit Claude Code welcome screen
Set Shell bash
Set FontSize 16
Set Width 1200
Set Height 600
Set Theme "Catppuccin Mocha"
Set Padding 20
Set Framerate 30
Set PlaybackSpeed 1

# Hide the command, just show the output
Hide
Type "bash demo-simulation.sh"
Enter
Sleep 100ms
Show
Sleep 48s
