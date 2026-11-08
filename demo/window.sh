#!/bin/zsh
printf '\e]0;shotlog-demo\a'
sleep 2; clear
echo '$ ssh -V'; ssh -V 2>&1
echo; echo '$ uname -sm'; uname -sm
echo; echo '$ which sshd scp'; which sshd scp
exec sleep 600
