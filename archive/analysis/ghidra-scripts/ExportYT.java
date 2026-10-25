import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.mem.*;
import java.io.*;
public class ExportYT extends GhidraScript {
 public void run() throws Exception {
  File out = new File(getScriptArgs()[0]); out.mkdirs();
  try (PrintWriter w=new PrintWriter(new File(out,"program.txt"))) {
   w.println(currentProgram.getLanguageID());
   for(MemoryBlock b:currentProgram.getMemory().getBlocks()) w.println(b.getName()+" "+b.getStart()+" - "+b.getEnd());
   for(var s:currentProgram.getSymbolTable().getExternalEntryPointIterator()) w.println("ENTRY "+s);
  }
  try(PrintWriter w=new PrintWriter(new File(out,"listing.txt"))) {
   var it=currentProgram.getListing().getCodeUnits(true);
   while(it.hasNext()){var c=it.next();w.println(c.getAddress()+"  "+c.toString());}
  }
  DecompInterface d=new DecompInterface(); d.openProgram(currentProgram);
  try(PrintWriter w=new PrintWriter(new File(out,"decompiled.c"))) {
   var it=currentProgram.getFunctionManager().getFunctions(true);
   while(it.hasNext()){var f=it.next();w.println("\n/* "+f.getEntryPoint()+" "+f.getName()+" */");var r=d.decompileFunction(f,30,monitor);if(r.decompileCompleted())w.println(r.getDecompiledFunction().getC());else w.println("/* "+r.getErrorMessage()+" */");}
  } finally {d.dispose();}
 }
}
