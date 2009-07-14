//Args
var args = WScript.Arguments;
var progName = args(0);
var progPath = args(1);
var varsFile = progPath + "\\" + progName + "Vars.bat";
var fso, tf;
fso = new ActiveXObject("Scripting.FileSystemObject");
WScript.Echo("Writting " + varsFile);
tf = fso.CreateTextFile(varsFile, true);

//Write out the vars bat file
tf.WriteLine("@echo off");
tf.WriteLine("rem Set the current environment to have " + progPath + " in the path");
tf.WriteLine("echo Putting " + progName +" in the current PATH environment variable.");
tf.WriteLine("echo All done...");
tf.WriteLine("set PATH="+progPath+";%PATH%");
tf.Close();

tf = fso.CreateTextFile(progPath + "\\" + progName + "CommandPrompt.bat", true);
//Write out the cmd bat file
tf.WriteLine("@echo off");
tf.WriteLine("%COMSPEC% /k  \"" + varsFile + "\"");
tf.Close();

