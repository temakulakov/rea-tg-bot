# states/states.py
from aiogram.fsm.state import State, StatesGroup

class SpeakerState(StatesGroup):
    choosing_name = State()      # Waiting for speaker's full name input
    confirm_identity = State()   # Asking "Is this you?" confirmation
    main_menu = State()          # Speaker main menu (after successful identification)

class ChaperoneState(StatesGroup):
    entering_login = State()     # Waiting for teacher login
    entering_password = State()  # Waiting for teacher password
    main_menu = State()          # Teacher main menu (after successful auth)
    viewing_students = State()   # (Optional) State when viewing student list (for pagination)
    admin_upload = State()
    # Note: workshop viewing could reuse the same state or separate, but we handle via callbacks.
