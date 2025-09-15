# Prompter Plotter
## Introduction


![ Watch the video in the repo! ](https://github.com/user-attachments/assets/4e38d26d-b78d-4b40-9968-4daa16c79359)


I am building a machine that will use AI image generation to process a natural language text prompt into a real life drawing. 

After providing a creative unrestricted request, the user will have to wait and see their prompt slowly comes to life in the physical world.

I wanted to connect my love for machine building with creative artistic work and generative algorithms.

I relied a lot on Jake Read's stepper motor control firmware and circuits. I was also (heavily) inspired Quentin Bolsée's mechanical design idea for the machine itself. So many thanks to both of them. 

## Mechanics


![ Watch the video in the repo! ](https://github.com/user-attachments/assets/ebbefab2-2eee-4592-a7b4-9ad754dcc5d3)


The machine achieves a fast and smooth 2-axis motion by controlling two carriages on only one track. If the distance between the carriages stays the same, and the carriages move along the track, the pointer will move on the x-axis. 

If the distance between the carriages changes however, the v-shaped arm will get pushed \ pulled and create the y-axis motion.

**Specs:**
\
I used two stepper motors, each controlling a different carriage. All custom parts are laser-cut acrylic or 3d-printed PLA. The end effector is controlled by a servo motor that can pick it up or let it 'fall' freely on the working area to accommodate any height imperfection in the surface or the machine.

I also used MGN12 rails for both the main track and the V tracks as well as GT2 timing belts. For the end effector I used a MGN7 rail. 

## Electronics

Each stepper motor is controlled by a XIAO RP2040 microcontroller on Jake's board for a dual H-bridge stepper control. The board takes care of power management as it takes a 20v voltage from an external power supply. Both microcontrollers' clock can are synchronized with each other and the computer running them in order to achieve accurate, full machine level control.

The servo is also controlled by a XIAO RP2040.

## Machine operation software

The whole machine is abstracted to a python instance and can be controlled through a convenient python code. This piece of software mostly takes care of high level issues like setting up the communication and time synchronization, homing the machine, loading and processing machine instructions, etc.

## Image generation 

I am yet to plug in the API of a strong external model for the purpose of image generation but the pipeline of processing its outputs is mostly ready. 

First the user's prompt is edited to fit the machine capabilities (i.e. one color line drawings), then a list of contours is extracted from the generated image. Those are filtered, scaled and sent to the machine as drawing instructions.

![](/assets/contours.png)
