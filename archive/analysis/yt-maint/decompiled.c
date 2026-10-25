
/* 1000:0030 entry */

/* WARNING: Instruction at (ram,0x00010115) overlaps instruction at (ram,0x00010114)
    */
/* WARNING: Control flow encountered bad instruction data */
/* WARNING: Stack frame is not setup normally: Input value of stackpointer is not used */
/* WARNING: This function may have set the stack pointer */

void entry(void)

{
  byte *pbVar1;
  char *pcVar2;
  uint *puVar3;
  code *pcVar4;
  undefined1 *puVar5;
  byte bVar6;
  uint uVar7;
  undefined2 uVar8;
  char cVar10;
  char cVar9;
  byte extraout_DL;
  undefined2 extraout_DX;
  undefined2 extraout_DX_00;
  int extraout_DX_01;
  uint extraout_DX_02;
  uint uVar11;
  int extraout_DX_03;
  uint extraout_DX_04;
  uint extraout_DX_05;
  uint extraout_DX_06;
  int extraout_DX_07;
  int in_BX;
  int iVar12;
  int iVar13;
  undefined2 *puVar14;
  undefined1 *puVar15;
  undefined1 *puVar16;
  undefined1 *puVar18;
  undefined2 *puVar17;
  undefined2 unaff_BP;
  undefined1 *unaff_SI;
  byte *pbVar19;
  undefined2 unaff_DI;
  undefined2 unaff_DS;
  byte in_CF;
  byte bVar20;
  bool bVar21;
  byte in_AF;
  undefined1 uVar22;
  char cVar23;
  char cVar24;
  undefined4 uVar25;
  
  DAT_2252_13fe = 0x1000;
  DAT_2252_13fc = 0x35;
  FUN_19e3_0000();
  DAT_2252_13fe = 0x19e3;
  DAT_2252_13fc = 0x3a;
  FUN_18a6_01c0();
  pcVar4 = (code *)swi(0x3e);
  bVar6 = (*pcVar4)();
  *(uint *)(unaff_SI + in_BX + -0x6570) = *(int *)(unaff_SI + in_BX + -0x6570) + 0x73 + (uint)in_CF;
  pbVar1 = unaff_SI + in_BX;
  bVar20 = *pbVar1;
  *pbVar1 = *pbVar1 + bVar6;
  pcVar2 = (char *)0xfc07;
  *pcVar2 = *pcVar2 + (char)in_BX + CARRY1(bVar20,bVar6);
  uVar22 = *pcVar2 < '\0';
  pcVar4 = (code *)swi(0x3f);
  (*pcVar4)();
  pcVar4 = (code *)swi(0x3f);
  (*pcVar4)();
  out(*unaff_SI,extraout_DX);
  pcVar4 = (code *)swi(0x3e);
  (*pcVar4)();
  if (!(bool)uVar22) {
                    /* WARNING: Bad instruction - Truncating control flow here */
    halt_baddata();
  }
  pcVar4 = (code *)swi(0x3f);
  (*pcVar4)();
  puVar14 = (undefined2 *)0x9090;
  iVar12 = 0x7e64;
  pcVar4 = (code *)swi(0x3f);
  (*pcVar4)();
  pbVar19 = unaff_SI + 2;
  out(unaff_SI[1],extraout_DX_00);
  pcVar4 = (code *)swi(0x3e);
  (*pcVar4)();
  if (!(bool)uVar22) {
                    /* WARNING: Bad instruction - Truncating control flow here */
    halt_baddata();
  }
  pcVar4 = (code *)swi(0x3e);
  (*pcVar4)();
  *(int *)(pbVar19 + iVar12 + -0x1670) = *(int *)(pbVar19 + iVar12 + -0x1670) + extraout_DX_01;
  uVar8 = *puVar14;
  *puVar14 = unaff_DI;
  pcVar4 = (code *)swi(0x3f);
  (*pcVar4)();
  puVar15 = (undefined1 *)((int)puVar14 + -2);
  *(undefined2 *)((int)puVar14 + -2) = uVar8;
  pcVar4 = (code *)swi(0x3d);
  (*pcVar4)();
  pcVar4 = (code *)swi(0x3f);
  (*pcVar4)();
  iVar12 = 0x1a;
  pcVar4 = (code *)swi(0x3e);
  (*pcVar4)();
  *(uint *)(pbVar19 + iVar12 + -0x4470) = *(uint *)(pbVar19 + iVar12 + -0x4470) | extraout_DX_02;
  pcVar4 = (code *)swi(0x3e);
  uVar7 = (*pcVar4)();
  pbVar19[iVar12 + -0x4470] = pbVar19[iVar12 + -0x4470] & extraout_DL;
  puVar3 = (uint *)(pbVar19 + iVar12);
  bVar20 = CARRY2(*puVar3,uVar7);
  *puVar3 = *puVar3 + uVar7;
  pcVar4 = (code *)swi(0x3e);
  (*pcVar4)();
  puVar16 = puVar15 + -2;
  *(undefined2 *)(puVar15 + -2) = unaff_DS;
  pcVar4 = (code *)swi(0x3f);
  (*pcVar4)();
  pcVar4 = (code *)swi(0x3f);
  (*pcVar4)();
  pcVar4 = (code *)swi(0x3f);
  (*pcVar4)();
  pcVar4 = (code *)swi(0x3f);
  (*pcVar4)();
  pcVar4 = (code *)swi(0x3f);
  (*pcVar4)();
  pcVar4 = (code *)swi(0x3f);
  (*pcVar4)();
  pcVar4 = (code *)swi(0x3f);
  (*pcVar4)();
  pcVar4 = (code *)swi(0x3f);
  (*pcVar4)();
  pcVar4 = (code *)swi(0x3f);
  (*pcVar4)();
  pcVar4 = (code *)swi(0x3f);
  (*pcVar4)();
  pcVar4 = (code *)swi(0x3f);
  (*pcVar4)();
  pcVar4 = (code *)swi(0x3f);
  (*pcVar4)();
  pcVar4 = (code *)swi(0x3f);
  (*pcVar4)();
  pcVar4 = (code *)swi(0x3f);
  (*pcVar4)();
code_r0x00010117:
  pcVar4 = (code *)swi(0x3f);
  (*pcVar4)();
  pcVar4 = (code *)swi(0x3f);
  (*pcVar4)();
  pcVar4 = (code *)swi(0x3f);
  (*pcVar4)();
  pcVar4 = (code *)swi(0x3f);
  (*pcVar4)();
  puVar5 = puVar16;
LAB_1000_0134:
  puVar16 = puVar5;
  pcVar4 = (code *)swi(0x3f);
  (*pcVar4)();
  pcVar4 = (code *)swi(0x3f);
  (*pcVar4)();
LAB_1000_0144:
  pcVar4 = (code *)swi(0x3f);
  (*pcVar4)();
  pcVar4 = (code *)swi(0x3f);
  (*pcVar4)();
LAB_1000_0154:
  pcVar4 = (code *)swi(0x3f);
  (*pcVar4)();
  pcVar4 = (code *)swi(0x3f);
  (*pcVar4)();
  do {
    iVar12 = 0x18c4;
    pcVar4 = (code *)swi(0x3f);
    (*pcVar4)();
    while( true ) {
      pcVar4 = (code *)swi(0x3e);
      (*pcVar4)();
      iVar13 = 0x1868;
      pcVar4 = (code *)swi(0x3d);
      uVar25 = (*pcVar4)();
      pbVar1 = pbVar19 + iVar13 + -0x3270;
      *(uint *)pbVar1 = (*(int *)pbVar1 - (int)((ulong)uVar25 >> 0x10)) - (uint)bVar20;
      bVar20 = 9 < ((byte)uVar25 & 0xf) | in_AF;
      uVar7 = CONCAT11((char)((ulong)uVar25 >> 8) - bVar20,(byte)uVar25 + bVar20 * -6) & 0xff0f;
      in_AF = bVar20;
      if (!(bool)bVar20 && *(int *)pbVar1 != 0) goto code_r0x00010117;
      pcVar4 = (code *)swi(0x3d);
      uVar25 = (*pcVar4)();
      uVar11 = *(uint *)(pbVar19 + uVar7 + 0xba90);
      *(int *)(puVar16 + -2) = (int)uVar25;
      *(int *)(puVar16 + -4) = iVar12;
      *(uint *)(puVar16 + -6) = (uint)((ulong)uVar25 >> 0x10) | uVar11;
      *(uint *)(puVar16 + -8) = uVar7;
      *(undefined1 **)(puVar16 + -10) = puVar16;
      *(undefined2 *)(puVar16 + -0xc) = unaff_BP;
      *(byte **)(puVar16 + -0xe) = pbVar19;
      *(undefined2 *)(puVar16 + -0x10) = unaff_DI;
      bVar20 = 9 < ((byte)uVar25 & 0xf) | bVar20;
      unaff_DI = *(undefined2 *)(puVar16 + -0x10);
      pbVar19 = *(byte **)(puVar16 + -0xe);
      unaff_BP = *(undefined2 *)(puVar16 + -0xc);
      uVar8 = *(undefined2 *)(puVar16 + -4);
      iVar12 = 0x186c;
      pcVar4 = (code *)swi(0x3d);
      bVar6 = bVar20;
      uVar25 = (*pcVar4)();
      uVar11 = (uint)((ulong)uVar25 >> 0x10);
      puVar3 = (uint *)(pbVar19 + iVar12 + -0x4070);
      uVar7 = *puVar3 - uVar11;
      bVar21 = *puVar3 < uVar11 || uVar7 < bVar20;
      *puVar3 = uVar7 - bVar20;
      puVar17 = (undefined2 *)(puVar16 + -2);
      puVar18 = puVar16 + -2;
      puVar16 = puVar16 + -2;
      *puVar17 = (int)uVar25;
      cVar24 = (char)uVar8;
      cVar10 = (char)((uint)uVar8 >> 8);
      cVar23 = cVar10 - cVar24;
      cVar9 = cVar23 - bVar21;
      iVar12 = CONCAT11(cVar9,cVar24);
      bVar20 = 9 < ((byte)uVar25 & 0xf) | bVar6;
      puVar5 = puVar18;
      in_AF = bVar20;
      if ((SBORROW1(cVar10,cVar24) != SBORROW1(cVar23,bVar21)) == cVar9 < '\0') goto LAB_1000_0134;
      iVar13 = 0x1870;
      pcVar4 = (code *)swi(0x3d);
      (*pcVar4)();
      *(uint *)(pbVar19 + iVar13 + -0x4070) =
           (*(int *)(pbVar19 + iVar13 + -0x4070) - extraout_DX_03) - (uint)bVar20;
      pbVar1 = pbVar19;
      bVar6 = (byte)iVar13;
      bVar20 = *pbVar1 < bVar6;
      cVar24 = SBORROW1(*pbVar1,bVar6);
      *pbVar1 = *pbVar1 - bVar6;
      cVar23 = (char)*pbVar1 < '\0';
      pcVar4 = (code *)swi(0x3f);
      (*pcVar4)();
      if (cVar24 == cVar23) goto LAB_1000_0144;
      iVar13 = 0x1874;
      pcVar4 = (code *)swi(0x3d);
      (*pcVar4)();
      puVar3 = (uint *)(pbVar19 + iVar13 + -0x4070);
      uVar7 = (uint)bVar20;
      uVar11 = *puVar3 - extraout_DX_04;
      bVar20 = *puVar3 < extraout_DX_04 || uVar11 < uVar7;
      cVar24 = SBORROW2(*puVar3,extraout_DX_04) != SBORROW2(uVar11,uVar7);
      *puVar3 = uVar11 - uVar7;
      cVar23 = (int)*puVar3 < 0;
      pcVar4 = (code *)swi(0x3f);
      (*pcVar4)();
      if (cVar24 == cVar23) goto LAB_1000_0154;
      iVar13 = 0x1878;
      pcVar4 = (code *)swi(0x3d);
      (*pcVar4)();
      puVar3 = (uint *)(pbVar19 + iVar13 + -0x4070);
      uVar7 = (uint)bVar20;
      uVar11 = *puVar3 - extraout_DX_05;
      bVar20 = *puVar3 < extraout_DX_05 || uVar11 < uVar7;
      cVar24 = SBORROW2(*puVar3,extraout_DX_05) != SBORROW2(uVar11,uVar7);
      *puVar3 = uVar11 - uVar7;
      cVar23 = (int)*puVar3 < 0;
      iVar12 = iVar12 + -1;
      if (iVar12 != 0 && *puVar3 != 0) goto LAB_1000_01e8;
      pcVar4 = (code *)swi(0x3f);
      (*pcVar4)();
      if (cVar24 == cVar23) break;
      iVar13 = 0x187c;
      pcVar4 = (code *)swi(0x3d);
      (*pcVar4)();
      puVar3 = (uint *)(pbVar19 + iVar13 + -0x4070);
      uVar7 = (uint)bVar20;
      uVar11 = *puVar3 - extraout_DX_06;
      bVar20 = *puVar3 < extraout_DX_06 || uVar11 < uVar7;
      cVar24 = SBORROW2(*puVar3,extraout_DX_06) != SBORROW2(uVar11,uVar7);
      *puVar3 = uVar11 - uVar7;
      cVar23 = (int)*puVar3 < 0;
      in(0x18);
      pcVar4 = (code *)swi(0x3f);
      (*pcVar4)();
      if (cVar24 != cVar23) {
        iVar13 = 0x1894;
LAB_1000_01e8:
        pcVar4 = (code *)swi(0x3d);
        (*pcVar4)();
        *(uint *)(pbVar19 + iVar13 + -0x4070) =
             (*(int *)(pbVar19 + iVar13 + -0x4070) - extraout_DX_07) - (uint)bVar20;
        return;
      }
    }
  } while( true );
}



