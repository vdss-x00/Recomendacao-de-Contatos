import json
import random


class HashTable:
    """Tabela hash simples com encadeamento externo."""

    def __init__(self, capacity=211):
        self.capacity = capacity
        self.buckets = [[] for _ in range(capacity)]
        self._size = 0

    def _hash(self, key):
        return hash(key) % self.capacity

    def insert(self, key, value):
        index = self._hash(key)
        bucket = self.buckets[index]

        for position, (stored_key, _) in enumerate(bucket):
            if stored_key == key:
                bucket[position] = (key, value)
                return

        bucket.append((key, value))
        self._size += 1

    def get(self, key):
        index = self._hash(key)
        for stored_key, value in self.buckets[index]:
            if stored_key == key:
                return value
        return None

    def contains(self, key):
        return self.get(key) is not None

    def __len__(self):
        return self._size


class WeightedGraph:
    """Grafo não direcionado representado por uma lista de adjacência."""

    def __init__(self):
        self.adjacency = {}

    def add_vertex(self, vertex_id):
        if vertex_id not in self.adjacency:
            self.adjacency[vertex_id] = {}

    def add_edge(self, first_id, second_id, weight):
        self.add_vertex(first_id)
        self.add_vertex(second_id)
        if first_id == second_id:
            return
        self.adjacency[first_id][second_id] = weight
        self.adjacency[second_id][first_id] = weight

    def get_neighbors(self, vertex_id):
        return self.adjacency.get(vertex_id, {})

    def has_edge(self, first_id, second_id):
        return second_id in self.adjacency.get(first_id, {})

    def vertices(self):
        return list(self.adjacency.keys())


class RecommendationSystem:
    def __init__(self, users_file="users.json", selected_count=35, random_seed=None):
        self.users_file = users_file
        self.selected_count = selected_count
        self.random_seed = random_seed
        self.user_table = HashTable()
        self.graph = WeightedGraph()
        self.load_users()

    def load_users(self):
        with open(self.users_file, "r", encoding="utf-8") as file:
            data = json.load(file)

        for user in data["users"]:
            self.user_table.insert(user["id"], user)

        if len(self.user_table) < self.selected_count:
            raise ValueError("O arquivo não possui usuários suficientes.")

        rng = random.Random(self.random_seed)
        all_ids = [user["id"] for user in data["users"]]
        selected_ids = rng.sample(all_ids, self.selected_count)

        for user_id in selected_ids:
            self.graph.add_vertex(user_id)

        # Primeiro cria um ciclo aleatório para garantir que todos tenham ao menos uma conexão.
        shuffled_ids = selected_ids.copy()
        rng.shuffle(shuffled_ids)
        for index, first_id in enumerate(shuffled_ids):
            second_id = shuffled_ids[(index + 1) % len(shuffled_ids)]
            weight = rng.randint(1, 10)
            self.graph.add_edge(first_id, second_id, weight)

        # Depois adiciona outras conexões aleatórias sem duplicá-las.
        for position, first_id in enumerate(selected_ids):
            for second_id in selected_ids[position + 1:]:
                if not self.graph.has_edge(first_id, second_id) and rng.random() < 0.15:
                    weight = rng.randint(1, 10)
                    self.graph.add_edge(first_id, second_id, weight)

    def get_user(self, user_id):
        return self.user_table.get(user_id)

    def get_recommendations(self, user_id):
        if not self.graph.adjacency or user_id not in self.graph.adjacency:
            return None

        direct_friends = set(self.graph.get_neighbors(user_id).keys())
        scores = {}

        for friend_id in direct_friends:
            weight_user_friend = self.graph.get_neighbors(user_id)[friend_id]

            for candidate_id, weight_friend_candidate in self.graph.get_neighbors(friend_id).items():
                if candidate_id == user_id:
                    continue
                if candidate_id in direct_friends:
                    continue

                scores[candidate_id] = scores.get(candidate_id, 0)
                scores[candidate_id] += weight_user_friend + weight_friend_candidate

        recommendations = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
        return recommendations


class TerminalApplication:
    def __init__(self):
        try:
            self.system = RecommendationSystem()
        except (FileNotFoundError, json.JSONDecodeError, KeyError, ValueError) as error:
            print(f"Erro ao iniciar a aplicação: {error}")
            raise SystemExit(1)

    def format_user(self, user):
        return f"ID {user['id']} - {user['name']} - {user['age']} anos"

    def consult_user(self):
        user_id = read_integer("Informe o ID do usuário: ")
        if user_id is None:
            return

        user = self.system.get_user(user_id)
        if user is None:
            print("Usuário inexistente.")
            return

        print("\nDados do usuário:")
        print(self.format_user(user))

    def view_connections(self):
        user_id = read_integer("Informe o ID do usuário: ")
        if user_id is None:
            return

        if user_id not in self.system.graph.adjacency:
            print("Usuário inexistente no grafo.")
            return

        neighbors = self.system.graph.get_neighbors(user_id)
        if not neighbors:
            print("Este usuário não possui conexões.")
            return

        print("\nConexões:")
        for friend_id, weight in sorted(neighbors.items(), key=lambda item: item[0]):
            friend = self.system.get_user(friend_id)
            print(f"- {friend['name']} (ID {friend_id}) | peso: {weight}")

    def recommend_contacts(self):
        user_id = read_integer("Informe o ID do usuário: ")
        if user_id is None:
            return

        recommendations = self.system.get_recommendations(user_id)
        if recommendations is None:
            print("Usuário inexistente no grafo.")
            return
        if not recommendations:
            print("Não há recomendações disponíveis para este usuário.")
            return

        print("\nRecomendações (maior pontuação primeiro):")
        for candidate_id, score in recommendations:
            candidate = self.system.get_user(candidate_id)
            print(f"- {candidate['name']} (ID {candidate_id}) | pontuação: {score}")

    def list_graph_users(self):
        print("\nUsuários selecionados no grafo:")
        for user_id in sorted(self.system.graph.vertices(), key=lambda value: int(value)):
            print(self.format_user(self.system.get_user(user_id)))
        print(f"\nTotal: {len(self.system.graph.vertices())} usuários")

    def run(self):
        print("Sistema de Recomendação de Contatos")
        print(f"Usuários cadastrados: {len(self.system.user_table)}")
        print(f"Usuários no grafo: {len(self.system.graph.vertices())}")

        while True:
            print("\n1. Consultar dados de um usuário")
            print("2. Visualizar conexões")
            print("3. Solicitar recomendações")
            print("4. Listar usuários do grafo")
            print("0. Sair")

            option = read_text("Escolha uma opção: ").strip()
            if option == "1":
                self.consult_user()
            elif option == "2":
                self.view_connections()
            elif option == "3":
                self.recommend_contacts()
            elif option == "4":
                self.list_graph_users()
            elif option == "0":
                print("Encerrando o programa.")
                break
            else:
                print("Opção inválida.")


def read_integer(prompt):
    try:
        return int(input(prompt).strip())
    except ValueError:
        print("Entrada inválida. Informe um número inteiro.")
        return None


def read_text(prompt):
    return input(prompt)


if __name__ == "__main__":
    TerminalApplication().run()
