"""Tests target errors that would materially distort the research interpretation."""
import numpy as np
import networkx as nx
import pytest
from src.transfer_access import directed_matrix, paired_distances, conditional_co2_kg
from src.transfers import store_number
from src.corroboration import directory_records


def test_directed_returns_and_parallel_edges():
    graph = nx.MultiDiGraph()
    graph.add_edge('home', 'store', length=100)
    graph.add_edge('home', 'store', length=700)
    graph.add_edge('store', 'junction', length=80)
    graph.add_edge('junction', 'home', length=90)
    matrix, index = directed_matrix(graph)
    outbound, inbound = paired_distances(matrix, np.array([index['home']]), np.array([index['store']]))
    assert outbound[0] == 100  # not 800 from summing parallel edges
    assert inbound[0] == 170   # not doubling the outbound leg


def test_unreachable_destination_remains_missing():
    graph = nx.MultiDiGraph()
    graph.add_edge(1, 2, length=100)
    matrix, index = directed_matrix(graph)
    outbound, inbound = paired_distances(matrix, np.array([index[1]]), np.array([index[2]]))
    assert outbound[0] == 100
    assert np.isinf(inbound[0])


def test_roundtrip_emissions_units_and_sign():
    assert conditional_co2_kg(1.609344, trips=1, car_share=1) == pytest.approx(.4)
    assert conditional_co2_kg(-1.609344, trips=1, car_share=1) == pytest.approx(-.4)
    assert conditional_co2_kg(0) == 0
    with pytest.raises(ValueError):
        conditional_co2_kg(1, car_share=2)


def test_store_identity_does_not_match_cvs_with_same_number():
    assert store_number('Rite Aid Pharmacy #0872') == '872'
    assert store_number('CVS Pharmacy #11136') is None


def test_directory_excludes_index_and_preserves_address():
    page = 'RITE AID PHARMACY 01956\nNPI: 1932298684\n12353 ACADEMY ROAD\nPHILADELPHIA, PA 19154\n'
    parsed = directory_records(page + '\fIndex RITE AID PHARMACY 01956........106')
    assert len(parsed) == 1
    assert parsed.iloc[0].directory_address == '12353 ACADEMY ROAD'
    assert parsed.iloc[0].store_number == '1956'
