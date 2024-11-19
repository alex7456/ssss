import spacy
import networkx as nx
import matplotlib.pyplot as plt

# Загружаем модель SpaCy
nlp = spacy.load("ru_core_news_sm")

class SemanticObjectEditor:
    def __init__(self):
        """
        Инициализация класса.
        """
        self.graph = nx.DiGraph()  # Создаем пустой граф

    def process_text(self, text):
        """
        Обработка текста для выделения сущностей, атрибутов и отношений.
        """
        doc = nlp(text)
        entities = []
        relations = []

        # Определение главных объектов (субъектов)
        main_entities = set()
        for token in doc:
            if token.dep_ in ("nsubj", "conj", "ROOT") and token.pos_ in ("NOUN", "PROPN"):
                main_entities.add(token.text)

        # Добавляем главные сущности
        for entity in main_entities:
            entities.append((entity, "MainEntity"))

        # Обработка атрибутов и связей
        for token in doc:
            # Атрибуты через "amod" (например, "сильный лев")
            if token.dep_ == "amod" and token.head.text in main_entities:
                entities.append((token.text, "Attribute"))
                relations.append((token.head.text, token.text, "has_quality"))

            # Обработка действий (глаголов) и их атрибутов
            if token.pos_ == "VERB":
                entities.append((token.lemma_, "Action"))
                for entity in main_entities:
                    relations.append((entity, token.lemma_, "can_do"))

                # Обработка зависимостей глаголов
                for child in token.children:
                    # Наречия (например, "громко рычать")
                    if child.dep_ == "advmod":
                        entities.append((child.text, "Attribute"))
                        relations.append((token.lemma_, child.text, "has_attribute"))

        # Удаляем дубликаты сущностей и отношений
        entities = list(dict.fromkeys(entities))
        relations = list(dict.fromkeys(relations))

        return entities, relations

    def add_to_graph(self, entities, relations):
        """
        Добавление сущностей и связей в графовую модель.
        """
        for entity, label in entities:
            self.graph.add_node(entity, label=label)

        for head, tail, relation in relations:
            if self.graph.has_node(head) and self.graph.has_node(tail):
                self.graph.add_edge(head, tail, relation=relation)

    def create_model_from_text(self, text):
        """
        Основная функция для создания модели из текста.
        """
        entities, relations = self.process_text(text)
        self.add_to_graph(entities, relations)

    def display_graph(self):
        """
        Вывод графа в консоль.
        """
        print("\nGraph Nodes:")
        for node in self.graph.nodes(data=True):
            print(f"Node: {node}")

        print("\nGraph Edges:")
        for edge in self.graph.edges(data=True):
            print(f"Edge: {edge}")

    def visualize_graph(self):
        """
        Графическая визуализация графа.
        """
        pos = nx.spring_layout(self.graph)
        labels = nx.get_edge_attributes(self.graph, "relation")
        node_colors = [
            "skyblue"
            if self.graph.nodes[node]["label"] == "MainEntity"
            else "lightgreen"
            if self.graph.nodes[node]["label"] == "Action"
            else "orange"
            for node in self.graph.nodes
        ]
        nx.draw(
            self.graph,
            pos,
            with_labels=True,
            node_size=2000,
            node_color=node_colors,
            font_size=10,
        )
        nx.draw_networkx_edge_labels(self.graph, pos, edge_labels=labels)
        plt.show()

    def clear_graph(self):
        """
        Очистка графа для работы с новым текстом.
        """
        self.graph.clear()


# Пример использования
editor = SemanticObjectEditor()

# Новый текст для примера
text = "Лев и тигр — сильные животные, которые громко рычат и охотятся."
editor.create_model_from_text(text)
editor.display_graph()
editor.visualize_graph()
