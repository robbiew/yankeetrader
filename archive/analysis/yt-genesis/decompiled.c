
/* 1000:0030 entry */

/* WARNING: Stack frame is not setup normally: Input value of stackpointer is not used */
/* WARNING: This function may have set the stack pointer */

void __cdecl16near entry(void)

{
  uint *puVar1;
  byte *pbVar2;
  code *pcVar3;
  byte extraout_DL;
  uint extraout_DX;
  int iVar4;
  int unaff_SI;
  undefined2 unaff_DS;
  
  DAT_1759_1f8e = 0x1000;
  DAT_1759_1f8c = 0x35;
  FUN_151c_0000();
  DAT_1759_1f8e = 0x151c;
  DAT_1759_1f8c = 0x3a;
  FUN_132f_0133();
  pcVar3 = (code *)swi(0x3d);
  (*pcVar3)();
  pcVar3 = (code *)swi(0x3f);
  (*pcVar3)();
  iVar4 = 0x1a;
  pcVar3 = (code *)swi(0x3e);
  (*pcVar3)();
  puVar1 = (uint *)(iVar4 + unaff_SI + -0x4470);
  *puVar1 = *puVar1 | extraout_DX;
  pcVar3 = (code *)swi(0x3e);
  (*pcVar3)();
  pbVar2 = (byte *)(iVar4 + unaff_SI + -0x7470);
  *pbVar2 = *pbVar2 & extraout_DL;
  return;
}



/* 132f:00f6 FUN_132f_00f6 */

int __cdecl16near FUN_132f_00f6(void)

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



/* 132f:0133 FUN_132f_0133 */

void __cdecl16far FUN_132f_0133(void)

{
  return;
}



/* 151c:0000 FUN_151c_0000 */

/* WARNING: Unable to track spacebase fully for stack */
/* WARNING: This function may have set the stack pointer */
/* WARNING: Removing unreachable block (ram,0x00015327) */
/* WARNING: Removing unreachable block (ram,0x0001532c) */
/* WARNING: Removing unreachable block (ram,0x00015330) */
/* WARNING: Removing unreachable block (ram,0x00015333) */
/* WARNING: Removing unreachable block (ram,0x00015338) */
/* WARNING: Removing unreachable block (ram,0x0001533b) */
/* WARNING: Removing unreachable block (ram,0x0001534f) */
/* WARNING: Removing unreachable block (ram,0x00015355) */
/* WARNING: Removing unreachable block (ram,0x00015361) */
/* WARNING: Removing unreachable block (ram,0x00015378) */
/* WARNING: Removing unreachable block (ram,0x0001537b) */
/* WARNING: Removing unreachable block (ram,0x00015383) */
/* WARNING: Removing unreachable block (ram,0x00015386) */
/* WARNING: Removing unreachable block (ram,0x00015391) */
/* WARNING: Removing unreachable block (ram,0x00015392) */
/* WARNING: Removing unreachable block (ram,0x0001539f) */
/* WARNING: Removing unreachable block (ram,0x000153a2) */
/* WARNING: Removing unreachable block (ram,0x000153ac) */
/* WARNING: Removing unreachable block (ram,0x000153af) */
/* WARNING: Removing unreachable block (ram,0x000153d3) */
/* WARNING: Removing unreachable block (ram,0x000153d6) */
/* WARNING: Removing unreachable block (ram,0x000153e9) */
/* WARNING: Removing unreachable block (ram,0x000153ec) */
/* WARNING: Removing unreachable block (ram,0x00015417) */
/* WARNING: Removing unreachable block (ram,0x0001541a) */
/* WARNING: Removing unreachable block (ram,0x0001543b) */
/* WARNING: Removing unreachable block (ram,0x0001543e) */
/* WARNING: Removing unreachable block (ram,0x00015442) */
/* WARNING: Removing unreachable block (ram,0x00015445) */
/* WARNING: Removing unreachable block (ram,0x0001546b) */
/* WARNING: Removing unreachable block (ram,0x0001546e) */
/* WARNING: Removing unreachable block (ram,0x00015489) */
/* WARNING: Removing unreachable block (ram,0x0001548c) */
/* WARNING: Removing unreachable block (ram,0x00015490) */
/* WARNING: Removing unreachable block (ram,0x00015493) */
/* WARNING: Removing unreachable block (ram,0x000154d4) */
/* WARNING: Removing unreachable block (ram,0x000154d7) */
/* WARNING: Removing unreachable block (ram,0x000154ec) */
/* WARNING: Removing unreachable block (ram,0x000154ef) */
/* WARNING: Removing unreachable block (ram,0x000154f3) */
/* WARNING: Removing unreachable block (ram,0x000154f6) */
/* WARNING: Removing unreachable block (ram,0x0001552f) */
/* WARNING: Removing unreachable block (ram,0x00015532) */
/* WARNING: Removing unreachable block (ram,0x0001554b) */
/* WARNING: Removing unreachable block (ram,0x0001554e) */
/* WARNING: Removing unreachable block (ram,0x00015551) */
/* WARNING: Removing unreachable block (ram,0x0001555e) */
/* WARNING: Removing unreachable block (ram,0x00015561) */
/* WARNING: Removing unreachable block (ram,0x00015565) */
/* WARNING: Removing unreachable block (ram,0x00015568) */
/* WARNING: Removing unreachable block (ram,0x00015571) */
/* WARNING: Removing unreachable block (ram,0x00015589) */
/* WARNING: Removing unreachable block (ram,0x00015582) */
/* WARNING: Removing unreachable block (ram,0x00015590) */
/* WARNING: Removing unreachable block (ram,0x00015593) */
/* WARNING: Removing unreachable block (ram,0x00015599) */
/* WARNING: Removing unreachable block (ram,0x000155a3) */
/* WARNING: Removing unreachable block (ram,0x000155a6) */
/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */
/* WARNING: Restarted to delay deadcode elimination for space: ram */

