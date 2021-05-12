#include "F2806x_Device.h"

/**
 * main.c
 */
Uint32 i = 0;
Uint32 j;

int main(void)
{
    i = 0;
    int64 count = 0;
    if(j == 1)
    {
        asm(" EALLOW");
        SysCtrlRegs.WDCR = 0x68;
        asm(" EDIS");
    }

    if(j == 2)
    {
        asm(" EALLOW");
        SysCtrlRegs.WDCR = 0x28;
        asm(" EDIS");
    }

    while(1)
    {

        count++;
        if(count == 100000)
        {
            i++;
            count = 0;
        }

        if(j == 2)
        {
            asm(" EALLOW");
            SysCtrlRegs.WDKEY = 0x55;
            SysCtrlRegs.WDKEY = 0xAA;
            asm(" EDIS");
        }

    }

	return 0;
}
