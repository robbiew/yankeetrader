
/* 1000:0030 entry */
/* Low-level Error: Bad instruction count exceeded:
    ...
    Instruction at (ram,0x00010036) overlaps instruction at (ram,0x00010035)
 */

/* 1000:009c FUN_1000_009c */

undefined2 __cdecl16near FUN_1000_009c(void)

{
  code *pcVar1;
  undefined2 uVar2;
  int *unaff_SI;
  undefined2 unaff_DS;
  byte in_AF;
  
  pcVar1 = (code *)swi(0x3f);
  uVar2 = (*pcVar1)();
  in_AF = 9 < ((byte)uVar2 & 0xf) | in_AF;
  *unaff_SI = *unaff_SI +
              (CONCAT11((char)((uint)uVar2 >> 8) - in_AF,(byte)uVar2 + in_AF * -6) & 0xff0f);
  pcVar1 = (code *)swi(0x3f);
  (*pcVar1)();
  return 0x9090;
}



/* 1000:00b5 FUN_1000_00b5 */
/* Low-level Error: Bad instruction count exceeded:
    ...
    Instruction at (ram,0x00010031) overlaps instruction at (ram,0x00010030)
 */

/* 1000:0602 FUN_1000_0602 */
/* Low-level Error: Bad instruction count exceeded:
    ...
    Instruction at (ram,0x000109e6) overlaps instruction at (ram,0x000109e5)
 */

/* 1265:00f6 FUN_1265_00f6 */

int __cdecl16near FUN_1265_00f6(void)

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



/* 1265:0133 FUN_1265_0133 */

void __cdecl16far FUN_1265_0133(void)

{
  return;
}



/* 1452:0000 FUN_1452_0000 */

/* WARNING: Unable to track spacebase fully for stack */
/* WARNING: This function may have set the stack pointer */
/* WARNING: Removing unreachable block (ram,0x00014687) */
/* WARNING: Removing unreachable block (ram,0x0001468c) */
/* WARNING: Removing unreachable block (ram,0x00014690) */
/* WARNING: Removing unreachable block (ram,0x00014693) */
/* WARNING: Removing unreachable block (ram,0x00014698) */
/* WARNING: Removing unreachable block (ram,0x0001469b) */
/* WARNING: Removing unreachable block (ram,0x000146af) */
/* WARNING: Removing unreachable block (ram,0x000146b5) */
/* WARNING: Removing unreachable block (ram,0x000146c1) */
/* WARNING: Removing unreachable block (ram,0x000146d8) */
/* WARNING: Removing unreachable block (ram,0x000146db) */
/* WARNING: Removing unreachable block (ram,0x000146e3) */
/* WARNING: Removing unreachable block (ram,0x000146e6) */
/* WARNING: Removing unreachable block (ram,0x000146f1) */
/* WARNING: Removing unreachable block (ram,0x000146f2) */
/* WARNING: Removing unreachable block (ram,0x000146ff) */
/* WARNING: Removing unreachable block (ram,0x00014702) */
/* WARNING: Removing unreachable block (ram,0x0001470c) */
/* WARNING: Removing unreachable block (ram,0x0001470f) */
/* WARNING: Removing unreachable block (ram,0x00014733) */
/* WARNING: Removing unreachable block (ram,0x00014736) */
/* WARNING: Removing unreachable block (ram,0x00014749) */
/* WARNING: Removing unreachable block (ram,0x0001474c) */
/* WARNING: Removing unreachable block (ram,0x00014777) */
/* WARNING: Removing unreachable block (ram,0x0001477a) */
/* WARNING: Removing unreachable block (ram,0x0001479b) */
/* WARNING: Removing unreachable block (ram,0x0001479e) */
/* WARNING: Removing unreachable block (ram,0x000147a2) */
/* WARNING: Removing unreachable block (ram,0x000147a5) */
/* WARNING: Removing unreachable block (ram,0x000147cb) */
/* WARNING: Removing unreachable block (ram,0x000147ce) */
/* WARNING: Removing unreachable block (ram,0x000147e9) */
/* WARNING: Removing unreachable block (ram,0x000147ec) */
/* WARNING: Removing unreachable block (ram,0x000147f0) */
/* WARNING: Removing unreachable block (ram,0x000147f3) */
/* WARNING: Removing unreachable block (ram,0x00014834) */
/* WARNING: Removing unreachable block (ram,0x00014837) */
/* WARNING: Removing unreachable block (ram,0x0001484c) */
/* WARNING: Removing unreachable block (ram,0x0001484f) */
/* WARNING: Removing unreachable block (ram,0x00014853) */
/* WARNING: Removing unreachable block (ram,0x00014856) */
/* WARNING: Removing unreachable block (ram,0x0001488f) */
/* WARNING: Removing unreachable block (ram,0x00014892) */
/* WARNING: Removing unreachable block (ram,0x000148ab) */
/* WARNING: Removing unreachable block (ram,0x000148ae) */
/* WARNING: Removing unreachable block (ram,0x000148b1) */
/* WARNING: Removing unreachable block (ram,0x000148be) */
/* WARNING: Removing unreachable block (ram,0x000148c1) */
/* WARNING: Removing unreachable block (ram,0x000148c5) */
/* WARNING: Removing unreachable block (ram,0x000148c8) */
/* WARNING: Removing unreachable block (ram,0x000148d1) */
/* WARNING: Removing unreachable block (ram,0x000148e9) */
/* WARNING: Removing unreachable block (ram,0x000148e2) */
/* WARNING: Removing unreachable block (ram,0x000148f0) */
/* WARNING: Removing unreachable block (ram,0x000148f3) */
/* WARNING: Removing unreachable block (ram,0x000148f9) */
/* WARNING: Removing unreachable block (ram,0x00014903) */
/* WARNING: Removing unreachable block (ram,0x00014906) */
/* WARNING: Restarted to delay deadcode elimination for space: ram */

