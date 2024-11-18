import spacy
import networkx as nx
import matplotlib.pyplot as plt

# Загружаем модель SpaCy
nlp = spacy.load("en_core_web_sm")

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
        main_entities = []
        for token in doc:
            if token.dep_ in ("nsubj", "ROOT") and token.pos_ in ("NOUN", "PROPN"):
                main_entities.append(token.text)

        # Обработка зависимых существительных через союз
        for token in doc:
            if token.dep_ == "cc":  # Ищем союзы (например, "and")
                if token.head.text in main_entities:
                    for child in token.head.children:
                        if child.dep_ == "conj" and child.pos_ in ("NOUN", "PROPN"):
                            if child.text not in main_entities:
                                main_entities.append(child.text)

        # Добавляем главные сущности
        for entity in main_entities:
            entities.append((entity, "MainEntity"))

        # Обработка атрибутов и связок (например, "are strong animals")
        for token in doc:
            # Атрибуты через "amod" (например, "strong animals")
            if token.dep_ == "amod" and token.head.text in main_entities:
                entities.append((token.text, "Attribute"))
                relations.append((token.head.text, token.text, "has_quality"))

            # Атрибуты через "acomp" (например, "are strong")
            if token.dep_ == "acomp" and token.head.text in main_entities:
                entities.append((token.text, "Attribute"))
                relations.append((token.head.text, token.text, "has_quality"))

            # Прямые указания типа ("animals")
            if token.dep_ == "attr" and token.head.text in main_entities:
                entities.append((token.text, "Attribute"))
                relations.append((token.head.text, token.text, "is_a"))

        # Обработка действий (глаголов) и их атрибутов
        for token in doc:
            if token.pos_ == "VERB" and token.dep_ not in ("aux", "cop"):
                for subject in main_entities:
                    # Добавляем действие
                    entities.append((token.lemma_, "Action"))
                    relations.append((subject, token.lemma_, "can_do"))

                    for child in token.children:
                        # Наречия (например, "hunt skillfully")
                        if child.dep_ == "advmod":
                            entities.append((child.text.lower(), "Attribute"))
                            relations.append((token.lemma_, child.text.lower(), "has_attribute"))

                        # Прямые объекты (например, "hunt animals")
                        if child.dep_ == "dobj" and child.pos_ in ("NOUN", "PROPN"):
                            entities.append((child.text, "Object"))
                            relations.append((token.lemma_, child.text, "acts_on"))

                        # Атрибуты объектов (например, "strong animals")
                        if child.dep_ == "amod" and child.head.dep_ == "dobj":
                            entities.append((child.text, "Attribute"))
                            relations.append((child.head.text, child.text, "has_quality"))

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
text = "The lion and the tiger are strong animals that roar loudly and hunt skillfully."
editor.create_model_from_text(text)
editor.display_graph()
editor.visualize_graph()
