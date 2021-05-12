#include "F2806x_Device.h"


int main(void)
{
    asm(" EALLOW");
    SysCtrlRegs.WDCR = 0x28;

    // Set MUXs
    // HEX 3,2,1,0
    GpioCtrlRegs.GPAMUX1.bit.GPIO15 = 0;
    GpioCtrlRegs.GPAMUX1.bit.GPIO14 = 0;
    GpioCtrlRegs.GPAMUX1.bit.GPIO13 = 0;
    GpioCtrlRegs.GPAMUX1.bit.GPIO12 = 0;

    //LED 1,2,3,4
    GpioCtrlRegs.GPAMUX1.bit.GPIO9 = 0;
    GpioCtrlRegs.GPAMUX1.bit.GPIO11 = 0;
    GpioCtrlRegs.GPBMUX1.bit.GPIO34 = 0;
    GpioCtrlRegs.GPBMUX1.bit.GPIO41 = 0;

    //Set Directions
    //For Hex
    GpioCtrlRegs.GPADIR.bit.GPIO15 = 0;
    GpioCtrlRegs.GPADIR.bit.GPIO14 = 0;
    GpioCtrlRegs.GPADIR.bit.GPIO13 = 0;
    GpioCtrlRegs.GPADIR.bit.GPIO12 = 0;

    //For LED
    GpioCtrlRegs.GPADIR.bit.GPIO9 = 1;
    GpioCtrlRegs.GPADIR.bit.GPIO11 = 1;
    GpioCtrlRegs.GPBDIR.bit.GPIO34 = 1;
    GpioCtrlRegs.GPBDIR.bit.GPIO41 = 1;

    SysCtrlRegs.WDCR = 0x68;
    asm(" EDIS");


    while(1)
    {
        GpioDataRegs.GPACLEAR.bit.GPIO9 = 1;
        GpioDataRegs.GPACLEAR.bit.GPIO11 = 1;
        GpioDataRegs.GPBCLEAR.bit.GPIO34 = 1;
        GpioDataRegs.GPBCLEAR.bit.GPIO41 = 1;

        GpioDataRegs.GPASET.bit.GPIO9 = GpioDataRegs.GPADAT.bit.GPIO15;
        GpioDataRegs.GPASET.bit.GPIO11 = GpioDataRegs.GPADAT.bit.GPIO14;
        GpioDataRegs.GPBSET.bit.GPIO34 = GpioDataRegs.GPADAT.bit.GPIO13;
        GpioDataRegs.GPBSET.bit.GPIO41 = GpioDataRegs.GPADAT.bit.GPIO12;


        asm(" EALLOW");
        SysCtrlRegs.WDKEY = 0x55;
        SysCtrlRegs.WDKEY = 0xAA;
        asm(" EDIS");
    }


    return 0;
}
