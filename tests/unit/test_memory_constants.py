def test_memory_constants_exist() -> None:
    from memory.constants import ATOM_LABEL, LINK_REL_TYPE

    assert ATOM_LABEL == "Atom"
    assert LINK_REL_TYPE == "LINK"
