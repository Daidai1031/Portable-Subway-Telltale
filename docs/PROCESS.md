# Design Process — Portable Subway Telltale

This document describes the design process, iterations, and decisions behind the **Portable Subway Telltale** project.



## 1. Motivation

The project began with a simple, personal problem:  
living on **Roosevelt Island**, I frequently need to decide whether to rush to the subway or whether I still have time before leaving home.

Although mobile apps provide accurate arrival times, checking a phone repeatedly felt distracting and cognitively heavy for such a small, recurring decision. Inspired by Mark Weiser’s description of a *telltale by the door*, I wanted to design a device that communicates urgency **calmly, peripherally, and without demanding attention**.



## 2. From Numbers to States

### Early Idea: Display Minutes Directly  
My first instinct was to display the number of minutes until the next train. While technically straightforward, this approach required interpretation every time and felt closer to a miniature app than a calm device.

### Key Shift: State-Based Interpretation  
I instead mapped arrival times into **three action-oriented states**:

- **WAIT** (> 7 min): you have time  
- **GO NOW** (3–7 min): leave immediately  
- **ARRIVE** (0–2 min): train is arriving  

The **7-minute threshold** was chosen deliberately—it closely matches my walking time from home to the station, making the state transitions personally meaningful.

This abstraction reduced cognitive load and made the display interpretable in a single glance.



## 3. Choosing the Data Source

I used a real-time subway arrival API that provides predicted minutes for trains at Roosevelt Island station (B06).  
Rather than hard-coding a single subway line, the system dynamically detects whether **F or M** service is active, since service varies by time of day and week.

This decision improved robustness and ensured the telltale remained accurate across different schedules.



## 4. Visual Language and Redundancy

Given the small screen size, I relied heavily on **redundant cues**—multiple signals reinforcing the same state.

### Color
Each state is mapped to a distinct color:
- **WAIT:** grey (calm, neutral)
- **GO NOW:** blue (`#3236A6`)
- **ARRIVE:** orange (`#FF6319`, inspired by MTA signage)

These colors are applied consistently across text, icons, animations, and borders.

### Text
A bold status line (“WAIT~”, “GO NOW!”, “ARRIVE!”) provides explicit confirmation of the current state.



## 5. Pixel Animations as Metaphors

To move beyond static indicators, I introduced **pixel animations** as metaphors for each state:

- **WAIT:** a steaming coffee cup  
- **GO NOW:** a walking figure  
- **ARRIVE:** a moving subway train  

These animations are deliberately low-resolution and loop continuously, reinforcing the state without drawing excessive attention. The animations are scaled up (2×) to remain legible on the small screen.



## 6. Direction Selection and Interaction

The telltale always shows both directions:
- To Manhattan
- To Queens

Two physical buttons allow the user to select which direction is currently relevant. The selected direction drives the main state logic, while the unselected direction is visually de-emphasized using grey text and outlined indicators.

This interaction supports quick switching without navigating menus and keeps the interface simple.



## 7. Representing Time Without Numbers: Edge Flow

One of the later additions was the **edge flow border**: a series of small pixel blocks moving clockwise around the screen.

- The **color** of the border matches the current state.
- The **speed** increases from WAIT → GO NOW → ARRIVE.
- The speed is gently tuned by remaining minutes to avoid jitter.

This element communicates the passage of time in a continuous, ambient way—users can sense urgency increasing without reading exact values.



## 8. Iteration and Technical Constraints

Throughout development, I iterated frequently in response to CircuitPython constraints:

- Pre-allocating display objects instead of resizing them at runtime
- Using sprite sheets and palette-based transparency
- Avoiding excessive blinking to preserve calmness

These constraints shaped the final design and encouraged efficiency and clarity.



## 9. Reflection

This project shifted my thinking from “displaying information” to **interpreting information on behalf of the user**. By combining data processing, state abstraction, and expressive visual design, the telltale becomes less like a dashboard and more like a quiet companion.

Future iterations could further explore portability (keychain form factor), haptic feedback, or adaptive thresholds—but even in its current form, the telltale successfully supports a real, everyday decision.
