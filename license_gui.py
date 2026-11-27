"""PyQt6 front end for the shared license generator."""

from pathlib import Path

from license_gen import (
    LICENSES,
    PERSONALIZED,
    VERSION,
    copyright_year,
    git_author,
    git_root,
    license_filename,
    license_key,
    render,
    save_config,
    write_license,
)


def run(config, project_name=""):
    try:
        from PyQt6.QtGui import QIcon
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
    app.setDesktopFileName("license-gen")
    app.setWindowIcon(QIcon(str(Path(__file__).with_name("license-gen.png"))))
    window = QWidget()
    window.setWindowTitle(f"License Generator v{VERSION}")
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
    year = QLineEdit()
    project = QLineEdit(project_name)
    project.setPlaceholderText("Optional")
    form.addRow("&Project name:", project)
    template_actions = QHBoxLayout()
    append = QPushButton("&Append license")
    replace = QPushButton("&Replace text")
    template_actions.addWidget(append)
    template_actions.addWidget(replace)
    form.addRow("&License template:", selection)
    form.addRow(template_actions)
    form.addRow("&Author / copyright holder:", holder)
    form.addRow("&Year:", year)
    directory = QLineEdit(str(Path.cwd()))
    browse = QPushButton("&Browse…")
    location = QHBoxLayout()
    location.addWidget(directory)
    location.addWidget(browse)
    filename = QLineEdit()
    destination = QLabel()
    destination.setWordWrap(True)
    form.addRow("&Save folder:", location)
    form.addRow("&File name:", filename)
    form.addRow("Target:", destination)
    status = QLabel()
    status.setWordWrap(True)
    layout.addWidget(status)
    preview = QPlainTextEdit()
    preview.setAccessibleName("License text")
    layout.addWidget(preview, 1)
    actions = QHBoxLayout()
    layout.addLayout(actions)
    defaults = QPushButton("Save as &default")
    copy = QPushButton("Cop&y")
    save = QPushButton("&Save…")
    for button in (defaults, copy, save):
        actions.addWidget(button)
    suggested_name = license_filename(project.text())
    loaded_key = selection.currentData()
    root = None
    folder = None
    target = None

    def update_actions():
        has_text = bool(preview.toPlainText().strip())
        copy.setEnabled(has_text)
        save.setEnabled(has_text and target is not None)

    def refresh(force=False):
        nonlocal loaded_key
        key = selection.currentData()
        if not force and (preview.document().isModified() or key != loaded_key):
            return
        try:
            text = render(key, holder.text(), year.text())
            status.setText(
                ""
                if key in PERSONALIZED
                else "Copyright fields do not change this template. Edit the text directly."
            )
        except (ValueError, OSError) as error:
            status.setText(str(error))
            if force:
                return
            text = ""
        loaded_key = key
        preview.setPlainText(text)
        preview.document().setModified(False)
        update_actions()

    def append_template():
        key = selection.currentData()
        try:
            text = render(key, holder.text(), year.text())
        except (ValueError, OSError) as error:
            status.setText(str(error))
            return
        cursor = preview.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        current = preview.toPlainText()
        trailing_newlines = len(current) - len(current.rstrip("\n"))
        separator = "\n" * max(0, 2 - trailing_newlines) if current else ""
        cursor.insertText(separator + text)
        preview.setTextCursor(cursor)
        preview.document().setModified(True)
        status.setText(
            f"Appended {LICENSES[key]}. Edit the text to explain how the licenses apply."
        )

    def replace_template():
        if preview.document().isModified() and preview.toPlainText().strip():
            answer = QMessageBox.question(
                window,
                "Replace license text?",
                "Replace the entire document with the selected template?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
        refresh(force=True)

    def update_target():
        nonlocal target
        name = filename.text().strip()
        target = None
        if root is not None:
            target = root / "LICENSE"
        elif folder is not None and name not in {"", ".", ".."} and "/" not in name:
            target = folder / name
        destination.setText(
            str(target) if target else "Choose a folder and a valid file name."
        )
        update_actions()

    def update_folder():
        nonlocal root, folder
        path = Path(directory.text().strip()).expanduser()
        folder = path.absolute() if directory.text().strip() and path.is_dir() else None
        root = git_root(folder) if folder is not None else None
        if folder is not None and not year.isModified():
            year.setText(copyright_year(folder))
        filename.setReadOnly(root is not None)
        filename.setText("LICENSE" if root is not None else suggested_name)
        update_target()

    def update_project():
        nonlocal suggested_name
        suggested_name = license_filename(project.text())
        if root is None:
            filename.setText(suggested_name)

    def browse_folder():
        selected = QFileDialog.getExistingDirectory(
            window, "Choose save folder", directory.text()
        )
        if selected:
            directory.setText(selected)
            update_folder()

    def export():
        # Recheck Git in case the working tree changed after the folder was selected.
        current_root = git_root(folder) if folder is not None else None
        if current_root != root:
            update_folder()
        if target is None:
            return
        text = preview.toPlainText().rstrip("\n") + "\n"

        def confirm():
            return (
                QMessageBox.question(
                    window,
                    "Overwrite file?",
                    f"Replace the existing file at {target}?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                )
                == QMessageBox.StandardButton.Yes
            )

        try:
            if write_license(target, text, confirm):
                status.setText(f"License saved to {target}.")
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

    append.clicked.connect(append_template)
    replace.clicked.connect(replace_template)
    holder.textChanged.connect(lambda: refresh())
    year.textChanged.connect(lambda: refresh())
    project.textChanged.connect(update_project)
    directory.editingFinished.connect(update_folder)
    browse.clicked.connect(browse_folder)
    filename.textChanged.connect(update_target)
    preview.textChanged.connect(update_actions)
    defaults.clicked.connect(persist)
    copy.clicked.connect(lambda: app.clipboard().setText(preview.toPlainText()))
    save.clicked.connect(export)
    update_folder()
    refresh()
    window.show()
    return app.exec()
