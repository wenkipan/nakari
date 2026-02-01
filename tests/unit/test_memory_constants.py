def test_memory_constants_exist() -> None:
    from memory.constants import ATOM_LABEL, LINK_REL_TYPE

    assert ATOM_LABEL == "Atom"
    assert LINK_REL_TYPE == "LINK"


def test_memory_constants_reexported_on_package() -> None:
    from memory import ATOM_LABEL, LINK_REL_TYPE

    assert ATOM_LABEL == "Atom"
    assert LINK_REL_TYPE == "LINK"
