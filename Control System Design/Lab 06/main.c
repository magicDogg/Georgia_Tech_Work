#include "F2806x_Device.h"

#define pi 3.14159

// Quadrature encoder is a sensor for measuring the position of rotor

// Time interrupt will be used to establish time periodicity
// for both writing actuators and reading from the sensors
interrupt void TimerIsr (void);

float32 maxvoltage = 24;
float32 avgvoltage = 0;
int32 sensor = 0;
float32 theta = 0;
float32 duty = 0;
Uint16 i = 0;
Uint16 n = 0;
float32 V[2000];
float32 angle[2000];

Uint16 count = 0;
Uint16 countMax = 1000;

float32 desiredR = 10*pi;
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
Bool antiwindup = 1;

int main(void)
{
// Define Parameters
L1 = 2*lambda_e - alpha;
L2 = (lambda_e-alpha)*(lambda_e-alpha);
K11 = 3/beta*lambda_r*lambda_r;
K12 = 1/beta*(3*lambda_r-alpha);
K2 = 1/beta*lambda_r*lambda_r*lambda_r;
// Access to protected registers and deactivate watchdog timer
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
// Changes output every 1 second
if(count == countMax)
{
if(r != 0)
    r = 0;
else
    r = desiredR;

count = 0; // Reset the counter variable
}
else
count++;

// Read value from quadrature
sensor = EQep1Regs.QPOSCNT;
theta = (2*pi*sensor/1000);
// Actuating u(t)
u = -K11*xhat1 - K12*xhat2 - K2*sigma;
    // Anti-windup for voltage
if(u >= maxvoltage) // Check for saturation
{
duty = 1;
avgvoltage = 24;
}
else if(u<=-maxvoltage)
{
duty = 0;
avgvoltage = -24;
}
else
{
avgvoltage = u;
duty = (avgvoltage/(2*maxvoltage)) + 0.5;
}

// Set duty cycle
    EPwm1Regs.CMPA.half.CMPA = 1500 * duty;
    EPwm2Regs.CMPB = 1500 * duty;
// Update controller signals
new_xhat1 = xhat1 + T*xhat2 - T*L1*(xhat1 - theta);
new_xhat2 = xhat2 - T*alpha*xhat2 + T*beta*u -T*L2*(xhat1 - theta);
xhat1 = new_xhat1;
xhat2 = new_xhat2;

// Anti-windup for sigma
if((u >= maxvoltage || u <= -maxvoltage))
{
    sigma = sigma + T*(theta - r);
}
else
sigma = sigma + T*(theta - r);

n++;

// Updating values
if(i < 2000 & n>1000)
{
    angle[i] = theta;
    V[i] = avgvoltage;
    i++;
}

    PieCtrlRegs.PIEACK.all = PIEACK_GROUP1; // clears respective interrupt bit/acknowledges interrupt in Group 1 (CPU Timer 0)

}