/* 18a6:0183 FUN_18a6_0183 */

int __cdecl16near FUN_18a6_0183(void)

{
  undefined2 in_AX;
  int in_CX;
  undefined2 in_DX;
  int unaff_ES;
  
  *(undefined2 *)0x0 = in_AX;
  *(int *)0x2 = in_CX;
  *(int *)0x4 = in_CX << 4;
  *(uint *)0x6 = (((uint)(in_CX < 0) << 1 | (uint)(in_CX << 1 < 0)) << 1 | (uint)(in_CX << 2 < 0))
                 << 1 | (uint)(in_CX << 3 < 0);
  *(undefined2 *)0x8 = 0;
  *(undefined2 *)0xa = in_DX;
  *(undefined2 *)0xc = 0;
  *(undefined2 *)0xe = 0;
  return unaff_ES + in_CX + 1;
}



/* 18a6:01c0 FUN_18a6_01c0 */

void __cdecl16far FUN_18a6_01c0(void)

{
  return;
}



/* 19e3:0000 FUN_19e3_0000 */

/* WARNING: Unable to track spacebase fully for stack */
/* WARNING: This function may have set the stack pointer */
/* WARNING: Removing unreachable block (ram,0x00019f97) */
/* WARNING: Removing unreachable block (ram,0x00019f9c) */
/* WARNING: Removing unreachable block (ram,0x00019fa0) */
/* WARNING: Removing unreachable block (ram,0x00019fa3) */
/* WARNING: Removing unreachable block (ram,0x00019fa8) */
/* WARNING: Removing unreachable block (ram,0x00019fab) */
/* WARNING: Removing unreachable block (ram,0x00019fbf) */
/* WARNING: Removing unreachable block (ram,0x00019fc5) */
/* WARNING: Removing unreachable block (ram,0x00019fd1) */
/* WARNING: Removing unreachable block (ram,0x00019fe8) */
/* WARNING: Removing unreachable block (ram,0x00019feb) */
/* WARNING: Removing unreachable block (ram,0x00019ff3) */
/* WARNING: Removing unreachable block (ram,0x00019ff6) */
/* WARNING: Removing unreachable block (ram,0x0001a001) */
/* WARNING: Removing unreachable block (ram,0x0001a002) */
/* WARNING: Removing unreachable block (ram,0x0001a00f) */
/* WARNING: Removing unreachable block (ram,0x0001a012) */
/* WARNING: Removing unreachable block (ram,0x0001a01c) */
/* WARNING: Removing unreachable block (ram,0x0001a01f) */
/* WARNING: Removing unreachable block (ram,0x0001a043) */
/* WARNING: Removing unreachable block (ram,0x0001a046) */
/* WARNING: Removing unreachable block (ram,0x0001a059) */
/* WARNING: Removing unreachable block (ram,0x0001a05c) */
/* WARNING: Removing unreachable block (ram,0x0001a087) */
/* WARNING: Removing unreachable block (ram,0x0001a08a) */
/* WARNING: Removing unreachable block (ram,0x0001a0ab) */
/* WARNING: Removing unreachable block (ram,0x0001a0ae) */
/* WARNING: Removing unreachable block (ram,0x0001a0b2) */
/* WARNING: Removing unreachable block (ram,0x0001a0b5) */
/* WARNING: Removing unreachable block (ram,0x0001a0db) */
/* WARNING: Removing unreachable block (ram,0x0001a0de) */
/* WARNING: Removing unreachable block (ram,0x0001a0f9) */
/* WARNING: Removing unreachable block (ram,0x0001a0fc) */
/* WARNING: Removing unreachable block (ram,0x0001a100) */
/* WARNING: Removing unreachable block (ram,0x0001a103) */
/* WARNING: Removing unreachable block (ram,0x0001a144) */
/* WARNING: Removing unreachable block (ram,0x0001a147) */
/* WARNING: Removing unreachable block (ram,0x0001a15c) */
/* WARNING: Removing unreachable block (ram,0x0001a15f) */
/* WARNING: Removing unreachable block (ram,0x0001a163) */
/* WARNING: Removing unreachable block (ram,0x0001a166) */
/* WARNING: Removing unreachable block (ram,0x0001a19f) */
/* WARNING: Removing unreachable block (ram,0x0001a1a2) */
/* WARNING: Removing unreachable block (ram,0x0001a1bb) */
/* WARNING: Removing unreachable block (ram,0x0001a1be) */
/* WARNING: Removing unreachable block (ram,0x0001a1c1) */
/* WARNING: Removing unreachable block (ram,0x0001a1ce) */
/* WARNING: Removing unreachable block (ram,0x0001a1d1) */
/* WARNING: Removing unreachable block (ram,0x0001a1d5) */
/* WARNING: Removing unreachable block (ram,0x0001a1d8) */
/* WARNING: Removing unreachable block (ram,0x0001a1e1) */
/* WARNING: Removing unreachable block (ram,0x0001a1f9) */
/* WARNING: Removing unreachable block (ram,0x0001a1f2) */
/* WARNING: Removing unreachable block (ram,0x0001a200) */
/* WARNING: Removing unreachable block (ram,0x0001a203) */
/* WARNING: Removing unreachable block (ram,0x0001a209) */
/* WARNING: Removing unreachable block (ram,0x0001a213) */
/* WARNING: Removing unreachable block (ram,0x0001a216) */
/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */
/* WARNING: Restarted to delay deadcode elimination for space: ram */

