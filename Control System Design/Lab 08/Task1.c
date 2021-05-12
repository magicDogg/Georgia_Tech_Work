#include "F2806x_Device.h"

#define pi 3.14159

interrupt void TimerIsr (void);

float32 maxV = 24;
float32 avgVa = 16;
float32 avgVb = 8;
float32 avgVc = 12;
int32 sensor = 0;
float32 theta = 0;
float32 duty1;
float32 duty2;
float32 duty3;
Uint16 i = 0;
Uint16 n = 0;
float32 V[2000];
float32 angle[2000];

Uint16 count = 0;
Uint16 countMax = 2500;

float32 desiredR = 2*pi;
float32 r = 0;
float32 u = 0;
float32 sigma = 0;
float32 xhat1 = 0;
float32 xhat2 = 0;
float32 new_xhat1 = 0;
float32 new_xhat2 = 0;
float32 alpha = 105;
float32 beta = 584;
float32 lambda_r = 60;
float32 lambda_e = 300;
float32 T = 0.001;
float32 K11, K12, K2, L1, L2;

int main(void)
{
    asm(" EALLOW");             // Activate an access to restricted registers
    SysCtrlRegs.WDCR = 0x68;    // Deactivate WatchDog Timer

    // Set PMW Multiplexors to general purpose input output
    GpioCtrlRegs.GPAMUX1.bit.GPIO0 = 1; // PWM pin A; ePMW1 output
    GpioCtrlRegs.GPAMUX1.bit.GPIO1 = 0; // PWM pin A reset; general purpose I/O
    GpioCtrlRegs.GPAMUX1.bit.GPIO2 = 1; // PWM pin B; ePMW2 output
    GpioCtrlRegs.GPAMUX1.bit.GPIO3 = 0; // PWM pin B reset; general purpose I/O
    GpioCtrlRegs.GPAMUX1.bit.GPIO4 = 1; // PWM pin C; ePMW3 output
    GpioCtrlRegs.GPAMUX1.bit.GPIO5 = 0; // PWM pin C reset; general purpose I/O

    GpioCtrlRegs.GPAMUX2.bit.GPIO20 = 1; // QEP1A
    GpioCtrlRegs.GPAMUX2.bit.GPIO21 = 1; // QEP1B

    GpioCtrlRegs.GPADIR.bit.GPIO1 = 1; // Configure this pin as an output
    GpioCtrlRegs.GPADIR.bit.GPIO3 = 1; // Configure this pin as an output
    GpioCtrlRegs.GPADIR.bit.GPIO5 = 1; // Configure this pin as an output
    GpioDataRegs.GPASET.bit.GPIO1 = 1; // RESETA; reset by setting to 0
    GpioDataRegs.GPASET.bit.GPIO3 = 1; // RESETB; reset by setting to 0
    GpioDataRegs.GPASET.bit.GPIO5 = 1; // RESETC; reset by setting to 0

    // Basic set up in order to set up correct frequencies

    // Follow the chart to set up Clock Timer
    SysCtrlRegs.PLLSTS.bit.DIVSEL = 0;
    SysCtrlRegs.PLLSTS.bit.MCLKOFF = 1;
    SysCtrlRegs.PLLCR.bit.DIV = 18; // fCPU = 90MHz
    while(SysCtrlRegs.PLLSTS.bit.PLLLOCKS != 1) { }
    SysCtrlRegs.PLLSTS.bit.MCLKOFF = 0;
    SysCtrlRegs.PLLSTS.bit.DIVSEL = 2;

    // Set Timer frequency
    CpuTimer0Regs.PRD.all = 17999; // fTMR = 5kHz

    // Preparation steps to use CPU Timer 0
    CpuTimer0Regs.TCR.bit.TSS = 1;
    CpuTimer0Regs.TCR.bit.TRB = 1;
    CpuTimer0Regs.TCR.bit.TIE = 1;
    CpuTimer0Regs.TCR.bit.TSS = 0;


    // Set PMW frequency
    SysCtrlRegs.PCLKCR1.bit.EPWM1ENCLK = 1; // Enable EPWM1 Clock
    SysCtrlRegs.PCLKCR1.bit.EPWM2ENCLK = 1; // Enable EPWM2 Clock
    SysCtrlRegs.PCLKCR1.bit.EPWM3ENCLK = 1; // Enable EPWM2 Clock

    EPwm1Regs.TBCTL.bit.CTRMODE = 10;   // Up-Down Count Mode
    EPwm2Regs.TBCTL.bit.CTRMODE = 10;   // Up-Down Count Mode
    EPwm3Regs.TBCTL.bit.CTRMODE = 10;   // Up-Down Count Mode

    EPwm1Regs.TBPRD = 1500; // Set up Vres for Pwm1
    EPwm2Regs.TBPRD = 1500; // Set up Vres for Pwm2
    EPwm3Regs.TBPRD = 1500; // Set up Vres for Pwm3

    EPwm1Regs.TBCTL.bit.HSPCLKDIV = 000;
    EPwm2Regs.TBCTL.bit.HSPCLKDIV = 000;
    EPwm3Regs.TBCTL.bit.HSPCLKDIV = 000;

    EPwm1Regs.TBCTL.bit.CLKDIV = 000;
    EPwm2Regs.TBCTL.bit.CLKDIV = 000;
    EPwm3Regs.TBCTL.bit.CLKDIV = 000;

    // Set EPWM Output Actions
    EPwm1Regs.AQCTLA.bit.CAU = 1; // Force PWM1A output low when the counter is incrementing
    EPwm1Regs.AQCTLA.bit.CAD = 2; // Force PWM1A output high when the counter is decrementing

    EPwm2Regs.AQCTLA.bit.CAU = 1; // Force PWM2A output high when the counter is incrementing
    EPwm2Regs.AQCTLA.bit.CAD = 2; // Force PWM2A output low when the counter is decrementing

    EPwm3Regs.AQCTLA.bit.CAU = 1; // Force PWM3A output high when the counter is incrementing
    EPwm3Regs.AQCTLA.bit.CAD = 2; // Force PWM3A output low when the counter is decrementing



    // Enable Time Base Clock
    SysCtrlRegs.PCLKCR0.bit.TBCLKSYNC = 1;


    // Enable QEP Module Clock
    SysCtrlRegs.PCLKCR1.bit.EQEP1ENCLK = 1;
    SysCtrlRegs.PCLKCR1.bit.EQEP2ENCLK = 1;


    // Set Moulde Maximum Count
    EQep1Regs.QPOSMAX = 0xFFFFFFFF;
    EQep2Regs.QPOSMAX = 0xFFFFFFFF;


    // Enable and Initialize Module Counter
    EQep1Regs.QPOSINIT = 0;         // Initialize the position value
    EQep1Regs.QEPCTL.bit.QPEN = 1;  // Enable Position counter
    EQep1Regs.QEPCTL.bit.SWI = 1;   // Initialize Position counter

    EQep2Regs.QPOSINIT = 0;         // Initialize the position value
    EQep2Regs.QEPCTL.bit.QPEN = 1;  // Enable Position counter
    EQep2Regs.QEPCTL.bit.SWI = 1;   // Initialize Position counter

    // Set initial duty cycles
        duty1 = 0.5;
        duty2 = 0.5;
        duty3 = 0.5;


    // Set up to use interrupt services

    // Load the PIE Vector Table
    PieCtrlRegs.PIECTRL.bit.ENPIE = 1;  // Enable PIE Vector table
    PieVectTable.TINT0 = &TimerIsr;     // Load PIE Vector Table, TimerIsr

    // Enable Interrupts at the PIE Level
    PieCtrlRegs.PIEIER1.bit.INTx7 = 1;  // Enable servicing of CPU Timer 0 interrupt
    PieCtrlRegs.PIEACK.all = 1;        

    // Enable interrupts at the CPU Level
    IER = 1;    
    EINT;       // Globally enable CPU interrupt

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
    // Set duty cycles
    duty1 = avgVa/maxV;
    duty2 = avgVb/maxV;
    duty3 = avgVc/maxV;

    // Set duty cycle
    EPwm1Regs.CMPA.half.CMPA = 1500 * duty1;
    EPwm2Regs.CMPA.half.CMPA = 1500 * duty2;
    EPwm3Regs.CMPA.half.CMPA = 1500 * duty3;

    PieCtrlRegs.PIEACK.all = PIEACK_GROUP1; // clears respective interrupt bit/acknowledges interrupt in Group 1 (CPU Timer 0)
}
