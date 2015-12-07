# Installation #

RAFT is written in Python and PyQT. This is done so that the application can be multi-platform. The current version of RAFT has been ported to Python 3.3.

You must use a version of Python that is greater than Python 3.3. Other versions may work, but are untested.

### Dependencies ###

RAFT requires Python 2.6.5 and above. Python 3 is not supported.
<pre>
- Python 3.3 or later<br>
- PyQT4<br>
- QScintilla2<br>
- lxml<br>
</pre>

## <font color='blue'>OSX</font> ##
**Note** We still do not have an installable binary available for Mac OSX. It will be necessary to download the source and use your installed environment.

Versions of OSX that are supported are 10.6 (Snow Leopard), 10.7 (Lion), and 10.8 (Mountain Lion). Other versions may work, but are just untested.

The absolute quickest and easiest way to get RAFT up and running on the Mac is to use `MacPorts` http://macports.org to install a new Python environment as well as all of the dependencies. This will change once we have a stand alone application but will still be necessary to run the SVN version of RAFT.

### Install ###
Ensure that you have the development tools installed that came from Apple prior to installing `MacPorts`.

Install `MacPorts` and configure environment.

Use the following command to install dependencies.

```

sudo port install <package_name>
```

Install the following packages with `MacPorts`
<pre>
- python33<br>
- qt4-mac<br>
- py33-pyqt4<br>
- py33-qscintilla<br>
- py33-pip<br>
</pre>

Then install lxml using pip

```

sudo pip-3.3 install lxml
```

You will have to wait until everything is compiled and installed. Feel free to grab a cup of coffee because it's going to be a while.

You have the option to use the python\_select command to make the macports version of Python the default for the system. This isn't necessary unless it is a preference of yours. All this means is that you need to specify which version of Python you would like to use at the command line. For instance instead of running
```

python raft.py
```
You would have to run this instead
```

python3.3 raft.py
```
Not making the MacPorts version your default version allows the version of Python that came with your system to be called as normal for other applications that may require it.

### Now Go ###

If everything installed properly you should just be able to run RAFT from the directory by using your installed version of python. The following assumes Python 2.6 was used from MacPorts.

```

python3.3 raft.py
```

## OUTDATED INFO BELOW ##
Will be updated soon.

## <font color='blue'>Linux</font> ##
### Ubuntu ###
RAFT has been tested on Ubuntu 11.04 (Natty) and 10.04 (Lucid).
You will need to install the python bindings for the dependencies:
```

sudo apt-get install python-qscintilla2
sudo apt-get install python-lxml
```
After the installation, change to your RAFT directory and run RAFT as normal.

```

python raft.pyw
```

### BackTrack 5 ###
BackTrack 5 is almost ready to run RAFT out of the box.  Only the Python qScintilla packages are missing.  Run the following:
```

apt-get install python-qscintilla2
```

After the installation, change to your RAFT directory and run RAFT as normal.

```

python raft.pyw
```

### Other Linux Distributions ###
RAFT has not been tested with other distributions.  In theory, RAFT should work fine if you install the dependencies listed above.  Please let the RAFT team know of your results, successful or otherwise.

We have had some reports of crashes and other post-installation problems from users who are not on our supported Linux distros.  Unfortunately we do not have the resources to test and debug other distributions.  Try comparing your versions of our dependencies (and their dependencies, and so on) against the versions of those dependencies on our supported Linux distributions.

## <font color='blue'>Windows</font> ##

**Note** We still do not have a self contained executable for Windows. It will be necessary to download the source and use your installed environment.

### Getting Python ###
You can choose to go two ways when installing Python on Windows. You can choose the standard Python distribution from http://python.org or you can use `ActivePython` from `ActiveState` http://www.activestate.com/activepython

Ensure that you set whatever version of python you install to the default version for the system for ease of use.

### Getting PyQT ###
Download the appropriate binary package of PyQT for your installed Python version from the following location.
http://www.riverbankcomputing.co.uk/software/pyqt/download

Binary packages for Windows include QScintilla which is a dependency for RAFT. This inclusion makes life easier.

### Getting lxml ###

The lxml binary can be obtained most easily by using one of two methods, but using Python's easy\_install command or by using `ActivePython's` PyPM command if using an `ActivePython` install.
```

easy_install lxml
```
```

pypm install lxml
```
**Note** If you are on a 64bit Windows system PyPM requires that you have a valid business license to install lxml.

### Now Go ###

After installing the previous items you should be able to run RAFT from the project directory by using the following command.

```

python raft.pyw
```