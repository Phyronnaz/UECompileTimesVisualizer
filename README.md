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
  * Find the following line: `Log.TraceInformation("{0}", CompletedAction.LogLines[LineIdx]);` (should be around line 198) and replace it by `Log.TraceLog("{0}", CompletedAction.LogLines[LineIdx]);`
  * Rebuild the solution (will only rebuild UBT in a launcher build)
* Once the build is finished, copy `Engine\Programs\UnrealBuildTool\Log.txt` next to **main.py**
* Run **main.py** with python
* It'll create 3 csv: *result_includes.csv*, *result_functions.csv*, *result_classes.csv*. You can open those in [wiztree](https://antibody-software.com/web/software/software/wiztree-finds-the-files-and-folders-using-the-most-disk-space-on-your-hard-drive/)
* 1MB = 1s

## Includes
See which includes are included by your files, and how long they take to compile. Surprisingly the file itself is often a really small portion of the total compile time. Can help you decide if it's worth moving the functions definitions to a cpp.
![](https://i.imgur.com/XtHL6Ze.png)

## Classes
See which classes are compiled in your files, and how long it took. Here too the compiler is probably spending most of its time compiling headers classes.
![](https://i.imgur.com/oPjaMpt.png)

## Functions
See which functions are compiled in your files, and how long it took. Can help determining which function to put between `PRAGMA_DISABLE_OPTIMIZATION` / `PRAGMA_ENABLE_OPTIMIZATION`
![](https://i.imgur.com/ICrtPfJ.png)
