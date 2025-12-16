import asyncio
from playsound3 import playsound
import flet as ft
from flet import (
    Page,
    Column,
    Row,
    TextField,
    Text,
    ElevatedButton,
    FilePicker,
    KeyboardEvent,
)
from docx import Document
from pathlib import Path


def main(page: Page) -> None:
    # -----------------------------
    # App State
    # -----------------------------
    wpm = 100
    words: list[str] = []
    word_index = 0
    is_active = False
    is_file_valid = False

    # -----------------------------
    # SFX - AUDIO
    # -----------------------------
    sfx_word_appear = Path("assets/audio/Word_Appear_SFX/TOON_Pop.wav")
    sfx_button_hover = Path("assets/audio/Button_SFX/Hover/Bonk Hover A.wav")
    sfx_button_start_click = Path(
        "assets/audio/Button_SFX/Click/Light Click A_Start.wav"
    )
    sfx_button_stop_click = Path("assets/audio/Button_SFX/Click/Light Click B_Stop.wav")
    sfx_writing = Path("assets/audio/Writing_SFX/ui_menu_button_beep_08.wav")
    sfx_reading_complete = Path(
        "assets/audio/Reading_Complete_SFX/collect_item_sparkle_pop_03.wav"
    )

    # -----------------------------
    # Page Setup
    # -----------------------------
    page.title = "Static Reader"
    page.theme_mode = ft.ThemeMode.DARK
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    text_color = "ORANGE"

    txt_the_word = Text(
        value="Import a file to begin",
        size=45,
        weight=ft.FontWeight.BOLD,
        color=text_color,
    )

    def set_btn_visibilities(**kwargs) -> None:
        nonlocal btn_start, btn_stop, btn_reset
        for key, value in kwargs.items():
            if key == "btn_start":
                btn_start.visible = value
            elif key == "btn_stop":
                btn_stop.visible = value
            elif key == "btn_reset":
                btn_reset.visible = value

        page.update()

    # -----------------------------
    # File Import Logic
    # -----------------------------
    def import_file(path: str) -> str:
        nonlocal is_file_valid

        file_path = Path(path)
        suffix = file_path.suffix.lower()

        if suffix == ".txt":
            is_file_valid = True
            return file_path.read_text(encoding="utf-8", errors="ignore")

        if suffix == ".docx":
            doc = Document(str(file_path))
            is_file_valid = True
            return "\n".join(p.text for p in doc.paragraphs)

        raise ValueError(f"Unsupported file type: {suffix}")

    def on_file_picked(e: ft.FilePickerResultEvent):
        nonlocal words, word_index

        if not e.files:
            return

        try:
            text = import_file(e.files[0].path)
            words = text.split()
            word_index = 0
            txt_the_word.value = f"Loaded {len(words)} words"
            set_btn_visibilities(btn_stop=False, btn_start=True, btn_restart=False)
        except Exception as ex:
            txt_the_word.value = str(ex)

        page.update()

    file_picker = FilePicker(on_result=on_file_picked)
    page.overlay.append(file_picker)

    # -----------------------------
    # Reader Logic (ASYNC)
    # -----------------------------
    def reading_completed() -> None:
        nonlocal is_active, txt_the_word
        is_active = False

        txt_the_word.value = "- THE END -"
        set_btn_visibilities(btn_start=False, btn_stop=False, btn_reset=True)
        playsound(sfx_reading_complete, False)

    async def reader_loop():
        nonlocal word_index, is_active

        while is_active:
            try:
                playsound(sfx_word_appear, False)
                txt_the_word.value = words[word_index]
                page.update()
                word_index += 1
            except Exception:
                reading_completed()
                return

            delay = 60 / wpm
            await asyncio.sleep(delay)

        is_active = False

    def start_reader(e):
        nonlocal is_active

        if not words or is_active:
            return

        set_btn_visibilities(btn_start=False, btn_stop=True, btn_reset=True)

        playsound(sfx_button_start_click, False)

        is_active = True
        page.update()

        page.run_task(reader_loop)

    def reset_reader(e):
        nonlocal words, word_index, txt_the_word

        stop_reader(e)
        word_index = 0
        txt_the_word.value = "Static Reader"
        set_btn_visibilities(btn_start=True, btn_stop=False, btn_reset=False)

        playsound(sfx_button_start_click, False)

    def stop_reader(e):
        nonlocal is_active

        set_btn_visibilities(btn_start=True, btn_stop=False)

        playsound(sfx_button_stop_click, False)

        is_active = False
        page.update()

    # ------------------------------
    # Other Logic
    # ------------------------------
    def keyboard_event(ke: KeyboardEvent) -> None:
        nonlocal is_active

        playsound(sfx_writing, False)

        if ke.key == " ":
            if is_active:
                stop_reader(ke)
            else:
                start_reader(ke)
        else:
            #print(f"UNSIGNED KEY: {ke.key}")
            pass

    page.on_keyboard_event = keyboard_event

    txt_wpm: TextField = TextField()

    def wpm_handler(e) -> None:
        nonlocal wpm

        latest_valid_input = int(wpm or 60)

        print("WPM HANDLER")
        try:
            if str(txt_wpm.value).isdigit():
                new_wpm = int(txt_wpm.value or 0)
            else:
                raise ValueError
        except (ValueError, TypeError) as e:
            print(f"ERROR: {e}")
            txt_wpm.value = str(latest_valid_input)
            return

        lower_limit = 1
        upper_limit = 1000

        if lower_limit <= new_wpm <= upper_limit:
            wpm = new_wpm
        elif new_wpm < lower_limit:
            wpm = lower_limit
        else:
            wpm = upper_limit

        page.update()

        if txt_wpm:
            txt_wpm.value = str(wpm)
        print(f"new WPM: {wpm}")

    def playsound_btn_start_hover(e) -> None:
        playsound(sfx_button_hover, False)

    def playsound_btn_stop_hover(e) -> None:
        playsound(sfx_button_hover, False)

    txt_wpm: TextField = TextField(
        value="100",
        text_align=ft.TextAlign.CENTER,
        width=80,
        text_size=20,
        hint_text="WPM",
        on_submit=wpm_handler,
        # on_change=wpm_handler,
        on_tap_outside=wpm_handler,
    )

    # -----------------------------
    # Buttons
    # -----------------------------
    import_button = ElevatedButton(
        "Import File",
        on_click=lambda _: file_picker.pick_files(
            allow_multiple=False,
            allowed_extensions=["txt", "docx"],
        ),
        on_hover=playsound_btn_start_hover,
    )

    btn_start = ElevatedButton(
        text="Start",
        height=40,
        width=80,
        color=text_color,
        on_click=start_reader,
        on_hover=playsound_btn_start_hover,
        visible=False,
    )

    btn_reset = ElevatedButton(
        text="Reset",
        height=40,
        width=80,
        color="BLUE",
        on_click=reset_reader,
        on_hover=playsound_btn_start_hover,
        visible=False,
    )

    btn_stop = ElevatedButton(
        text="Stop",
        height=40,
        width=80,
        color="RED",
        on_click=stop_reader,
        on_hover=playsound_btn_stop_hover,
        visible=False,
    )

    page.add(
        Row(
            [
                Column(
                    [
                        txt_wpm,
                        txt_the_word,
                        import_button,
                        btn_start,
                        btn_stop,
                        btn_reset,
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                )
            ],
            expand=True,
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
    )


if __name__ == "__main__":
    ft.app(target=main)
