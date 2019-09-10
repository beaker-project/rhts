if command -v python3 >/dev/null ; then
    python_command="python3"
elif [ -f /usr/libexec/platform-python ] && \
/usr/libexec/platform-python --version 2>&1 | grep -q "Python 3" ; then
    python_command="/usr/libexec/platform-python"
else
    python_command="python"
fi
echo $python_command;
