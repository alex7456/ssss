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
            if token.dep_ in ("nsubj", "ROOT") and token.pos_ in ("NOUN", "PROPN"):
                main_entity = token.text
                entities.append((main_entity, "MainEntity"))
                break

        if main_entity:
            for token in doc:
                # Составные атрибуты (например, "loyal animal")
                if token.dep_ == "amod" and token.head.dep_ in ("attr", "nsubj"):
                    compound_text = f"{token.text} {token.head.text}"
                    entities.append((compound_text, "Attribute"))
                    relations.append((main_entity, compound_text, "has_attribute"))

                # Обычные атрибуты
                elif token.head.text == main_entity and token.dep_ in ("amod", "compound", "attr", "nummod"):
                    entities.append((token.text, "Attribute"))
                    relations.append((main_entity, token.text, "has_attribute"))

                # Действия (глаголы)
                if token.pos_ == "VERB" and token.dep_ not in ("aux", "cop"):
                    entities.append((token.lemma_, "Action"))
                    relations.append((main_entity, token.lemma_, "can_do"))

                    # Добавление наречий к глаголу (например, "barks loudly")
                    for child in token.children:
                        if child.dep_ == "advmod":
                            entities.append((child.text.lower(), "Attribute"))
                            relations.append((token.lemma_, child.text.lower(), "has_attribute"))

                    # Обработка объектов, связанных с глаголами
                    for child in token.children:
                        if child.dep_ in ("dobj", "pobj", "attr"):
                            entities.append((child.text, "Attribute"))
                            relations.append((token.lemma_, child.text, "has_attribute"))

                        # Уточняющие предлоги (например, "with its owner")
                        if child.dep_ == "prep":
                            for grandchild in child.children:
                                if grandchild.dep_ in ("pobj", "dobj"):
                                    entities.append((grandchild.text, "Attribute"))
                                    relations.append((token.lemma_, grandchild.text, "has_attribute"))

                # Обработка связанных объектов через предлоги
                if token.dep_ == "prep" and token.head.text == main_entity:
                    for child in token.children:
                        if child.dep_ == "pobj" and child.pos_ in ("NOUN", "PROPN"):
                            entities.append((child.text, "RelatedEntity"))
                            relations.append((main_entity, child.text, "related_to"))

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

# Новый текст для примера
text = "The lion is a strong and fierce animal that roars loudly and hunts in the wild."
editor.create_model_from_text(text)
editor.display_graph()
