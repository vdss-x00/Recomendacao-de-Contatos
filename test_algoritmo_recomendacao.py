import json

import pytest

from algoritmo_recomendacao import (
    HashTable,
    RecommendationSystem,
    WeightedGraph,
)


class TestHashTable:
    def test_insert_get_contains_and_size(self):
        table = HashTable()

        table.insert(10, {"id": 10, "name": "Ana"})
        table.insert(20, {"id": 20, "name": "Bia"})

        assert table.get(10) == {"id": 10, "name": "Ana"}
        assert table.get(20) == {"id": 20, "name": "Bia"}
        assert table.contains(10)
        assert not table.contains(999)
        assert len(table) == 2

    def test_insert_existing_key_updates_without_increasing_size(self):
        table = HashTable()
        table.insert(1, "valor antigo")
        table.insert(1, "valor novo")

        assert table.get(1) == "valor novo"
        assert len(table) == 1

    def test_collision_keeps_both_entries(self):
        table = HashTable(capacity=1)

        table.insert("a", {"name": "Ana"})
        table.insert("b", {"name": "Bia"})

        assert table.get("a") == {"name": "Ana"}
        assert table.get("b") == {"name": "Bia"}
        assert len(table) == 2


class TestWeightedGraph:
    def test_add_vertex_and_edge(self):
        graph = WeightedGraph()

        graph.add_edge(1, 2, 7)

        assert graph.vertices() == [1, 2]
        assert graph.get_neighbors(1) == {2: 7}
        assert graph.get_neighbors(2) == {1: 7}
        assert graph.has_edge(1, 2)
        assert graph.has_edge(2, 1)

    def test_edge_is_symmetric_and_duplicate_is_updated(self):
        graph = WeightedGraph()

        graph.add_edge(1, 2, 3)
        graph.add_edge(2, 1, 9)

        assert graph.get_neighbors(1)[2] == 9
        assert graph.get_neighbors(2)[1] == 9

    def test_self_loop_is_ignored(self):
        graph = WeightedGraph()

        graph.add_edge(1, 1, 5)

        assert graph.vertices() == [1]
        assert graph.get_neighbors(1) == {}


class TestRecommendationSystem:
    def test_load_users_and_create_35_unique_graph_vertices(self):
        system = RecommendationSystem(
            users_file="users.json",
            selected_count=35,
            random_seed=42,
        )

        assert len(system.user_table) == 100
        assert len(system.graph.vertices()) == 35
        assert len(set(system.graph.vertices())) == 35

        for vertex in system.graph.vertices():
            assert system.graph.get_neighbors(vertex)

        for first_id, neighbors in system.graph.adjacency.items():
            for second_id, weight in neighbors.items():
                assert 1 <= weight <= 10
                assert system.graph.has_edge(second_id, first_id)
                assert first_id != second_id

    def test_load_users_rejects_too_few_available_users(self, tmp_path):
        users_file = tmp_path / "users.json"
        users_file.write_text(
            json.dumps(
                {
                    "users": [
                        {"id": 1, "name": "Ana", "age": 22},
                        {"id": 2, "name": "Bia", "age": 23},
                    ]
                }
            ),
            encoding="utf-8",
        )

        with pytest.raises(ValueError, match="usuários suficientes"):
            RecommendationSystem(users_file=str(users_file), selected_count=3)

    def test_recommendations_use_two_hops_sum_scores_and_sort(self):
        system = RecommendationSystem.__new__(RecommendationSystem)
        system.user_table = HashTable()
        system.graph = WeightedGraph()

        for vertex in (1, 2, 3, 4, 5, 6):
            system.graph.add_vertex(vertex)

        system.graph.add_edge(1, 2, 4)
        system.graph.add_edge(1, 3, 5)
        system.graph.add_edge(2, 4, 2)
        system.graph.add_edge(2, 5, 3)
        system.graph.add_edge(3, 4, 6)
        system.graph.add_edge(3, 6, 1)

        recommendations = system.get_recommendations(1)

        assert recommendations == [(4, 17), (5, 7), (6, 6)]

    def test_recommendations_exclude_user_and_direct_friends(self):
        system = RecommendationSystem.__new__(RecommendationSystem)
        system.graph = WeightedGraph()

        system.graph.add_edge(1, 2, 5)
        system.graph.add_edge(2, 3, 4)

        recommendations = system.get_recommendations(1)

        assert recommendations == [(3, 9)]

    def test_recommendations_return_none_for_user_outside_graph(self):
        system = RecommendationSystem.__new__(RecommendationSystem)
        system.graph = WeightedGraph()
        system.graph.add_vertex(1)

        assert system.get_recommendations(999) is None

    def test_recommendations_return_empty_list_when_no_candidates_exist(self):
        system = RecommendationSystem.__new__(RecommendationSystem)
        system.graph = WeightedGraph()
        system.graph.add_edge(1, 2, 5)

        assert system.get_recommendations(1) == []