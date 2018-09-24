# Description

The operator has to perform the inspection of a given part of the rig. The operator has to plan the mission according to the data that she needs to obtain and the environment.

### Expected steps:

1. Inform the robot manager about the landmark/item that is going to be inspected.
2. Ask for robots available.
3. Based on their status, battery level, functionalities and distance from the inspected item decide which robot is going to do the task.
4. Request data needed (e.g.: picture, video stream, ...)
5. Return robot to base location.

The scenario is considered to be successful if robot has provided the data to the operator and return to the base location.

### Possible Problems

* Lost connection with the robot.
* Obstacle on the way.
* Sudden loss of battery from the robot performing the operation. 