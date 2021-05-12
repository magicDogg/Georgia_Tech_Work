#include "F2806x_Device.h"
struct ECAN_REGS ECanaCopy;
#define pi 3.14159

/**
 * main.c
 */
Uint8 PB1;
Uint8 PB2;
Uint8 hex;
Uint8 i;
float32 r;
Uint8 count = 0;
float32 t = 0;
Uint32 rCasted;

interrupt void TimerIsr(void);

int main(void)
{
    count = 0;
    t = 0;
    r = 0;

    asm(" EALLOW");             // Activate an access to restricted registers
    SysCtrlRegs.WDCR = 0x68;    // Deactivate WatchDog Timer


    //Set up push buttons and HEX encoder
    //Set MUXs
    GpioCtrlRegs.GPAMUX2.bit.GPIO17 = 0; //PB1
    GpioCtrlRegs.GPBMUX1.bit.GPIO40 = 0; //PB2

    // HEX 3,2,1,0
    GpioCtrlRegs.GPAMUX1.bit.GPIO15 = 0;
    GpioCtrlRegs.GPAMUX1.bit.GPIO14 = 0;
    GpioCtrlRegs.GPAMUX1.bit.GPIO13 = 0;
    GpioCtrlRegs.GPAMUX1.bit.GPIO12 = 0;


    //Set Directions
    GpioCtrlRegs.GPADIR.bit.GPIO17 = 0; // Input
    GpioCtrlRegs.GPBDIR.bit.GPIO40 = 0; // Input
    //For Hex
    GpioCtrlRegs.GPADIR.bit.GPIO15 = 0;
    GpioCtrlRegs.GPADIR.bit.GPIO14 = 0;
    GpioCtrlRegs.GPADIR.bit.GPIO13 = 0;
    GpioCtrlRegs.GPADIR.bit.GPIO12 = 0;



    // Basic set up in order to set up correct frequencies
    // Follow the chart to set up Clock Timer
    SysCtrlRegs.PLLSTS.bit.DIVSEL = 0;
    SysCtrlRegs.PLLSTS.bit.MCLKOFF = 1;
    SysCtrlRegs.PLLCR.bit.DIV = 18; // fCPU = 90MHz
    while(SysCtrlRegs.PLLSTS.bit.PLLLOCKS != 1) { }
    SysCtrlRegs.PLLSTS.bit.MCLKOFF = 0;
    SysCtrlRegs.PLLSTS.bit.DIVSEL = 2;
     // Set Timer frequency
    CpuTimer0Regs.PRD.all = 89999; // fTMR = 1kHz
     // Preparation steps to use CPU Timer 0
    CpuTimer0Regs.TCR.bit.TSS = 1;
    CpuTimer0Regs.TCR.bit.TRB = 1;
    CpuTimer0Regs.TCR.bit.TIE = 1;
    CpuTimer0Regs.TCR.bit.TSS = 0;
     // Enable Time Base Clock
    SysCtrlRegs.PCLKCR0.bit.TBCLKSYNC = 1;
      // Load the PIE Vector Table
    PieCtrlRegs.PIECTRL.bit.ENPIE = 1;  // Enable PIE Vector table
    PieVectTable.TINT0 = &TimerIsr;     // Load PIE Vector Table, TimerIsr
     // Enable Interrupts at the PIE Level
    PieCtrlRegs.PIEIER1.bit.INTx7 = 1;  // Enable servicing of CPU Timer 0 interrupt
    PieCtrlRegs.PIEACK.all = 1;        
    
    // Enable interrupts at the CPU Level
    IER = 1;    // ?
    EINT;       // Globally enable CPU interrupt


    // This is for CAN

    // Set Pin Multiplexer
    GpioCtrlRegs.GPAMUX2.bit.GPIO30 = 01;
    GpioCtrlRegs.GPAMUX2.bit.GPIO31 = 01;

    // Enable Module Clock
    SysCtrlRegs.PCLKCR0.bit.ECANAENCLK = 1;

    // Enable Pin Functions
    ECanaCopy.CANTIOC.all = ECanaRegs.CANTIOC.all;
    ECanaCopy.CANTIOC.bit.TXFUNC = 1;
    ECanaRegs.CANTIOC.all = ECanaCopy.CANTIOC.all;
    ECanaCopy.CANRIOC.all = ECanaRegs.CANRIOC.all;
    ECanaCopy.CANRIOC.bit.RXFUNC = 1;
    ECanaRegs.CANRIOC.all = ECanaRegs.CANRIOC.all;

    // Set Timing Parameters
    ECanaCopy.CANBTC.all = ECanaRegs.CANBTC.all;
    ECanaCopy.CANBTC.bit.TSEG1REG = 6;
    ECanaCopy.CANBTC.bit.TSEG2REG = 6; // Together, time quanta per bit will be 15
    ECanaCopy.CANBTC.bit.BRPREG = 5; // It makes bit rate prescaler become 6, so fbus will be 0.5Mbps
    ECanaRegs.CANBTC.all = ECanaCopy.CANBTC.all;

    // Active Normal Operation
    ECanaCopy.CANMC.all = ECanaRegs.CANMC.all;
    ECanaCopy.CANMC.bit.CCR = 0;
    ECanaRegs.CANMC.all = ECanaCopy.CANMC.all;

    do ECanaCopy.CANES.all = ECanaRegs.CANES.all;
    while (ECanaCopy.CANES.bit.CCE != 0);

    // Configure Mailboxes
    // Use Mail Box 0 as a Transmitter
    ECanaMboxes.MBOX0.MSGCTRL.all = 0;
    ECanaMboxes.MBOX0.MSGCTRL.all = 3;
    ECanaMboxes.MBOX0.MSGID.all = 100;
    ECanaCopy.CANMD.all = ECanaRegs.CANMD.all;
    ECanaCopy.CANMD.bit.MD0 = 0; // Transmitter
    ECanaRegs.CANMD.all = ECanaCopy.CANMD.all;
    ECanaCopy.CANME.all = ECanaRegs.CANME.all;
    ECanaCopy.CANME.bit.ME0 = 1;
    ECanaRegs.CANME.all = ECanaCopy.CANME.all;


    SysCtrlRegs.WDCR = 0x28;    // Activate WatchDog Timer again

    asm(" EDIS");               // Deactivate an access to restricted registers


    while(1)
    {
        // Reset WatchDog Timer logics
        asm(" EALLOW");
        SysCtrlRegs.WDKEY = 0x55;
        SysCtrlRegs.WDKEY = 0xAA;
        asm(" EDIS");
    }

    return 0;
}


