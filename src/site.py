import streamlit as st
import os
from datetime import datetime
import io
import subprocess
import platform
from user_files_analysis import analyse_user_data
import time

# Инициализация сессионного состояния для хранения файлов
if 'audio_files' not in st.session_state:
    st.session_state.audio_files = []
if 'pending_recording' not in st.session_state:
    st.session_state.pending_recording = None
if 'show_save_dialog' not in st.session_state:
    st.session_state.show_save_dialog = False
if 'widget_key_suffix' not in st.session_state:
    st.session_state.widget_key_suffix = 0


@st.dialog("Результат")
def show_result(result: int):
    match result:
        case -1:
            st.error('В детали присутствует дефект')
        case 0:
            st.warning('Определить наличие дефекта по заданным данным не удалось. Попробуйте ещё раз')
        case 1:
            st.success('Дефекты в детали отстутвуют')
    if st.button('Назад'):
        st.session_state.audio_files = []
        st.session_state.pending_recording = None
        st.session_state.show_save_dialog = False
        st.session_state.widget_key_suffix += 1
        st.rerun()


# Функция для сохранения аудиофайла
def save_audio_file(audio_data, filename_prefix="audio"):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{filename_prefix}_{timestamp}.mp3"

    # Сохраняем в папку saved_audio
    os.makedirs("saved_audio", exist_ok=True)
    filepath = os.path.join("saved_audio", filename)

    audio_bytes = audio_data.getvalue() if hasattr(audio_data, 'getvalue') else audio_data

    with open(filepath, "wb") as f:
        f.write(audio_bytes)

    return filename, filepath


# Функция для открытия папки
def open_folder(path):
    try:
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(['open', path])
        else:  # Linux
            subprocess.run(['xdg-open', path])
        return True
    except Exception as e:
        st.error(f"Не удалось открыть папку: {e}")
        return False


# Создаем две колонки
col1, col2 = st.columns([2, 1])

with col1:
    st.title("Сайт для работы с аудио")
    st.write("Запишите звук или загрузите готовый файл. Все данные сохраняются на компьютер.")

    # Вкладки для записи и загрузки
    tab1, tab2 = st.tabs(["🎤 Запись с микрофона", "📁 Загрузка файла"])

    with tab1:
        st.write("Запишите аудио")

        # Запись аудио
        recorded_audio = st.audio_input(
            "Записать аудио с микрофона",
            key=f"audio_recorder_{st.session_state.widget_key_suffix}"
        )

        if recorded_audio is not None:
            st.session_state.pending_recording = recorded_audio
            st.session_state.show_save_dialog = True

            # Показываем записанное аудио
            st.audio(recorded_audio, format="audio/wav")
            st.success("Запись завершена!")

    with tab2:
        uploaded_files = st.file_uploader(
            "Загрузите готовые файлы (.mp3)",
            type=["mp3"],
            accept_multiple_files=True,
            key=f"file_uploader_{st.session_state.widget_key_suffix}"
        )

        if uploaded_files:
            for uploaded_file in uploaded_files:
                # Проверяем, не загружен ли уже такой файл
                if uploaded_file.name not in [f['name'] for f in st.session_state.audio_files if
                                              f['type'] == 'uploaded']:
                    # Сохраняем файл
                    filename, filepath = save_audio_file(uploaded_file, "uploaded")

                    # Добавляем в список
                    st.session_state.audio_files.append({
                        'name': uploaded_file.name,
                        'filepath': filepath,
                        'type': 'uploaded',
                        'data': uploaded_file.getvalue(),
                        'timestamp': datetime.now().strftime("%H:%M:%S")
                    })
                    st.success(f"Файл {uploaded_file.name} загружен!")

    # Диалог сохранения записи
    if st.session_state.show_save_dialog and st.session_state.pending_recording is not None:
        st.write("---")
        st.subheader("Что сделать с записью?")

        col_save, col_delete = st.columns(2)

        with col_save:
            if st.button("💾 Сохранить запись", type="primary"):
                # Сохраняем запись
                filename, filepath = save_audio_file(
                    st.session_state.pending_recording,
                    "recorded"
                )

                # Добавляем в список файлов
                st.session_state.audio_files.append({
                    'name': filename,
                    'filepath': filepath,
                    'type': 'recorded',
                    'data': st.session_state.pending_recording.getvalue(),
                    'timestamp': datetime.now().strftime("%H:%M:%S")
                })

                st.success(f"Запись сохранена как {filename}")
                st.session_state.pending_recording = None
                st.session_state.show_save_dialog = False
                st.rerun()

        with col_delete:
            if st.button("🗑️ Удалить запись"):
                st.session_state.pending_recording = None
                st.session_state.show_save_dialog = False
                st.info("Запись удалена")
                st.rerun()

    # Кнопка определения дефекта
    st.write("---")

    files_count = len(st.session_state.audio_files)
    can_analyze = 3 <= files_count <= 10

    if can_analyze:
        st.write(f"✅ Загружено {files_count} файлов. Можно провести анализ.")
    else:
        st.write(f"📊 Загружено {files_count} файлов. Нужно от 3 до 10 файлов для анализа.")

    analyze_button = st.button(
        "🔍 Определение дефекта",
        type="primary",
        disabled=not can_analyze,
        use_container_width=True
    )

    if analyze_button:
        st.success("Анализ запущен!")
        st.write("Анализируемые файлы:")
        for i, file in enumerate(st.session_state.audio_files, 1):
            st.write(f"{i}. {file['name']} ({file['type']})")
        result = analyse_user_data()
        show_result(result)


