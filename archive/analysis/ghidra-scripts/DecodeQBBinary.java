import ghidra.app.script.GhidraScript;
import ghidra.app.util.PseudoDisassembler;
import java.io.*;
public class DecodeQBBinary extends GhidraScript {
 public void run() throws Exception {
  var out=new File(getScriptArgs()[0]);out.mkdirs();int end=Integer.decode(getScriptArgs()[1]);
  var mem=currentProgram.getMemory();var base=toAddr(getScriptArgs().length>2?getScriptArgs()[2]:"1000:0000");var dis=new PseudoDisassembler(currentProgram);int runtimeLen=getScriptArgs().length>3?Integer.decode(getScriptArgs()[3]):5;
  currentProgram.getProgramContext().setValue(currentProgram.getRegister("CS"),base,base.add(end-1),new java.math.BigInteger(getScriptArgs().length>2?getScriptArgs()[2].split(":")[0]:"1000",16));
  try(var w=new PrintWriter(new File(out,"qb-listing.txt"))){
   int pos=0x30;
   while(pos<end){
    var a=base.add(pos);int op=mem.getByte(a)&255;int num=mem.getByte(a.add(1))&255;
    if(op==0xcd && num>=0x3d && num<=0x3f){
     int selector=mem.getByte(a.add(2))&255;
     w.printf("%s  QB_%02x_%02x%n",a,num,selector);
     int extra=(num==0x3f && (selector==0x71 || selector==0x72 || selector==0x85 || selector==0x86 || selector==0x8e || selector==0x96 || selector==0x95 || selector==0x9d || selector==0xa5 || selector==0xa6 || selector==0x4f || selector==0x50 || selector==0x51 || selector==0xb5))?1:((num==0x3f && (selector==0xb7 || selector==0x58))?2:0);
     if(extra>0){w.print("    INLINE ");for(int j=0;j<extra;j++)w.printf("%02x ",mem.getByte(a.add(runtimeLen+j))&255);w.println();}
     pos+=runtimeLen+extra;continue;
    }
    try{var i=dis.disassemble(a);if(i==null){w.println(a+" UNKNOWN");pos++;continue;}w.println(a+"  "+i);pos+=i.getLength();}catch(Exception e){w.println(a+" ERROR "+e);pos++;}
   }
  }
 }
}
