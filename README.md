# 1. Overview

This package can be used for solving for flow values through edges of a (directed) network/graph, given known values for a subset of edges. The solving facility also detects inconsistencies within the given known values, and can also solve for certain flows/edges if not enough knowns are given to determine all values.

e.g.
![image](network_flow_solver/images/img_01.png)
solves to
![image](network_flow_solver/images/img_02.png)


# 2. Fully Solving a Network

Given a simple flow network with some known values on some edges, Network Flow Solver calculates the remaining flows in the network.

Given the below network as inputs

```py
from network_flow_solver import Edge

edges = [Edge('A','B'), Edge('B','C'), Edge('B','D'), Edge('C','E'), Edge('D','F'), Edge('D','G'), Edge('E','G'), Edge('F','H'), Edge('G','H'), Edge('H','I')]

knowns_list = [(Edge('B','C'), 7), (Edge('D','G'), 2), (Edge('F','H'), 1)]
```

![image](network_flow_solver/images/img_01.png)

The solver finds the flows for all remaining edges

```py
from network_flow_solver import solve_network
solution = solve_network(edges, knowns_list)

# solution = {
#     Edge('A','B'): 10,
#     Edge('B','C'): 7,
#     Edge('B','D'): 3,
#     Edge('C','E'): 7,
#     Edge('D','F'): 1,
#     Edge('D','G'): 2,
#     Edge('E','G'): 7,
#     Edge('F','H'): 1,
#     Edge('G','H'): 9,
#     Edge('H','I'): 10,
# }
```

![image](network_flow_solver/images/img_02.png)

**Note**

In this example, we know that 3 known variables are required to provide a full solution, because the number of known variables is the total number of edges (10), minus the number of total number of nodes (9: A to I), add the number of source/sink nodes (2: A and I).

This calculation provides the number of required known variables for any network. If the number of knowns given exceeds this, the network is guaranteed to be *overconstrained*, and a solution will not be given.

And even if the total number of knowns is equal or less than required, they may overconstrain sub-sections of the network.

See *'Overconstraining the Network'* for more information.

# 3. Partially Solving a Network

Even if not enough knowns are given to fully solve the network, the solver will try to solve for as many knowns as it can.

```py
from network_flow_solver import Edge

edges = [Edge('A','B'), Edge('B','C'), Edge('B','D'), Edge('C','E'), Edge('D','F'), Edge('D','G'), Edge('E','G'), Edge('F','H'), Edge('G','H'), Edge('H','I')]

knowns_list = [(Edge('D','G'), 2), (Edge('F','H'), 1)]
```
![image](network_flow_solver/images/img_03.png)
```py
from network_flow_solver import solve_network
solution = solve_network(edges, knowns_list)

# solution = {
#     Edge('B','D'): 3,
#     Edge('D','F'): 1,
#     Edge('D','G'): 2,
#     Edge('F','H'): 1,
# }
```
![image](network_flow_solver/images/img_04.png)

# 4. Overconstraining the Network

The solving facility of this package expects known variables to not overconstrain the system - for example the set of known values in this next network.

```py
from network_flow_solver import Edge

edges = [Edge('A','B'), Edge('B','C'), Edge('B','D'), Edge('C','E'), Edge('D','F'), Edge('D','G'), Edge('E','G'), Edge('F','H'), Edge('G','H'), Edge('H','I')]

knowns_list = [(Edge('B','C'), 7), (Edge('D','G'), 2), (Edge('F','H'), 1), (Edge('H','I'), 10)]
```
![image](network_flow_solver/images/img_05.png)
```py
from network_flow_solver import solve_network
solution = solve_network(edges, knowns_list)

# RedundancyError: Values for 4 edges were given as known, exceeding the (3 == 10 - 9 + 2) total degrees of freedom. Please remove knowns until they are equal or fewer than this.
```

The given knowns must also not overconstrain the network in other ways. For example with the next set of knowns, 'DF' can be calculated both using 'BD=DG+DF' and 'DF=FH'.
```py
from network_flow_solver import Edge

edges = [Edge('A','B'), Edge('B','C'), Edge('B','D'), Edge('C','E'), Edge('D','F'), Edge('D','G'), Edge('E','G'), Edge('F','H'), Edge('G','H'), Edge('H','I')]

knowns_list = [(Edge('B','D'), 3), (Edge('D','G'), 2), (Edge('F','H'), 1)]
```
![image](network_flow_solver/images/img_06.png)
```py
from network_flow_solver import solve_network
solution = solve_network(edges, knowns_list)

# RedundancyError: The value of Edge(source='F', sink='H') is given as a known value, but can also be calculated from known values [Edge(source='B', sink='D'), Edge(source='D', sink='G'), Edge(source='F', sink='H')]. Please remove one of these edges from the list of knowns to stop overconstraining the system.
```

# 5. Known Issues for Partial Solving / Auxiliary Equations

The solving algorithm is simple and works well when fully solving a network, but can run into issues when solving a network partially, for certain given knowns, such as the following:

```py
from network_flow_solver import Edge

edges = [Edge('A','B'), Edge('B','C'), Edge('B','D'), Edge('C','E'), Edge('D','F'), Edge('D','G'), Edge('E','G'), Edge('F','H'), Edge('G','H'), Edge('H','I')]

knowns_list = [(Edge('B','D'), 3), (Edge('D','G'), 2), (Edge('F','H'), 1)]
```
![image](network_flow_solver/images/img_07.png)

Attempting to solve this normally yields the following result

```py
from network_flow_solver import solve_network
solution = solve_network(edges, knowns_list)

# solution = {
#     Edge('A','B'): 10,
#     Edge('B','C'): 7,
#     Edge('B','D'): 3,
#     Edge('C','E'): 7,
#     Edge('E','G'): 7,
# }
```

![image](network_flow_solver/images/img_08.png)

Some edges are correctly solved for - however, with 'BC' and 'BD' given, we also know that the value of 'HI' should be 10. This is because we assume flow is conserved, so AB must equal HI. We can explicitly specify this equality as an *auxiliary equation*, and network is correctly solved.

```py
from network_flow_solver import solve_network, AuxiliaryEquation

aux_eqns = [AuxiliaryEquation([Edge('A','B')], [Edge('H','I')])]
solution = solve_network(edges, knowns_list, aux_eqns)

# solution = {
#     Edge('A','B'): 10,
#     Edge('B','C'): 7,
#     Edge('B','D'): 3,
#     Edge('C','E'): 7,
#     Edge('E','G'): 7,
#     Edge('H','I'): 10,
# }
```
![image](network_flow_solver/images/img_09.png)
