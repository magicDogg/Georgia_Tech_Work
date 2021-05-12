#include "F2802x_Device.h"

interrupt void BlinkLED(void);
interrupt void External(void);

int count;
int status;

int main(void)
{
                                                                                                                                                                                                              status=0;
    count=0;

    asm(" EALLOW");             // Activate an access to restricted registers
    SysCtrlRegs.WDCR = 0x68;    // Deactivate WatchDog Timer

    // Set MUXs

    // LED 1,2,3,4
    GpioCtrlRegs.GPAMUX1.bit.GPIO0 = 0;
    GpioCtrlRegs.GPAMUX1.bit.GPIO1 = 0;
    GpioCtrlRegs.GPAMUX1.bit.GPIO2 = 0;
    GpioCtrlRegs.GPAMUX1.bit.GPIO3 = 0;

    // PB 3
    GpioCtrlRegs.GPAMUX1.bit.GPIO12 = 0;

    // Set Directions

    // LED 1,2,3,4 : Outputs
    GpioCtrlRegs.GPADIR.bit.GPIO0 = 1;
    GpioCtrlRegs.GPADIR.bit.GPIO1 = 1;
    GpioCtrlRegs.GPADIR.bit.GPIO2 = 1;
    GpioCtrlRegs.GPADIR.bit.GPIO3 = 1;

    // PB 3 : Input
    GpioCtrlRegs.GPADIR.bit.GPIO12 = 0;

    // More setting for PB3'

    // Enable Pull-down resistor
    GpioCtrlRegs.GPAPUD.bit.GPIO12 = 1;
    GpioCtrlRegs.GPAQSEL1.bit.GPIO12 = 10;
    GpioCtrlRegs.GPACTRL.bit.QUALPRD1 = 0x01;

    // Interrupt set up

    // Follow the chart to set up Clock Timer
    SysCtrlRegs.PLLSTS.bit.DIVSEL = 0;
    SysCtrlRegs.PLLSTS.bit.MCLKOFF = 1;
    SysCtrlRegs.PLLCR.bit.DIV = 0;
    while(SysCtrlRegs.PLLSTS.bit.PLLLOCKS != 1) { }
    SysCtrlRegs.PLLSTS.bit.MCLKOFF = 0;
    SysCtrlRegs.PLLSTS.bit.DIVSEL = 3;

    // Set Timer frequency
    CpuTimer0Regs.PRD.all = 1249999; // 16Hz

    // Preparation steps to use CPU Timer 0
    CpuTimer0Regs.TCR.bit.TSS = 1;
    CpuTimer0Regs.TCR.bit.TRB = 1;
    CpuTimer0Regs.TCR.bit.TIE = 1;

    CpuTimer0Regs.TCR.bit.TSS = 0;


    // External interrupt set up
    GpioIntRegs.GPIOXINT1SEL.bit.GPIOSEL = 0x0c;
    XIntruptRegs.XINT1CR.bit.POLARITY = 01;
    XIntruptRegs.XINT1CR.bit.ENABLE = 1;


    // Set up to use interrupt services

    // Load the PIE Vector Table
    PieCtrlRegs.PIECTRL.bit.ENPIE = 1;
    PieVectTable.TINT0 = &BlinkLED;
    PieVectTable.XINT1 = &External;

    // Enable Interrupts at the PIE Level
    PieCtrlRegs.PIEIER1.bit.INTx7 = 1;
    PieCtrlRegs.PIEIER1.bit.INTx4 = 1;
    PieCtrlRegs.PIEACK.all = 1;

    // Enable interrupts at the CPU Level
    IER = 1;
    EINT;

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

interrupt void BlinkLED(void)
{
    asm(" EALLOW");

    if(status == 0)
    {

        if ((count % 16) < 8)
        {
            GpioDataRegs.GPASET.bit.GPIO0 = 1;    // Light the LED1
            GpioDataRegs.GPASET.bit.GPIO1 = 1;
            GpioDataRegs.GPASET.bit.GPIO2 = 1;
            GpioDataRegs.GPASET.bit.GPIO3 = 1;
        }
        else
        {
            // Otherwise, clear the light from LED 1, 2, 3, 4
            GpioDataRegs.GPACLEAR.bit.GPIO0 = 1;

        }
    }
    else if(status == 1)
    {
        if ((count % 8) < 4)
        {
            GpioDataRegs.GPASET.bit.GPIO1 = 1;    // Light the LED2
            GpioDataRegs.GPASET.bit.GPIO0 = 1;
            GpioDataRegs.GPASET.bit.GPIO2 = 1;
            GpioDataRegs.GPASET.bit.GPIO3 = 1;
        }
        else
        {
            // Otherwise, clear the light from LED 1, 2, 3, 4
            GpioDataRegs.GPACLEAR.bit.GPIO1 = 1;
        }
    }
    else if(status == 2)
    {
        if ((count % 4) < 2)
        {
            GpioDataRegs.GPASET.bit.GPIO2 = 1;    // Light the LED3
            GpioDataRegs.GPASET.bit.GPIO0 = 1;
            GpioDataRegs.GPASET.bit.GPIO1 = 1;
            GpioDataRegs.GPASET.bit.GPIO3 = 1;
        }
        else
        {
            // Otherwise, clear the light from LED 1, 2, 3, 4
            GpioDataRegs.GPACLEAR.bit.GPIO2 = 1;
        }
    }
    else
    {
        if (count % 2 == 0)
        {
           GpioDataRegs.GPASET.bit.GPIO3 = 1;    // Light the LED4
           GpioDataRegs.GPASET.bit.GPIO1 = 1;
           GpioDataRegs.GPASET.bit.GPIO2 = 1;
           GpioDataRegs.GPASET.bit.GPIO0 = 1;
        }
        else
        {
           // Otherwise, clear the light from LED 1, 2, 3, 4
           GpioDataRegs.GPACLEAR.bit.GPIO3 = 1;
        }

    }

    count++;

    if(count > 2000)
        count = 0;



    PieCtrlRegs.PIEACK.all = 1; // This one enables PIE to drive a pulse into the CPU; going back to running CPU mode to go back to use while loop

    asm(" EDIS");
}

interrupt void External(void)
{
    status++;

    if(status >= 4)
    {
        status = 0;
    }

    PieCtrlRegs.PIEACK.all = 1;
}
