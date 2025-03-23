## Implementation:

### Main Game Loop:
does what the name tells you.
</br>

### Agents
Agent is a state machine. According to certain input (events) or conditions it changes it's state. Each agent is implemented through a subclass based on the parent agent class. 
</br>

#### Agent attributes: 
- name: name of this specific entity
- type: agent type (drone, animal, poacher)
- states: dictionary of possible states
- active_state: current state of the agent
- controller: controller instance, that is connected to this specific agent 
- base_speed: standard speed (dependent on agent type)
- position: position in pygame
- scan_range: standard scan range (dependent on agent type)
- pygame_stuff
</br>

#### Agent methods:
- update: updates the agent to the changed environment (performs state actions, etc.)
- set_state: changes the state for the agent. Calls the state methods exit and enter.
- move: moves the agent in a specified direction with the speed allowed in this state
- scan_surroundings: Scans the agent's surrounding for other agents of a specified type. 
</br>

#### Drone specific attributes:
None
</br>

#### Animal specific attributes:
- thread: Poacher which is hunting / attacking this animal
</br>

#### Poacher specific attributes:
- attack_range: How close a poacher has to be to be able to attack
- attack_duration: How long an attack can last max
- target: Animal which the Poacher is hunting / attacking
</br>


#### Basic agent workflow:
- initialize agent with respective parameters
- set starting state of agent
- for each state:
  - do state action (defined and implemented by specific state)
  - check transition conditions
  - if conditions are met (for drone, if controller says so):
    - change state to new state
</br>


### States
States define the current situation and action portfolio for the agents. States are implemented as childs of the State class and specific to the different agent types
</br>

#### State attributes:
- agent: Which agent the state is assigned to
- speed_modifier: How the base speed of the agent changes in this state
- scan_range_modifier: How the base scan range of the agent changes in this state
- detection_probability: not sure yet
</br>

#### State methods:
- enter: assignes this state to the agent
- exit: removes the agent out of the state
- action: shell method for state specific actions (implemented by subclasses)
- check_transition: Check if agent can transition to another state
</br>


### Controller
Controllers are used to manipulate the agents in the environment. The controllers determine the actions of the agents based on the current state of the agent and the environment. The controllers are implemented as classes that inherit from the Controller class. Controllers also are the interface for the drone to connect to Optimization Algorithms Particle Swarm and Reinforcement Learning.
</br>

#### Controller Methods
- get_direction: Define the direction the agent should move in
- evaluate_state_transition: evaluates if a state transition that is possible should be done (mainly for drone class)
</br>

### Settings
Collection of settings that have to be set for the simulation to work. Can be modified without having to touch the actual implementation.
</br>
