"""PyQt6 front end for the shared license generator."""

from datetime import date
from pathlib import Path

from license_gen import (
    LICENSES,
    PERSONALIZED,
    git_author,
    license_filename,
    license_key,
    render,
    save_config,
    write_license,
)


def run(config, project_name=""):
    try:
        from PyQt6.QtWidgets import (
            QApplication,
            QComboBox,
            QFileDialog,
            QFormLayout,
            QHBoxLayout,
            QLabel,
            QLineEdit,
            QMessageBox,
            QPlainTextEdit,
            QPushButton,
            QVBoxLayout,
            QWidget,
        )
    except ModuleNotFoundError as error:
        if error.name != "PyQt6":
            raise
        raise ValueError(
            "PyQt6 is missing. Install PyQt6 or your distribution's package."
        ) from error

    app = QApplication([])
    window = QWidget()
    window.setWindowTitle("License Generator v1.0.0")
    window.resize(820, 640)
    layout = QVBoxLayout(window)
    form = QFormLayout()
    layout.addLayout(form)
    selection = QComboBox()
    for key, label in LICENSES.items():
        selection.addItem(label, key)
    selection.setCurrentIndex(
        selection.findData(license_key(config.get("license", "mit")))
    )
    holder = QLineEdit(config.get("author") or git_author())
    year = QLineEdit(str(date.today().year))
    project = QLineEdit(project_name)
    project.setPlaceholderText("Optional")
    form.addRow("&Project name:", project)
    form.addRow("&License:", selection)
    form.addRow("&Copyright holder:", holder)
    form.addRow("&Year:", year)
    status = QLabel()
    status.setWordWrap(True)
    layout.addWidget(status)
    preview = QPlainTextEdit()
    preview.setReadOnly(True)
    preview.setAccessibleName("License preview")
    layout.addWidget(preview, 1)
    actions = QHBoxLayout()
    layout.addLayout(actions)
    defaults = QPushButton("Save as &default")
    copy = QPushButton("Cop&y")
    save = QPushButton("&Save…")
    for button in (defaults, copy, save):
        actions.addWidget(button)
    text = ""

    def refresh():
        nonlocal text
        key = selection.currentData()
        editable = key in PERSONALIZED
        holder.setEnabled(editable)
        year.setEnabled(editable)
        try:
            text = render(key, holder.text(), year.text())
            status.setText(
                "" if editable else "The standard license text is used unchanged."
            )
        except (ValueError, OSError) as error:
            text = ""
            status.setText(str(error))
        preview.setPlainText(text)
        copy.setEnabled(bool(text))
        save.setEnabled(bool(text))

    def export():
        filename, _ = QFileDialog.getSaveFileName(
            window,
            "Save license",
            license_filename(project.text()),
            "All files (*)",
            options=QFileDialog.Option.DontConfirmOverwrite
            | QFileDialog.Option.DontUseNativeDialog,
        )
        if not filename:
            return

        def confirm():
            return (
                QMessageBox.question(
                    window,
                    "Overwrite file?",
                    "The file already exists.",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                )
                == QMessageBox.StandardButton.Yes
            )

        try:
            if write_license(Path(filename), text, confirm):
                status.setText("License saved.")
        except OSError as error:
            QMessageBox.critical(window, "Could not save the file", str(error))

    def persist():
        try:
            save_config(
                {
                    **config,
                    "license": selection.currentData(),
                    "author": holder.text().strip(),
                }
            )
            status.setText("Defaults saved for the CLI and GUI.")
        except OSError as error:
            QMessageBox.critical(window, "Could not save defaults", str(error))

    selection.currentIndexChanged.connect(refresh)
    holder.textChanged.connect(refresh)
    year.textChanged.connect(refresh)
    defaults.clicked.connect(persist)
    copy.clicked.connect(lambda: app.clipboard().setText(text))
    save.clicked.connect(export)
    refresh()
    window.show()
    return app.exec()