undefined2 __cdecl16far FUN_19e3_0000(void)

{
  undefined1 *puVar1;
  char *pcVar2;
  char cVar3;
  undefined2 *puVar4;
  char *pcVar5;
  undefined2 *puVar6;
  code *pcVar7;
  byte bVar8;
  int iVar9;
  undefined2 uVar10;
  int iVar11;
  int iVar12;
  uint uVar13;
  undefined1 *puVar14;
  undefined2 *puVar15;
  char *pcVar16;
  undefined2 *puVar17;
  char *pcVar18;
  undefined2 unaff_ES;
  int unaff_SS;
  undefined1 uVar19;
  bool bVar20;
  undefined2 in_stack_00000002;
  undefined2 in_stack_0000000e;
  
  iVar12 = *(int *)0x0;
  DAT_19e3_086e = (undefined1)iVar12;
  if ((iVar12 != 0x6d62) && (iVar12 != 0x7a62)) {
    uVar10 = FUN_19e3_06c7();
    return uVar10;
  }
  pcVar7 = (code *)swi(0x21);
  bVar8 = (*pcVar7)();
  if (bVar8 < 2) {
    uVar10 = FUN_19e3_06cc();
    return uVar10;
  }
  DAT_19e3_087b = *(uint *)0x2;
  DAT_19e3_0879 = *(undefined2 *)0x2c;
  DAT_19e3_0877 = 0x18e6;
  DAT_19e3_087d = 0x2a6c;
  puVar17 = (undefined2 *)0x0;
  puVar15 = (undefined2 *)0x0;
  DAT_19e3_087f = unaff_ES;
  for (iVar12 = 0x900; uVar10 = DAT_19e3_0879, iVar12 != 0; iVar12 = iVar12 + -1) {
    puVar6 = puVar17;
    puVar17 = puVar17 + 1;
    puVar4 = puVar15;
    puVar15 = puVar15 + 1;
    *puVar6 = *puVar4;
  }
  DAT_18c3_0000 = 0;
  DAT_18c3_0002 = 0;
  DAT_18c3_0004 = 0;
  pcVar16 = (char *)0x0;
  pcVar5 = (char *)0x0;
  do {
    do {
      pcVar18 = pcVar5;
      pcVar2 = pcVar16;
      pcVar16 = pcVar16 + 1;
      cVar3 = *pcVar2;
      pcVar5 = pcVar18 + 1;
      *pcVar18 = cVar3;
    } while (cVar3 != '\0');
  } while (*pcVar16 != '\0');
  pcVar5[0] = '\0';
  pcVar5[1] = '\0';
  uVar10 = 0;
  *(undefined2 *)0x0 = 7;
  *(undefined2 *)0x4 = pcVar18 + 3;
  *(undefined2 *)0x6 = 0;
  iVar12 = ((uint)(pcVar18 + 3) >> 4) + 1;
  *(int *)0x2 = iVar12;
  *(undefined2 *)0xa = 0;
  *(undefined2 *)0x8 = 0;
  *(undefined2 *)0xc = 0;
  *(undefined2 *)0xe = 0;
  DAT_19e3_087d = DAT_19e3_087d + iVar12 + 1;
  if (DAT_19e3_087b <= DAT_19e3_087d) {
    uVar10 = FUN_19e3_06c2();
    return uVar10;
  }
  FUN_19e3_049d();
  uVar19 = DAT_19e3_0853 < 0x2eb;
  DAT_19e3_086f = uVar10;
  if (DAT_19e3_0853 != 0x2eb) {
    uVar10 = FUN_19e3_06b3();
    return uVar10;
  }
  DAT_19e3_0828 = FUN_19e3_0638();
  FUN_19e3_0672();
  if ((bool)uVar19) {
    uVar10 = FUN_19e3_06b3();
    return uVar10;
  }
  if (*(char *)0x3 != '\x05') {
    uVar10 = FUN_19e3_06ad();
    return uVar10;
  }
  if (*(char *)0x4 != '\x06') {
    uVar10 = FUN_19e3_06ad();
    return uVar10;
  }
  if (*(char *)0x5 != '\0') {
    uVar10 = FUN_19e3_06ad();
    return uVar10;
  }
  bVar20 = false;
  pcVar7 = (code *)swi(0x21);
  (*pcVar7)();
  if (bVar20) {
    uVar10 = FUN_19e3_06b3();
    return uVar10;
  }
  uVar19 = CARRY2(unaff_SS + 0xe594,ram0x00010855);
  FUN_19e3_042e();
  pcVar7 = (code *)swi(0x21);
  (*pcVar7)();
  if ((bool)uVar19) {
    uVar10 = FUN_19e3_06b3();
    return uVar10;
  }
  s___Maintenance_Program_Ran_H_18c3_010a[2] = (char)DAT_1000_0828;
  s___Maintenance_Program_Ran_H_18c3_010a[3] = DAT_1000_0828._1_1_;
  DAT_18c3_0106 = DAT_1000_087f;
  uVar13 = DAT_1000_087d + 0xe594;
  iVar12 = 0x1a6c;
  s___Maintenance_Program_Ran_H_18c3_010a._0_2_ = in_stack_0000000e;
  s___Maintenance_Program_Ran_H_18c3_010a[4] = '\x04';
  s___Maintenance_Program_Ran_H_18c3_010a[5] = '\0';
  if (DAT_1000_082a != 0) {
    s___Maintenance_Program_Ran_H_18c3_010a[4] = '\x05';
    s___Maintenance_Program_Ran_H_18c3_010a[5] = '\0';
  }
  DAT_18c3_0108 = -0x6da0;
  iVar9 = DAT_1000_0877;
  while( true ) {
    puVar15 = (undefined2 *)0x0;
    puVar17 = (undefined2 *)0x0;
    DAT_18c3_0104 = 0xfff;
    if (uVar13 < 0xfff) {
      DAT_18c3_0104 = uVar13;
    }
    for (iVar11 = DAT_18c3_0104 << 3; iVar11 != 0; iVar11 = iVar11 + -1) {
      puVar6 = puVar17;
      puVar17 = puVar17 + 1;
      puVar4 = puVar15;
      puVar15 = puVar15 + 1;
      *puVar6 = *puVar4;
    }
    uVar13 = uVar13 - DAT_18c3_0104;
    if (uVar13 == 0) break;
    iVar12 = iVar12 + DAT_18c3_0104;
    iVar9 = iVar9 + DAT_18c3_0104;
  }
  DAT_18c3_0104 = DAT_18c3_0000;
  DAT_18c3_0102 = DAT_18c3_0002;
  DAT_18c3_0100 = DAT_18c3_0004;
  DAT_18c3_00fe = -0x74b3;
  FUN_18a6_0183();
  DAT_18c3_00fe = -0x74a7;
  FUN_18a6_0183();
  DAT_18c3_00fe = 0x18c3;
  DAT_18c3_00fc = 0x8b66;
  FUN_18a6_0183();
  puVar15 = (undefined2 *)0x0;
  for (iVar12 = 0x80; iVar9 = DAT_18c3_0106, iVar12 != 0; iVar12 = iVar12 + -1) {
    puVar4 = puVar15;
    puVar15 = puVar15 + 1;
    *puVar4 = 0;
  }
  s_Loading_players__deleting_inacti_18c3_0128[0x24] = '\a';
  s_Loading_players__deleting_inacti_18c3_0128[0x25] = '\0';
  s_Loading_players__deleting_inacti_18c3_0128[0x26] = '\x06';
  s_Loading_players__deleting_inacti_18c3_0128[0x27] = '\0';
  DAT_18c3_0184 = DAT_18c3_0100;
  DAT_18c3_0182 = DAT_18c3_0102;
  DAT_18c3_0186 = DAT_18c3_0104;
  s___Maintenance_Program_Ran_H_18c3_010a._24_2_ = DAT_18c3_00fe + *(int *)0x2;
  puVar15 = (undefined2 *)0x81;
  puVar14 = (undefined1 *)0x81;
  DAT_18c3_01a0 = *(char *)0x80;
  DAT_18c3_0106 = DAT_18c3_00fe + 1;
  for (iVar12 = (int)DAT_18c3_01a0; iVar12 != 0; iVar12 = iVar12 + -1) {
    puVar4 = puVar15;
    puVar15 = (undefined2 *)((int)puVar15 + 1);
    puVar1 = puVar14;
    puVar14 = puVar14 + 1;
    *(undefined1 *)puVar4 = *puVar1;
  }
  *puVar15 = 0;
  uVar10 = s___Maintenance_Program_Ran_H_18c3_010a._2_2_;
  iVar9 = DAT_18c3_0108;
  iVar12 = DAT_18c3_0106;
  if (s___Maintenance_Program_Ran_H_18c3_010a._4_2_ != 4) {
    s_Loading_players__deleting_inacti_18c3_0128[0x40] = '\b';
    s_Loading_players__deleting_inacti_18c3_0128[0x41] = '\0';
  }
  *(undefined2 *)(char *)(DAT_18c3_0108 + -2) = s___Maintenance_Program_Ran_H_18c3_010a._0_2_;
  *(undefined2 *)(iVar9 + -4) = 0;
  *(undefined2 *)((undefined1 *)&LAB_0000_fffa + iVar9) = uVar10;
  *(undefined2 *)(iVar9 + -8) = 7;
  return 0x18c3;
}



