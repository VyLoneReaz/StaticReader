import pygame.mixer
import asyncio
import flet as ft
from flet import (
    Page,
    Column,
    Row,
    TextField,
    Text,
    Switch,
    Slider,
    ElevatedButton,
    FilePicker,
    KeyboardEvent,
    ControlEvent,
)
from docx import Document
from pathlib import Path

# -----------------------------
# Pygame.mixer setup - Audio
# -----------------------------
pygame.mixer.init(
    frequency=44100,
    size=-16,
    channels=2,
    buffer=512,  # affects latency
)


def load_sfx(path: str, volume: float = 1) -> pygame.mixer.Sound:
    sound = pygame.mixer.Sound(path)
    sound.set_volume(volume)
    return sound


def main(page: Page) -> None:
    # -----------------------------
    # App State
    # -----------------------------
    words: list[str] = []
    word_index = 0
    is_active = False
    is_file_valid = False
    show_ui = True

    # -----------------------------
    # Reading Speed [WPM] (Properties)
    # -----------------------------
    wpm = 60
    lower_limit = 1
    upper_limit = 1000

    # -----------------------------
    # Smart Pacing
    # -----------------------------
    use_smart_pacing = False
    base_delay = 60 / wpm
    word = None
    word_length = None
    AVG_WORD_LEN = 4.5
    LENGTH_WEIGHT = 0.3
    MIN_FACTOR = 0.7

    # -----------------------------
    # SFX - Audio
    # -----------------------------
    mute_audio = False
    ICON_NOT_MUTED = ft.Icons.MUSIC_NOTE
    ICON_MUTED = ft.Icons.MUSIC_OFF

    def play_sfx(sound: pygame.mixer.Sound):
        nonlocal mute_audio
        if not mute_audio:
            sound.play()

    def toggle_mute_audio(e: ControlEvent) -> None:
        nonlocal mute_audio, btn_toggle_mute_audio
        mute_audio = not mute_audio
        if mute_audio:
            btn_toggle_mute_audio.icon = ICON_MUTED
        else:
            btn_toggle_mute_audio.icon = ICON_NOT_MUTED
            play_sfx(sfx_button_start_click)
        page.update()

    sfx_word_appear = load_sfx("assets/audio/_UsedSFX/TOON_Pop.wav", volume=0.7)
    sfx_button_hover = load_sfx("assets/audio/_UsedSFX/Bonk Hover A.wav", volume=0.4)
    sfx_button_start_click = load_sfx("assets/audio/_UsedSFX/Light Click A_Start.wav")
    sfx_button_stop_click = load_sfx("assets/audio/_UsedSFX/Light Click B_Stop.wav")
    sfx_writing = load_sfx(
        "assets/audio/_UsedSFX/ui_menu_button_beep_08.wav", volume=0.9
    )
    sfx_reading_complete = load_sfx(
        "assets/audio/_UsedSFX/collect_item_sparkle_pop_03.wav"
    )

    # -----------------------------
    # Page Setup
    # -----------------------------
    page.title = "Static Reader"
    page.theme_mode = ft.ThemeMode.DARK
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.window.frameless = False
    page.window.shadow = True
    # page.window.full_screen = True

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
            stop_reader(e)
            text = import_file(e.files[0].path)
            words = text.split()
            word_index = 0
            txt_the_word.value = f"Loaded {len(words)} words"
            if show_ui:
                set_btn_visibilities(btn_stop=False, btn_start=True, btn_reset=False)
        except Exception as ex:
            txt_the_word.value = str(ex)

        page.update()

    file_picker = FilePicker(on_result=on_file_picked)
    page.overlay.append(file_picker)

    # -----------------------------
    # Reader Logic (ASYNC)
    # -----------------------------
    def reading_completed() -> None:
        nonlocal is_active, txt_the_word, word_index
        is_active = False
        word_index = 0
        txt_the_word.value = "- THE END -"
        if show_ui:
            set_btn_visibilities(btn_start=False, btn_stop=False, btn_reset=True)
        else:
            toggle_show_ui()
        play_sfx(sfx_reading_complete)

    async def reader_loop():
        nonlocal \
            base_delay, \
            words, \
            word, \
            word_length, \
            word_index, \
            is_active, \
            AVG_WORD_LEN, \
            LENGTH_WEIGHT, \
            MIN_FACTOR

        while is_active:
            try:
                play_sfx(sfx_word_appear)
                txt_the_word.value = words[word_index]
                page.update()

                if use_smart_pacing:
                    word = words[word_index]
                    word_length = len(word)

                    length_factor = (
                        1.0
                        + ((word_length - AVG_WORD_LEN) / AVG_WORD_LEN) * LENGTH_WEIGHT
                    )
                    length_factor = max(MIN_FACTOR, length_factor)

                    # Punctuation pauses
                    punctuation_factor = 1.0
                    if word.endswith((",", ";", ":", '"', "'", ")", "]", "}")):
                        punctuation_factor = 1.225
                    elif word.endswith((".", "!", "?")):
                        punctuation_factor = 1.375

                    delay = base_delay * length_factor * punctuation_factor
                else:
                    delay = base_delay

                word_index += 1
            except Exception:
                reading_completed()
                return

            await asyncio.sleep(delay)

        is_active = False

    def start_reader(e):
        nonlocal is_active

        if not words or is_active:
            return

        if show_ui:
            set_btn_visibilities(btn_start=False, btn_stop=True, btn_reset=True)
        play_sfx(sfx_button_start_click)

        is_active = True

        page.update()
        page.run_task(reader_loop)

    def reset_reader(e):
        nonlocal words, word_index, txt_the_word

        stop_reader(e)
        word_index = 0
        txt_the_word.value = "Static Reader"
        if show_ui:
            set_btn_visibilities(btn_start=True, btn_stop=False, btn_reset=False)
        play_sfx(sfx_button_start_click)

    def stop_reader(e):
        nonlocal is_active

        if show_ui:
            set_btn_visibilities(btn_start=True, btn_stop=False)
        play_sfx(sfx_button_stop_click)

        is_active = False

        page.update()

    # ------------------------------
    # Input Handling
    # ------------------------------
    def keyboard_event(ke: KeyboardEvent) -> None:
        nonlocal is_active

        play_sfx(sfx_writing)

        if ke.key == " ":
            if is_active:
                stop_reader(ke)
            else:
                start_reader(ke)
        elif ke.key.lower() == "i":
            file_picker.pick_files(
                allow_multiple=False,
                allowed_extensions=["txt", "docx"],
            )
        elif ke.key.lower() == "s":
            adjust_use_smart_pace_state(ke, not use_smart_pacing)
        elif ke.key.lower() == "r":
            reset_reader(ke)
        elif ke.key.lower() == "m":
            toggle_mute_audio(ke)
        elif ke.key.lower() == "h":
            toggle_show_ui()
        else:
            # print(f"UNSIGNED KEY: {ke.key}")
            pass

    page.on_keyboard_event = keyboard_event

    txt_wpm: TextField = TextField()

    def mouse_tap_event(e) -> None:
        if not show_ui:
            toggle_show_ui()

    # ------------------------------
    # Other Logic
    # ------------------------------
    def wpm_handler(e) -> None:
        nonlocal wpm, base_delay, lower_limit, upper_limit, slider_wpm

        latest_valid_input = int(wpm or 60)

        try:
            if str(txt_wpm.value).isdigit():
                new_wpm = int(txt_wpm.value or 0)
            else:
                raise ValueError
        except (ValueError, TypeError) as e:
            print(f"ERROR: {e}")
            txt_wpm.value = str(latest_valid_input)
            return

        if lower_limit <= new_wpm <= upper_limit:
            wpm = new_wpm
        elif new_wpm < lower_limit:
            wpm = lower_limit
        else:
            wpm = upper_limit

        base_delay = 60 / wpm

        if txt_wpm:
            txt_wpm.value = str(wpm)
        if slider_wpm:
            # slider_wpm.label = str(wpm)
            slider_wpm.value = wpm

        page.update()

    def slider_wpm_handler(e) -> None:
        nonlocal wpm, txt_wpm, base_delay, lower_limit, upper_limit, slider_wpm
        try:
            if slider_wpm:
                new_wpm = int(slider_wpm.value)
            else:
                raise ValueError
        except (ValueError, TypeError) as e:
            print(f"ERROR: {e}")
            return
        if lower_limit <= new_wpm <= upper_limit:
            wpm = new_wpm
        elif new_wpm < lower_limit:
            wpm = lower_limit
        else:
            wpm = upper_limit
        base_delay = 60 / wpm

        if slider_wpm:
            # slider_wpm.label = str(wpm)
            pass
        if txt_wpm:
            txt_wpm.value = str(wpm)

        page.update()

    def playsound_btn_hover(ce: ControlEvent) -> None:
        if ce.data == "true":
            play_sfx(sfx_button_hover)

    def adjust_use_smart_pace_state(e, *args) -> None:
        nonlocal switch_smart_pacing, use_smart_pacing, label_smart_pacing

        if args:
            switch_smart_pacing.value = args[0]

        if switch_smart_pacing:
            use_smart_pacing = switch_smart_pacing.value
            # print(f"Using Smart Pacing : {use_smart_pacing}")

            """
            label_smart_pacing.value = (
                "Smart Pacing | Enabled"
                if use_smart_pacing
                else "Smart Pacing | Disabled"
            )
            """

            label_smart_pacing.color = "#8CE4FF" if use_smart_pacing else "#7C7C7C"

            page.update()

    def toggle_show_ui() -> None:
        nonlocal \
            label_smart_pacing, \
            switch_smart_pacing, \
            txt_wpm, \
            slider_wpm, \
            btn_reset, \
            btn_start, \
            btn_stop, \
            import_button, \
            btn_toggle_mute_audio, \
            show_ui

        show_ui = not show_ui

        label_smart_pacing.visible = show_ui
        switch_smart_pacing.visible = show_ui
        txt_wpm.visible = show_ui
        slider_wpm.visible = show_ui
        btn_reset.visible = show_ui
        btn_start.visible = show_ui
        btn_stop.visible = show_ui
        import_button.visible = show_ui
        btn_toggle_mute_audio.visible = show_ui
        page.update()

    txt_wpm: TextField = TextField(
        value=str(wpm),
        text_align=ft.TextAlign.CENTER,
        width=80,
        text_size=20,
        hint_text="WPM",
        border_width=1,
        border_radius=7,
        border_color="RED",
        color="WHITE",
        cursor_color="RED",
        on_submit=wpm_handler,
        # on_change=wpm_handler,
        on_tap_outside=wpm_handler,
    )

    slider_wpm: Slider = Slider(
        value=wpm,
        min=lower_limit,
        max=upper_limit,
        width=333,
        thumb_color="WHITE",
        active_color="RED",
        inactive_color="#470000",
        # divisions=int(upper_limit/10),
        # label=str(wpm),
        on_change=slider_wpm_handler,
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
        on_hover=playsound_btn_hover,
    )

    btn_start = ElevatedButton(
        text="Start",
        height=40,
        width=80,
        color=text_color,
        on_click=start_reader,
        on_hover=playsound_btn_hover,
        visible=False,
    )

    btn_reset = ElevatedButton(
        text="Reset",
        height=40,
        width=80,
        color="BLUE",
        on_click=reset_reader,
        on_hover=playsound_btn_hover,
        visible=False,
    )

    btn_stop = ElevatedButton(
        text="Stop",
        height=40,
        width=80,
        color="RED",
        on_click=stop_reader,
        on_hover=playsound_btn_hover,
        visible=False,
    )

    btn_toggle_mute_audio = ft.IconButton(
        tooltip="Toggle Sounds",
        icon=ICON_NOT_MUTED,
        icon_size=20,
        icon_color="WHITE",
        on_click=toggle_mute_audio,
        on_hover=playsound_btn_hover,
    )

    # -----------------------------
    # Other UI-Elements
    # -----------------------------
    tooltip_sp = "Smart Pacing is a Feature that adjusts word render durations to improve reading flow."

    label_smart_pacing: Text = Text(
        value="Smart Pacing",
        tooltip=tooltip_sp,
        size=25,
        color="#7C7C7C",
    )

    switch_smart_pacing: Switch = Switch(
        # label="Enable Smart Pacing",
        label_position=ft.LabelPosition.LEFT,
        tooltip=tooltip_sp,
        on_change=adjust_use_smart_pace_state,
        on_focus=playsound_btn_hover,
    )

    def show_ui_info(e) -> None:
        nonlocal txt_show_ui_info

        txt_show_ui_info.visible = True

    def hide_ui_info(e) -> None:
        nonlocal txt_show_ui_info
        txt_show_ui_info.visible = False

    gesture_detector = ft.GestureDetector(
        on_tap=mouse_tap_event,
        on_secondary_tap=mouse_tap_event,
        #on_pan_start=show_ui_info,
        #on_pan_end=hide_ui_info,
        content=ft.Container(),  # size comes from Stack
    )

    txt_show_ui_info: Text = Text(
        value="Press 'H' to toggle UI", 
        size=10, 
        color="#444444"
    )

    # -----------------------------
    # Adding UI-Elements to Page
    # -----------------------------
    page.add(
        ft.Stack(
            expand=True,
            controls=[
                # Fullscreen click catcher (BOTTOM)
                ft.Container(
                    expand=True,
                    content=gesture_detector,
                ),
                # UI LAYER (TOP)
                ft.Column(
                    expand=True,
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        label_smart_pacing,
                        switch_smart_pacing,
                        Row(
                            expand=True,
                            alignment=ft.MainAxisAlignment.CENTER,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                Column(
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    controls=[
                                        txt_wpm,
                                        slider_wpm,
                                        txt_the_word,
                                        import_button,
                                        btn_start,
                                        btn_stop,
                                        btn_reset,
                                    ],
                                )
                            ],
                        ),
                        btn_toggle_mute_audio,
                        txt_show_ui_info,
                    ],
                ),
            ],
        )
    )


if __name__ == "__main__":
    ft.app(target=main)
