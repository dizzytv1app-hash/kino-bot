from aiogram.fsm.state import State, StatesGroup


class AddMovie(StatesGroup):
    code = State()
    name = State()
    poster = State()
    video = State()
    rating = State()
    confirm = State()


class EditMovie(StatesGroup):
    code = State()
    choose = State()
    value = State()


class DeleteMovie(StatesGroup):
    code = State()
    confirm = State()


class Broadcast(StatesGroup):
    message = State()
    confirm = State()


class AddChannel(StatesGroup):
    waiting = State()


class AddAdmin(StatesGroup):
    waiting = State()


class SetChannelLink(StatesGroup):
    waiting = State()


class RestoreBackup(StatesGroup):
    file = State()
    confirm = State()
