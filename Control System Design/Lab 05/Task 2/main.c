#include "F2806x_Device.h"

#define pi 3.14159

// Quadrature encoder is a sensor for measuring the position of rotor

// Time interrupt will be used to establish time periodicity
// for both writing actuators and reading from the sensors
interrupt void TimerIsr (void);

float32 maxvoltage = 24;
float32 avgvoltage = 20;
int32 theta = 0;
float32 duty = 0;
Uint16 t = 0;
Uint16 k = 0;
Uint16 i = 0;
float32 V[2000];
float32 vpin = 0;
float32 angle[2000];

int main(void)
{
    asm(" EALLOW");             // Activate an access to restricted registers
    SysCtrlRegs.WDCR = 0x68;    // Deactivate WatchDog Timer


    // Set PMW Multiplexors to general purpose input output
    GpioCtrlRegs.GPAMUX1.bit.GPIO0 = 1; // PWM pin A; ePMW1 output A(O)
    GpioCtrlRegs.GPAMUX1.bit.GPIO1 = 0; // PWM pin A reset; general purpose I/O
    GpioCtrlRegs.GPAMUX1.bit.GPIO2 = 1; // PWM pin B; ePMW2 output A(O)
    GpioCtrlRegs.GPAMUX1.bit.GPIO3 = 0; // PWM pin B reset; general purpose I/O

    GpioCtrlRegs.GPAMUX2.bit.GPIO20 = 1; // QEP1A
    GpioCtrlRegs.GPAMUX2.bit.GPIO21 = 1; // QEP1B

    GpioCtrlRegs.GPADIR.bit.GPIO1 = 1; // Configure this pin as an output
    GpioCtrlRegs.GPADIR.bit.GPIO3 = 1; // Configure this pin as an output
    GpioDataRegs.GPASET.bit.GPIO1 = 1; // RESETA; reset by setting to 0
    GpioDataRegs.GPASET.bit.GPIO3 = 1; // RESETB; reset by setting to 0


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


    // Set PMW frequency
    SysCtrlRegs.PCLKCR1.bit.EPWM1ENCLK = 1; // Enable EPWM1 Clock
    SysCtrlRegs.PCLKCR1.bit.EPWM2ENCLK = 1; // Enable EPWM2 Clock

    EPwm1Regs.TBCTL.bit.CTRMODE = 10;   // Up-Down Count Mode
    EPwm2Regs.TBCTL.bit.CTRMODE = 10;   // Up-Down Count Mode

    EPwm1Regs.TBPRD = 1500; // Set up Vres for Pwm1
    EPwm2Regs.TBPRD = 1500; // Set up Vres for Pwm2

    EPwm1Regs.TBCTL.bit.HSPCLKDIV = 000;
    EPwm2Regs.TBCTL.bit.HSPCLKDIV = 000;

    EPwm1Regs.TBCTL.bit.CLKDIV = 000;
    EPwm2Regs.TBCTL.bit.CLKDIV = 000;


    // Set EPWM Output Actions
    EPwm1Regs.AQCTLA.bit.CAU = 1; // Force PWM1A output low when the counter is incrementing
    EPwm1Regs.AQCTLA.bit.CAD = 2; // Force PWM1A output high when the counter is decrementing

    EPwm2Regs.AQCTLA.bit.CBU = 2; // Force PWM2A output high when the counter is incrementing
    EPwm2Regs.AQCTLA.bit.CBD = 1; // Force PWM2A output low when the counter is decrementing


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


    // Set up to use interrupt services

    // Load the PIE Vector Table
    PieCtrlRegs.PIECTRL.bit.ENPIE = 1;  // Enable PIE Vector table
    PieVectTable.TINT0 = &TimerIsr;     // Load PIE Vector Table, TimerIsr

    // Enable Interrupts at the PIE Level
    PieCtrlRegs.PIEIER1.bit.INTx7 = 1;  // Enable servicing of CPU Timer 0 interrupt
    PieCtrlRegs.PIEACK.all = 1;         

    // Enable interrupts at the CPU Level
    IER = 1;    // ?
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
    if(i<2000)
    {
        theta = EQep1Regs.QPOSCNT;

        if(t>=200 && t<399 | t>=600 && t<799 )
        {
            avgvoltage = 0;
        }

        if(t>=400 && t<599)
        {
            avgvoltage = -20;
        }

        if(t==0 | (t>0 && t<199))
        {
            avgvoltage = 20;
        }

        duty = (avgvoltage/(2*maxvoltage)) + 0.5;

        EPwm1Regs.CMPA.half.CMPA = 1500 * duty;
        EPwm2Regs.CMPB = 1500 * duty;

        t++;

        if(t>=799)
        {
            t=0;
        }

        angle[i]=(2*pi*theta/4000);

        V[i] = avgvoltage;

        i++;
    }
    else
    {
            if(t>=200 && t<399 | t>=600 && t<799 )
            {
                avgvoltage = 0;
            }

            if(t>=400 && t<599)
            {
                avgvoltage = -20;
            }

            if(t==0 | (t>0 && t<199))
            {
                avgvoltage = 20;
            }

            duty = (avgvoltage/(2*maxvoltage)) + 0.5;

            EPwm1Regs.CMPA.half.CMPA = 1500 * duty;
            EPwm2Regs.CMPB = 1500 * duty;

            t++;

            if(t>=799)
            {
                t=0;
            }
    }

    PieCtrlRegs.PIEACK.all = PIEACK_GROUP1; // clears respective interrupt bit/acknowledges interrupt in Group 1 (CPU Timer 0)

}

