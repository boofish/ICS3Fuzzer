## Preface

Our instrumentation is based on DynamoRIO & WinAFL.
Here, we express our sincere thanks to the authors & developers of DynamoRIO and WinAFL. 

## Compiling the project

To run the fuzzing process, this step is `NOT` necessary.

+ Prepare the DynamoRIO framework
Before compile the project, 
we need to download&install DynamoRIO framework, 
which can be seen from https://github.com/DynamoRIO/dynamorio

+ Preparing the compiler

I used the Visual Studio 2015 for this. 

+ Generating the DLL for instrumentation  

Once everything is OK, we can compile the project and generate the dll file.

```
mkdir build
cd build
cmake -DDynamoRIO_DIR=C:\Users\xxx\Documents\Test\DynamoRIO-Windows-7.1.0-1\cmake   ..
cmake --build  . --config  Release
```
Note that the path `C:\Users\xxx\Documents\Test\DynamoRIO-Windows-7.1.0-1\cmake` is your DynamoRIO environment.




