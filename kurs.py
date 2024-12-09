import spacy
import networkx as nx
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import ttk
from tkinter import Scrollbar
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

        # Настраиваем стиль
        style = ttk.Style()
        style.configure("TLabel", font=("Arial", 14, "bold"), padding=5, background="#f0f8ff", foreground="#333333")
        style.configure("TButton", font=("Arial", 12, "bold"), padding=5, background="#4caf50", foreground="#1f7502")
        style.configure("TFrame", background="#f4f4f4")
        style.configure("TText", font=("Arial", 10), background="#ffffff", foreground="#333333")
        style.configure("TScrollbar", background="#cccccc")

        # Основной фрейм
        self.main_frame = ttk.Frame(root, padding=10, style="TFrame")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Заголовок
        self.title_label = ttk.Label(
            self.main_frame, text="Редактор Семантических Объектов", style="TLabel", anchor="center"
        )
        self.title_label.pack(pady=10)

       
        # Окно ввода текста
        self.text_input_label = ttk.Label(self.main_frame, text="Введите текст:", style="TLabel")
        self.text_input_label.pack(anchor="w")

        # Поле ввода текста с прокруткой
        self.text_input_frame = ttk.Frame(self.main_frame)
        self.text_input_frame.pack(fill=tk.X, pady=5)

        self.text_input = tk.Text(self.text_input_frame, height=6, wrap=tk.WORD, font=("Arial", 12))
        self.text_input.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.scrollbar = Scrollbar(self.text_input_frame, command=self.text_input.yview, orient=tk.VERTICAL)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_input.configure(yscrollcommand=self.scrollbar.set)
        self.add_context_menu()  # Добавляем контекстное меню для вставки

        # Кнопка обработки текста
        self.process_button = ttk.Button(
            self.main_frame,
            text="Обработать текст",
            command=self.process_text,
            style="TButton",
        )
        self.process_button.pack(pady=10)

        # Поле вывода формализованной модели
        self.model_output_label = ttk.Label(self.main_frame, text="Формализованная модель:", style="TLabel")
        self.model_output_label.pack(anchor="w", pady=5)

        self.model_output = tk.Text(
            self.main_frame, height=10, wrap=tk.WORD, font=("Arial", 12), state=tk.DISABLED, background="#f9f9f9"
        )
        self.model_output.pack(fill=tk.BOTH, pady=5)

        # Поле вывода JSON
        self.json_output_label = ttk.Label(self.main_frame, text="Модель в формате JSON:", style="TLabel")
        self.json_output_label.pack(anchor="w", pady=5)

        self.json_output = tk.Text(
            self.main_frame, height=15, wrap=tk.WORD, font=("Arial", 12), state=tk.DISABLED, background="#f9f9f9"
        )
        self.json_output.pack(fill=tk.BOTH, pady=5)

        # Нижняя панель кнопок
        self.button_frame = ttk.Frame(self.main_frame)
        self.button_frame.pack(fill=tk.X, pady=10)

        self.clear_button = ttk.Button(
            self.button_frame, text="Очистить", command=self.clear_text, style="TButton", width=15
        )
        self.clear_button.pack(side=tk.LEFT, padx=5)

        self.exit_button = ttk.Button(
            self.button_frame, text="Выход", command=self.root.quit, style="TButton", width=15
        )
        self.exit_button.pack(side=tk.RIGHT, padx=5)
    def add_context_menu(self):
        """Добавляет контекстное меню для текстового поля."""
        self.context_menu = tk.Menu(self.text_input, tearoff=0)
        self.context_menu.add_command(label="Вставить", command=self.paste_text)

        def show_context_menu(event):
            self.context_menu.tk_popup(event.x_root, event.y_root)

        self.text_input.bind("<Button-3>", show_context_menu)  # Правая кнопка мыши для контекстного меню

    def paste_text(self):
        """Вставляет текст из буфера обмена в поле ввода текста."""
        clipboard_content = self.root.clipboard_get()  # Получаем текст из буфера обмена
        self.text_input.insert(tk.INSERT, clipboard_content)  # Вставляем текст в текущее положение курсора


    def process_text(self):
        """Обрабатывает введённый текст и отображает результаты."""
        text = self.text_input.get("1.0", "end-1c")
        self.editor.clear_graph()
        self.editor.create_model_from_text(text)

        entities, relations = self.editor.process_text(text)
        formatted_model = "Сущности:\n"
        for entity, label in entities:
            formatted_model += f"{entity} ({label})\n"
        formatted_model += "\nСвязи:\n"
        for head, tail, relation in relations:
            formatted_model += f"{head} -[{relation}]-> {tail}\n"

        self.model_output.config(state=tk.NORMAL)
        self.model_output.delete("1.0", "end")
        self.model_output.insert("1.0", formatted_model)
        self.model_output.config(state=tk.DISABLED)

        json_output = self.editor.generate_json(entities, relations)
        self.json_output.config(state=tk.NORMAL)
        self.json_output.delete("1.0", "end")
        self.json_output.insert("1.0", json_output)
        self.json_output.config(state=tk.DISABLED)
        self.editor.save_json_to_file(json_output, file_name="C:/Users/Alexandr/Desktop/kurs/processed_text.json") 
        self.editor.visualize_graph()

    def clear_text(self):
        """Очищает все текстовые поля."""
        self.text_input.delete("1.0", "end")
        self.model_output.config(state=tk.NORMAL)
        self.model_output.delete("1.0", "end")
        self.model_output.config(state=tk.DISABLED)
        self.json_output.config(state=tk.NORMAL)
        self.json_output.delete("1.0", "end")
        self.json_output.config(state=tk.DISABLED)


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Редактор Семантических Объектов")
    root.geometry("900x700")
    app = SemanticApp(root)
    root.mainloop()
