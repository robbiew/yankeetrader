
/* 1000:0030 entry */
/* Low-level Error: Bad instruction count exceeded:
    ...
    Instruction at (ram,0x00010038) overlaps instruction at (ram,0x00010035)
 */

/* 3230:00f6 FUN_3230_00f6 */

int __cdecl16near FUN_3230_00f6(void)

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



/* 3230:0133 FUN_3230_0133 */

void __cdecl16far FUN_3230_0133(void)

{
  return;
}



/* 3927:0000 FUN_3927_0000 */

/* WARNING: Unable to track spacebase fully for stack */
/* WARNING: This function may have set the stack pointer */
/* WARNING: Removing unreachable block (ram,0x000393d7) */
/* WARNING: Removing unreachable block (ram,0x000393dc) */
/* WARNING: Removing unreachable block (ram,0x000393e0) */
/* WARNING: Removing unreachable block (ram,0x000393e3) */
/* WARNING: Removing unreachable block (ram,0x000393e8) */
/* WARNING: Removing unreachable block (ram,0x000393eb) */
/* WARNING: Removing unreachable block (ram,0x000393ff) */
/* WARNING: Removing unreachable block (ram,0x00039405) */
/* WARNING: Removing unreachable block (ram,0x00039411) */
/* WARNING: Removing unreachable block (ram,0x00039428) */
/* WARNING: Removing unreachable block (ram,0x0003942b) */
/* WARNING: Removing unreachable block (ram,0x00039433) */
/* WARNING: Removing unreachable block (ram,0x00039436) */
/* WARNING: Removing unreachable block (ram,0x00039441) */
/* WARNING: Removing unreachable block (ram,0x00039442) */
/* WARNING: Removing unreachable block (ram,0x0003944f) */
/* WARNING: Removing unreachable block (ram,0x00039452) */
/* WARNING: Removing unreachable block (ram,0x0003945c) */
/* WARNING: Removing unreachable block (ram,0x0003945f) */
/* WARNING: Removing unreachable block (ram,0x00039483) */
/* WARNING: Removing unreachable block (ram,0x00039486) */
/* WARNING: Removing unreachable block (ram,0x00039499) */
/* WARNING: Removing unreachable block (ram,0x0003949c) */
/* WARNING: Removing unreachable block (ram,0x000394c7) */
/* WARNING: Removing unreachable block (ram,0x000394ca) */
/* WARNING: Removing unreachable block (ram,0x000394eb) */
/* WARNING: Removing unreachable block (ram,0x000394ee) */
/* WARNING: Removing unreachable block (ram,0x000394f2) */
/* WARNING: Removing unreachable block (ram,0x000394f5) */
/* WARNING: Removing unreachable block (ram,0x0003951b) */
/* WARNING: Removing unreachable block (ram,0x0003951e) */
/* WARNING: Removing unreachable block (ram,0x00039539) */
/* WARNING: Removing unreachable block (ram,0x0003953c) */
/* WARNING: Removing unreachable block (ram,0x00039540) */
/* WARNING: Removing unreachable block (ram,0x00039543) */
/* WARNING: Removing unreachable block (ram,0x00039584) */
/* WARNING: Removing unreachable block (ram,0x00039587) */
/* WARNING: Removing unreachable block (ram,0x0003959c) */
/* WARNING: Removing unreachable block (ram,0x0003959f) */
/* WARNING: Removing unreachable block (ram,0x000395a3) */
/* WARNING: Removing unreachable block (ram,0x000395a6) */
/* WARNING: Removing unreachable block (ram,0x000395df) */
/* WARNING: Removing unreachable block (ram,0x000395e2) */
/* WARNING: Removing unreachable block (ram,0x000395fb) */
/* WARNING: Removing unreachable block (ram,0x000395fe) */
/* WARNING: Removing unreachable block (ram,0x00039601) */
/* WARNING: Removing unreachable block (ram,0x0003960e) */
/* WARNING: Removing unreachable block (ram,0x00039611) */
/* WARNING: Removing unreachable block (ram,0x00039615) */
/* WARNING: Removing unreachable block (ram,0x00039618) */
/* WARNING: Removing unreachable block (ram,0x00039621) */
/* WARNING: Removing unreachable block (ram,0x00039639) */
/* WARNING: Removing unreachable block (ram,0x00039632) */
/* WARNING: Removing unreachable block (ram,0x00039640) */
/* WARNING: Removing unreachable block (ram,0x00039643) */
/* WARNING: Removing unreachable block (ram,0x00039649) */
/* WARNING: Removing unreachable block (ram,0x00039653) */
/* WARNING: Removing unreachable block (ram,0x00039656) */
/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */
/* WARNING: Restarted to delay deadcode elimination for space: ram */