interrupt void TimerIsr(void)
{
    if(count < 42)
    {
        r = 1500*t*t;
    }
    else if(count >= 42 && count < 252)
    {
        r = 5*pi + 125*(t-0.14655);
    }
    else if(count >= 252 && count < 294)
    {
        r = 10*pi - 1500*(0.2931 - t)*(0.2931 - t);
    }
    else if(count >= 294 && count < 500)
    {
        r = 10*pi;
    }
    else if(count >= 500 && count < 542)
    {
        r = 10*pi - 1500*(t-0.5)*(t-0.5);
    }
    else if(count >= 542 && count < 752)
    {
        r = 5*pi - 125*(t-0.64655);
    }
    else if(count >= 752 && count < 794)
    {
        r = 1500*(0.7931 - t)*(0.7931 - t);
    }
    else
    {
        r = 0;
    }

    r = r*1e5;
    rCasted = (Uint32) r;

    PB1 = GpioDataRegs.GPADAT.bit.GPIO17;
    PB2 = GpioDataRegs.GPBDAT.bit.GPIO40;
    hex = GpioDataRegs.GPADAT.bit.GPIO15 * 8 + GpioDataRegs.GPADAT.bit.GPIO14 * 4 +  GpioDataRegs.GPADAT.bit.GPIO13 * 2 + GpioDataRegs.GPADAT.bit.GPIO12;

    // Transmit Data
    ECanaMboxes.MBOX0.MDL.byte.BYTE0 = PB1; // Sensor variable from Push button 1 to transmit
    ECanaMboxes.MBOX0.MDL.byte.BYTE1 = PB2; // Sensor variable from Push button 2 to transmit
    ECanaMboxes.MBOX0.MDL.byte.BYTE2 = hex; // Sensor variable from Hex Encoder to transmit
    ECanaMboxes.MBOX0.MDL.all = rCasted;

    ECanaCopy.CANTRS.all = 0;
    ECanaCopy.CANTRS.bit.TRS0 = 1;
    ECanaRegs.CANTRS.all = ECanaCopy.CANTRS.all;

    count++;
    t = t + 0.001;
    if(count == 1000)
    {
        count = 0;
        t = 0;
    }


    PieCtrlRegs.PIEACK.all = PIEACK_GROUP1; // clears respective interrupt bit/acknowledges interrupt in Group 1 (CPU Timer 0)
}