/* 19e3:042e FUN_19e3_042e */

void __cdecl16near FUN_19e3_042e(uint param_1)

{
  uint *puVar1;
  int *piVar2;
  uint uVar3;
  uint *puVar4;
  code *pcVar5;
  int iVar6;
  uint unaff_BP;
  uint unaff_SI;
  uint unaff_DI;
  undefined2 unaff_DS;
  bool bVar7;
  bool bVar8;
  uint in_stack_00000000;
  
  *(undefined2 *)0x871 = *(undefined2 *)0x832;
  bVar7 = false;
  pcVar5 = (code *)swi(0x21);
  (*pcVar5)();
  bVar8 = false;
  if (bVar7) {
    FUN_19e3_06b3();
    return;
  }
  do {
    pcVar5 = (code *)swi(0x21);
    (*pcVar5)();
    if (bVar8) {
      FUN_19e3_06b3();
      return;
    }
    puVar4 = (uint *)*(undefined2 *)0x873;
    uVar3 = *(uint *)0x875;
    if (uVar3 < unaff_DI) {
      bVar8 = false;
      if (uVar3 < in_stack_00000000) {
        iVar6 = uVar3 + unaff_BP;
        if (*puVar4 < unaff_DI) goto LAB_19e3_0493;
LAB_19e3_047e:
        *puVar4 = *puVar4 - unaff_DI;
        puVar1 = puVar4;
        bVar8 = CARRY2(*puVar1,unaff_SI);
        *puVar1 = *puVar1 + unaff_SI;
      }
    }
    else {
      bVar8 = false;
      if (uVar3 < param_1) {
        iVar6 = (uVar3 - unaff_DI) + 0x1a6c;
        if (unaff_DI <= *puVar4) goto LAB_19e3_047e;
LAB_19e3_0493:
        puVar1 = puVar4;
        bVar8 = CARRY2(*puVar1,unaff_BP);
        *puVar1 = *puVar1 + unaff_BP;
      }
    }
    piVar2 = (int *)0x871;
    *piVar2 = *piVar2 + -1;
    if (*piVar2 == 0) {
      return;
    }
  } while( true );
}



