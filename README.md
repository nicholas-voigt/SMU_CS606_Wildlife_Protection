# SMU_CS606_Wildlife_Protection
This is the repository for the group project of the CS606 class at SMU focusing on swarm optimization for poacher detection.

## Background
Swarm behavior and its optimization have undergone intensive research. Many publications aim to introduce algorithms and methods which introduce swarm behavior based on biological processes, such as the movement of a fish swarm. Furthermore, recent years have shown a spike in the application of reinforcement learning for multi-agent-tasks. However, it seems that most research is done under the assumption of a perfect environment and homogeneous swarms. 

## Project Scope
In this project, we would like to introduce an empirical analysis of current state-of-the-art algorithms for swarm-based search optimization in the context of animal and wildlife protection. This scenario not only contains the controlled agents, e.g. drones, and the targets to search for, in this case poachers, but also animal herds themselves. The poachers disguise imposes an additional challenge, as search and identification of them is further complicated. In general, we describe the problem as follows:</br>
Animals often travel in herds. Hence they will try to stay close together and move in random directions (in reallife they are not moving random but this is not part of our research). However, animals do react to poachers if they identify them and try to run away from them. Poachers approach and follow animal herds. They usually prefer smaller herds or lone animals as it simplifies their attack. Furthermore, poachers are well disguised and therefore difficult to identify. Lastly, drones are the controlled agents used to find and identify poachers. The drones have have different operating states: A high-level search allowing to scan large areas in short time to identify animal herds and a low-level search for precise scanning of the environment to identify disguised poachers. While the first mode allows to scan a large area at high speed, scanning accuracy drops. On the contrary, the second mode allows high-precision scanning but is limited to a small range and low speed.</br></br>
Given the constraints of this project, it is not possible to train or apply the proposed algorithms on real-world data. Instead, development and evaluation will be done in a simulation. Hence, a simulator will be developed to accompany the attributes of the different agents and the environment. The simulator will also be the primary focus for algorithm validation and evaluation.

## Project Milestones

|    | Milestones                     | Description                                                                                                           |
| -- | ------------------------------ | --------------------------------------------------------------------------------------------------------------------- |
| 1  | Define Research Scope          | 1. define project scope and research boundaries</br> 2. define different actors</br> 3. define simulation environment |
| 2  | Develop Simulator              | Setup simulator using Pygame framework                                                                                |
| 3  | Design Optimization Algorithms | 1. Single Solution Heuristics: Greedy Hill-Climb, Simulated Annealing, Adaptive Large Neighborhood Search</br> 2. Population Heuristics: Particle Swarm, Ant Colony Optimization</br> 3. Machine Learning: Reinforcement Learning (Q-Learning)                                                                                    |
| 4  | Evaluate Algorithms            | 1. Use-Case Specific Evaluation metrics:</br> time needed for the swarm to identify targets,</br> number of targets identified,</br> energy consumed</br> 2. Process Evaluation metrics: computation time needed,</br> something else???                                                                                           |
| 5  | Write report                   | We all hate it but we have to...                                                                                      |



## Setup

Python Version 3.12

necessary modules: </br>
1. pygame
2. numpy
3. notebook (dev only)
4. matplotlib (dev only)