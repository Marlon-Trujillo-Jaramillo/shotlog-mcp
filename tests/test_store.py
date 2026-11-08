from shotlog_mcp.store import Store, slugify


def test_slugify():
    assert slugify("act 1/ssh?") == "act_1_ssh_"
    assert slugify("") == "shot"


def test_numbering_never_reuses_after_delete(tmp_path):
    s = Store(tmp_path)
    for name in ("a", "b", "c"):
        p = s.next_path(name)
        p.write_bytes(b"x")
        s.register(p, "test")
    (tmp_path / "002_b.png").unlink()
    assert s.next_path("d").name == "004_d.png"


def test_corrupt_manifest_is_backed_up(tmp_path):
    s = Store(tmp_path)
    s.manifest.write_text("{not json")
    assert s.load() == []
    assert list(tmp_path.glob("manifest.corrupt-*.json"))


def test_update_and_export(tmp_path):
    s = Store(tmp_path)
    p = s.next_path("x")
    p.write_bytes(b"x")
    s.register(p, "test")
    e = s.update(p.name, activity="Install", command="ssh -V", result="")
    assert e["activity"] == "Install" and e["result"] == ""
    assert s.update("missing.png", activity="z") is None
    md = s.export_markdown("Lab").read_text()
    assert "## Install" in md and "ssh -V" in md and f"]({p.name})" in md