undefined2 __cdecl16far FUN_3927_0000(void)

{
  undefined1 *puVar1;
  char *pcVar2;
  char cVar3;
  undefined2 *puVar4;
  char *pcVar5;
  undefined2 *puVar6;
  code *pcVar7;
  undefined2 uVar8;
  undefined2 uVar9;
  byte bVar10;
  int iVar11;
  undefined2 uVar12;
  int iVar13;
  int iVar14;
  uint uVar15;
  undefined1 *puVar16;
  undefined2 *puVar17;
  char *pcVar18;
  undefined2 *puVar19;
  char *pcVar20;
  undefined2 unaff_ES;
  int unaff_SS;
  undefined1 uVar21;
  bool bVar22;
  undefined2 in_stack_00000002;
  undefined2 in_stack_0000000e;
  
  iVar14 = *(int *)0x0;
  DAT_3927_086e = (undefined1)iVar14;
  if ((iVar14 != 0x6d62) && (iVar14 != 0x7a62)) {
    uVar12 = FUN_3927_06c7();
    return uVar12;
  }
  pcVar7 = (code *)swi(0x21);
  bVar10 = (*pcVar7)();
  if (bVar10 < 2) {
    uVar12 = FUN_3927_06cc();
    return uVar12;
  }
  DAT_3927_087b = *(uint *)0x2;
  DAT_3927_0879 = *(undefined2 *)0x2c;
  DAT_3927_0877 = 0x3267;
  DAT_3927_087d = 0x49b0;
  puVar19 = (undefined2 *)0x0;
  puVar17 = (undefined2 *)0x0;
  DAT_3927_087f = unaff_ES;
  for (iVar14 = 0x3718; uVar12 = DAT_3927_0879, iVar14 != 0; iVar14 = iVar14 + -1) {
    puVar6 = puVar19;
    puVar19 = puVar19 + 1;
    puVar4 = puVar17;
    puVar17 = puVar17 + 1;
    *puVar6 = *puVar4;
  }
  DAT_3244_0000._0_1_ = '\0';
  DAT_3244_0000._1_1_ = '\0';
  DAT_3244_0002._0_1_ = '\0';
  DAT_3244_0002._1_1_ = '\0';
  DAT_3244_0004 = 0;
  pcVar18 = (char *)0x0;
  pcVar5 = (char *)0x0;
  do {
    do {
      pcVar20 = pcVar5;
      pcVar2 = pcVar18;
      pcVar18 = pcVar18 + 1;
      cVar3 = *pcVar2;
      pcVar5 = pcVar20 + 1;
      *pcVar20 = cVar3;
    } while (cVar3 != '\0');
  } while (*pcVar18 != '\0');
  pcVar5[0] = '\0';
  pcVar5[1] = '\0';
  uVar12 = 0;
  *(undefined2 *)0x0 = 7;
  *(undefined2 *)0x4 = pcVar20 + 3;
  *(undefined2 *)0x6 = 0;
  iVar14 = ((uint)(pcVar20 + 3) >> 4) + 1;
  *(int *)0x2 = iVar14;
  *(undefined2 *)0xa = 0;
  *(undefined2 *)0x8 = 0;
  *(undefined2 *)0xc = 0;
  *(undefined2 *)0xe = 0;
  DAT_3927_087d = DAT_3927_087d + iVar14 + 1;
  if (DAT_3927_087b <= DAT_3927_087d) {
    uVar12 = FUN_3927_06c2();
    return uVar12;
  }
  FUN_3927_049d();
  uVar21 = DAT_3927_0853 < 0x2eb;
  DAT_3927_086f = uVar12;
  if (DAT_3927_0853 != 0x2eb) {
    uVar12 = FUN_3927_06b3();
    return uVar12;
  }
  DAT_3927_0828 = FUN_3927_0638();
  FUN_3927_0672();
  if ((bool)uVar21) {
    uVar12 = FUN_3927_06b3();
    return uVar12;
  }
  if (*(char *)0x3 != '\x05') {
    uVar12 = FUN_3927_06ad();
    return uVar12;
  }
  if (*(char *)0x4 != '\x06') {
    uVar12 = FUN_3927_06ad();
    return uVar12;
  }
  if (*(char *)0x5 != '\0') {
    uVar12 = FUN_3927_06ad();
    return uVar12;
  }
  bVar22 = false;
  pcVar7 = (code *)swi(0x21);
  (*pcVar7)();
  if (bVar22) {
    uVar12 = FUN_3927_06b3();
    return uVar12;
  }
  uVar21 = CARRY2(unaff_SS + 0xc650,ram0x00030855);
  FUN_3927_042e();
  pcVar7 = (code *)swi(0x21);
  (*pcVar7)();
  if ((bool)uVar21) {
    uVar12 = FUN_3927_06b3();
    return uVar12;
  }
  s_bGenerating_ScoreBoard_3244_0101[0xb] = (char)DAT_2e79_2098;
  s_bGenerating_ScoreBoard_3244_0101[0xc] = DAT_2e79_2098._1_1_;
  s_bGenerating_ScoreBoard_3244_0101[5] = (char)DAT_2e79_20ef;
  s_bGenerating_ScoreBoard_3244_0101[6] = DAT_2e79_20ef._1_1_;
  uVar15 = DAT_2e79_20ed + 0xc650;
  iVar14 = 0x39b0;
  s_bGenerating_ScoreBoard_3244_0101._9_2_ = in_stack_0000000e;
  s_bGenerating_ScoreBoard_3244_0101[0xd] = '\x04';
  s_bGenerating_ScoreBoard_3244_0101[0xe] = '\0';
  if (DAT_2e79_209a != 0) {
    s_bGenerating_ScoreBoard_3244_0101[0xd] = '\x05';
    s_bGenerating_ScoreBoard_3244_0101[0xe] = '\0';
  }
  s_bGenerating_ScoreBoard_3244_0101[7] = -0x40;
  s_bGenerating_ScoreBoard_3244_0101[8] = -0x2f;
  iVar11 = DAT_2e79_20e7;
  while( true ) {
    puVar17 = (undefined2 *)0x0;
    puVar19 = (undefined2 *)0x0;
    s_bGenerating_ScoreBoard_3244_0101._3_2_ = 0xfff;
    if (uVar15 < 0xfff) {
      s_bGenerating_ScoreBoard_3244_0101._3_2_ = uVar15;
    }
    for (iVar13 = s_bGenerating_ScoreBoard_3244_0101._3_2_ << 3; iVar13 != 0; iVar13 = iVar13 + -1)
    {
      puVar6 = puVar19;
      puVar19 = puVar19 + 1;
      puVar4 = puVar17;
      puVar17 = puVar17 + 1;
      *puVar6 = *puVar4;
    }
    uVar15 = uVar15 - s_bGenerating_ScoreBoard_3244_0101._3_2_;
    if (uVar15 == 0) break;
    iVar14 = iVar14 + s_bGenerating_ScoreBoard_3244_0101._3_2_;
    iVar11 = iVar11 + s_bGenerating_ScoreBoard_3244_0101._3_2_;
  }
  s_bGenerating_ScoreBoard_3244_0101[3] = (char)DAT_3244_0000;
  s_bGenerating_ScoreBoard_3244_0101[4] = DAT_3244_0000._1_1_;
  s_bGenerating_ScoreBoard_3244_0101[1] = (char)DAT_3244_0002;
  s_bGenerating_ScoreBoard_3244_0101[2] = DAT_3244_0002._1_1_;
  _DAT_3244_0100 = DAT_3244_0004;
  DAT_3244_00fe = 0x2360;
  FUN_3230_00f6();
  DAT_3244_00fe = 0x236c;
  FUN_3230_00f6();
  DAT_3244_00fe = 0x3244;
  DAT_3244_00fc = 0x2379;
  FUN_3230_00f6();
  puVar17 = (undefined2 *)0x0;
  for (iVar14 = 0x80; uVar12 = s_bGenerating_ScoreBoard_3244_0101._5_2_, iVar14 != 0;
      iVar14 = iVar14 + -1) {
    puVar4 = puVar17;
    puVar17 = puVar17 + 1;
    *puVar4 = 0;
  }
  DAT_3244_014c = 7;
  DAT_3244_014e = 6;
  DAT_3244_0184 = _DAT_3244_0100;
  DAT_3244_0182._0_1_ = s_bGenerating_ScoreBoard_3244_0101[1];
  DAT_3244_0182._1_1_ = s_bGenerating_ScoreBoard_3244_0101[2];
  DAT_3244_0186 = s_bGenerating_ScoreBoard_3244_0101[3];
  s_cInitializing____3244_0187[0] = s_bGenerating_ScoreBoard_3244_0101[4];
  s_bPLEASE_HELP_YOUR_SYSOP_REGISTER_3244_011b._7_2_ = DAT_3244_00fe + *(int *)0x2;
  puVar17 = (undefined2 *)0x81;
  puVar16 = (undefined1 *)0x81;
  DAT_3244_01a0 = *(char *)0x80;
  s_bGenerating_ScoreBoard_3244_0101._5_2_ = DAT_3244_00fe + 1;
  for (iVar14 = (int)DAT_3244_01a0; iVar14 != 0; iVar14 = iVar14 + -1) {
    puVar4 = puVar17;
    puVar17 = (undefined2 *)((int)puVar17 + 1);
    puVar1 = puVar16;
    puVar16 = puVar16 + 1;
    *(undefined1 *)puVar4 = *puVar1;
  }
  *puVar17 = 0;
  uVar9 = s_bGenerating_ScoreBoard_3244_0101._11_2_;
  uVar8 = s_bGenerating_ScoreBoard_3244_0101._7_2_;
  uVar12 = s_bGenerating_ScoreBoard_3244_0101._5_2_;
  if (s_bGenerating_ScoreBoard_3244_0101._13_2_ != 4) {
    DAT_3244_0168 = 8;
  }
  *(undefined2 *)(char *)(s_bGenerating_ScoreBoard_3244_0101._7_2_ + -2) =
       s_bGenerating_ScoreBoard_3244_0101._9_2_;
  *(undefined2 *)(uVar8 + -4) = 0;
  *(undefined2 *)(char *)(uVar8 + -6) = uVar9;
  *(undefined2 *)(uVar8 + -8) = 7;
  return 0x3244;
}



