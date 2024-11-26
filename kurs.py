import spacy
import networkx as nx
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import Scrollbar

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
                relations.add((token.head.lemma_, place.lower(), "has_location"))

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
                    # Если есть субъект в императивном предложении, он становится объектом
                    if child.dep_ == "nsubj" and token.morph.get("Mood") == ["Imp"]:
                        entities.add((child.text.lower(), "Object"))
                        relations.add((token.lemma_, child.text.lower(), "acts_on"))

                    # Обработка прямых объектов (obj)
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
        pos = nx.spring_layout(self.graph)
        labels = nx.get_edge_attributes(self.graph, "relation")
        node_colors = [
            "orange" if "Question" in self.graph.nodes[node]["label"] else
            "skyblue" if "MainEntity" in self.graph.nodes[node]["label"] else
            "lightgreen" if "Action" in self.graph.nodes[node]["label"] else
            "yellow"
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
        """Очищает граф."""
        self.graph.clear()


class SemanticApp:
    def __init__(self, root):
        self.root = root
        self.editor = SemanticObjectEditor()

        # Окно ввода текста
        self.text_input_label = tk.Label(root, text="Введите текст:")
        self.text_input_label.pack()

        # Добавляем поле прокрутки

        self.text_input_frame = tk.Frame(root)
        self.text_input_frame.pack()

        # Текстовое поле с горизонтальной прокруткой
        self.text_input = tk.Text(self.text_input_frame, height=6, width=60)
        self.text_input.pack(side=tk.LEFT)

        self.scrollbar = Scrollbar(self.text_input_frame, orient="horizontal", command=self.text_input.xview)
        self.scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        self.text_input.config(xscrollcommand=self.scrollbar.set)

        # Создание контекстного меню с пунктом вставки
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Вставить", command=self.paste_text)

        # Привязка контекстного меню к полю ввода
        self.text_input.bind("<Button-3>", self.show_context_menu)

        # Кнопка обработки текста
        self.process_button = tk.Button(root, text="Обработать", command=self.process_text)
        self.process_button.pack()

        # Поле для вывода формализованной модели
        self.model_output_label = tk.Label(root, text="Формализованная модель:")
        self.model_output_label.pack()

        self.model_output = tk.Text(root, height=10, width=60)
        self.model_output.pack()

    def show_context_menu(self, event):
        """Отображаем контекстное меню при нажатии правой кнопки мыши."""
        self.context_menu.post(event.x_root, event.y_root)

    def paste_text(self):
        """Вставляем текст из буфера обмена в поле ввода."""
        clipboard = self.root.clipboard_get()  # Получаем текст из буфера обмена
        self.text_input.insert("insert", clipboard)  # Вставляем в поле ввода

    def process_text(self):
        """Обрабатывает введенный текст и отображает результаты."""
        text = self.text_input.get("1.0", "end-1c")
        self.editor.clear_graph()  # Очистим граф перед новым анализом
        self.editor.create_model_from_text(text)

        # Получение формализованной модели
        entities, relations = self.editor.process_text(text)
        formatted_model = "Сущности:\n"
        for entity, label in entities:
            formatted_model += f"{entity} ({label})\n"
        formatted_model += "\nСвязи:\n"
        for head, tail, relation in relations:
            formatted_model += f"{head} -[{relation}]-> {tail}\n"

        self.model_output.delete("1.0", "end")
        self.model_output.insert("1.0", formatted_model)

        # Отображение графика
        self.editor.visualize_graph()

        # Вывод информации о графе в консоль
        self.editor.display_graph()


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Редактор Семантических Объектов")

    app = SemanticApp(root)

    root.mainloop()