/* 19e3:049d FUN_19e3_049d */

void __cdecl16near FUN_19e3_049d(void)

{
  undefined2 uVar1;
  char *pcVar2;
  char *pcVar3;
  char cVar4;
  code *pcVar5;
  int in_CX;
  int iVar6;
  char extraout_DL;
  undefined2 in_DX;
  int extraout_DX;
  char *pcVar7;
  uint uVar8;
  char *unaff_SI;
  char *pcVar9;
  char *pcVar10;
  char *pcVar11;
  undefined2 unaff_DS;
  undefined2 uVar12;
  undefined1 in_CF;
  bool bVar13;
  
  *(undefined2 *)0x611 = in_DX;
  pcVar5 = (code *)swi(0x21);
  (*pcVar5)();
  if (!(bool)in_CF) goto LAB_19e3_05a6;
  if (*(int *)0x611 != 0x812) {
    pcVar7 = (char *)(extraout_DX + -1);
    do {
      pcVar7 = pcVar7 + 1;
      cVar4 = *pcVar7;
      if ((cVar4 == ':') || (cVar4 == '\\')) goto LAB_19e3_0533;
    } while (cVar4 != '\0');
  }
  uVar12 = *(undefined2 *)0x879;
  pcVar7 = (char *)0x0;
  bVar13 = true;
  do {
    iVar6 = in_CX;
    pcVar11 = unaff_SI;
    do {
      if (iVar6 == 0) break;
      iVar6 = iVar6 + -1;
      pcVar3 = pcVar7;
      pcVar7 = pcVar7 + 1;
      pcVar2 = pcVar11;
      pcVar11 = pcVar11 + 1;
      bVar13 = *pcVar2 == *pcVar3;
    } while (bVar13);
    if (bVar13) {
      uVar12 = unaff_DS;
      goto LAB_19e3_04e7;
    }
    iVar6 = 0x50;
    do {
      if (iVar6 == 0) break;
      iVar6 = iVar6 + -1;
      pcVar2 = pcVar7;
      pcVar7 = pcVar7 + 1;
    } while (*pcVar2 != '\0');
    bVar13 = *(int *)(pcVar7 + -1) == 0;
  } while (!bVar13);
  goto LAB_19e3_0533;
  while (uVar12 = unaff_DS, *pcVar9 != '\0') {
LAB_19e3_04e7:
    uVar1 = *(undefined2 *)0x879;
    pcVar11 = (char *)0x82c;
    pcVar9 = pcVar7;
    while( true ) {
      pcVar7 = pcVar9 + 1;
      cVar4 = *pcVar9;
      if ((cVar4 == ';') || (cVar4 == '\0')) break;
      pcVar2 = pcVar11;
      pcVar11 = pcVar11 + 1;
      *pcVar2 = cVar4;
      pcVar9 = pcVar7;
    }
    unaff_DS = 0x19e3;
    if ((pcVar11 != (char *)0x82c) && ((pcVar11[-1] != ':' && (pcVar11[-1] != '\\')))) {
      pcVar2 = pcVar11;
      pcVar11 = pcVar11 + 1;
      *pcVar2 = '\\';
    }
    pcVar10 = DAT_19e3_0611;
    do {
      pcVar2 = pcVar10;
      pcVar10 = pcVar10 + 1;
      cVar4 = *pcVar2;
      pcVar2 = pcVar11;
      pcVar11 = pcVar11 + 1;
      *pcVar2 = cVar4;
      in_CF = false;
    } while (cVar4 != '\0');
    pcVar5 = (code *)swi(0x21);
    (*pcVar5)();
    if (!(bool)in_CF) goto LAB_19e3_05a6;
  }
LAB_19e3_0533:
  do {
    unaff_DS = 0x19e3;
    pcVar5 = (code *)swi(0x21);
    (*pcVar5)();
    do {
      pcVar5 = (code *)swi(0x21);
      (*pcVar5)();
    } while (extraout_DL != '\0');
    pcVar5 = (code *)swi(0x21);
    (*pcVar5)();
    DAT_19e3_082c = 0x40;
    pcVar5 = (code *)swi(0x21);
    (*pcVar5)();
    pcVar5 = (code *)swi(0x21);
    (*pcVar5)();
    uVar8 = (uint)DAT_19e3_082d;
    *(undefined1 *)(uVar8 + 0x82e) = 0;
    bVar13 = DAT_19e3_0611 < (char *)0x812;
    if (DAT_19e3_0611 == (char *)0x812) {
      if ((*(char *)(uVar8 + 0x82d) != ':') && (*(char *)(uVar8 + 0x82d) != '\\')) {
        *(undefined1 *)(uVar8 + 0x82e) = 0x5c;
        uVar8 = uVar8 + 1;
      }
      pcVar11 = (char *)(uVar8 + 0x82e);
      pcVar7 = DAT_19e3_0611;
      do {
        pcVar2 = pcVar7;
        pcVar7 = pcVar7 + 1;
        cVar4 = *pcVar2;
        pcVar2 = pcVar11;
        pcVar11 = pcVar11 + 1;
        *pcVar2 = cVar4;
        bVar13 = false;
      } while (cVar4 != '\0');
    }
    pcVar5 = (code *)swi(0x21);
    (*pcVar5)();
    in_CF = 0;
  } while (bVar13);
LAB_19e3_05a6:
  pcVar5 = (code *)swi(0x21);
  (*pcVar5)();
  if ((bool)in_CF) {
    FUN_19e3_06b3();
    return;
  }
  if (*(int *)0x82c != 0x5a4d) {
    FUN_19e3_06b3();
    return;
  }
  bVar13 = false;
  pcVar5 = (code *)swi(0x21);
  (*pcVar5)();
  if (bVar13) {
    FUN_19e3_06b3();
    return;
  }
  pcVar5 = (code *)swi(0x21);
  (*pcVar5)();
  if (bVar13) {
    FUN_19e3_06b3();
    return;
  }
  pcVar5 = (code *)swi(0x21);
  (*pcVar5)();
  if (bVar13) {
    FUN_19e3_06b3();
    return;
  }
  return;
}



