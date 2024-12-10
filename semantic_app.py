import tkinter as tk
from tkinter import ttk
from tkinter import Scrollbar
from text_processor import SemanticObjectEditor
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
        self.model_output_label = ttk.Label(self.main_frame, text="Список сущностей и связей:", style="TLabel")
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
        self.editor.save_json_to_file(json_output, file_name="C:/Users/Alexandr/Desktop/testkurs/processed_text.json") 
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
