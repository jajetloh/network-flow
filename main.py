from typing import Any, List, Dict, NamedTuple, Optional, Tuple, Union
from copy import deepcopy

ITER_MAX = 100

class Edge(NamedTuple):
    source: Any
    sink: Any

class Node(NamedTuple):
    name: Any
    sources: List[Any]
    sinks: List[Any]

class AuxiliaryEquation(NamedTuple):
    lhs: List[Edge]
    rhs: List[Edge]

class RedundancyError(Exception):
    pass

class AuxiliaryEquationsRequiredException(Exception):
    pass

def solve_for_var(node: Node, solve_for_var: Edge, knowns: Dict[Edge, float]):
    if solve_for_var.sink in node.sinks:
        new_value = sum([knowns[Edge(source, node.name)] for source in node.sources]) - sum([knowns[Edge(node.name, o_sink)] for o_sink in node.sinks if o_sink != solve_for_var.sink])
    elif solve_for_var.source in node.sources:
        new_value = sum([knowns[Edge(node.name, sink)] for sink in node.sinks]) - sum([knowns[Edge(o_source, node.name)] for o_source in node.sources if o_source != solve_for_var.source])
    else:
        raise ValueError('solve_for_var not related to the given node?!')
    return new_value

def solve_for_aux(solve_for_var: Edge, knowns: Dict[Edge, float], aux_eq: AuxiliaryEquation):
    if solve_for_var in aux_eq.lhs:
        new_value = sum([knowns[edge] for edge in aux_eq.rhs]) - sum([knowns[edge] for edge in aux_eq.lhs if edge != solve_for_var])
    elif solve_for_var in aux_eq.rhs:
        new_value = sum([knowns[edge] for edge in aux_eq.lhs]) - sum([knowns[edge] for edge in aux_eq.rhs if edge != solve_for_var])
    else:
        raise ValueError('solve_for_var not related to the given aux_eq?!')
    return new_value

