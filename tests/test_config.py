from ronin.config import get_profile


def test_all_profiles_validate():
    for name in ("tiny", "seed-0", "seed-1", "seed-2"):
        model, training = get_profile(name)
        model.validate()
        training.validate()


def test_unknown_profile_fails():
    try:
        get_profile("not-a-profile")
    except ValueError as exc:
        assert "perfil desconocido" in str(exc)
    else:
        raise AssertionError("unknown profile should fail")
