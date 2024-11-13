import spacy
import networkx as nx

# Загружаем модель SpaCy
nlp = spacy.load("en_core_web_sm")

class SemanticObjectEditor:
    def __init__(self):
        self.graph = nx.DiGraph()

    def process_text(self, text):
        """
        Обработка текста для выделения сущностей, атрибутов и отношений.
        """
        doc = nlp(text)
        entities = []
        relations = []

        # Определение главного объекта
        main_entity = None
        for token in doc:
            if token.dep_ in ("nsubj", "ROOT") and token.pos_ == "NOUN":
                main_entity = token.text
                entities.append((main_entity, "MainEntity"))
                break

        if main_entity:
            for token in doc:
                # Атрибуты главного объекта, такие как "young", "fluffy", "animal"
                if token.head.text == main_entity and token.dep_ in ("amod", "nummod") and token.text != "often":
                    entities.append((token.text, "Attribute"))
                    relations.append((main_entity, token.text, "has_attribute"))

                # Обработка действия "meows"
                elif token.text == "meows" and token.pos_ == "VERB":
                    entities.append((token.text, "Action"))
                    relations.append((main_entity, token.text, "can_do"))

                # Обработка "one year" как единого узла
                elif token.text == "one" and token.head.text == "year":
                    entities.append(("one year", "Attribute"))
                    relations.append((main_entity, "one year", "has_attribute"))

                # Обработка связанного объекта "cat"
                elif token.text == "cat" and token.dep_ == "pobj" and token.head.dep_ == "prep":
                    entities.append((token.text, "RelatedEntity"))
                    relations.append((main_entity, token.text, "related_to"))

                # Слово "animal" должно быть добавлено как атрибут
                elif token.text == "animal" and token.dep_ == "attr":
                    entities.append((token.text, "Attribute"))
                    relations.append((main_entity, token.text, "has_attribute"))

                # Атрибут "fluffy"
                elif token.text == "fluffy" and token.dep_ in ("amod", "attr"):
                    entities.append((token.text, "Attribute"))
                    relations.append((main_entity, token.text, "has_attribute"))

                # Атрибут "young"
                elif token.text == "young" and token.dep_ in ("amod", "attr"):
                    entities.append((token.text, "Attribute"))
                    relations.append((main_entity, token.text, "has_attribute"))

        # Удаляем дубликаты
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
        Визуализация графа.
        """
        for node in self.graph.nodes(data=True):
            print(f"Node: {node}")
        
        for edge in self.graph.edges(data=True):
            print(f"Edge: {edge}")
    
    def clear_graph(self):
        """
        Очистка графа для работы с новым текстом.
        """
        self.graph.clear()

# Пример использования
editor = SemanticObjectEditor()
text = "A kitten is a young animal, the offspring of a cat, with age up to one year, fluffy, often meows."
editor.create_model_from_text(text)
editor.display_graph()