undefined2 __cdecl16far FUN_1452_0000(void)

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
  DAT_1452_086e = (undefined1)iVar14;
  if ((iVar14 != 0x6d62) && (iVar14 != 0x7a62)) {
    uVar12 = FUN_1452_06c7();
    return uVar12;
  }
  pcVar7 = (code *)swi(0x21);
  bVar10 = (*pcVar7)();
  if (bVar10 < 2) {
    uVar12 = FUN_1452_06cc();
    return uVar12;
  }
  DAT_1452_087b = *(uint *)0x2;
  DAT_1452_0879 = *(undefined2 *)0x2c;
  DAT_1452_0877 = 0x129c;
  DAT_1452_087d = 0x24db;
  puVar19 = (undefined2 *)0x0;
  puVar17 = (undefined2 *)0x0;
  DAT_1452_087f = unaff_ES;
  for (iVar14 = 0xec8; uVar12 = DAT_1452_0879, iVar14 != 0; iVar14 = iVar14 + -1) {
    puVar6 = puVar19;
    puVar19 = puVar19 + 1;
    puVar4 = puVar17;
    puVar17 = puVar17 + 1;
    *puVar6 = *puVar4;
  }
  DAT_1279_0000._0_1_ = '\0';
  DAT_1279_0000._1_1_ = '\0';
  DAT_1279_0002._0_1_ = '\0';
  DAT_1279_0002._1_1_ = '\0';
  DAT_1279_0004._0_1_ = '\0';
  DAT_1279_0004._1_1_ = '\0';
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
  DAT_1452_087d = DAT_1452_087d + iVar14 + 1;
  if (DAT_1452_087b <= DAT_1452_087d) {
    uVar12 = FUN_1452_06c2();
    return uVar12;
  }
  FUN_1452_049d();
  uVar21 = DAT_1452_0853 < 0x2eb;
  DAT_1452_086f = uVar12;
  if (DAT_1452_0853 != 0x2eb) {
    uVar12 = FUN_1452_06b3();
    return uVar12;
  }
  DAT_1452_0828 = FUN_1452_0638();
  FUN_1452_0672();
  if ((bool)uVar21) {
    uVar12 = FUN_1452_06b3();
    return uVar12;
  }
  if (*(char *)0x3 != '\x05') {
    uVar12 = FUN_1452_06ad();
    return uVar12;
  }
  if (*(char *)0x4 != '\x06') {
    uVar12 = FUN_1452_06ad();
    return uVar12;
  }
  if (*(char *)0x5 != '\0') {
    uVar12 = FUN_1452_06ad();
    return uVar12;
  }
  bVar22 = false;
  pcVar7 = (code *)swi(0x21);
  (*pcVar7)();
  if (bVar22) {
    uVar12 = FUN_1452_06b3();
    return uVar12;
  }
  uVar21 = CARRY2(unaff_SS + 0xeb25,uRam00010855);
  FUN_1452_042e();
  pcVar7 = (code *)swi(0x21);
  (*pcVar7)();
  if ((bool)uVar21) {
    uVar12 = FUN_1452_06b3();
    return uVar12;
  }
  s_This_program_will_initialize_Yan_1279_00fa[0x12] = (char)uRam00010828;
  s_This_program_will_initialize_Yan_1279_00fa[0x13] = uRam00010828._1_1_;
  s_This_program_will_initialize_Yan_1279_00fa[0xc] = (char)uRam0001087f;
  s_This_program_will_initialize_Yan_1279_00fa[0xd] = uRam0001087f._1_1_;
  uVar15 = iRam0001087d + 0xeb25;
  iVar14 = 0x14db;
  s_This_program_will_initialize_Yan_1279_00fa._16_2_ = in_stack_0000000e;
  s_This_program_will_initialize_Yan_1279_00fa[0x14] = '\x04';
  s_This_program_will_initialize_Yan_1279_00fa[0x15] = '\0';
  if (iRam0001082a != 0) {
    s_This_program_will_initialize_Yan_1279_00fa[0x14] = '\x05';
    s_This_program_will_initialize_Yan_1279_00fa[0x15] = '\0';
  }
  s_This_program_will_initialize_Yan_1279_00fa[0xe] = -0x20;
  s_This_program_will_initialize_Yan_1279_00fa[0xf] = -0x3b;
  iVar11 = iRam00010877;
  while( true ) {
    puVar17 = (undefined2 *)0x0;
    puVar19 = (undefined2 *)0x0;
    s_This_program_will_initialize_Yan_1279_00fa._10_2_ = 0xfff;
    if (uVar15 < 0xfff) {
      s_This_program_will_initialize_Yan_1279_00fa._10_2_ = uVar15;
    }
    for (iVar13 = s_This_program_will_initialize_Yan_1279_00fa._10_2_ << 3; iVar13 != 0;
        iVar13 = iVar13 + -1) {
      puVar6 = puVar19;
      puVar19 = puVar19 + 1;
      puVar4 = puVar17;
      puVar17 = puVar17 + 1;
      *puVar6 = *puVar4;
    }
    uVar15 = uVar15 - s_This_program_will_initialize_Yan_1279_00fa._10_2_;
    if (uVar15 == 0) break;
    iVar14 = iVar14 + s_This_program_will_initialize_Yan_1279_00fa._10_2_;
    iVar11 = iVar11 + s_This_program_will_initialize_Yan_1279_00fa._10_2_;
  }
  s_This_program_will_initialize_Yan_1279_00fa[10] = (char)DAT_1279_0000;
  s_This_program_will_initialize_Yan_1279_00fa[0xb] = DAT_1279_0000._1_1_;
  s_This_program_will_initialize_Yan_1279_00fa[8] = (char)DAT_1279_0002;
  s_This_program_will_initialize_Yan_1279_00fa[9] = DAT_1279_0002._1_1_;
  s_This_program_will_initialize_Yan_1279_00fa[6] = (char)DAT_1279_0004;
  s_This_program_will_initialize_Yan_1279_00fa[7] = DAT_1279_0004._1_1_;
  s_This_program_will_initialize_Yan_1279_00fa[4] = -0x50;
  s_This_program_will_initialize_Yan_1279_00fa[5] = '&';
  FUN_1265_00f6();
  s_This_program_will_initialize_Yan_1279_00fa[4] = -0x44;
  s_This_program_will_initialize_Yan_1279_00fa[5] = '&';
  FUN_1265_00f6();
  s_This_program_will_initialize_Yan_1279_00fa[4] = 'y';
  s_This_program_will_initialize_Yan_1279_00fa[5] = '\x12';
  s_This_program_will_initialize_Yan_1279_00fa[2] = -0x37;
  s_This_program_will_initialize_Yan_1279_00fa[3] = '&';
  FUN_1265_00f6();
  puVar17 = (undefined2 *)0x0;
  for (iVar14 = 0x80; uVar12 = s_This_program_will_initialize_Yan_1279_00fa._12_2_, iVar14 != 0;
      iVar14 = iVar14 + -1) {
    puVar4 = puVar17;
    puVar17 = puVar17 + 1;
    *puVar4 = 0;
  }
  s_least_once_when_you_start_up_the_1279_0146[6] = '\a';
  s_least_once_when_you_start_up_the_1279_0146[7] = '\0';
  s_least_once_when_you_start_up_the_1279_0146[8] = '\x06';
  s_least_once_when_you_start_up_the_1279_0146[9] = '\0';
  s_least_once_when_you_start_up_the_1279_0146[0x3e] =
       s_This_program_will_initialize_Yan_1279_00fa[6];
  s_least_once_when_you_start_up_the_1279_0146[0x3f] =
       s_This_program_will_initialize_Yan_1279_00fa[7];
  s_least_once_when_you_start_up_the_1279_0146[0x3c] =
       s_This_program_will_initialize_Yan_1279_00fa[8];
  s_least_once_when_you_start_up_the_1279_0146[0x3d] =
       s_This_program_will_initialize_Yan_1279_00fa[9];
  s_least_once_when_you_start_up_the_1279_0146[0x40] =
       s_This_program_will_initialize_Yan_1279_00fa[10];
  s_least_once_when_you_start_up_the_1279_0146[0x41] =
       s_This_program_will_initialize_Yan_1279_00fa[0xb];
  s_This_program_will_initialize_Yan_1279_00fa._40_2_ =
       s_This_program_will_initialize_Yan_1279_00fa._4_2_ + *(int *)0x2;
  puVar17 = (undefined2 *)0x81;
  puVar16 = (undefined1 *)0x81;
  DAT_1279_01a0 = *(char *)0x80;
  s_This_program_will_initialize_Yan_1279_00fa._12_2_ =
       s_This_program_will_initialize_Yan_1279_00fa._4_2_ + 1;
  for (iVar14 = (int)DAT_1279_01a0; iVar14 != 0; iVar14 = iVar14 + -1) {
    puVar4 = puVar17;
    puVar17 = (undefined2 *)((int)puVar17 + 1);
    puVar1 = puVar16;
    puVar16 = puVar16 + 1;
    *(undefined1 *)puVar4 = *puVar1;
  }
  *puVar17 = 0;
  uVar9 = s_This_program_will_initialize_Yan_1279_00fa._18_2_;
  uVar8 = s_This_program_will_initialize_Yan_1279_00fa._14_2_;
  uVar12 = s_This_program_will_initialize_Yan_1279_00fa._12_2_;
  if (s_This_program_will_initialize_Yan_1279_00fa._20_2_ != 4) {
    s_least_once_when_you_start_up_the_1279_0146[0x22] = '\b';
    s_least_once_when_you_start_up_the_1279_0146[0x23] = '\0';
  }
  *(undefined2 *)(char *)(s_This_program_will_initialize_Yan_1279_00fa._14_2_ + -2) =
       s_This_program_will_initialize_Yan_1279_00fa._16_2_;
  *(undefined2 *)(uVar8 + -4) = 0;
  *(undefined2 *)(char *)(uVar8 + -6) = uVar9;
  *(undefined2 *)(uVar8 + -8) = 7;
  return 0x1279;
}