/* 3927:042e FUN_3927_042e */

void __cdecl16near FUN_3927_042e(uint param_1)

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
    FUN_3927_06b3();
    return;
  }
  do {
    pcVar5 = (code *)swi(0x21);
    (*pcVar5)();
    if (bVar8) {
      FUN_3927_06b3();
      return;
    }
    puVar4 = (uint *)*(undefined2 *)0x873;
    uVar3 = *(uint *)0x875;
    if (uVar3 < unaff_DI) {
      bVar8 = false;
      if (uVar3 < in_stack_00000000) {
        iVar6 = uVar3 + unaff_BP;
        if (*puVar4 < unaff_DI) goto LAB_3927_0493;
LAB_3927_047e:
        *puVar4 = *puVar4 - unaff_DI;
        puVar1 = puVar4;
        bVar8 = CARRY2(*puVar1,unaff_SI);
        *puVar1 = *puVar1 + unaff_SI;
      }
    }
    else {
      bVar8 = false;
      if (uVar3 < param_1) {
        iVar6 = (uVar3 - unaff_DI) + 0x39b0;
        if (unaff_DI <= *puVar4) goto LAB_3927_047e;
LAB_3927_0493:
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



/* 3927:049d FUN_3927_049d */

void __cdecl16near FUN_3927_049d(void)

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
  if (!(bool)in_CF) goto LAB_3927_05a6;
  if (*(int *)0x611 != 0x812) {
    pcVar7 = (char *)(extraout_DX + -1);
    do {
      pcVar7 = pcVar7 + 1;
      cVar4 = *pcVar7;
      if ((cVar4 == ':') || (cVar4 == '\\')) goto LAB_3927_0533;
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
      goto LAB_3927_04e7;
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
  goto LAB_3927_0533;
  while (uVar12 = unaff_DS, *pcVar9 != '\0') {
LAB_3927_04e7:
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
    unaff_DS = 0x3927;
    if ((pcVar11 != (char *)0x82c) && ((pcVar11[-1] != ':' && (pcVar11[-1] != '\\')))) {
      pcVar2 = pcVar11;
      pcVar11 = pcVar11 + 1;
      *pcVar2 = '\\';
    }
    pcVar10 = DAT_3927_0611;
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
    if (!(bool)in_CF) goto LAB_3927_05a6;
  }
LAB_3927_0533:
  do {
    unaff_DS = 0x3927;
    pcVar5 = (code *)swi(0x21);
    (*pcVar5)();
    do {
      pcVar5 = (code *)swi(0x21);
      (*pcVar5)();
    } while (extraout_DL != '\0');
    pcVar5 = (code *)swi(0x21);
    (*pcVar5)();
    DAT_3927_082c = 0x40;
    pcVar5 = (code *)swi(0x21);
    (*pcVar5)();
    pcVar5 = (code *)swi(0x21);
    (*pcVar5)();
    uVar8 = (uint)DAT_3927_082d;
    *(undefined1 *)(uVar8 + 0x82e) = 0;
    bVar13 = DAT_3927_0611 < (char *)0x812;
    if (DAT_3927_0611 == (char *)0x812) {
      if ((*(char *)(uVar8 + 0x82d) != ':') && (*(char *)(uVar8 + 0x82d) != '\\')) {
        *(undefined1 *)(uVar8 + 0x82e) = 0x5c;
        uVar8 = uVar8 + 1;
      }
      pcVar11 = (char *)(uVar8 + 0x82e);
      pcVar7 = DAT_3927_0611;
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
LAB_3927_05a6:
  pcVar5 = (code *)swi(0x21);
  (*pcVar5)();
  if ((bool)in_CF) {
    FUN_3927_06b3();
    return;
  }
  if (*(int *)0x82c != 0x5a4d) {
    FUN_3927_06b3();
    return;
  }
  bVar13 = false;
  pcVar5 = (code *)swi(0x21);
  (*pcVar5)();
  if (bVar13) {
    FUN_3927_06b3();
    return;
  }
  pcVar5 = (code *)swi(0x21);
  (*pcVar5)();
  if (bVar13) {
    FUN_3927_06b3();
    return;
  }
  pcVar5 = (code *)swi(0x21);
  (*pcVar5)();
  if (bVar13) {
    FUN_3927_06b3();
    return;
  }
  return;
}



/* 3927:0638 FUN_3927_0638 */

void __cdecl16near FUN_3927_0638(void)

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
      FUN_3927_06c2();
      return;
    }
    bVar3 = uVar2 < *(uint *)0x87f;
    pcVar1 = (code *)swi(0x21);
    (*pcVar1)();
    if (bVar3) {
      FUN_3927_06c2();
      return;
    }
    pcVar1 = (code *)swi(0x21);
    (*pcVar1)();
    if (bVar3) {
      FUN_3927_06c2();
      return;
    }
  }
  return;
}



/* 3927:0672 FUN_3927_0672 */

int __cdecl16near FUN_3927_0672(void)

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



/* 3927:06ad FUN_3927_06ad */

void __cdecl16far FUN_3927_06ad(void)

{
  code *pcVar1;
  
  pcVar1 = (code *)swi(0x21);
  (*pcVar1)();
  pcVar1 = (code *)swi(0x21);
  (*pcVar1)();
  return;
}



/* 3927:06b3 FUN_3927_06b3 */

void __cdecl16far FUN_3927_06b3(void)

{
  code *pcVar1;
  
  pcVar1 = (code *)swi(0x21);
  (*pcVar1)();
  pcVar1 = (code *)swi(0x21);
  (*pcVar1)();
  return;
}



/* 3927:06b8 FUN_3927_06b8 */

void __cdecl16far FUN_3927_06b8(void)

{
  code *pcVar1;
  
  pcVar1 = (code *)swi(0x21);
  (*pcVar1)();
  pcVar1 = (code *)swi(0x21);
  (*pcVar1)();
  return;
}



/* 3927:06bd FUN_3927_06bd */

void __cdecl16far FUN_3927_06bd(void)

{
  code *pcVar1;
  
  pcVar1 = (code *)swi(0x21);
  (*pcVar1)();
  pcVar1 = (code *)swi(0x21);
  (*pcVar1)();
  return;
}



/* 3927:06c2 FUN_3927_06c2 */

void __cdecl16far FUN_3927_06c2(void)

{
  code *pcVar1;
  
  pcVar1 = (code *)swi(0x21);
  (*pcVar1)();
  pcVar1 = (code *)swi(0x21);
  (*pcVar1)();
  return;
}



/* 3927:06c7 FUN_3927_06c7 */

void __cdecl16far FUN_3927_06c7(void)

{
  code *pcVar1;
  
  pcVar1 = (code *)swi(0x21);
  (*pcVar1)();
  pcVar1 = (code *)swi(0x21);
  (*pcVar1)();
  return;
}



/* 3927:06cc FUN_3927_06cc */

void __cdecl16far FUN_3927_06cc(void)

{
  code *pcVar1;
  
  pcVar1 = (code *)swi(0x21);
  (*pcVar1)();
  pcVar1 = (code *)swi(0x21);
  (*pcVar1)();
  return;
}


