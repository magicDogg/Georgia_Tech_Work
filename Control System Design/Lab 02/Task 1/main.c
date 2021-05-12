 #include "F2806x_Device.h"

int main(void)
{
    asm(" EALLOW");             // Activate an access to restricted registers
    SysCtrlRegs.WDCR = 0x28;    // Deactivate WatchDog Timer

    //Set MUXs
    GpioCtrlRegs.GPAMUX2.bit.GPIO17 = 0; //PB1
    GpioCtrlRegs.GPBMUX1.bit.GPIO40 = 0; //PB2
    GpioCtrlRegs.GPAMUX1.bit.GPIO9 = 0;  //LED1
    GpioCtrlRegs.GPAMUX1.bit.GPIO11 = 0; //LED2
    GpioCtrlRegs.GPBMUX1.bit.GPIO34 = 0; //LED3
    GpioCtrlRegs.GPBMUX1.bit.GPIO41 = 0; //LED4

    //Set Directions
    GpioCtrlRegs.GPADIR.bit.GPIO17 = 0; // Input
    GpioCtrlRegs.GPBDIR.bit.GPIO40 = 0; // Input
    GpioCtrlRegs.GPADIR.bit.GPIO9 = 1;  // Output
    GpioCtrlRegs.GPADIR.bit.GPIO11 = 1; // Output
    GpioCtrlRegs.GPBDIR.bit.GPIO34 = 1; // Output
    GpioCtrlRegs.GPBDIR.bit.GPIO41 = 1; // Output

    SysCtrlRegs.WDCR = 0x68;    // Activate WatchDog Timer again
    asm(" EDIS");               // Deactivate an access to restricted registers

    // Set LED 3 and 4 to = 0 because I don't need them
    GpioDataRegs.GPBSET.bit.GPIO41 = 0;
    GpioDataRegs.GPBSET.bit.GPIO34 = 0;

    while(1)
    {
        // Logic for PB1
        if(GpioDataRegs.GPADAT.bit.GPIO17 == 0)     // If PB0 is pushed
            GpioDataRegs.GPASET.bit.GPIO9 = 1;      // Light the LED1
        else
            GpioDataRegs.GPACLEAR.bit.GPIO9 = 1;    // Otherwise, clear the light from LED1

        // Logic for PB2
        if(GpioDataRegs.GPBDAT.bit.GPIO40 == 0)
            GpioDataRegs.GPASET.bit.GPIO11 = 1;
        else
            GpioDataRegs.GPACLEAR.bit.GPIO11 = 1;

        // Reset WatchDog Timer logics
        asm(" EALLOW");
        SysCtrlRegs.WDKEY = 0x55;
        SysCtrlRegs.WDKEY = 0xAA;-
        asm(" EDIS");
    }


    return 0;
}
