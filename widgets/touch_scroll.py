from PyQt6.QtWidgets import QScrollArea
from PyQt6.QtCore import Qt, QEvent


class TouchScrollArea(QScrollArea):
    """QScrollArea עם תמיכה בגלילה מסך-מגע."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._touch_start = None
        self._scroll_start = None
        self.viewport().setAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents, True)

    def viewportEvent(self, event):
        t = event.type()
        if t == QEvent.Type.TouchBegin:
            pts = event.points()
            if pts:
                self._touch_start = pts[0].position().toPoint()
                self._scroll_start = self.verticalScrollBar().value()
            return True
        if t == QEvent.Type.TouchUpdate:
            pts = event.points()
            if pts and self._touch_start is not None:
                delta = pts[0].position().toPoint().y() - self._touch_start.y()
                self.verticalScrollBar().setValue(self._scroll_start - delta)
            return True
        if t == QEvent.Type.TouchEnd:
            self._touch_start = None
            return True
        return super().viewportEvent(event)
