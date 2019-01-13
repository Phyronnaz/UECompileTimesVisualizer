# Unreal Engine Compilation Times Visualizer

## What is this
It's a frontend for the msvc timing output log. With it you'll be able to see which function takes time to compile, which headers are included by your files and how expensive they are...

Basically if you want to speed up your compilation in UE this should help a lot :)

## Quick start

* Copy **BuildConfiguration.xml** to `%appdata%\Unreal Engine\UnrealBuildTool\BuildConfiguration.xml`
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
  * Rebuild the solution (will only rebuild UBT in a launcher build)
  * Note: some errors/warnings might not be shown with this hack. You should change it back once you're done testing 
* Once the build is finished, copy `Engine\Programs\UnrealBuildTool\Log.txt` next to **main.py**
* Run **main.py** with python
* It'll create 3 csv: *result_includes.csv*, *result_functions.csv*, *result_classes.csv*. You can open those in [wiztree](https://antibody-software.com/web/software/software/wiztree-finds-the-files-and-folders-using-the-most-disk-space-on-your-hard-drive/)
* 1MB = 1s

## Most included files

The script will print the headers and the number of times they were included. This can be used to decide which headers should go in a PCH.

## Includes
See which headers are included by your files, and how long they take to compile. Surprisingly the file itself is often a really small portion of the total compile time. Can help you decide if it's worth moving the functions definitions to a cpp.
![](https://i.imgur.com/XtHL6Ze.png)

## Classes
See which classes are compiled in your files, and how long it took. Here too the compiler is probably spending most of its time compiling classes from included headers.
![](https://i.imgur.com/oPjaMpt.png)

## Functions
See which functions are compiled in your files, and how long it took. Can help determining which function to put between `PRAGMA_DISABLE_OPTIMIZATION` / `PRAGMA_ENABLE_OPTIMIZATION`
![](https://i.imgur.com/ICrtPfJ.png)
