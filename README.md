#NSAptr
##A Non-Sketchy Android Platform Tools Retriever

I wanted to perform an ADB backup, but my new computer didn't have ADB installed in it.

I could have done one of the following:

1. Download a recent JDK
1. Install said JDK
1. Download the Standalone SDK Tools ZIP file for my computer's OS
1. Extract the SDK Tools
1. Run the SDK Manager to install the Platform Tools for my computer's OS
1. Delete the SDK Tools
1. Uninstall the JDK
1. And in the future, should I need to update a tool, go back to step 1

OR

1. Download a *sketchy* "Easy Installer" for the platform tools for my computer's OS.
1. Fail to find official checksums for the Platform Tools binaries.
1. Execute it hoping that whoever packaged it didn't inject something nasty into it.

I ended up going with the former method, but, in my opinion, neither option is sustainable.

Given that all my computers will **always** have Python 3 installed, I decided to port the relevant functionality from the SDK Manager from Java to Python.
Namely, to retrieve the Platform Tools archive for the computer's OS and extract it to a directory of my choosing, updating existing installations if necessary.

Until I can dedicate time to actually code it, see "how_it_will_work.txt" for an overview of the desired script functionality.
