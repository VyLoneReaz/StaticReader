import flet as ft
from flet import Page, Column, Row, TextField, Text, ElevatedButton

## Parameter
file_path = "assets/text.txt"
wpm = None
custom_font = None
words_list = []

txt_path_input = None

def file_handler(e) -> None:
    try:
        if TextField(txt_path_input):
            file_path = str(TextField(txt_path_input).value)
            with open(file_path, "r") as file:
                for line in file:
                    words_list.append(line.split(" "))
                    print(words_list)
        else:
            print("txt_path_input is not defined!")
    except FileNotFoundError as e:
        print(f"ERROR: {e}")

def start(e):
    print("START")
    file_handler(e)


def main(page: Page) -> None:
    Page.title = "Static Reader"
    Page.theme_mode = ft.ThemeMode.DARK
    Page.vertical_alignment = ft.MainAxisAlignment.CENTER
    Page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    ## Custom Styles
    text_color = "ORANGE"
    
    ## Text
    txt_the_word: Text = Text(value="WORD", size=45, color=text_color)
    txt_path_input: TextField = TextField(value="", hint_text="// Path", width=500, color=text_color, border_color=text_color, fill_color="BLACK", on_change=file_handler)

    ## Buttons
    btn_start: ElevatedButton = ElevatedButton(text="Start", height=40, width=80, color=text_color,on_click=start)

    page.add(
        Row(
            [
                Column([
                        txt_the_word,
                        txt_path_input,
                        btn_start,
                ],  
                alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            ],  
            expand=True, alignment=ft.MainAxisAlignment.CENTER, vertical_alignment=ft.CrossAxisAlignment.CENTER
        )
    )

if __name__ == "__main__":
    ft.app(target=main)