/* 19e3:0638 FUN_19e3_0638 */

void __cdecl16near FUN_19e3_0638(void)

{
  code *pcVar1;
  uint uVar2;
  int extraout_DX;
  undefined2 unaff_DS;
  undefined1 in_CF;
  bool bVar3;
  
  pcVar1 = (code *)swi(0x21);
  (*pcVar1)();
  if ((bool)in_CF) {
    uVar2 = *(int *)0x87b - (extraout_DX + 1);
    *(uint *)0x87b = uVar2;
    if (uVar2 < *(uint *)0x87d) {
      FUN_19e3_06c2();
      return;
    }
    bVar3 = uVar2 < *(uint *)0x87f;
    pcVar1 = (code *)swi(0x21);
    (*pcVar1)();
    if (bVar3) {
      FUN_19e3_06c2();
      return;
    }
    pcVar1 = (code *)swi(0x21);
    (*pcVar1)();
    if (bVar3) {
      FUN_19e3_06c2();
      return;
    }
  }
  return;
}



/* 19e3:0672 FUN_19e3_0672 */

int __cdecl16near FUN_19e3_0672(void)

{
  code *pcVar1;
  int iVar2;
  uint uVar3;
  int iVar4;
  uint in_DX;
  bool bVar5;
  
  while( true ) {
    uVar3 = 0xfff;
    if (in_DX < 0xfff) {
      uVar3 = in_DX;
    }
    bVar5 = (int)(uVar3 << 3) < 0;
    iVar4 = uVar3 << 4;
    pcVar1 = (code *)swi(0x21);
    iVar2 = (*pcVar1)();
    if ((bVar5) || (iVar2 != iVar4)) break;
    in_DX = in_DX - uVar3;
    if (in_DX == 0) {
      return 0;
    }
  }
  return iVar2;
}