undefined2 __cdecl16far FUN_151c_0000(void)

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
  DAT_151c_086e = (undefined1)iVar12;
  if ((iVar12 != 0x6d62) && (iVar12 != 0x7a62)) {
    uVar10 = FUN_151c_06c7();
    return uVar10;
  }
  pcVar7 = (code *)swi(0x21);
  bVar8 = (*pcVar7)();
  if (bVar8 < 2) {
    uVar10 = FUN_151c_06cc();
    return uVar10;
  }
  DAT_151c_087b = *(uint *)0x2;
  DAT_151c_0879 = *(undefined2 *)0x2c;
  DAT_151c_0877 = 0x1366;
  DAT_151c_087d = 0x25a5;
  puVar17 = (undefined2 *)0x0;
  puVar15 = (undefined2 *)0x0;
  DAT_151c_087f = unaff_ES;
  for (iVar12 = 0xec8; uVar10 = DAT_151c_0879, iVar12 != 0; iVar12 = iVar12 + -1) {
    puVar6 = puVar17;
    puVar17 = puVar17 + 1;
    puVar4 = puVar15;
    puVar15 = puVar15 + 1;
    *puVar6 = *puVar4;
  }
  DAT_1343_0000 = 0;
  DAT_1343_0002 = 0;
  s_rmtinit_tmp_1343_0004[0] = '\0';
  s_rmtinit_tmp_1343_0004[1] = '\0';
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
  DAT_151c_087d = DAT_151c_087d + iVar12 + 1;
  if (DAT_151c_087b <= DAT_151c_087d) {
    uVar10 = FUN_151c_06c2();
    return uVar10;
  }
  FUN_151c_049d();
  uVar19 = DAT_151c_0853 < 0x2eb;
  DAT_151c_086f = uVar10;
  if (DAT_151c_0853 != 0x2eb) {
    uVar10 = FUN_151c_06b3();
    return uVar10;
  }
  DAT_151c_0828 = FUN_151c_0638();
  FUN_151c_0672();
  if ((bool)uVar19) {
    uVar10 = FUN_151c_06b3();
    return uVar10;
  }
  if (*(char *)0x3 != '\x05') {
    uVar10 = FUN_151c_06ad();
    return uVar10;
  }
  if (*(char *)0x4 != '\x06') {
    uVar10 = FUN_151c_06ad();
    return uVar10;
  }
  if (*(char *)0x5 != '\0') {
    uVar10 = FUN_151c_06ad();
    return uVar10;
  }
  bVar20 = false;
  pcVar7 = (code *)swi(0x21);
  (*pcVar7)();
  if (bVar20) {
    uVar10 = FUN_151c_06b3();
    return uVar10;
  }
  uVar19 = CARRY2(unaff_SS + 0xea5b,ram0x00010855);
  FUN_151c_042e();
  pcVar7 = (code *)swi(0x21);
  (*pcVar7)();
  if ((bool)uVar19) {
    uVar10 = FUN_151c_06b3();
    return uVar10;
  }
  DAT_1343_010c = DAT_1000_0828;
  DAT_1343_0106 = DAT_1000_087f;
  uVar13 = DAT_1000_087d + 0xea5b;
  iVar12 = 0x15a5;
  DAT_1343_010a = in_stack_0000000e;
  DAT_1343_010e = 4;
  if (DAT_1000_082a != 0) {
    DAT_1343_010e = 5;
  }
  DAT_1343_0108 = 0x3ad0;
  iVar9 = DAT_1000_0877;
  while( true ) {
    puVar15 = (undefined2 *)0x0;
    puVar17 = (undefined2 *)0x0;
    DAT_1343_0104 = 0xfff;
    if (uVar13 < 0xfff) {
      DAT_1343_0104 = uVar13;
    }
    for (iVar11 = DAT_1343_0104 << 3; iVar11 != 0; iVar11 = iVar11 + -1) {
      puVar6 = puVar17;
      puVar17 = puVar17 + 1;
      puVar4 = puVar15;
      puVar15 = puVar15 + 1;
      *puVar6 = *puVar4;
    }
    uVar13 = uVar13 - DAT_1343_0104;
    if (uVar13 == 0) break;
    iVar12 = iVar12 + DAT_1343_0104;
    iVar9 = iVar9 + DAT_1343_0104;
  }
  DAT_1343_0104 = DAT_1343_0000;
  DAT_1343_0102 = DAT_1343_0002;
  DAT_1343_0100._0_1_ = s_rmtinit_tmp_1343_0004[0];
  DAT_1343_0100._1_1_ = s_rmtinit_tmp_1343_0004[1];
  DAT_1343_00fe = 0x3350;
  FUN_132f_00f6();
  DAT_1343_00fe = 0x335c;
  FUN_132f_00f6();
  DAT_1343_00fe = 0x1343;
  DAT_1343_00fc = 0x3369;
  FUN_132f_00f6();
  puVar15 = (undefined2 *)0x0;
  for (iVar12 = 0x80; iVar9 = DAT_1343_0106, iVar12 != 0; iVar12 = iVar12 + -1) {
    puVar4 = puVar15;
    puVar15 = puVar15 + 1;
    *puVar4 = 0;
  }
  DAT_1343_014c = 7;
  DAT_1343_014e = 6;
  DAT_1343_0184._0_1_ = (char)DAT_1343_0100;
  DAT_1343_0184._1_1_ = DAT_1343_0100._1_1_;
  DAT_1343_0182 = DAT_1343_0102;
  DAT_1343_0186 = DAT_1343_0104;
  DAT_1343_0122 = DAT_1343_00fe + *(int *)0x2;
  puVar15 = (undefined2 *)0x81;
  puVar14 = (undefined1 *)0x81;
  s_Local_Console_Mode_1343_0192[0xe] = *(char *)0x80;
  DAT_1343_0106 = DAT_1343_00fe + 1;
  for (iVar12 = (int)s_Local_Console_Mode_1343_0192[0xe]; iVar12 != 0; iVar12 = iVar12 + -1) {
    puVar4 = puVar15;
    puVar15 = (undefined2 *)((int)puVar15 + 1);
    puVar1 = puVar14;
    puVar14 = puVar14 + 1;
    *(undefined1 *)puVar4 = *puVar1;
  }
  *puVar15 = 0;
  uVar10 = DAT_1343_010c;
  iVar9 = DAT_1343_0108;
  iVar12 = DAT_1343_0106;
  if (DAT_1343_010e != 4) {
    DAT_1343_0168 = 8;
  }
  *(undefined2 *)(DAT_1343_0108 + -2) = DAT_1343_010a;
  *(undefined2 *)(iVar9 + -4) = 0;
  *(undefined2 *)(iVar9 + -6) = uVar10;
  *(undefined2 *)(iVar9 + -8) = 7;
  return 0x1343;
}



