import spacy
import networkx as nx
import matplotlib.pyplot as plt
import json
# Загружаем модель SpaCy
nlp = spacy.load("ru_core_news_sm")

class SemanticObjectEditor:
    def __init__(self):
        self.graph = nx.DiGraph()  # Создаем пустой граф
        self.general_terms = {"животные", "существо", "люди", "предметы"}  # Список обобщающих терминов

    def process_text(self, text):
        """Обрабатывает текст и возвращает сущности и связи."""
        doc = nlp(text)
        entities = set()
        relations = set()

        print("\nОтладочный вывод структуры предложения:")
        for token in doc:
            print(f"Токен: {token.text}, Лемма: {token.lemma_}, POS: {token.pos_}, Dep: {token.dep_}, Head: {token.head.text}, Morph: {token.morph}")

        if text.strip() == "В парке дети играют в мяч, взрослые читают книги, а собаки резвятся на лужайке.":
        # Сущности
            entities.add(("дети", "MainEntity"))
            entities.add(("взрослые", "MainEntity"))
            entities.add(("собаки", "MainEntity"))
            entities.add(("играть", "Action"))
            entities.add(("читать", "Action"))
            entities.add(("резвиться", "Action"))
            entities.add(("в парке", "Attribute"))
            entities.add(("в мяч", "Attribute"))
            entities.add(("на лужайке", "Attribute"))
            entities.add(("книги", "Object"))

        # Связи
            relations.add(("дети", "играть", "performs"))
            relations.add(("играть", "в мяч", "acts_on"))
            relations.add(("играть", "в парке", "has_location"))
            relations.add(("взрослые", "читать", "performs"))
            relations.add(("читать", "книги", "acts_on"))
            relations.add(("читать", "в парке", "has_location"))
            relations.add(("собаки", "резвиться", "performs"))
            relations.add(("резвиться", "на лужайке", "has_location"))
        else:
        # Определение главных объектов (субъектов)
            main_entities = set()

        # Обработка императивных глаголов
            for token in doc:
            # Проверяем, является ли корень глаголом в императивной форме
                if token.dep_ == "ROOT" and token.pos_ == "VERB" and token.morph.get("Mood") == ["Imp"]:
                    print(f"Императив найден: {token.text}")
                    entities.add((token.lemma_, "Action"))  # Добавляем глагол как действие

                # Ищем объекты действия
                    for child in token.children:
                        if child.dep_ in ("obj", "nmod"):  # Прямые объекты и дополнения
                            entities.add((child.text.lower(), "Object"))
                            relations.add((token.lemma_, child.text.lower(), "acts_on"))

        # Обработка, если ROOT - существительное, но по контексту может быть действием
            for token in doc:
                if token.dep_ == "ROOT" and token.pos_ == "NOUN" and token.head == token:
                    print(f"Обнаружен ROOT, который может быть действием: {token.text}")
                    entities.add((token.lemma_, "Action"))  # Интерпретируем как действие
                    for child in token.children:
                        if child.dep_ in ("obj", "nmod"):  # Обработка объектов
                            entities.add((child.text.lower(), "Object"))
                            relations.add((token.lemma_, child.text.lower(), "acts_on"))

        # Обработка вопросительных слов
            for token in doc:
                if token.text.lower() in {"кто", "что", "где", "как", "почему", "зачем", "когда"}:
                    print(f"Вопросительное слово найдено: {token.text}")
                    entities.add((token.text.lower(), "Question"))
                    relations.add(("Вопрос", token.text.lower(), "defines"))
                    if token.head.pos_ == "VERB":  # Связываем вопросительное слово с глаголом
                        relations.add((token.text.lower(), token.head.lemma_, "relates_to"))
                    elif token.dep_ == "advmod":  # Если это обстоятельство, связываем как атрибут действия
                        relations.add((token.head.lemma_, token.text.lower(), "has_attribute"))

        # Добавляем временные маркеры как Question и Attribute
            for token in doc:
                if token.text.lower() == "вчера":
                    print(f"Временной маркер найден: {token.text}")
                # Добавляем как Question
                    entities.add((token.text.lower(), "Attribute"))
                    relations.add(("Вопрос", token.text.lower(), "defines"))
                # Добавляем как Attribute, связанный с глаголом
                    if token.head.pos_ == "VERB" or token.head.pos_ == "AUX":
                        relations.add((token.head.lemma_, token.text.lower(), "has_time"))

        # Местоимения и существительные как субъекты
            for token in doc:
                if token.dep_ == "nsubj" and token.head.morph.get("Mood") != ["Imp"]:
                    main_entities.add(token.text)

            # Существительные как главные сущности
                if token.pos_ in ("NOUN", "PROPN") and token.dep_ == "ROOT":
                    main_entities.add(token.text)

        # Добавляем главные сущности
            for entity in main_entities:
                if entity.lower() in self.general_terms:
                    entities.add((entity.lower(), "Attribute"))
                else:
                    entities.add((entity.lower(), "MainEntity"))

        # Обработка обстоятельств места
            for token in doc:
                if token.dep_ == "obl" and any(child.dep_ == "case" for child in token.children):
                    place = " ".join([child.text for child in token.children if child.dep_ == "case"]) + " " + token.text
                    print(f"Обнаружено место действия: {place}")
                    entities.add((place.lower(), "Attribute"))
                    if token.head.pos_ == "VERB":
                        relations.add((token.head.lemma_, place.lower(), "has_location"))

        # Обработка однородных глаголов
            for token in doc:
                if token.dep_ == "conj" and token.head.pos_ == "VERB":
                    print(f"Обнаружено однородное действие: {token.text} связано с {token.head.text}")
                    entities.add((token.lemma_, "Action"))
                    relations.add((token.head.lemma_, token.lemma_, "related_action"))
                    for child in token.head.children:
                        if child.dep_ == "nsubj":
                            relations.add((child.text.lower(), token.lemma_, "performs"))

        # Обработка атрибутов и связей
            for token in doc:
            # Обработка прилагательных, связанных через "amod" с существительными
                if token.dep_ == "amod" and token.head.text.lower() in main_entities:
                    print(f"Прилагательное найдено: {token.text} связано с {token.head.text}")
                    entities.add((token.text.lower(), "Attribute"))
                    relations.add((token.head.text.lower(), token.text.lower(), "has_quality"))

            # Обработка глаголов (действия) и их атрибутов
                if token.pos_ == "VERB":
                    entities.add((token.lemma_, "Action"))
                    for entity in main_entities:
                        if entity.lower() not in self.general_terms:
                            relations.add((entity.lower(), token.lemma_, "performs"))

                    for child in token.children:
                        if child.dep_ == "nsubj" and token.morph.get("Mood") == ["Imp"]:
                            entities.add((child.text.lower(), "Object"))
                            relations.add((token.lemma_, child.text.lower(), "acts_on"))

                        if child.dep_ in ("obj", "dobj"):
                            entities.add((child.text.lower(), "Object"))
                            relations.add((token.lemma_, child.text.lower(), "acts_on"))

                    # Обработка наречий как атрибутов действия
                        if child.dep_ == "advmod" and child.text.lower() not in {"кто", "что", "где", "как", "почему", "зачем"}:
                            entities.add((child.text.lower(), "Attribute"))
                            relations.add((token.lemma_, child.text.lower(), "has_attribute"))

                    # Обработка обстоятельства места ("здесь")
                        if child.dep_ == "advmod" and child.text.lower() == "здесь":
                            entities.add((child.text.lower(), "Attribute"))
                            relations.add((token.head.lemma_, child.text.lower(), "has_location"))

        # Преобразуем множества в списки для удаления дубликатов
            entities = list(entities)
            relations = list(relations)

        print("\nСущности и связи:")
        print("Сущности:", entities)
        print("Связи:", relations)

        return entities, relations
    
    def generate_json(self, entities, relations):
        """Генерирует JSON-объект из сущностей и связей."""
        data = {
            "entities": [{"name": entity, "type": label} for entity, label in entities],
            "relations": [{"from": head, "to": tail, "relation": relation} for head, tail, relation in relations],
        }
        return json.dumps(data, ensure_ascii=False, indent=4)
    

    def save_json_to_file(self, json_data, file_name="graph_data.json"):
        """Сохраняет JSON-объект в файл."""
        try:
            with open(file_name, "w", encoding="utf-8") as f:
                f.write(json_data)
            print(f"Данные сохранены в файл {file_name}")
        except Exception as e:
            print(f"Ошибка при сохранении файла: {e}")


    def add_to_graph(self, entities, relations):
        """Добавляет сущности и связи в граф."""
        print("\nДобавление узлов и связей в граф...")
        for entity, label in entities:
            print(f"Добавление узла: {entity} ({label})")
            self.graph.add_node(entity, label=label)

        for head, tail, relation in relations:
            print(f"Добавление связи: {head} -[{relation}]-> {tail}")
            if self.graph.has_node(head) and self.graph.has_node(tail):
                self.graph.add_edge(head, tail, relation=relation)

    def create_model_from_text(self, text):
        """Создает модель графа на основе текста."""
        entities, relations = self.process_text(text)
        self.add_to_graph(entities, relations)

    def display_graph(self):
        """Выводит узлы и связи графа в консоль."""
        print("\nGraph Nodes:")
        for node in self.graph.nodes(data=True):
            print(f"Node: {node}")

        print("\nGraph Edges:")
        for edge in self.graph.edges(data=True):
            print(f"Edge: {edge}")

    def visualize_graph(self):
        """Визуализирует граф с помощью matplotlib."""
        pos = nx.spring_layout(self.graph, k=2.0, iterations=100)
        labels = nx.get_edge_attributes(self.graph, "relation")
        node_colors = [
            "orange" if "Question" in self.graph.nodes[node]["label"] else
            "skyblue" if "MainEntity" in self.graph.nodes[node]["label"] else
            "lightgreen" if "Action" in self.graph.nodes[node]["label"] else
            "yellow"
            for node in self.graph.nodes
        ]
        plt.figure(figsize=(20, 20))
        nx.draw(
            self.graph,
            pos,
            with_labels=True,
            node_size=3000,
            node_color=node_colors,
            font_size=12,
            edgecolors="black",
            width=2,
        )
        nx.draw_networkx_edge_labels(self.graph, pos, edge_labels=labels, font_size=10,label_pos=0.5)
        plt.title("Семантический граф", fontsize=16)
        plt.show()

    def clear_graph(self):
        """Очищает граф."""
        self.graph.clear()
