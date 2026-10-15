"""
Паттерн Bridge (Мост) для системы уведомлений.

Две независимые иерархии:

    Абстракция (ЧТО отправляем и насколько это срочно)
        Notification
        ├── NormalNotification
        ├── ImportantNotification
        └── EmergencyNotification

    Реализация (КУДА и КАК доставляем)
        Channel
        ├── EmailChannel
        ├── SMSChannel
        └── TelegramChannel

Связь между ними - композиция: у Notification есть поле self.channel.
Это и есть "мост". Любой приоритет работает с любым каналом,
а новый канал или приоритет добавляется одним классом.
"""

from abc import ABC, abstractmethod


# ======================================================================
# Реализация (Implementor): каналы доставки
# ======================================================================
class Channel(ABC):
    """Интерфейс канала доставки. Знает только про формат канала."""

    name = ""

    @abstractmethod
    def deliver(self, title: str, body: str, urgent: bool) -> str:
        """Имитирует отправку и возвращает текст того, что ушло получателю."""


class EmailChannel(Channel):
    name = "Email"

    def deliver(self, title, body, urgent):
        flag = "X-Priority: 1 (высокий)\n" if urgent else ""
        return f"{flag}Тема: {title}\n\n{body}"


class SMSChannel(Channel):
    name = "SMS"
    MAX_LEN = 160

    def deliver(self, title, body, urgent):
        text = f"{title}: {body}"
        if len(text) > self.MAX_LEN:
            text = text[: self.MAX_LEN - 3] + "..."
        return text


class TelegramChannel(Channel):
    name = "Telegram"

    def deliver(self, title, body, urgent):
        sound = "со звуком" if urgent else "без звука"
        return f"*{title}*\n{body}\n(доставка {sound})"


# ======================================================================
# Абстракция (Abstraction): приоритеты
# ======================================================================
class Notification(ABC):
    """
    Базовая абстракция. Хранит ссылку на канал (мост)
    и делегирует ему доставку, не зная, какой именно это канал.
    """

    priority_name = ""
    title = ""
    urgent = False
    attempts = 1  # сколько раз пробуем доставить

    def __init__(self, channel: Channel):
        self.channel = channel  # <-- мост

    def decorate(self, message: str) -> str:
        """Приоритет решает, как дополнить текст. Переопределяется в наследниках."""
        return message

    def send(self, message: str) -> dict:
        body = self.decorate(message)
        delivered = self.channel.deliver(self.title, body, self.urgent)
        return {
            "channel": self.channel.name,
            "priority": self.priority_name,
            "attempts": self.attempts,
            "payload": delivered,
        }


class NormalNotification(Notification):
    priority_name = "Normal"
    title = "Уведомление"


class ImportantNotification(Notification):
    priority_name = "Important"
    title = "ВАЖНО"
    urgent = True

    def decorate(self, message):
        return f"{message}\nПожалуйста, ознакомьтесь сегодня."


class EmergencyNotification(Notification):
    priority_name = "Emergency"
    title = "ЭКСТРЕННО"
    urgent = True
    attempts = 3

    def decorate(self, message):
        return f"{message}\nТребуются немедленные действия!"


# ======================================================================
# Реестры и фабрика: единственное место, где перечислены варианты
# ======================================================================
CHANNELS = {
    "Email": EmailChannel,
    "SMS": SMSChannel,
    "Telegram": TelegramChannel,
}

PRIORITIES = {
    "Normal": NormalNotification,
    "Important": ImportantNotification,
    "Emergency": EmergencyNotification,
}


def create_notification(notification_type: str, priority: str) -> Notification:
    """Собирает мост: выбранный приоритет + выбранный канал."""
    if notification_type not in CHANNELS:
        raise ValueError(f"Неизвестный тип уведомления: {notification_type}")
    if priority not in PRIORITIES:
        raise ValueError(f"Неизвестный приоритет: {priority}")
    channel = CHANNELS[notification_type]()
    return PRIORITIES[priority](channel)
