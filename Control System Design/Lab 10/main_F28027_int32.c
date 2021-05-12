#include "F2802x_Device.h"

void main(void) {
	
	EALLOW;
	SysCtrlRegs.WDCR = 0x68;
	SysCtrlRegs.PLLSTS.bit.DIVSEL = 0;
	SysCtrlRegs.PLLSTS.bit.MCLKOFF = 1;
	SysCtrlRegs.PLLCR.bit.DIV = 6;
	while(SysCtrlRegs.PLLSTS.bit.PLLLOCKS != 1);
	SysCtrlRegs.PLLSTS.bit.MCLKOFF = 0;
	SysCtrlRegs.PLLSTS.bit.DIVSEL = 3;
	GpioCtrlRegs.GPADIR.bit.GPIO0 = 1;
	GpioCtrlRegs.GPADIR.bit.GPIO1 = 1;
	GpioCtrlRegs.GPADIR.bit.GPIO2 = 1;
	GpioCtrlRegs.GPADIR.bit.GPIO3 = 1;
	EDIS;
	GpioDataRegs.GPASET.bit.GPIO0 = 1;
	GpioDataRegs.GPASET.bit.GPIO1 = 1;
	GpioDataRegs.GPASET.bit.GPIO2 = 1;
	GpioDataRegs.GPASET.bit.GPIO3 = 1;

	int32 j, m, n, p;

	int32 m3[5][5] = {							// first breakpoint
			{0 , 0 , 0 , 0 , 0},
			{0 , 0 , 0 , 0 , 0},
			{0 , 0 , 0 , 0 , 0},
			{0 , 0 , 0 , 0 , 0},
			{0 , 0 , 0 , 0 , 0} };

	const int32 m1[5][5] = {
			{1, 2, 3, 4, 5},
			{6, 7, 8, 9, 10},
			{11, 12, 13, 14, 15},
			{16, 17, 18, 19, 20},
			{21, 22, 23, 24, 25} };

	const int32 m2[5][5] = {
			{1, 2, 3, 4, 5},
			{6, 7, 8, 9, 10},
			{11, 12, 13, 14, 15},
			{16, 17, 18, 19, 20},
			{21, 22, 23, 24, 25} };

	for(j = 0; j < 100000; j++)
	{
		for(m = 0; m < 5; m++)
		{
			for(p = 0; p < 5; p++)
			{
				m3[m][p] = 0;
				for(n = 0; n < 5; n++)
				{
					m3[m][p] += m1[m][n] * m2[n][p];
				}
			}
		}
	}

	while(1)
	{
		GpioDataRegs.GPACLEAR.bit.GPIO0 = 1;
		GpioDataRegs.GPACLEAR.bit.GPIO1 = 1;
		GpioDataRegs.GPACLEAR.bit.GPIO2 = 1;
		GpioDataRegs.GPACLEAR.bit.GPIO3 = 1;	// second breakpoint
	}

}