# Правая колонка - список файлов
with col2:
    st.subheader("📋 Список файлов")

    if not st.session_state.audio_files:
        st.info("Файлы пока не загружены")
    else:
        st.write(f"Всего файлов: {len(st.session_state.audio_files)}")

        for idx, file in enumerate(st.session_state.audio_files):
            with st.container():
                col_file, col_del = st.columns([3, 1])

                with col_file:
                    icon = "🎤" if file['type'] == 'recorded' else "📁"
                    st.write(f"{icon} {file['name']}")
                    st.caption(f"Добавлен: {file['timestamp']}")

                with col_del:
                    if st.button("❌", key=f"del_{idx}", help="Удалить файл"):
                        try:
                            if os.path.exists(file['filepath']):
                                os.remove(file['filepath'])
                        except Exception as e:
                            st.error(f"Ошибка удаления файла: {e}")

                        st.session_state.audio_files.pop(idx)
                        st.rerun()

        if st.button("🗑️ Очистить все", type="secondary"):
            for file in st.session_state.audio_files:
                try:
                    if os.path.exists(file['filepath']):
                        os.remove(file['filepath'])
                except Exception:
                    pass

            st.session_state.audio_files = []
            st.rerun()

# Боковая панель
st.sidebar.write("---")
st.sidebar.write("### 📊 Статистика")
st.sidebar.write(f"Записанных файлов: {len([f for f in st.session_state.audio_files if f['type'] == 'recorded'])}")
st.sidebar.write(f"Загруженных файлов: {len([f for f in st.session_state.audio_files if f['type'] == 'uploaded'])}")
st.sidebar.write(f"Всего файлов: {len(st.session_state.audio_files)}")

if can_analyze:
    st.sidebar.success("Можно запускать анализ!")
else:
    st.sidebar.warning("Нужно 3-10 файлов для анализа")

# Кнопка открытия папки
st.sidebar.write("---")
if st.sidebar.button("📂 Открыть папку с файлами", use_container_width=True):
    save_path = os.path.abspath("saved_audio")
    if open_folder(save_path):
        st.sidebar.success("Папка открыта!")
    else:
        st.sidebar.error("Не удалось открыть папку")
