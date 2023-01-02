from main import Edge, solve_network, RedundancyError, AuxiliaryEquation, AuxiliaryEquationsRequiredException
import pytest

CASE_1_EDGES = [Edge(0,1), Edge(1,2), Edge(1,3), Edge(2,4), Edge(3,5), Edge(3,6), Edge(4,6), Edge(5,7), Edge(6,7), Edge(7,8)]
"""
[Node 0] --(10)-> [Node 1] --(7)-> [Node 2] --(7)-> [Node 4] --(7)-> [Node 6] --(9)-> [Node 7] --(10)-> [Node 8]
                     |                                                  A                A
                     |                 |-----------------------(2)------|                |
                     |                 |                                                 |
                     |-------(3)-> [Node 3] -------------------(1)-> [Node 5] --(1)------|
"""

def test_solving_a_simple_network():
    edges = CASE_1_EDGES
    knowns_list = [(Edge(1,2), 7), (Edge(3,6), 2), (Edge(5,7), 1)]

    solution = {
        Edge(0,1): 10,
        Edge(1,2): 7,
        Edge(1,3): 3,
        Edge(2,4): 7,
        Edge(3,5): 1,
        Edge(3,6): 2,
        Edge(4,6): 7,
        Edge(5,7): 1,
        Edge(6,7): 9,
        Edge(7,8): 10,
    }

    assert solution == solve_network(edges, knowns_list)

def test_solving_a_partial_case():
    edges = CASE_1_EDGES
    knowns_list = [(Edge(3,6), 2), (Edge(5,7), 1)]

    solution = {
        Edge(1,3): 3,
        Edge(3,5): 1,
        Edge(3,6): 2,
        Edge(5,7): 1,
    }

    assert solution == solve_network(edges, knowns_list)

def test_raise_error_if_overconstrained_by_too_many_knowns():
    with pytest.raises(RedundancyError):
        edges = CASE_1_EDGES
        knowns_list = [(Edge(0,1), 10), (Edge(1,2), 7), (Edge(1,3), 3), (Edge(7,8), 10)]
        solve_network(edges, knowns_list)

def test_raise_error_if_initially_overconstrained_at_node():
    with pytest.raises(RedundancyError):
        edges = CASE_1_EDGES
        knowns_list = [(Edge(0,1), 10), (Edge(1,2), 7), (Edge(1,3), 3)]
        solve_network(edges, knowns_list)

def test_raise_error_if_not_obviously_overconstrained():
    with pytest.raises(RedundancyError):
        edges = CASE_1_EDGES
        knowns_list = [(Edge(0,1), 10), (Edge(4,6), 7), (Edge(1,3), 3)]
        solve_network(edges, knowns_list)

def test_should_identify_when_aux_equations_required():
    with pytest.raises(AuxiliaryEquationsRequiredException):
        edges = CASE_1_EDGES
        knowns_list = [(Edge(0,1), 10), (Edge(5,7), 1), (Edge(6,7), 9)]
        solve_network(edges, knowns_list)

def test_aux_equation_fixes_otherwise_bad_equation_set():
    with pytest.raises(RedundancyError):
        edges = CASE_1_EDGES
        knowns_list = [(Edge(0,1), 10), (Edge(5,7), 1), (Edge(6,7), 9)]
        aux_eqns = [AuxiliaryEquation([Edge(0,1)], [Edge(7,8)])]
        solve_network(edges, knowns_list, aux_eqns)

def test_node_ids_can_be_strings():
    edges = [Edge('A','B'), Edge('B','C'), Edge('B','D'), Edge('C','E'), Edge('D','F'), Edge('D','G'), Edge('E','G'), Edge('F','H'), Edge('G','H'), Edge('H','I')]
    knowns_list = [(Edge('B','C'), 7), (Edge('D','G'), 2), (Edge('F','H'), 1)]

    solution = {
        Edge('A','B'): 10,
        Edge('B','C'): 7,
        Edge('B','D'): 3,
        Edge('C','E'): 7,
        Edge('D','F'): 1,
        Edge('D','G'): 2,
        Edge('E','G'): 7,
        Edge('F','H'): 1,
        Edge('G','H'): 9,
        Edge('H','I'): 10,
    }
    # assert True
    print(solution)
    print(solve_network(edges, knowns_list))

    assert solution == solve_network(edges, knowns_list)