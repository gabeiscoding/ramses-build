http://code.google.com/p/ramses-build/

Dependencies:
twisted and twisted.conch
pyinstaller (http://www.pyinstaller.org/ - latest from svn) If you want to build a native frozen binary of ramses (otherwise you can just use ramses/build.py directly)

= Notes on Installing =
Under the build/ directory are scripts for ramses building and deploying itself. The are also good example scripts.

They could be run like:
build/> python ../ramses/build.py ramsesBuild.des

Note that to be succefuly frozen, you should create a file:
$PyInstallerHome/hooks/hook-twisted.conch.ssh.py that has the line:

hiddenimports = [     "Crypto.Cipher.AES"     ]

where $PyInstallerHome is where you have pyinstaller installed
