# UnrealIncludesAnalysis

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

![](https://i.imgur.com/oPjaMpt.png)
![](https://i.imgur.com/XtHL6Ze.png)
![](https://i.imgur.com/ICrtPfJ.png)
