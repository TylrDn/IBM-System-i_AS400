import sys
import types
import pytest


def import_gui(monkeypatch, module_name):
    class DummyWidget:
        def __init__(self, *a, **k):
            raise NotImplementedError()

        def pack(self, *a, **k):
            raise NotImplementedError()

        def config(self, *a, **k):
             raise NotImplementedError()

        def configure(self, *a, **k):
             raise NotImplementedError()

    class DummyWindow(DummyWidget):
        def __init__(self):
            self.tk = object()

        def geometry(self, *a):
            raise NotImplementedError()

        def title(self, *a):
            raise NotImplementedError()

        def update_idletasks(self):
            raise NotImplementedError()

        def quit(self):
            raise NotImplementedError()

        def resizable(self, *a):
            raise NotImplementedError()

        def mainloop(self):
            raise NotImplementedError()

    monkeypatch.setattr(sys, "argv", [module_name])
    monkeypatch.setattr("tkinter.Tk", lambda: DummyWindow())
    monkeypatch.setattr("tkinter.Label", DummyWidget)
    monkeypatch.setattr("tkinter.Button", DummyWidget)
    monkeypatch.setattr("tkinter.ttk.Label", DummyWidget)
    monkeypatch.setattr("tkinter.ttk.Button", DummyWidget)
    monkeypatch.setattr("tkinter.ttk.Progressbar", DummyWidget)
    monkeypatch.setattr("tkinter.StringVar", lambda: types.SimpleNamespace(set=lambda *a, **k: None))
    monkeypatch.setattr("PIL.Image.open", lambda *a, **k: object())
    monkeypatch.setattr("PIL.ImageTk.PhotoImage", lambda *a, **k: object())
    __import__(module_name)
    return sys.modules[module_name]


@pytest.mark.parametrize("module_name,win_attr", [("payroll", "window"), ("src.payroll", "WindowFrame")])
def test_button_confirm_success(monkeypatch, module_name, win_attr):
    mod = import_gui(monkeypatch, module_name)
    monkeypatch.setattr(mod.time, "sleep", lambda s: None)
    monkeypatch.setattr(mod.Path, "is_file", lambda self: True)
    setattr(mod, win_attr, types.SimpleNamespace(update_idletasks=lambda: None, quit=lambda: None))
    mod.progress_bar = {"value": 0}
    mod.percent = types.SimpleNamespace(set=lambda *a, **k: None)
    mod.payroll_b = types.SimpleNamespace(main=lambda: 0)
    mod.button_confirm()
    assert mod.progress_bar["value"] == 100


@pytest.mark.parametrize("module_name,win_attr", [("payroll", "window"), ("src.payroll", "WindowFrame")])
def test_button_confirm_error(monkeypatch, module_name, win_attr):
    mod = import_gui(monkeypatch, module_name)
    monkeypatch.setattr(mod.time, "sleep", lambda s: None)
    monkeypatch.setattr(mod.Path, "is_file", lambda self: True)
    setattr(mod, win_attr, types.SimpleNamespace(update_idletasks=lambda: None, quit=lambda: None))
    mod.progress_bar = {"value": 0}
    mod.percent = types.SimpleNamespace(set=lambda *a, **k: None)
    mod.payroll_b = types.SimpleNamespace(main=lambda: 1)
    with pytest.raises(RuntimeError):
        mod.button_confirm()


@pytest.mark.parametrize("module_name,win_attr", [("payroll", "window"), ("src.payroll", "WindowFrame")])
def test_button_cancel(monkeypatch, module_name, win_attr):
    mod = import_gui(monkeypatch, module_name)
    called = {}
    setattr(mod, win_attr, types.SimpleNamespace(quit=lambda: called.setdefault("q", True)))
    mod.button_cancel()
    assert called.get("q")
