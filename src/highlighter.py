import logging

from maya import OpenMayaUI

try:
    import shiboken2
    from PySide2 import QtCore, QtGui, QtWidgets
    QRegExp = QtCore.QRegExp

    def get_text_document(script_editor_output_object):
        script_editor_output_widget = shiboken2.wrapInstance(
            int(script_editor_output_object), QtWidgets.QTextEdit
        )
        document = script_editor_output_widget.document()
        return document, script_editor_output_widget

except ImportError:
    import shiboken6
    from PySide6 import QtCore, QtGui, QtWidgets
    QRegExp = QtCore.QRegularExpression

    def get_text_document(script_editor_output_object):
        # TODO : this might not work as expected since it appears to freeze Maya after attaching the highlighter to the TextDocument.
        script_editor_output_widget = shiboken6.wrapInstance(
            int(script_editor_output_object), QtWidgets.QWidget
        )
        for child in script_editor_output_widget.children():
            for each in child.children():
                if isinstance(each, QtGui.QTextDocument):
                    return each, script_editor_output_widget

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class StdOut_Syntax(QtGui.QSyntaxHighlighter):
    kWhite = QtGui.QColor(200, 200, 200)
    kRed = QtGui.QColor(255, 0, 0)
    kOrange = QtGui.QColor(255, 160, 0)
    kGreen = QtGui.QColor(35, 170, 30)
    kBlue = QtGui.QColor(35, 160, 255)

    rx_error = QRegExp(r"[Ee][Rr][Rr][Oo][Rr]")
    error_format = QtGui.QTextCharFormat()
    error_format.setForeground(kRed)

    rx_warning = QRegExp(r"[Ww][Aa][Rr][Nn][Ii][Nn][Gg]")
    warning_format = QtGui.QTextCharFormat()
    warning_format.setForeground(kOrange)

    rx_debug = QRegExp(r"[Dd][Ee][Bb][Uu][Gg]")
    debug_format = QtGui.QTextCharFormat()
    debug_format.setForeground(kGreen)

    rx_traceback_start = QRegExp("Traceback \(most recent call last\)")
    traceback_format = QtGui.QTextCharFormat()
    traceback_format.setForeground(kBlue)

    default_format = QtGui.QTextCharFormat()
    default_format.setForeground(kWhite)

    Rules = [
        (rx_debug, debug_format),
        (rx_warning, warning_format),
        (rx_error, error_format),
    ]

    def __init__(self, parent):
        super(StdOut_Syntax, self).__init__(parent)
        self.parent = parent
        self.normal, self.traceback = range(2)

    def highlightBlock(self, t):
        self.setCurrentBlockState(self.normal)
        if self.isTraceback(t):
            self.setFormat(0, len(t), self.traceback_format)
            self.setCurrentBlockState(self.traceback)
        elif self.isPySideError(t):
            self.setFormat(0, len(t), self.error_format)
            self.setCurrentBlockState(self.traceback)
        else:
            self.line_formatting(t)

    def line_formatting(self, t):
        for regex, formatting in StdOut_Syntax.Rules:
            i = regex.indexIn(t)
            if i > 0:
                self.setFormat(0, len(t), formatting)

    def isTraceback(self, t):
        return (
            self.previousBlockState() == self.normal
            and self.rx_traceback_start.indexIn(t) > 0
        ) or (
            self.previousBlockState() == self.traceback
            and (t.startswith("#   ") or t.startswith("# # "))
        )

    def isPySideError(self, t):
        return t.startswith("# Error") or t.startswith("# TypeError")


def __se_highlight():
    logger.debug("Attaching highlighter")
    i = 1
    while True:
        script_editor_output_name = "cmdScrollFieldReporter{0}".format(i)
        script_editor_output_object = OpenMayaUI.MQtUtil.findControl(
            script_editor_output_name
        )
        if not script_editor_output_object:
            break
        document, script_editor_output_widget = get_text_document(
            script_editor_output_object)
        StdOut_Syntax(document)
        logger.debug("Done attaching highlighter to : %s" % script_editor_output_widget)
        i += 1


__qt_focus_change_callback = {"cmdScrollFieldReporter": __se_highlight}


def __on_focus_changed(old_widget, new_widget):
    """Enable the highlighter when changing focus to the script editor.

    :param old_widget: previously focused widget. Argument passed by the signal triggering this.
    :param new_widget: currently focused widget. Argument passed by the signal triggering this.
    """
    if new_widget:
        widget_name = new_widget.objectName()
        for callback in [
            name for name in __qt_focus_change_callback if widget_name.startswith(name)
        ]:
            __qt_focus_change_callback[callback]()


def setup_highlighter():
    try:
        app = QtWidgets.QApplication.instance()
        app.focusChanged.connect(__on_focus_changed)
        __se_highlight()
    except Exception as exp:
        pass
