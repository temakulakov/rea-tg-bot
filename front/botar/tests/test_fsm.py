import types
from handlers.chaperone import show_students_page

class DummyMessage:
    # dummy Message with minimal interface needed
    async def answer(self, text, reply_markup=None, parse_mode=None, **kwargs):
        self.sent_text = text
        self.sent_markup = reply_markup
        return self

@pytest.mark.asyncio
async def test_show_students_page_first_page():
    students = [{"id": i, "name": f"Student{i}"} for i in range(1, 12)]  # 11 students
    dummy_msg = DummyMessage()
    await show_students_page(dummy_msg, students, page=0)
    # The first page should list Student1..Student8 and have a Next button
    assert "Выбери ученика" in dummy_msg.sent_text
    keyboard = dummy_msg.sent_markup
    # keyboard is InlineKeyboardMarkup with inline_keyboard property
    names = [btn.text for row in keyboard.inline_keyboard for btn in row if not btn.callback_data.startswith("students_page")]
    assert names[0] == "Student1" and names[-1] == "Student8"
    # Check that a Next button exists
    nav_buttons = [btn for row in keyboard.inline_keyboard for btn in row if btn.callback_data.startswith("students_page")]
    assert any(btn.callback_data == "students_page_1" for btn in nav_buttons)
