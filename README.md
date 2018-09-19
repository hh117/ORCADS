# ORCA DS
ORCA Dialogue System

## Ontology

The `requirements` folder contains the ontology. That is every piece of knowledge that will be hard-coded in the system.

It is divided in three blocks:
*   `dialogue_acts`:
    * `operator`: Dialogue acts produced by robot operator
    * `robot_manager`: Dialogue acts produced by the robot manager (i.e. the system)
* `objects`: all the objects that exist in the simulated oil rig
* `robots`: all the robots that are available in the simulation

### Objects

Objects are defined like this:

```
name: <name> // object name in natural language
id: <id> // unique object id
coordinates: // center coordinates of the object
  - x:
  - y:
  - z:
radius: // spherical area that corresponds to the object
inspection_type: // how the object is inspected (underwater/ground/aerial)
objects: // child objects which are part of the main objects
  - <obj_id1>
  - <obj_id2>
  - ...
```

### Robots

Robots are defined like this:

```
name: <name> // name of the robot in natural language
id: <id> // unique robot id
type: <type> // robot type (terrestrial/aerial/underwater)
sensors: // list of sensors available in the robot (if any, otherwise can be removed)
  -
manipulators: // list of manipulators available in the robot (if any, otherwise can be removed)
  - 
actions: // list of actions that the robot can do (eg.: move, fly, take picture, stream video, ...)
  - 
base_location: // coordinates of the base location
  - x:
  - y:
  - z:
```

### Dialogue Acts

TBD

## Code

`src/python`: Scripts for the interface and the dialogue ORCA dialogue system.

