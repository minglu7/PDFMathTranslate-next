def test_plugin_loader_smoke():
    # Ensure plugin loader runs without crashing and returns an int
    from pdf2zh_next.translator import load_plugins

    count = load_plugins()
    assert isinstance(count, int)
    assert count >= 0


def test_plugin_doctor_smoke():
    # Ensure the doctor CLI logic runs and returns a status code
    from pdf2zh_next import plugin_doctor

    rc = plugin_doctor.doctor()
    # 0 = all ok or no plugins; 1 = some unmet deps
    assert rc in (0, 1)