/* 1452:042e FUN_1452_042e */

void __cdecl16near FUN_1452_042e(uint param_1)

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
    FUN_1452_06b3();
    return;
  }
  do {
    pcVar5 = (code *)swi(0x21);
    (*pcVar5)();
    if (bVar8) {
      FUN_1452_06b3();
      return;
    }
    puVar4 = (uint *)*(undefined2 *)0x873;
    uVar3 = *(uint *)0x875;
    if (uVar3 < unaff_DI) {
      bVar8 = false;
      if (uVar3 < in_stack_00000000) {
        iVar6 = uVar3 + unaff_BP;
        if (*puVar4 < unaff_DI) goto LAB_1452_0493;
LAB_1452_047e:
        *puVar4 = *puVar4 - unaff_DI;
        puVar1 = puVar4;
        bVar8 = CARRY2(*puVar1,unaff_SI);
        *puVar1 = *puVar1 + unaff_SI;
      }
    }
    else {
      bVar8 = false;
      if (uVar3 < param_1) {
        iVar6 = (uVar3 - unaff_DI) + 0x14db;
        if (unaff_DI <= *puVar4) goto LAB_1452_047e;
LAB_1452_0493:
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



/* 1452:049d FUN_1452_049d */

void __cdecl16near FUN_1452_049d(void)

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
  if (!(bool)in_CF) goto LAB_1452_05a6;
  if (*(int *)0x611 != 0x812) {
    pcVar7 = (char *)(extraout_DX + -1);
    do {
      pcVar7 = pcVar7 + 1;
      cVar4 = *pcVar7;
      if ((cVar4 == ':') || (cVar4 == '\\')) goto LAB_1452_0533;
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
      goto LAB_1452_04e7;
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
  goto LAB_1452_0533;
  while (uVar12 = unaff_DS, *pcVar9 != '\0') {
LAB_1452_04e7:
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
    unaff_DS = 0x1452;
    if ((pcVar11 != (char *)0x82c) && ((pcVar11[-1] != ':' && (pcVar11[-1] != '\\')))) {
      pcVar2 = pcVar11;
      pcVar11 = pcVar11 + 1;
      *pcVar2 = '\\';
    }
    pcVar10 = DAT_1452_0611;
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
    if (!(bool)in_CF) goto LAB_1452_05a6;
  }
LAB_1452_0533:
  do {
    unaff_DS = 0x1452;
    pcVar5 = (code *)swi(0x21);
    (*pcVar5)();
    do {
      pcVar5 = (code *)swi(0x21);
      (*pcVar5)();
    } while (extraout_DL != '\0');
    pcVar5 = (code *)swi(0x21);
    (*pcVar5)();
    DAT_1452_082c = 0x40;
    pcVar5 = (code *)swi(0x21);
    (*pcVar5)();
    pcVar5 = (code *)swi(0x21);
    (*pcVar5)();
    uVar8 = (uint)DAT_1452_082d;
    *(undefined1 *)(uVar8 + 0x82e) = 0;
    bVar13 = DAT_1452_0611 < (char *)0x812;
    if (DAT_1452_0611 == (char *)0x812) {
      if ((*(char *)(uVar8 + 0x82d) != ':') && (*(char *)(uVar8 + 0x82d) != '\\')) {
        *(undefined1 *)(uVar8 + 0x82e) = 0x5c;
        uVar8 = uVar8 + 1;
      }
      pcVar11 = (char *)(uVar8 + 0x82e);
      pcVar7 = DAT_1452_0611;
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
LAB_1452_05a6:
  pcVar5 = (code *)swi(0x21);
  (*pcVar5)();
  if ((bool)in_CF) {
    FUN_1452_06b3();
    return;
  }
  if (*(int *)0x82c != 0x5a4d) {
    FUN_1452_06b3();
    return;
  }
  bVar13 = false;
  pcVar5 = (code *)swi(0x21);
  (*pcVar5)();
  if (bVar13) {
    FUN_1452_06b3();
    return;
  }
  pcVar5 = (code *)swi(0x21);
  (*pcVar5)();
  if (bVar13) {
    FUN_1452_06b3();
    return;
  }
  pcVar5 = (code *)swi(0x21);
  (*pcVar5)();
  if (bVar13) {
    FUN_1452_06b3();
    return;
  }
  return;
}



/* 1452:0638 FUN_1452_0638 */

void __cdecl16near FUN_1452_0638(void)

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
      FUN_1452_06c2();
      return;
    }
    bVar3 = uVar2 < *(uint *)0x87f;
    pcVar1 = (code *)swi(0x21);
    (*pcVar1)();
    if (bVar3) {
      FUN_1452_06c2();
      return;
    }
    pcVar1 = (code *)swi(0x21);
    (*pcVar1)();
    if (bVar3) {
      FUN_1452_06c2();
      return;
    }
  }
  return;
}



/* 1452:0672 FUN_1452_0672 */

int __cdecl16near FUN_1452_0672(void)

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



/* 1452:06ad FUN_1452_06ad */

void __cdecl16far FUN_1452_06ad(void)

{
  code *pcVar1;
  
  pcVar1 = (code *)swi(0x21);
  (*pcVar1)();
  pcVar1 = (code *)swi(0x21);
  (*pcVar1)();
  return;
}



/* 1452:06b3 FUN_1452_06b3 */

void __cdecl16far FUN_1452_06b3(void)

{
  code *pcVar1;
  
  pcVar1 = (code *)swi(0x21);
  (*pcVar1)();
  pcVar1 = (code *)swi(0x21);
  (*pcVar1)();
  return;
}



/* 1452:06b8 FUN_1452_06b8 */

void __cdecl16far FUN_1452_06b8(void)

{
  code *pcVar1;
  
  pcVar1 = (code *)swi(0x21);
  (*pcVar1)();
  pcVar1 = (code *)swi(0x21);
  (*pcVar1)();
  return;
}



/* 1452:06bd FUN_1452_06bd */

void __cdecl16far FUN_1452_06bd(void)

{
  code *pcVar1;
  
  pcVar1 = (code *)swi(0x21);
  (*pcVar1)();
  pcVar1 = (code *)swi(0x21);
  (*pcVar1)();
  return;
}



/* 1452:06c2 FUN_1452_06c2 */

void __cdecl16far FUN_1452_06c2(void)

{
  code *pcVar1;
  
  pcVar1 = (code *)swi(0x21);
  (*pcVar1)();
  pcVar1 = (code *)swi(0x21);
  (*pcVar1)();
  return;
}



/* 1452:06c7 FUN_1452_06c7 */

void __cdecl16far FUN_1452_06c7(void)

{
  code *pcVar1;
  
  pcVar1 = (code *)swi(0x21);
  (*pcVar1)();
  pcVar1 = (code *)swi(0x21);
  (*pcVar1)();
  return;
}



/* 1452:06cc FUN_1452_06cc */

void __cdecl16far FUN_1452_06cc(void)

{
  code *pcVar1;
  
  pcVar1 = (code *)swi(0x21);
  (*pcVar1)();
  pcVar1 = (code *)swi(0x21);
  (*pcVar1)();
  return;
}


