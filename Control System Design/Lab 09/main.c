#include "F2806x_Device.h"
#include "math.h"

#define pi 3.14159

interrupt void TimerIsr (void);

float32 maxV = 24;
float32 avgVa;
float32 avgVb;
float32 avgVc;
int32 sensor = 0;
float32 theta = 0;
float32 duty1;
float32 duty2;
float32 duty3;
float32 volCoeff;
float32 phiV;
float32 alphaV;
Uint32 i = 0;
Uint32 n = 0;
float32 Y[1000];
float32 U[1000];

float32 g = 0.9256;
float32 vd = 1.4505;
float32 K = 0.0926;
float32 rho = 0;
float32 thetaE = 0;

Uint16 count = 0;
Uint16 countMax = 5000;

float32 r = 0;
float32 u = 0;
float32 sigma = 0;
float32 xhat1 = 0;
float32 xhat2 = 0;
float32 new_xhat1 = 0;
float32 new_xhat2 = 0;
float32 alpha = 9.1728;
float32 beta = 99.0886;
float32 lambda_r = 25;
float32 lambda_e = 125;
float32 T = 0.0002;
float32 K11, K12, K2, L1, L2;

int main(void)
{
    // Define Parameters
    L1 = 2*lambda_e - alpha;
    L2 = (lambda_e-alpha)*(lambda_e-alpha);
    K11 = 3/beta*lambda_r*lambda_r;
    K12 = 1/beta*(3*lambda_r-alpha);
    K2 = 1/beta*lambda_r*lambda_r*lambda_r;

    volCoeff = sqrt(0.2222222222);
    i = 0;
    n = 0;
    r = 0;

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


    EPwm1Regs.CMPA.half.CMPA = 750;
    EPwm2Regs.CMPA.half.CMPA = 750;
    EPwm3Regs.CMPA.half.CMPA = 750;

    GpioDataRegs.GPASET.bit.GPIO1 = 1; // RESETA; reset by setting to 0
    GpioDataRegs.GPASET.bit.GPIO3 = 1; // RESETB; reset by setting to 0
    GpioDataRegs.GPASET.bit.GPIO5 = 1; // RESETC; reset by setting to 0

    // Calculate Line-to-Line voltages
       avgVa = 13.2;
       avgVb = 10.8;
       avgVc = 12;

       // Set duty cycles
       duty1 = avgVa/maxV;
       duty2 = avgVb/maxV;
       duty3 = avgVc/maxV;

       EPwm1Regs.CMPA.half.CMPA = 1500*duty1;
       EPwm2Regs.CMPA.half.CMPA = 1500*duty2;
       EPwm3Regs.CMPA.half.CMPA = 1500*duty3;

    while(i<4000000)
    {
        i++;
    }

    // Enable and Initialize Module Counter
        EQep1Regs.QPOSINIT = 0;         // Initialize the position value
        EQep1Regs.QEPCTL.bit.QPEN = 1;  // Enable Position counter
        EQep1Regs.QEPCTL.bit.SWI = 1;   // Initialize Position counter


    i = 0;

    // Set up to use interrupt services

    // Load the PIE Vector Table
    PieCtrlRegs.PIECTRL.bit.ENPIE = 1;  // Enable PIE Vector table
    PieVectTable.TINT0 = &TimerIsr;     // Load PIE Vector Table, TimerIsr

    // Enable Interrupts at the PIE Level
    PieCtrlRegs.PIEIER1.bit.INTx7 = 1;  // Enable servicing of CPU Timer 0 interrupt
    PieCtrlRegs.PIEACK.all = 1;         //

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
    // Changes output every 1 second
    if(count == countMax)
    {
        if(r != 0)
            r = 0;
        else
            r = 2*pi;

        count = 0; // Reset the counter variable
    }
    else
        count++;

    // Read value from quadrature
    sensor = EQep1Regs.QPOSCNT;
    theta = (2*pi*sensor/4000);

    // Actuating u(t)
    u = -K11*xhat1 - K12*xhat2 - K2*sigma;

    // Anti-windup for sigma
    if((u >= maxV || u <= -maxV))
    {
        sigma = sigma;
    }
    else
        sigma = sigma + T*(theta - r);

    // Anti-windup for voltage
    if(u >= maxV) // Check for saturation
    {
        u = maxV;
    }
    else if(u <= -maxV)
    {
        u = -maxV;
    }

    // Calculate alphaV
    alphaV = sqrt(u*u + vd*vd);

    // Calculate phiV
    phiV = atan2(u, vd);

    // Update rho and thetaE
    rho = rho + 7.1027*T*u;
    thetaE = 0.3426*theta + rho;

    // Update controller signals
    new_xhat1 = xhat1 + T*xhat2 - T*L1*(xhat1 - theta);
    new_xhat2 = xhat2 - T*alpha*xhat2 + T*beta*u -T*L2*(xhat1 - theta);
    xhat1 = new_xhat1;
    xhat2 = new_xhat2;

    // Calculate Line-to-Line voltages
    avgVa = 12 + volCoeff*alphaV*cos(2*thetaE+phiV-pi/6);
    avgVb = 12 + volCoeff*alphaV*cos(2*thetaE+phiV-pi/6-2*pi/3);
    avgVc = 12 + volCoeff*alphaV*cos(2*thetaE+phiV-pi/6+2*pi/3);

    // Set duty cycles
    duty1 = avgVa/maxV;
    duty2 = avgVb/maxV;
    duty3 = avgVc/maxV;

    // Set duty cycle
    EPwm1Regs.CMPA.half.CMPA = 1500 * duty1;
    EPwm2Regs.CMPA.half.CMPA = 1500 * duty2;
    EPwm3Regs.CMPA.half.CMPA = 1500 * duty3;

    if (n%20 == 0)
    {

        if(i < 1000)
        {
               Y[i] = theta;
               U[i] = u;
               i++;
        }

    }


    if(n<40000)
        n++;

    PieCtrlRegs.PIEACK.all = PIEACK_GROUP1; // clears respective interrupt bit/acknowledges interrupt in Group 1 (CPU Timer 0)
}
