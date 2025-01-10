
import streamlit as st
import requests

# URL FastAPI (обновите на ваш URL или оставьте заглушку)
#API_URL = "https://my-fчastapi-app.onrender.com"
API_URL = "http://backend:80"
API_ML_URL = "http://ml_server:8007"
# Проверка авторизации пользователя
if "is_logged_in" not in st.session_state:
    st.session_state["is_logged_in"] = False
    st.session_state["user_data"] = None

# Регистрация пользователя
def register_user(name, email, password):
    response = requests.post(f"{API_URL}/register", json={
        "name": name,
        "email": email,
        "password": password
    })
    return response.json()

# Авторизация пользователя
def login_user(email, password):
    response = requests.post(f"{API_URL}/login", json={
        "email": email,
        "password": password
    })
    return response.json()

# Интерфейс Streamlit
st.sidebar.title("Навигация")
page = st.sidebar.selectbox("Выберите страницу", ["Эхо-чат", "Профиль", "Регистрация", "Авторизация"])

# Страница регистрации
if page == "Регистрация":
    st.title("Регистрация")
    name = st.text_input("Имя")
    email = st.text_input("Email")
    password = st.text_input("Пароль", type="password")
    if st.button("Зарегистрироваться"):
        if name and email and password:
            response = register_user(name, email, password)
            if response.get("status") == 200:
                st.success("Регистрация успешна! Теперь авторизуйтесь.")
            else:
                st.error(response.get("detail", "Ошибка регистрации."))
        else:
            st.error("Все поля обязательны для заполнения.")

# Страница авторизации
elif page == "Авторизация":
    st.title("Авторизация")
    email = st.text_input("Email")
    password = st.text_input("Пароль", type="password")
    if st.button("Войти"):
        if email and password:
            response = login_user(email, password)
            if response.get("status") == 200:
                st.session_state["is_logged_in"] = 1
                st.session_state["user_data"] = {
                    "name": response.get("name"),
                    "email": email
                }
                st.success("Вход выполнен успешно!")

            else:
                st.error(response.get("detail", "Ошибка авторизации."))
        else:
            st.error("Введите email и пароль.")

# Страница профиля
elif page == "Профиль":
    if st.session_state["is_logged_in"]:
        st.title("Профиль пользователя")
        st.write(f"**Имя:** {st.session_state['user_data']['name']}")
        st.write(f"**Email:** {st.session_state['user_data']['email']}")
    else:
        st.warning("Пожалуйста, авторизуйтесь, чтобы увидеть профиль.")

# Страница эхо-чата
# Страница эхо-чата
elif page == "Эхо-чат":
    if st.session_state["is_logged_in"] == 1:
        st.title("Чат досуга ⛺️")
    
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Показать все предыдущие сообщения
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Получить ввод от пользователя
        user_input = st.chat_input("What is up?")
        if user_input:
            # Добавить сообщение пользователя в список сообщений и сразу отобразить его
            st.session_state.messages.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.markdown(user_input)

            # Отправить запрос к API и получить ответ
            response = requests.post(f"{API_ML_URL}/ask", json={"request_text": user_input})
            if response.status_code == 200:
                response_text = response.json().get('response', '')
            else:
                response_text = "Произошла ошибка при получении ответа от сервера."

            # Добавить ответ от API в список сообщений и отобразить его
            st.session_state.messages.append({"role": "assistant", "content": response_text})
            with st.chat_message("assistant"):
                st.markdown(response_text)

    else:
        st.warning("Пожалуйста, авторизуйтесь, чтобы использовать чат.")