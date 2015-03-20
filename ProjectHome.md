Ramses allows you to automate the process of doing builds and deploys (or any similarly repeatable set of scripts) on multiple hosts.

It doesn't try to know more than you about dependencies or tasks. Instead it allows you to set up a set of shell, and a way to run those script on any host that supports a ssh shell.

Configuration of scripts is done through setting environment variables on the remote host that your shell script can use.