#include "F2806x_Device.h"
#include "math.h"
#define pi 3.14159

/**
 * main.c
 */
float32 x[300];
float32 y[300];

Uint32 i = 0;
Uint32 j;


int main(void)
{
       i = 0;
       int64 count = 0;
           asm(" EALLOW");
           SysCtrlRegs.WDCR = 0x28;
           asm(" EDIS");


    while(1)
    {
        if(count < 300)
        {
            x[count] = (float32)count/100;
            y[count] = 3*cos(2*pi*x[count]) - cos(6*pi*x[count]);
        }

        count++;
        asm(" EALLOW");
        SysCtrlRegs.WDKEY = 0x55;
        SysCtrlRegs.WDKEY = 0xAA;
        asm(" EDIS");




    }

    return 0;
}