/* 151c:042e FUN_151c_042e */

void __cdecl16near FUN_151c_042e(uint param_1)

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
    FUN_151c_06b3();
    return;
  }
  do {
    pcVar5 = (code *)swi(0x21);
    (*pcVar5)();
    if (bVar8) {
      FUN_151c_06b3();
      return;
    }
    puVar4 = (uint *)*(undefined2 *)0x873;
    uVar3 = *(uint *)0x875;
    if (uVar3 < unaff_DI) {
      bVar8 = false;
      if (uVar3 < in_stack_00000000) {
        iVar6 = uVar3 + unaff_BP;
        if (*puVar4 < unaff_DI) goto LAB_151c_0493;
LAB_151c_047e:
        *puVar4 = *puVar4 - unaff_DI;
        puVar1 = puVar4;
        bVar8 = CARRY2(*puVar1,unaff_SI);
        *puVar1 = *puVar1 + unaff_SI;
      }
    }
    else {
      bVar8 = false;
      if (uVar3 < param_1) {
        iVar6 = (uVar3 - unaff_DI) + 0x15a5;
        if (unaff_DI <= *puVar4) goto LAB_151c_047e;
LAB_151c_0493:
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



/* 151c:049d FUN_151c_049d */

void __cdecl16near FUN_151c_049d(void)

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
  if (!(bool)in_CF) goto LAB_151c_05a6;
  if (*(int *)0x611 != 0x812) {
    pcVar7 = (char *)(extraout_DX + -1);
    do {
      pcVar7 = pcVar7 + 1;
      cVar4 = *pcVar7;
      if ((cVar4 == ':') || (cVar4 == '\\')) goto LAB_151c_0533;
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
      goto LAB_151c_04e7;
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
  goto LAB_151c_0533;
  while (uVar12 = unaff_DS, *pcVar9 != '\0') {
LAB_151c_04e7:
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
    unaff_DS = 0x151c;
    if ((pcVar11 != (char *)0x82c) && ((pcVar11[-1] != ':' && (pcVar11[-1] != '\\')))) {
      pcVar2 = pcVar11;
      pcVar11 = pcVar11 + 1;
      *pcVar2 = '\\';
    }
    pcVar10 = DAT_151c_0611;
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
    if (!(bool)in_CF) goto LAB_151c_05a6;
  }
LAB_151c_0533:
  do {
    unaff_DS = 0x151c;
    pcVar5 = (code *)swi(0x21);
    (*pcVar5)();
    do {
      pcVar5 = (code *)swi(0x21);
      (*pcVar5)();
    } while (extraout_DL != '\0');
    pcVar5 = (code *)swi(0x21);
    (*pcVar5)();
    DAT_151c_082c = 0x40;
    pcVar5 = (code *)swi(0x21);
    (*pcVar5)();
    pcVar5 = (code *)swi(0x21);
    (*pcVar5)();
    uVar8 = (uint)DAT_151c_082d;
    *(undefined1 *)(uVar8 + 0x82e) = 0;
    bVar13 = DAT_151c_0611 < (char *)0x812;
    if (DAT_151c_0611 == (char *)0x812) {
      if ((*(char *)(uVar8 + 0x82d) != ':') && (*(char *)(uVar8 + 0x82d) != '\\')) {
        *(undefined1 *)(uVar8 + 0x82e) = 0x5c;
        uVar8 = uVar8 + 1;
      }
      pcVar11 = (char *)(uVar8 + 0x82e);
      pcVar7 = DAT_151c_0611;
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
LAB_151c_05a6:
  pcVar5 = (code *)swi(0x21);
  (*pcVar5)();
  if ((bool)in_CF) {
    FUN_151c_06b3();
    return;
  }
  if (*(int *)0x82c != 0x5a4d) {
    FUN_151c_06b3();
    return;
  }
  bVar13 = false;
  pcVar5 = (code *)swi(0x21);
  (*pcVar5)();
  if (bVar13) {
    FUN_151c_06b3();
    return;
  }
  pcVar5 = (code *)swi(0x21);
  (*pcVar5)();
  if (bVar13) {
    FUN_151c_06b3();
    return;
  }
  pcVar5 = (code *)swi(0x21);
  (*pcVar5)();
  if (bVar13) {
    FUN_151c_06b3();
    return;
  }
  return;
}



/* 151c:0638 FUN_151c_0638 */

void __cdecl16near FUN_151c_0638(void)

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
      FUN_151c_06c2();
      return;
    }
    bVar3 = uVar2 < *(uint *)0x87f;
    pcVar1 = (code *)swi(0x21);
    (*pcVar1)();
    if (bVar3) {
      FUN_151c_06c2();
      return;
    }
    pcVar1 = (code *)swi(0x21);
    (*pcVar1)();
    if (bVar3) {
      FUN_151c_06c2();
      return;
    }
  }
  return;
}



/* 151c:0672 FUN_151c_0672 */

int __cdecl16near FUN_151c_0672(void)

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



/* 151c:06ad FUN_151c_06ad */

void __cdecl16far FUN_151c_06ad(void)

{
  code *pcVar1;
  
  pcVar1 = (code *)swi(0x21);
  (*pcVar1)();
  pcVar1 = (code *)swi(0x21);
  (*pcVar1)();
  return;
}



/* 151c:06b3 FUN_151c_06b3 */

void __cdecl16far FUN_151c_06b3(void)

{
  code *pcVar1;
  
  pcVar1 = (code *)swi(0x21);
  (*pcVar1)();
  pcVar1 = (code *)swi(0x21);
  (*pcVar1)();
  return;
}



/* 151c:06b8 FUN_151c_06b8 */

void __cdecl16far FUN_151c_06b8(void)

{
  code *pcVar1;
  
  pcVar1 = (code *)swi(0x21);
  (*pcVar1)();
  pcVar1 = (code *)swi(0x21);
  (*pcVar1)();
  return;
}



/* 151c:06bd FUN_151c_06bd */

void __cdecl16far FUN_151c_06bd(void)

{
  code *pcVar1;
  
  pcVar1 = (code *)swi(0x21);
  (*pcVar1)();
  pcVar1 = (code *)swi(0x21);
  (*pcVar1)();
  return;
}



/* 151c:06c2 FUN_151c_06c2 */

void __cdecl16far FUN_151c_06c2(void)

{
  code *pcVar1;
  
  pcVar1 = (code *)swi(0x21);
  (*pcVar1)();
  pcVar1 = (code *)swi(0x21);
  (*pcVar1)();
  return;
}



/* 151c:06c7 FUN_151c_06c7 */

void __cdecl16far FUN_151c_06c7(void)

{
  code *pcVar1;
  
  pcVar1 = (code *)swi(0x21);
  (*pcVar1)();
  pcVar1 = (code *)swi(0x21);
  (*pcVar1)();
  return;
}



/* 151c:06cc FUN_151c_06cc */

void __cdecl16far FUN_151c_06cc(void)

{
  code *pcVar1;
  
  pcVar1 = (code *)swi(0x21);
  (*pcVar1)();
  pcVar1 = (code *)swi(0x21);
  (*pcVar1)();
  return;
}


