from pyrogram import Client

print("Для генерації рядка сесії потрібні ваші API ключі.")
print("Ви можете отримати їх на https://my.telegram.org/apps")

API_ID = int(input("Введіть ваш API_ID: "))
API_HASH = input("Введіть ваш API_HASH: ")

with Client(
    name="my_account",
    api_id=API_ID,
    api_hash=API_HASH,
    in_memory=True
) as app:
    session_string = app.export_session_string()
    print("\n✅ Ваша сесія успішно створена!")
    print("Це ваш рядок сесії. Скопіюйте його і збережіть у надійному місці.")
    print("Вставте цей рядок у змінну середовища PYROGRAM_SESSION на вашому сервері.\n")
    print(f"SESSION STRING:\n{session_string}")