def solve_network(edges: List[Edge], knowns_list: List[Tuple[Edge, float]], auxiliary_equations: List[AuxiliaryEquation] = []) -> Dict[Any, float]:
    # Setup
    knowns = {k:v for k,v in deepcopy(knowns_list)}
    nodes = {name:Node(name, [], []) for edge in edges for name in edge}
    for source, sink in edges:
        nodes[source].sinks.append(sink)
        nodes[sink].sources.append(source)

    varsets: Dict[Tuple[Edge, ...], Any] = {}
    for n, node in nodes.items():
        if len(node.sources) == 0 or len(node.sinks) == 0:
            continue
        varset = [*[Edge(x, n) for x in node.sources], *[Edge(n, x) for x in node.sinks]]
        varset.sort()
        varset = tuple(varset)
        varsets[varset] = {'assoc_node': n}
    for aux_eq in auxiliary_equations:
        varset = [*aux_eq.lhs, *aux_eq.rhs]
        varset.sort()
        varset = tuple(varset)
        varsets[varset] = {'aux_eq': aux_eq}

    # Check redundancy of initial knowns

    ## Each 'central' node has a conservation equation, total in == total out. Hence this number is the number of constraints
    nodes_with_sources_and_sinks = [name for name,node in nodes.items() if len(node.sources) > 0 and len(node.sinks) > 0]
    source_or_sink_nodes = [name for name in nodes.keys() if name not in nodes_with_sources_and_sinks]

    ## Immediately throw error if system is overconstrained by number of knowns exceeding degrees of freedom
    if len(knowns) > len(edges) - len(nodes) + len(source_or_sink_nodes):
        raise RedundancyError(f'Values for {len(knowns)} edges were given as known, exceeding the ({len(edges) - len(nodes) + len(source_or_sink_nodes)} == {len(edges)} - {len(nodes)} + {len(source_or_sink_nodes)}) total degrees of freedom. Please remove knowns until they are equal or fewer than this.')

    ## Otherwise check if system in overconstrained internally
    temp_knowns = []
    knowns_ordered = list(knowns.keys())
    for i, k in enumerate(knowns_ordered):
        if k in temp_knowns:
            raise RedundancyError(f'The value of {k} is given as a known value, but can also be calculated from known values {knowns_ordered[:i+1]}. Please remove one of these edges from the list of knowns to stop overconstraining the system.')
        temp_knowns.append(k)
        for _ in range(ITER_MAX):
            varset_unknowns = {varset:[v for v in varset if v not in temp_knowns] for varset in varsets.keys()}
            varset_single_unknowns = [(k,v[0]) for k,v in varset_unknowns.items() if len(v) == 1]
            if len(varset_single_unknowns) > 0:
                temp_knowns.append(varset_single_unknowns[0][1])
            else:
                break

    # Solve
    
    for _ in range(ITER_MAX):
        varsets_with_single_unknown = {varset:aux_eq for varset, aux_eq in varsets.items() if len([v for v in varset if v not in knowns]) == 1}
        if len(varsets_with_single_unknown) == 0:
            break
        else:
            varset = list(varsets_with_single_unknown)[0]
            var_to_solve = [v for v in varset if v not in knowns][0]
            if var_to_solve in knowns:
                raise RedundancyError(f'{var_to_solve} is overconstrained. Reduce the number of variables affecting {var_to_solve}.')

            aux_eq_or_assoc_node = varsets_with_single_unknown[varset]
            if 'assoc_node' in aux_eq_or_assoc_node:
                assoc_node = aux_eq_or_assoc_node['assoc_node']
                knowns[var_to_solve] = solve_for_var(nodes[assoc_node], var_to_solve, knowns)
            elif 'aux_eq' in aux_eq_or_assoc_node:
                aux_eq = aux_eq_or_assoc_node['aux_eq']
                knowns[var_to_solve] = solve_for_aux(var_to_solve, knowns, aux_eq)
            else:
                raise ValueError(f'aux_eq_or_assoc_node is neither an aux_eq or assoc_node?: {aux_eq_or_assoc_node}')
    
    # Each 'central' node has a conservation equation, total in == total out. Hence this number is the number of constraints
    nodes_with_sources_and_sinks = [name for name,node in nodes.items() if len(node.sources) > 0 and len(node.sinks) > 0]
    # If total constraint equations (incl. aux) and number of given knowns sum to the number of variables (edge count),
    # we expect a complete solution. If we don't have one, we need (more) auxiliary equations for the algorithm to solve fully.
    expect_full_solution = len(nodes_with_sources_and_sinks) + len(auxiliary_equations) + len(knowns_list) == len(edges)
    full_solution_obtained = len(knowns) == len(edges)
    if expect_full_solution and not full_solution_obtained:
        still_unknown_variables = [edge for edge in edges if edge not in knowns]
        raise AuxiliaryEquationsRequiredException('More auxiliary equations are required to solve for these edges:', still_unknown_variables)


    return knowns

if __name__ == '__main__':

    # import igraph as ig
    
    # edges = [Edge(0,1), Edge(1,2), Edge(1,3), Edge(2,4), Edge(3,5), Edge(3,6), Edge(4,6), Edge(5,7), Edge(6,7), Edge(7,8)]
    # # edges = (
    # #     [Edge(0, i) for i in range(11,15+1)]
    # #     + [Edge(i,j) for i in range(11,15+1) for j in range(21,25+1)]
    # #     + [Edge(i,j) for i in range(21,25+1) for j in range(31,35+1)]
    # #     + [Edge(i,40) for i in range(31, 35+1)]
    # # )
    # g = ig.Graph(edges=[(source, sink) for source, sink in edges], directed=True)

    # print(1)
    # print(g.all_st_cuts(0,40))

    edges = [Edge('A','B'), Edge('B','C'), Edge('B','D'), Edge('C','E'), Edge('D','F'), Edge('D','G'), Edge('E','G'), Edge('F','H'), Edge('G','H'), Edge('H','I')]

    knowns_list = [(Edge('B','D'), 3), (Edge('D','G'), 2), (Edge('F','H'), 1)]
    solution = solve_network(edges, knowns_list)
    print(solution)