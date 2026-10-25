import ghidra.app.script.GhidraScript;
import ghidra.app.util.PseudoDisassembler;
import java.io.*;
public class DecodeQB extends GhidraScript {
 public void run() throws Exception {
  var out=new File(getScriptArgs()[0]);
  var mem=currentProgram.getMemory();var base=toAddr("1000:0000");
  var dis=new PseudoDisassembler(currentProgram);
  try(var w=new PrintWriter(new File(out,"qb-listing.txt"))){
   int pos=0x30;
   while(pos<0x2650){
    var a=base.add(pos);int op=mem.getByte(a)&255;int num=mem.getByte(a.add(1))&255;
    if(op==0xcd && num>=0x3d && num<=0x3f){
     w.printf("%s  QB_%02x_%02x   ; raw %02x %02x %02x%n",a,num,mem.getByte(a.add(2))&255,mem.getByte(a.add(2))&255,mem.getByte(a.add(3))&255,mem.getByte(a.add(4))&255);int selector=mem.getByte(a.add(2))&255;
     int extra=(num==0x3f && (selector==0x71 || selector==0x95 || selector==0xb5))?1:((num==0x3f && selector==0xb7)?2:0);
     if(extra>0) {w.print("    INLINE ");for(int j=0;j<extra;j++)w.printf("%02x ",mem.getByte(a.add(5+j))&255);w.println();}
     pos+=5+extra;continue;
    }
    try{var i=dis.disassemble(a);if(i==null){pos++;continue;}w.println(a+"  "+i);pos+=i.getLength();}catch(Exception e){w.println(a+" ERROR "+e);pos++;}
   }
  }
  try(var w=new PrintWriter(new File(out,"data-words.txt"))){
   var b=toAddr("1279:0000");
   for(int i=0;i<0x1d90;i+=2)w.printf("%04x %04x%n",i,mem.getShort(b.add(i))&65535);
  }
 }
}