/* 19e3:06ad FUN_19e3_06ad */

void __cdecl16far FUN_19e3_06ad(void)

{
  code *pcVar1;
  
  pcVar1 = (code *)swi(0x21);
  (*pcVar1)();
  pcVar1 = (code *)swi(0x21);
  (*pcVar1)();
  return;
}



/* 19e3:06b3 FUN_19e3_06b3 */

void __cdecl16far FUN_19e3_06b3(void)

{
  code *pcVar1;
  
  pcVar1 = (code *)swi(0x21);
  (*pcVar1)();
  pcVar1 = (code *)swi(0x21);
  (*pcVar1)();
  return;
}



/* 19e3:06b8 FUN_19e3_06b8 */

void __cdecl16far FUN_19e3_06b8(void)

{
  code *pcVar1;
  
  pcVar1 = (code *)swi(0x21);
  (*pcVar1)();
  pcVar1 = (code *)swi(0x21);
  (*pcVar1)();
  return;
}



/* 19e3:06bd FUN_19e3_06bd */

void __cdecl16far FUN_19e3_06bd(void)

{
  code *pcVar1;
  
  pcVar1 = (code *)swi(0x21);
  (*pcVar1)();
  pcVar1 = (code *)swi(0x21);
  (*pcVar1)();
  return;
}



/* 19e3:06c2 FUN_19e3_06c2 */

void __cdecl16far FUN_19e3_06c2(void)

{
  code *pcVar1;
  
  pcVar1 = (code *)swi(0x21);
  (*pcVar1)();
  pcVar1 = (code *)swi(0x21);
  (*pcVar1)();
  return;
}



/* 19e3:06c7 FUN_19e3_06c7 */

void __cdecl16far FUN_19e3_06c7(void)

{
  code *pcVar1;
  
  pcVar1 = (code *)swi(0x21);
  (*pcVar1)();
  pcVar1 = (code *)swi(0x21);
  (*pcVar1)();
  return;
}



/* 19e3:06cc FUN_19e3_06cc */

void __cdecl16far FUN_19e3_06cc(void)

{
  code *pcVar1;
  
  pcVar1 = (code *)swi(0x21);
  (*pcVar1)();
  pcVar1 = (code *)swi(0x21);
  (*pcVar1)();
  return;
}


