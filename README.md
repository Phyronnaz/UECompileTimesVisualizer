# Unreal Engine & MSVC Compile Times Visualizer

**Note: as this is using a disk visualizer as output, the following convention is used:**

**1MB = 1s | 1B = 1 micro second**

Forum thread: https://forums.unrealengine.com/community/community-content-tools-and-tutorials/1572444-c-compile-times-visualizer

## What is this
It's a frontend for the msvc timing output log. With it you'll be able to see which function takes time to compile, which headers are included by your files and how expensive they are...

Basically if you want to speed up your compilation in UE or in a project using MSVC this should help a lot :)

## Usage

### Unreal Engine

* Copy **BuildConfiguration.xml** to `%appdata%\Unreal Engine\UnrealBuildTool\BuildConfiguration.xml`, or if your already have one add `<bPrintToolChainTimingInfo>true</bPrintToolChainTimingInfo>` to the `BuildConfiguration` section
 **Note**: Disabling Unity build is recommended to have a better log
* Build your solution (the output should be spammed with log)
* VS might crash because of that. If it happens, you can edit UBT to fix it (works even without a source build!):
  * Open `Engine\Source\Programs\UnrealBuildTool\UnrealBuildTool.csproj`
  * Open `System\ParallelExecutor.cs`
  * Find the following line: `Log.TraceInformation("{0}", CompletedAction.LogLines[LineIdx]);` (should be around line 198) and replace it by
```c#
var Line = CompletedAction.LogLines[LineIdx];
if (Line.Contains(" error") || Line.Contains(" warning") || Line.Contains(" note"))
{
    Log.TraceInformation("{0}", Line);
}
else
{
    Log.TraceLog("{0}", Line);
}
```
*
  * Rebuild the solution (will only rebuild UBT in a launcher build)
  * Note: some errors/warnings might not be shown with this hack. You should change it back once you're done testing 
* Once the build is finished, copy `Engine\Programs\UnrealBuildTool\Log.txt` next to **main.py**
* Run **main.py** with python
* It'll create 3 csv: *result_includes.csv*, *result_functions.csv*, *result_classes.csv*. You can open those in [wiztree](https://antibody-software.com/web/software/software/wiztree-finds-the-files-and-folders-using-the-most-disk-space-on-your-hard-drive/)
* 1MB = 1s

### MSVC

* Add the following arguments to the **C/C++ Command Line** option in your project settings: `/Bt+ /d2cgsummary /d1reportTime`
* Add the following arguments to the **Linker Command Line** option in your project settings: `/time+`
* Rebuild your solution. The output should be spammed with log
* Find your build log file. For me it was under `MyProject/MyProject/Debug/MyProject.log`
* Copy it next to the **main.py** and rename it to `Log.txt`
* Run **main.py** with python
* It'll create 3 csv: *result_includes.csv*, *result_functions.csv*, *result_classes.csv*. You can open those in [wiztree](https://antibody-software.com/web/software/software/wiztree-finds-the-files-and-folders-using-the-most-disk-space-on-your-hard-drive/)
* 1MB = 1s

### Script args

First arg: log file, defaults to `Log.txt`

Second arg: destination, defaults to `result`

## Outputs

To correctly understand the meaning of the following sections, you might want to read [this](https://blogs.msdn.microsoft.com/vcblog/2018/01/04/visual-studio-2017-throughput-improvements-and-advice/) 

### Most included files

The script will print the headers and the number of times they were included. This can be used to decide which headers should go in a PCH.

### Includes
See which headers are included by your files, and how long they took to include.
![](https://i.imgur.com/XtHL6Ze.png)

### Classes
See which classes are compiled in your files, and how long it took.
![](https://i.imgur.com/oPjaMpt.png)

### Functions
See which functions are compiled in your files, and how long it took.
![](https://i.imgur.com/ICrtPfJ.png)
