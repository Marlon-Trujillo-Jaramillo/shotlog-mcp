Output docs/demo-terminal.gif
# Recreate the README GIF: run demo/window.sh in a separate Terminal window, then `vhs demo/demo.tape`.
Set Shell zsh
Set FontSize 15
Set Width 1100
Set Height 560
Set Theme "Catppuccin Mocha"
Set TypingSpeed 35ms
Hide
Type "setopt interactivecomments; export SHOTLOG_DIR=~/os-lab PS1='$ ' && cd ~/shotlog-mcp && clear"
Enter
Show
Type "# What your AI assistant does when you ask: 'screenshot the terminal as step 1'"
Enter
Sleep 600ms
Type "uv run -q python demo/demo.py ."
Enter
Sleep 12s
Type "ls $SHOTLOG_DIR"
Enter
Sleep 3s
